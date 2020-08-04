from datetime import datetime
from bluvo_lib import login, APIgetStatus, APIgetLocation
from generic_lib import SendABRPtelemetry, distance
import logging


def processData(carstatus, location):
    try:
        #logging.info("enter procesdata")
        global homelocation, abrp_carmodel, abrp_token, WeatherApiKey, WeatherProvider
        heading = location['head']
        speed = location['speed']['value']
        rangeleft = carstatus['evStatus']['drvDistance'][0]['rangeByFuel']['totalAvailableRange']['value']
        soc = carstatus['evStatus']['batteryStatus']
        charging = carstatus['evStatus']['batteryCharge']
        trunkopen = carstatus['trunkOpen']
        doorlock = carstatus['doorLock']
        driverdooropen = carstatus['doorOpen']['frontLeft']
        soc12v = carstatus['battery']['batSoc']
        status12v = carstatus['battery']['batState']
        latitude = location['coord']['lat']
        longitude = location['coord']['lon']
        #logging.info("about to do something with home location %s", homelocation)
        loc = homelocation.split(";")
        homelat = float(loc[0])
        homelon = float(loc[1])
        #logging.info("about to calculate distance to home location %s", homelocation)
        afstand = round(distance(latitude, longitude, float(homelat), float(homelon)), 1)
        googlelocation = '<a href="http://www.google.com/maps/search/?api=1&query=' + str(latitude) + ',' + str(
            longitude) + '">eNiro - Afstand van huis</a>'
        #logging.info("link to google maps %s", googlelocation)
        try:
            #logging.info("about to send info to ABRP")
            SendABRPtelemetry(soc, speed, latitude, longitude, charging, abrp_carmodel, abrp_token, WeatherApiKey,
                              WeatherProvider)
            #logging.info("i sent info to ABRP")
        except: logging.info("something went wrong in ABRP procedure")
    except: logging.info("something went wrong in process data procedure")
    return afstand, heading, speed, googlelocation, rangeleft, soc, charging, trunkopen, doorlock, driverdooropen, soc12v, status12v


def initialise(p_email, p_password, p_pin, p_abrp_token, p_abrp_carmodel, p_WeatherApiKey, p_WeatherProvider,
               p_homelocation, p_forcepollinterval):
    global email, password, pin, abrp_token, abrp_carmodel, WeatherApiKey, WeatherProvider, homelocation, forcepollinterval
    # p_parameters are fed into global variables
    email = p_email
    password = p_password
    pin = p_pin
    abrp_token = p_abrp_token
    abrp_carmodel = p_abrp_carmodel
    WeatherApiKey = p_WeatherApiKey
    WeatherProvider = p_WeatherProvider
    homelocation = p_homelocation
    forcepollinterval = p_forcepollinterval

    global oldstatustime, oldpolltime
    oldstatustime = ""
    oldpolltime = ""
    car_brand = (abrp_carmodel.split(":", 1)[0])
    try:
        login(car_brand, email, password, pin)
        return True
    except:
        logging.info("Login Failed")
        return False


def pollcar(phoneincarflag):
    global oldstatustime, oldpolltime, forcepollinterval
    # TODO find a way to have better poll/refresh intervals
    updated = False
    afstand = heading = speed = odometer = googlelocation = rangeleft = soc = charging = trunkopen = doorlock = driverdooropen = soc12v = status12v = 0
    try:
        #logging.info('entering poll loop at %s', datetime.now())
        carstatus = APIgetStatus(False)
        odometer = carstatus['vehicleStatusInfo']['odometer']['value']
        location = carstatus['vehicleStatusInfo']['vehicleLocation']
        carstatus = carstatus['vehicleStatusInfo']['vehicleStatus']
        # use the vehicle status to determine stuff and shorten script
        if oldstatustime != carstatus['time']:
            oldstatustime = carstatus['time']
            logging.info('got a new timestamp of cache data %s, about to process it', oldstatustime)
            afstand, heading, speed, googlelocation, rangeleft, soc, charging, trunkopen, doorlock, driverdooropen, soc12v, status12v = processData(carstatus, location)
            updated = True
        try:
            sleepmodecheck = carstatus['sleepModeCheck']
        except KeyError:
            sleepmodecheck = False  # sleep mode check is not there...

        # at minimum every interval minutes a true poll
        try:
            if oldpolltime == '':
                forcedpolltimer = True
            else:
                forcedpolltimer = (
                            float((datetime.now() - oldpolltime).total_seconds()) > 60 * float(forcepollinterval))
        except:
            forcedpolltimer = False

        if sleepmodecheck or forcedpolltimer or phoneincarflag or carstatus['engine'] or (not (carstatus['doorLock'])) or carstatus['trunkOpen'] or carstatus['evStatus']['batteryCharge']:
            strings = ["sleepmodecheck", "forcedpolltimer", "phoneincarflag", "engine", 'doorLock','trunkOpen', 'charging']
            conditions = [sleepmodecheck,forcedpolltimer, phoneincarflag, carstatus['engine'], (not (carstatus['doorLock'])),
                         carstatus['trunkOpen'], carstatus['evStatus']['batteryCharge']]
            truecond = ''
            for i in range(len(strings)):
                if (conditions[i]==True): truecond = truecond + " " + strings[i]
            logging.info("at %s conditions for a reload were true %s", datetime.now(), truecond)

            APIgetStatus(True)  # get it and process it immediately
            carstatus = APIgetStatus(False)
            odometer = carstatus['vehicleStatusInfo']['odometer']['value']
            carstatus = carstatus['vehicleStatusInfo']['vehicleStatus']
            logging.info('got a fresh carstatus')

            freshlocation = APIgetLocation()
            freshlocation = freshlocation['gpsDetail']
            logging.info('got a fresh location')

            oldpolltime = datetime.now()
            oldstatustime = carstatus['time']
            updated = True
            #logging.info('about to enter process data')
            afstand, heading, speed, googlelocation, rangeleft, soc, charging, trunkopen, doorlock, driverdooropen, soc12v, status12v = processData(carstatus, freshlocation)
            #logging.info('exited process data')
            # process entire cachestring after timestamp is updated
            # TODO if the Engine is running then phone in carflag can be set to False, else leave unchanged
            if carstatus['engine'] == True:
                #logging.info('since engine is running, turn off the phone in car flag')
                phoneincarflag = False
            if not (location['coord'] == freshlocation['coord']):
                logging.info('%s location when entering worker ',location['coord'])
                logging.info('%s locatie after location-refresh-call ', freshlocation['coord'])
    except:
        return phoneincarflag, False, 0, 0, 0, 0, "error!", 0, 0, 0, 0, 0, 0, 0, 0

    return phoneincarflag, updated, afstand, heading, speed, odometer, googlelocation, rangeleft, soc, charging, trunkopen, doorlock, driverdooropen, soc12v, status12v
