
import time
import logging

from bluvo_main import initialise, pollcar

from params import *  # p_parameters are read
global email, password, pin, abrp_token,abrp_carmodel, WeatherApiKey, WeatherProvider, homelocation, forcedpolltimer

#logging.basicConfig(filename='bluvo.log', level=logging.INFO)
initialise(p_email, p_password, p_pin, p_abrp_token,p_abrp_carmodel, p_WeatherApiKey, p_WeatherProvider, p_homelocation, p_forcepollinterval)
while True:
    try:  # read flag of phone in car from or whereever you want
        session = requests.Session()
        response = session.get(p_URLphoneincar)
        response = json.loads(response.text)
        phoneincarflag = response['result'][0]['Status'] == 'On'
    except:
        #logging.info('error in phone in car flag')
        phoneincarflag = False
    updated,afstand,heading,speed,odometer,googlelocation,rangeleft,soc,charging,trunkopen,doorlock,driverdooropen,soc12v,status12v = pollcar(phoneincarflag)
    if updated:
        print('afstand van huis, rijrichting, snelheid en km-stand: ', afstand, ' / ', heading, '/', speed, '/',odometer)
        print(googlelocation)
        print("range ", rangeleft, "soc: ", soc)
        if charging: print("Laden")
        if trunkopen: print("kofferbak open")
        if not (doorlock): print("deuren van slot")
        if driverdooropen: print("bestuurdersportier open")
        print("soc12v ", soc12v, "status 12V", status12v)
        print("=============")
    time.sleep(30)
