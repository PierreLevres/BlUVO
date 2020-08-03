from datetime import datetime
from bluvo_lib import login, APIgetStatus, APIgetOdometer, APIgetLocation
from generic_lib import SendABRPtelemetry, distance

def processData(carstatus, odometer, location):
    global homelocation, abrp_carmodel, abrp_token, WeatherApiKey, WeatherProvider
    location = location['gpsDetail']
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
    except: bla=True
    return afstand,heading,speed,odometer,googlelocation,rangeleft,soc,charging,trunkopen,doorlock,driverdooropen,soc12v,status12v

def initialise(p_email, p_password, p_pin, p_abrp_token,p_abrp_carmodel, p_WeatherApiKey, p_WeatherProvider, p_homelocation, p_forcepollinterval):
    global runFromDomoticz, email, password, pin, abrp_token, abrp_carmodel, WeatherApiKey, WeatherProvider, homelocation, forcepollinterval
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
    oldpolltime=""
    car_brand = (abrp_carmodel.split(":", 1)[0])
    login(car_brand, email, password, pin)

def pollcar(phoneincarflag):
    global oldstatustime, oldpolltime, forcepollinterval, runFromDomoticz
    # TODO find a way to have better poll/refresh intervals
    updated = False
    afstand= heading= speed= odometer= googlelocation= rangeleft= soc= charging= trunkopen=doorlock=driverdooropen=soc12v=status12v =0
    try:
        carstatus = APIgetStatus(False)
        carstatus = carstatus['vehicleStatusInfo']['vehicleStatus'] #use the vehicle status to determine stuff and shorten script
        odometer = APIgetOdometer()
        location = APIgetLocation()
        updated = False

        if oldstatustime != carstatus['time']:
            oldstatustime = carstatus['time']
            afstand,heading,speed,odometer,googlelocation,rangeleft,soc,charging,trunkopen,doorlock,driverdooropen,soc12v,status12v=processData(carstatus,odometer,location)  # process entire cachestring after timestamp is updated
            updated = True

        try:
            sleepmodecheck = carstatus['sleepModeCheck']
        except KeyError: sleepmodecheck = False #sleep mode check is not there...

        # at minimum every interval minutes a true poll
        try:
            if oldpolltime =='': forcedpolltimer = True
            else: forcedpolltimer = (float((datetime.now() - oldpolltime).total_seconds()) > 60*float(forcepollinterval))
        except: forcedpolltimer=false

        if sleepmodecheck or forcedpolltimer or phoneincarflag or carstatus['engine'] or (not (carstatus['doorLock'])) or carstatus['trunkOpen'] or carstatus['evStatus']['batteryCharge']:
            APIgetStatus(True) #get it and process it immediately
            carstatus = APIgetStatus(False)
            carstatus = carstatus['vehicleStatusInfo']['vehicleStatus']  # use the vehicle status to determine stuff and shorten script
            odometer = APIgetOdometer()
            location = APIgetLocation()
            oldpolltime = datetime.now()
            oldstatustime = carstatus['time']
            updated = True
            afstand,heading,speed,odometer,googlelocation,rangeleft,soc,charging,trunkopen,doorlock,driverdooropen,soc12v,status12v=processData(carstatus, odometer, location)  # process entire cachestring after timestamp is updated
    except: return False,0,0,0,0,"error!",0,0,0,0,0,0,0,0
    return updated,afstand,heading,speed,odometer,googlelocation,rangeleft,soc,charging,trunkopen,doorlock,driverdooropen,soc12v,status12v
