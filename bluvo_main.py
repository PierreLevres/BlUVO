from datetime import datetime
from bluvo_lib import hex2temp, temp2hex, login, api_get_status, api_get_location, api_set_lock, api_set_HVAC, api_set_charge
from generic_lib import SendABRPtelemetry, distance
import logging


def process_data(carstatus, location, odometer):
    #this procedure does a few things
    # generate pretty data == parsed status
    # calculate distance from home
    # create a Google Maps link for location
    # send data to ABRP
    afstand = 0
    googlelocation = ""
    try:
        logging.debug("enter procesdata")
        global homelocation, abrp_carmodel, abrp_token, WeatherApiKey, WeatherProvider
        parsedstatus = {
            'hoodopen': carstatus['hoodOpen'],
            'trunkopen': carstatus['trunkOpen'],
            'locked': carstatus['doorLock'],
            'dooropenFL': carstatus['doorOpen']['frontLeft'],
            'dooropenFR': carstatus['doorOpen']['frontRight'],
            'dooropenRL': carstatus['doorOpen']['backLeft'],
            'dooropenRR': carstatus['doorOpen']['backRight'],
            'dooropenANY': carstatus['doorOpen']['frontLeft'] or carstatus['doorOpen']['backLeft'] or carstatus['doorOpen']['backRight'] or carstatus['doorOpen']['frontRight'],
            'tirewarningFL' : carstatus['tirePressureLamp']['tirePressureLampFL'],
            'tirewarningFR' : carstatus['tirePressureLamp']['tirePressureLampFR'],
            'tirewarningRL' : carstatus['tirePressureLamp']['tirePressureLampRL'],
            'tirewarningRR' : carstatus['tirePressureLamp']['tirePressureLampRR'],
            'tirewarningall' : carstatus['tirePressureLamp']['tirePressureLampAll'],
            'climateactive': carstatus['airCtrlOn'],
            'steerwheelheat': carstatus['steerWheelHeat'],
            'rearwindowheat': carstatus['sideBackWindowHeat'],
            'temperature': hex2temp(carstatus['airTemp']['value']),
            'defrost': carstatus['defrost'],
            'engine': carstatus['engine'],
            'acc': carstatus['acc'],
            'range' : carstatus['evStatus']['drvDistance'][0]['rangeByFuel']['totalAvailableRange']['value'],
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
            'time' : carstatus['time']
        }
        loc = homelocation.split(";")
        homelat = float(loc[0])
        homelon = float(loc[1])
        afstand = round(distance(parsedstatus['loclat'], parsedstatus['loclon'], float(homelat), float(homelon)), 1)
        googlelocation = '<a href="http://www.google.com/maps/search/?api=1&query=' + str(parsedstatus['loclat']) + ',' + str(
            parsedstatus['loclon']) + '">eNiro - Afstand van huis</a>'
        SendABRPtelemetry(parsedstatus['chargeHV'], parsedstatus['speed'], parsedstatus['loclat'], parsedstatus['loclon'], parsedstatus['charging'],
                          abrp_carmodel, abrp_token, WeatherApiKey,WeatherProvider)
    except:
        logging.error("something went wrong in process data procedure")
    return parsedstatus, afstand, googlelocation


def initialise(p_email, p_password, p_pin, p_vin, p_abrp_token, p_abrp_carmodel, p_WeatherApiKey, p_WeatherProvider,
               p_homelocation, p_forcepollinterval, p_charginginterval, p_heartbeatinterval):
    global email, password, pin, vin, abrp_token, abrp_carmodel, WeatherApiKey, WeatherProvider, homelocation, forcepollinterval, charginginterval, heartbeatinterval
    # p_parameters are fed into global variables
    email = p_email
    password = p_password
    pin = p_pin
    vin = p_vin
    abrp_token = p_abrp_token
    abrp_carmodel = p_abrp_carmodel
    WeatherApiKey = p_WeatherApiKey
    WeatherProvider = p_WeatherProvider
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
    return login(car_brand, email, password, pin, vin)


def pollcar(phoneincarflag):
    # get statusses from car; either cache or refreshed
    # return as [updated,[carstatus],[odometer],[location]]
    # return False if it fails (behaves as if info did not change)
    global oldstatustime, oldpolltime, forcepollinterval, charginginterval
    updated = False
    BP = ""  # breakpoint
    afstand = heading = speed = odometer = googlelocation = rangeleft = soc = charging = trunkopen = doorlock = driverdooropen = soc12v = status12v = 0
    logging.debug('entering poll procedure')
    try:
        carstatus = api_get_status(False)
        if carstatus == False: return False
        odometer = carstatus['vehicleStatusInfo']['odometer']['value']
        location = carstatus['vehicleStatusInfo']['vehicleLocation']
        carstatus = carstatus['vehicleStatusInfo']['vehicleStatus']
        logging.debug('information in cache when entering pollloop: engine: %s; trunk: %s; doorunlock %s; charging %s; odometer %s; location %s', carstatus['engine'], carstatus['trunkOpen'], not(carstatus['doorLock']),carstatus['evStatus']['batteryCharge'], odometer, location['coord'])
        # use the vehicle status to determine stuff and shorten script
        if oldstatustime != carstatus['time']:
            logging.debug('new timestamp of cache data (was %s now %s), about to process it', oldstatustime, carstatus['time'])
            parsedStatus, afstand, googlelocation = process_data(carstatus, location, odometer)
            oldstatustime = carstatus['time']
            updated = True
        try: sleepmodecheck = carstatus['sleepModeCheck']
        except KeyError: sleepmodecheck = False  # sleep mode check is not there...

        # at minimum every interval minutes a true poll
        if oldpolltime == '': forcedpolltimer = True #first run
        else:
            forcedpolltimer = (float((datetime.now() - oldpolltime).total_seconds()) >= forcepollinterval)
            if (not forcedpolltimer) and carstatus['evStatus']['batteryCharge']:
                forcedpolltimer = (float((datetime.now() - oldpolltime).total_seconds()) >= charginginterval)

        BP = "Before checking refresh conditions"
        if sleepmodecheck or forcedpolltimer or phoneincarflag or carstatus['engine'] or carstatus['evStatus']['batteryCharge']:
            strings = ["sleepmodecheck", "forcedpolltimer", "phoneincarflag", "engine", 'charging']
            conditions = [sleepmodecheck,forcedpolltimer, phoneincarflag, carstatus['engine'], carstatus['evStatus']['batteryCharge']]
            truecond = ''
            for i in range(len(strings)):
                if conditions[i]: truecond += (" " + strings[i])
            logging.info("these conditions for a reload were true:%s", truecond)
            carstatus = api_get_status(True)
            if carstatus == False: return False
            logging.debug('information after refresh engine: %s; trunk: %s; doorunlock %s; charging %s',carstatus['engine'],carstatus['trunkOpen'],not(carstatus['doorLock']),carstatus['evStatus']['batteryCharge'])
            carstatus = api_get_status(False)
            if carstatus == False: return False
            freshodometer = carstatus['vehicleStatusInfo']['odometer']['value']
            carstatus = carstatus['vehicleStatusInfo']['vehicleStatus']
            logging.debug('information in cache ==> engine: %s; trunk: %s; doorunlock %s; charging %s; odometer %s',carstatus['engine'],carstatus['trunkOpen'],not(carstatus['doorLock']),carstatus['evStatus']['batteryCharge'],freshodometer)
            # when engine is running or odometer changed ask for a location update
            logging.debug( "odometer before refresh %s and after %s", odometer, freshodometer)
            if carstatus['engine'] or (freshodometer != odometer):
                freshlocation = api_get_location()
                if  freshlocation != False:
                    freshlocation = freshlocation['gpsDetail']
                    logging.debug('location before refresh %s and after %s',location['coord'],freshlocation['coord'])
                    location = freshlocation
            odometer = freshodometer
            oldpolltime = datetime.now()
            oldstatustime = carstatus['time']
            updated = True
            # logging.debug("entering worker with location %s and status %s", freshlocation, carstatus)
            parsedStatus, afstand, googlelocation = process_data(carstatus, location, odometer)
            # process entire cachestring after timestamp is updated
            if carstatus['engine'] :
                logging.debug('since engine is running, turn off the phone in car flag')
                phoneincarflag = False
            #TODO if phoneincarflag is active for longer than 5 minutes, something must be wrong, reset it. May also be implemented as a counter from 10 to 0
    except:
        logging.error('error in poll procedure, breakpoint: %s',BP)
        oldpolltime = datetime.now()
        return phoneincarflag, False, parsedStatus, afstand, googlelocation
    return phoneincarflag, updated, parsedStatus, afstand, googlelocation


#todo make object oriented