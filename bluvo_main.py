from datetime import datetime
from bluvo_lib import login, APIgetStatus, APIgetOdometer, APIgetLocation
from generic_lib import SendABRPtelemetry, distance
import logging
import requests, json
#import Domoticz

def processData(carstatus, odometer, location):
    global homelocation, abrp_carmodel, abrp_token, WeatherApiKey, WeatherProvider
    location = location['gpsDetail']
    carstatus = carstatus['vehicleStatusInfo']['vehicleStatus']
    timestamp = carstatus['time']
    heading= location['head']
    speed = location['speed']['value']
    rangeleft  = carstatus['evStatus']['drvDistance'][0]['rangeByFuel']['totalAvailableRange']['value']
    soc = carstatus['evStatus']['batteryStatus']
    charging = carstatus['evStatus']['batteryCharge']
    trunkopen = carstatus['trunkOpen']
    doorlock = carstatus['doorLock']
    driverdooropen = carstatus['doorOpen']['frontLeft']
    soc12v = carstatus['battery']['batSoc']
    status12v = carstatus['battery']['batState']
    latitude = location['coord']['lat']
    longitude = location['coord']['lon']
    loc = homelocation.split(";")
    homelat = float(loc[0])
    homelon = float(loc[1])
    afstand = round(distance(latitude, longitude, float(homelat), float(homelon)), 1)
    googlelocation='<a href="http://www.google.com/maps/search/?api=1&query='+str(latitude)+','+str(longitude)+'">eNiro - Afstand van huis</a>'
    try:
        SendABRPtelemetry(soc, speed, latitude, longitude, charging, abrp_carmodel, abrp_token, WeatherApiKey, WeatherProvider)
    except: print('error in ABRP')
    return(afstand,heading,speed,odometer,googlelocation,rangeleft,soc,charging,trunkopen,doorlock,driverdooropen,soc12v,status12v)

def initialise(p_email, p_password, p_pin, p_abrp_token,p_abrp_carmodel, p_WeatherApiKey, p_WeatherProvider, p_homelocation, p_URLphoneincar, p_forcepollinterval):
    global email, password, pin, abrp_token, abrp_carmodel, WeatherApiKey, WeatherProvider, homelocation, URLphoneincar, forcepollinterval
    # p_parameters are fed into global variables
    email = p_email
    password = p_password
    pin = p_pin
    abrp_token = p_abrp_token
    abrp_carmodel = p_abrp_carmodel
    WeatherApiKey = p_WeatherApiKey
    WeatherProvider = p_WeatherProvider
    homelocation = p_homelocation
    URLphoneincar = p_URLphoneincar
    forcepollinterval = p_forcepollinterval

    global oldstatustime, oldpolltime
    oldstatustime = ""
    oldpolltime=""
    car_brand = (abrp_carmodel.split(":", 1)[0])
    login(car_brand, email, password, pin)
    logging.info('logged in %s',email)

def pollcar():
    global oldstatustime, oldpolltime, forcepollinterval
    # TODO find a way to have better poll/refresh intervals
    updated = False
    afstand= heading= speed= odometer= googlelocation= rangeleft= soc= charging= trunkopen=doorlock=driverdooropen=soc12v=status12v =0
    try:
        carstatus = APIgetStatus(False)
        odometer = APIgetOdometer()
        location = APIgetLocation()
        updated = False
        if oldstatustime != carstatus['vehicleStatusInfo']['vehicleStatus']['time']:
            oldstatustime = carstatus['vehicleStatusInfo']['vehicleStatus']['time']
            afstand,heading,speed,odometer,googlelocation,rangeleft,soc,charging,trunkopen,doorlock,driverdooropen,soc12v,status12v=processData(carstatus,odometer,location)  # process entire cachestring after timestamp is updated
            updated = True
        carstatus = carstatus['vehicleStatusInfo']['vehicleStatus'] #use the vehicle status to determine stuff and shorten script
        try:
            sleepmodecheck = carstatus['sleepModeCheck']
            logging.info('sleepmodecheck exists and its value = %s',sleepmodecheck)
        except KeyError:
            sleepmodecheck = False #sleep mode check is not there...
        try: #read flag of phone in car from domoticz, move a bit further since this is a call to domoticz it is slower
            if URLphoneincar == "":
                phoneincarflag = Devices[9].sValue
            else:
                session = requests.Session()
                response= session.get(URLphoneincar)
                response=json.loads(response.text)
                phoneincarflag = response['result'][0]['Status'] == 'On'
        except:
                phoneincarflag = False

        # at minimum every interval minutes a true poll
        if oldpolltime =='': forcedpolltimer = True
        else: forcedpolltimer = ((datetime.now() - oldpolltime).total_seconds() > forcepollinterval)
        shouldrefresh = sleepmodecheck or forcedpolltimer or phoneincarflag or carstatus['engine'] or (not (carstatus['doorLock'])) or carstatus['trunkOpen'] or carstatus['evStatus']['batteryCharge']
        if shouldrefresh:
            logging.info('should i refresh data %s: sleepmodecheck %s, phone in car %s, engine running %s, doors unlocked %s, trunk open %s, charging %s, forced poll timer %s', shouldrefresh, sleepmodecheck, phoneincarflag, carstatus['engine'], (not (carstatus['doorLock'])),
            carstatus['trunkOpen'], carstatus['evStatus']['batteryCharge'], forcedpolltimer)
            APIgetStatus(True) #get it and process it immediately
            carstatus = APIgetStatus(False)
            odometer = APIgetOdometer()
            location = APIgetLocation()
            oldpolltime = datetime.now()
            oldstatustime = carstatus['vehicleStatusInfo']['vehicleStatus']['time']
            updated = True
            afstand,heading,speed,odometer,googlelocation,rangeleft,soc,charging,trunkopen,doorlock,driverdooropen,soc12v,status12v=processData(carstatus, odometer, location)  # process entire cachestring after timestamp is updated
    except:
        logging.info("error somewhere")
    return updated,afstand,heading,speed,odometer,googlelocation,rangeleft,soc,charging,trunkopen,doorlock,driverdooropen,soc12v,status12v
