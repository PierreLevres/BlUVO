from datetime import datetime
from bluvo_lib import login, APIgetStatus, APIgetLocation
from generic_lib import SendABRPtelemetry, distance
import logging


def processData(carstatus, location):
    try:
        logging.debug("enter procesdata")
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
        logging.debug("about to do something with home location %s", homelocation)
        loc = homelocation.split(";")
        homelat = float(loc[0])
        homelon = float(loc[1])
        logging.debug("about to calculate distance to home location %s", homelocation)
        afstand = round(distance(latitude, longitude, float(homelat), float(homelon)), 1)
        googlelocation = '<a href="http://www.google.com/maps/search/?api=1&query=' + str(latitude) + ',' + str(
            longitude) + '">eNiro - Afstand van huis</a>'
        logging.debug("link to google maps %s", googlelocation)
        try:
            logging.debug("about to send info to ABRP")
            SendABRPtelemetry(soc, speed, latitude, longitude, charging, abrp_carmodel, abrp_token, WeatherApiKey,
                              WeatherProvider)
            logging.debug("i sent info to ABRP")
        except: logging.error("something went wrong in ABRP procedure")
    except: logging.error("something went wrong in process data procedure")
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
        logging.error("Login Failed")
        return False


def pollcar(phoneincarflag):
    global oldstatustime, oldpolltime, forcepollinterval
    # TODO find a way to have better poll/refresh intervals
    updated = False
    afstand = heading = speed = odometer = googlelocation = rangeleft = soc = charging = trunkopen = doorlock = driverdooropen = soc12v = status12v = 0
    try:
        logging.debug('entering poll loop')
        carstatus = APIgetStatus(False)
        odometer = carstatus['vehicleStatusInfo']['odometer']['value']
        location = carstatus['vehicleStatusInfo']['vehicleLocation']
        carstatus = carstatus['vehicleStatusInfo']['vehicleStatus']
        logging.debug('information in cache when entering pollloop: engine: %s; trunk: %s; doorunlock %s; charging %s; odometer %s; location %s', carstatus['engine'], carstatus['trunkOpen'], carstatus['doorLock'],carstatus['evStatus']['batteryCharge'], odometer, location['coord'])
        # use the vehicle status to determine stuff and shorten script
        if oldstatustime != carstatus['time']:
            logging.debug('new timestamp of cache data (was %s now %s), about to process it', oldstatustime, carstatus['time'])
            oldstatustime = carstatus['time']
            afstand, heading, speed, googlelocation, rangeleft, soc, charging, trunkopen, doorlock, driverdooropen, soc12v, status12v = processData(carstatus, location)
            updated = True

        try:
            sleepmodecheck = carstatus['sleepModeCheck']
            #sleepmodecheck = False  #omit this, there is no use in polling if the engine is off...
        except KeyError:
            sleepmodecheck = False  # sleep mode check is not there...

        # at minimum every interval minutes a true poll
        try:
            forcedpolltimer = True if oldpolltime == '' else (float((datetime.now() - oldpolltime).total_seconds()) > 60 * float(forcepollinterval))
        except:
            forcedpolltimer = False

        if sleepmodecheck or forcedpolltimer or phoneincarflag or carstatus['engine'] or (not (carstatus['doorLock'])) or carstatus['trunkOpen'] or carstatus['evStatus']['batteryCharge']:
            strings = ["sleepmodecheck", "forcedpolltimer", "phoneincarflag", "engine", 'doorunLock','trunkOpen', 'charging']
            conditions = [sleepmodecheck,forcedpolltimer, phoneincarflag, carstatus['engine'], (not (carstatus['doorLock'])),
                         carstatus['trunkOpen'], carstatus['evStatus']['batteryCharge']]
            truecond = ''
            for i in range(len(strings)):
                if (conditions[i]==True): truecond = truecond + " " + strings[i]
            logging.info("conditions for a reload were true %s", truecond)

            APIgetStatus(True)  # get it and process it immediately
            logging.debug('information after refresh engine: %s; trunk: %s; doorunlock %s; charging %s',carstatus['engine'],carstatus['trunkOpen'],carstatus['doorLock'],carstatus['evStatus']['batteryCharge'])
            carstatus = APIgetStatus(False)
            freshodometer = carstatus['vehicleStatusInfo']['odometer']['value']
            carstatus = carstatus['vehicleStatusInfo']['vehicleStatus']
            logging.info('information in cache ==> engine: %s; trunk: %s; doorlock %s; charging %s; odometer %s',carstatus['engine'],carstatus['trunkOpen'],carstatus['doorLock'],carstatus['evStatus']['batteryCharge'],freshodometer)
            # when enging is running or odometer changed ask for a location update
            logging.info( "odometer before refresh %s and after %s", odometer, freshodometer)
            if carstatus['engine'] or (freshodometer != odometer):
                freshlocation = APIgetLocation()
                freshlocation = freshlocation['gpsDetail']
                logging.info('got a fresh location %s',freshlocation['coord'])
            else:
                freshlocation = location
            odometer = freshodometer
            oldpolltime = datetime.now()
            oldstatustime = carstatus['time']
            updated = True
            logging.debug('about to enter process data')
            afstand, heading, speed, googlelocation, rangeleft, soc, charging, trunkopen, doorlock, driverdooropen, soc12v, status12v = processData(carstatus, freshlocation)
            logging.debug('exited process data')
            # process entire cachestring after timestamp is updated
            if carstatus['engine'] == True:
                logging.debug('since engine is running, turn off the phone in car flag')
                phoneincarflag = False
    except:
        logging.error('error opgetreden')
        return phoneincarflag, False, 0, 0, 0, 0, "error!", 0, 0, 0, 0, 0, 0, 0, 0

    return phoneincarflag, updated, afstand, heading, speed, odometer, googlelocation, rangeleft, soc, charging, trunkopen, doorlock, driverdooropen, soc12v, status12v
