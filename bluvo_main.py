from datetime import datetime
from bluvo_lib import hex2temp, temp2hex, login, api_get_status, api_get_location, api_set_lock, api_set_hvac, api_set_charge
from generic_lib import send_abr_ptelemetry, distance
import logging
import random
# todo make object oriented
global email, password, pin, vin, abrp_token, abrp_carmodel, WeatherApiKey, WeatherProvider, homelocation, forcepollinterval, charginginterval
global oldstatustime, oldpolltime
global pollcounter


def process_data(carstatus, location, odometer):
    # this procedure does a few things
    # generate pretty data == parsed status
    # calculate distance from home
    # create a Google Maps link for location
    # send data to ABRP
    afstand = 0
    googlelocation = ""
    parsedstatus = {}
    try:
        parsedstatus = {
            'hoodopen': carstatus['hoodOpen'],
            'trunkopen': carstatus['trunkOpen'],
            'locked': carstatus['doorLock'],
            'dooropenFL': carstatus['doorOpen']['frontLeft'],
            'dooropenFR': carstatus['doorOpen']['frontRight'],
            'dooropenRL': carstatus['doorOpen']['backLeft'],
            'dooropenRR': carstatus['doorOpen']['backRight'],
            'dooropenANY': (carstatus['doorOpen']['frontLeft'] or carstatus['doorOpen']['backLeft'] or carstatus['doorOpen']['backRight'] or carstatus['doorOpen']['frontRight']),
            'tirewarningFL': carstatus['tirePressureLamp']['tirePressureLampFL'],
            'tirewarningFR': carstatus['tirePressureLamp']['tirePressureLampFR'],
            'tirewarningRL': carstatus['tirePressureLamp']['tirePressureLampRL'],
            'tirewarningRR': carstatus['tirePressureLamp']['tirePressureLampRR'],
            'tirewarningall': carstatus['tirePressureLamp']['tirePressureLampAll'],
            'climateactive': carstatus['airCtrlOn'],
            'steerwheelheat': carstatus['steerWheelHeat'],
            'rearwindowheat': carstatus['sideBackWindowHeat'],
            'temperature': hex2temp(carstatus['airTemp']['value']),
            'defrost': carstatus['defrost'],
            'engine': carstatus['engine'],
            'acc': carstatus['acc'],
            'range': carstatus['evStatus']['drvDistance'][0]['rangeByFuel']['totalAvailableRange']['value'],
            'charge12V': carstatus['battery']['batSoc'],
            'status12V': carstatus['battery']['batState'],
            'charging': carstatus['evStatus']['batteryCharge'],
            'chargeHV': carstatus['evStatus']['batteryStatus'],
            'pluggedin': carstatus['evStatus']['batteryPlugin'],
            'heading': location['head'],
            'speed': location['speed']['value'],
            'loclat': location['coord']['lat'],
            'loclon': location['coord']['lon'],
            'odometer': odometer,
            'time': carstatus['time'],
            'chargingTime': carstatus['evStatus']['remainTime2']['atc'] ['value']
        }
        loc = homelocation.split(";")
        homelat = float(loc[0])
        homelon = float(loc[1])
        afstand = round(distance(parsedstatus['loclat'], parsedstatus['loclon'], float(homelat), float(homelon)), 1)
        googlelocation = 'href="http://www.google.com/maps/search/?api=1&query=' + str(parsedstatus['loclat']) + ',' + str(
            parsedstatus['loclon']) + '">'
        send_abr_ptelemetry(parsedstatus['chargeHV'], parsedstatus['speed'], parsedstatus['loclat'], parsedstatus['loclon'], parsedstatus['charging'],
                            abrp_carmodel, abrp_token, WeatherApiKey, WeatherProvider)
    except:
        logging.error("something went wrong in process data procedure")
    return parsedstatus, afstand, googlelocation


def initialise(p_email, p_password, p_pin, p_vin, p_abrp_token, p_abrp_carmodel, p_weather_api_key, p_weather_provider,
               p_homelocation, p_forcepollinterval, p_charginginterval, p_heartbeatinterval):
    global email, password, pin, vin, abrp_token, abrp_carmodel, WeatherApiKey, WeatherProvider, homelocation, forcepollinterval, charginginterval
    global pollcounter
    # heartbeatinterval
    # p_parameters are fed into global variables
    logging.debug("into Initialise")
    email = p_email
    password = p_password
    vin = p_vin
    pin = ('0000' + (str(p_pin) if isinstance(p_pin, int) else p_pin))[-4:]
    abrp_token = p_abrp_token
    abrp_carmodel = p_abrp_carmodel
    WeatherApiKey = p_weather_api_key
    WeatherProvider = p_weather_provider
    homelocation = p_homelocation
    if p_forcepollinterval == "":
        forcepollinterval = float(60*60)
    else:
        forcepollinterval = float(p_forcepollinterval)*60
    if p_charginginterval == "":
        charginginterval = float(forcepollinterval) / 4
    else:
        charginginterval = float(p_charginginterval) * 60
    if p_heartbeatinterval == "":
        heartbeatinterval = float(120)
    else:
        heartbeatinterval = float(p_heartbeatinterval) * 60
    logging.debug("forcedpoll: %s, charging: %s, heartbeat %s", forcepollinterval, charginginterval, heartbeatinterval)
    global oldstatustime, oldpolltime
    oldstatustime = ""
    oldpolltime = ""
    car_brand = (abrp_carmodel.split(":", 1)[0])
    pollcounter = 7
    return heartbeatinterval, login(car_brand, email, password, pin, vin)


def pollcar(manualForcePoll):
    # get statusses from car; either cache or refreshed
    # return as [updated,[carstatus],[odometer],[location]]
    # return False if it fails (behaves as if info did not change)
    global oldstatustime, oldpolltime, forcepollinterval, charginginterval, pollcounter
    # reset pollcounter at start of day
    break_point = "start poll procedure"  # breakpoint
    carstatus = "empty car status"
    if oldpolltime == "": pollcounter = 0
    else:
        if oldpolltime.date() != datetime.now().date(): pollcounter = 0
    parsed_status = {}
    updated = False
    afstand = 0
    googlelocation = ''
    try:
        pollcounter += 1
        carstatus = api_get_status(False)
        break_point = "got status"
        if carstatus is not False:
            logging.debug('carstatus in cache %s', carstatus)
            odometer = carstatus['vehicleStatusInfo']['odometer']['value']
            location = carstatus['vehicleStatusInfo']['vehicleLocation']
            carstatus = carstatus['vehicleStatusInfo']['vehicleStatus']
            # use the vehicle status to determine stuff and shorten script
            if oldstatustime != carstatus['time']:
                logging.debug('new timestamp of cache data (was %s now %s), about to process it', oldstatustime, carstatus['time'])
                parsed_status, afstand, googlelocation = process_data(carstatus, location, odometer)
                oldstatustime = carstatus['time']
                updated = True
            else:
                logging.debug("oldstatustime == carstatus['time']")
            try: sleepmodecheck = carstatus['sleepModeCheck']
            except KeyError: sleepmodecheck = False  # sleep mode check is not there...
            # at minimum every interval minutes a true poll
            forcedpolltimer = False
            if oldpolltime == '': forcedpolltimer = True  # first run
            else:
                if (float((datetime.now() - oldpolltime).total_seconds()) >= random.uniform(0.75, 1.5)*forcepollinterval): forcedpolltimer = True
                else:
                    if carstatus['evStatus']['batteryCharge']:
                        if (float((datetime.now() - oldpolltime).total_seconds()) >= random.uniform(0.75, 1.5)*charginginterval): forcedpolltimer = True

            break_point = "Before checking refresh conditions"
            if sleepmodecheck or forcedpolltimer or manualForcePoll or carstatus['engine']:
                strings = ["sleepmodecheck", "forcedpolltimer", "manualForcePoll", "engine", 'charging']
                conditions = [sleepmodecheck, forcedpolltimer, manualForcePoll, carstatus['engine'], carstatus['evStatus']['batteryCharge']]
                truecond = ''
                for i in range(len(strings)):
                    if conditions[i]: truecond += (" " + strings[i])
                logging.info("these conditions for a reload were true:%s", truecond)
                pollcounter += 1
                carstatus = api_get_status(True)

                if carstatus is not False:
                    logging.debug('information after refresh engine: %s; trunk: %s; doorunlock %s; charging %s',
                                  carstatus['engine'], carstatus['trunkOpen'], not(carstatus['doorLock']), carstatus['evStatus']['batteryCharge'])
                    pollcounter += 1
                    carstatus = api_get_status(False)

                    if carstatus is not False:

                        freshodometer = carstatus['vehicleStatusInfo']['odometer']['value']
                        carstatus = carstatus['vehicleStatusInfo']['vehicleStatus']
                        logging.debug('information in cache ==> engine: %s; trunk: %s; doorunlock %s; charging %s; odometer %s',
                                      carstatus['engine'], carstatus['trunkOpen'], not(carstatus['doorLock']), carstatus['evStatus']['batteryCharge'], freshodometer)
                        # when car is moging (engine is running or odometer changed) ask for a location update
                        logging.debug("odometer before refresh %s and after %s", odometer, freshodometer)
                        if carstatus['engine'] or (freshodometer != odometer):
                            pollcounter += 1
                            freshlocation = api_get_location()

                            if freshlocation is not False:
                                freshlocation = freshlocation['gpsDetail']
                                logging.debug('location before refresh %s and after %s', location['coord'], freshlocation['coord'])
                                location = freshlocation
                        odometer = freshodometer
                        oldpolltime = datetime.now()
                        oldstatustime = carstatus['time']
                        updated = True
                        # logging.debug("entering worker with location %s and status %s", freshlocation, carstatus)
                        parsed_status, afstand, googlelocation = process_data(carstatus, location, odometer)
        else:
            logging.debug("carstatus is False")
    except:
        oldpolltime = datetime.now()
        logging.error('error in poll procedure, breakpoint: %s', break_point)
        logging.error('carstatus: %s', carstatus)
    logging.debug('pollcount: %s', pollcounter)
    return updated, parsed_status, afstand, googlelocation


def setcharge(command):
    return api_set_charge(command)


def lockdoors(command):
    return api_set_lock(command)


def setairco(action, temp):
    return api_set_hvac(action, temp, False, False)
