import time
import logging
import requests, json
import consolemenu
from generic_lib import georeverse, geolookup
from bluvo_main import initialise, pollcar
from bluvo_lib import login, api_get_status, api_get_location, api_set_lock, api_set_HVAC, api_set_charge, api_get_chargeschedule, api_set_chargelimits, api_set_navigation

from params import *  # p_parameters are read
global email, password, pin, vin, abrp_token,abrp_carmodel, WeatherApiKey, WeatherProvider, homelocation
global forcedpolltimer, heartbeatinterval, charginginterval
global ServiceId, BasicToken, ApplicationId, BaseHost, BaseURL
global controlToken, controlTokenExpiresAt, accessToken, accessTokenExpiresAt, refreshToken
global deviceId, vehicleId

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='bluvo.log', level=logging.DEBUG)


menuoptions=["Lock","Unlock","Status","Status formatted","Status refresh","location","loop status","Navigate to", 'set Charge Limits','get charge schedule']
mymenu = consolemenu.SelectionMenu(menuoptions)
initsuccess=initialise(p_email, p_password, p_pin, p_vin, p_abrp_token, p_abrp_carmodel, p_WeatherApiKey, p_WeatherProvider, p_homelocation, p_forcepollinterval, p_charginginterval, p_heartbeatinterval)
if initsuccess:
    while True:
        x = mymenu.get_selection(menuoptions)

        if x == 0: api_set_lock('on')
        if x == 1: api_set_lock('off')
        if x == 2: print(api_get_status(False))
        if x == 3: print(api_get_status(False, False))
        if x == 4: print(api_get_status(True))
        if x == 5:
            locatie = api_get_location()
            if locatie:
                locatie = locatie['gpsDetail']['coord']
                print (georeverse(locatie['lat'],locatie['lon']))
        if x == 6:
            print(x)
            while True:
                try:  # read flag of phone in car from or whereever you want
                    session = requests.Session()
                    response = session.get(p_URLphoneincar)
                    response = json.loads(response.text)
                    phoneincarflag = response['result'][0]['Status'] == 'On'
                except:
                    logging.error('error in phone in car flag')
                    phoneincarflag = False
                phoneincarflag, updated, parsedStatus, afstand, googlelocation = pollcar(phoneincarflag)
#                phoneincarflag, updated, afstand, heading, speed, odometer, googlelocation, rangeleft, soc, charging, trunkopen, doorlock, driverdooropen, soc12v, status12v = pollcar(phoneincarflag)
                # TODO reset phoneincarflag to off
                #if not phoneincarflag:
                #    session = requests.Session()
                #    response = session.get(p_URLphoneincar)
                #   response = json.loads(response.text)
                #    phoneincarflag = response['result'][0]['Status'] == 'On'

                if updated:
                    print('afstand van huis, rijrichting, snelheid en km-stand: ', afstand, ' / ', parsedStatus['heading'], '/', parsedStatus['speed'], '/',parsedStatus['odometer'])
                    print(googlelocation)
                    print("range ", parsedStatus['range'], "soc: ", parsedStatus['chargeHV'])
                    if parsedStatus['charging']: print("Laden")
                    if parsedStatus['trunkopen']: print("kofferbak open")
                    if not (parsedStatus['locked']): print("deuren van slot")
                    if parsedStatus['dooropenFL']: print("bestuurdersportier open")
                    print("soc12v ", parsedStatus['charge12V'], "status 12V", parsedStatus['status12V'])
                    print("=============")
                time.sleep(120)
        if x==7: print(api_set_navigation(geolookup(input("Press Enter address to navigate to..."))))
        if x==8:
            invoer=input("Press maximum for fast and slow charging (space seperated)")
            print(api_set_chargelimits(invoer.split()[0],invoer.split()[1]))
        if x==9: print(api_get_chargeschedule())
        if x==10: exit()
        input("Press Enter to continue...")
else:
    logging.error("initialisation failed")