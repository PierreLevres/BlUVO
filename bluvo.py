import sys
import urllib
import requests
import uuid
import json
import urllib.parse as urlparse
from urllib.parse import parse_qs, urlencode, quote_plus
from datetime import datetime
import time

# parameters from parameter file or from domoticz
from params import *
# email = from Uvo or Bluelink App'
# password = from Uvo or Bluelink App
# pin = from Uvo or Bluelink App
# abrp_token = Obtain from ABRP app by choosing live data from Torque Pro
# abrp_carmodel = 'kia:niro:19:64:other' Obtain from ABRP API site
# DarkSkyApiKey = obtain from Darksky, or rewrite function

def main():

    from generic_lib import SendABRPtelemetry, distance
    from bluvo_lib import getConstants, APIgetDeviceID, APIgetCookie, APIsetLanguage, APIgetAuthCode, APIgetToken, APIgetVehicleId, APIsetWakeup, APIgetControlToken, APIgetStatus, APIgetOdometer, APIgetLocation
    from bluvo_lib import APIError
    #get the constants for this type of car
    car_brand=(abrp_carmodel.split(":",1)[0])
    ServiceId, BasicToken, ApplicationId, ContentLengthToken, BaseHost, BaseURL = getConstants(car_brand)

    lastConnected = 0
    previousRangeLeft = 0
    pollCounter = 0
    pollUnit = 60  # (seconds)

    while True:
        try:
            needToLogon = False
            #If it was 10 minutes or longer ago, connect to the car again
            if lastConnected == 0 : needToLogon = True
            else:
                if (datetime.now() - lastConnected).total_seconds()/60 > 10: needToLogon = True
            print('login? ',needToLogon)
            if needToLogon:
                # connect to the car
                # TOTO if one of these functions ERR's then skip to the end
                deviceId = APIgetDeviceID(BaseURL, ServiceId, BaseHost)
                cookies = APIgetCookie(ServiceId, BaseURL)
                APIsetLanguage(BaseURL, cookies)
                authCode = APIgetAuthCode(BaseURL, email, password, cookies)
                accessToken = APIgetToken(BaseURL, BasicToken, ContentLengthToken, BaseHost, authCode)
                vehicleId = APIgetVehicleId(BaseURL, accessToken, deviceId, ApplicationId, BaseHost)
                APIsetWakeup(BaseURL, vehicleId, accessToken, deviceId, ApplicationId, BaseHost)
                controlToken = APIgetControlToken(BaseURL, accessToken, BaseHost, deviceId, pin)
                lastConnected = datetime.now()

            #get values
            carstatus = APIgetStatus(BaseURL, vehicleId, controlToken, deviceId)
            odometer = APIgetOdometer(BaseURL, vehicleId, controlToken, deviceId)
            location = APIgetLocation(BaseURL, vehicleId, controlToken, deviceId)

            # from car status
            if carstatus != -1:
                lastupdated = carstatus['time']
                trunkopen = carstatus['trunkOpen']
                driverdooropen = carstatus['doorOpen']['frontLeft']
                soc = carstatus['evStatus']['batteryStatus']
                charging = carstatus['evStatus']['batteryCharge']
                rangeLeft = carstatus['evStatus']['drvDistance'][0]['rangeByFuel']['totalAvailableRange']['value']
                soc12V = carstatus['battery']['batSoc']
                status12V = carstatus['battery']['batState']
            if location != -1:
                #from location
                latitude = location['gpsDetail']['coord']['lat']
                longitude = location['gpsDetail']['coord']['lon']
                heading = location['gpsDetail']['head']
                speed = location['gpsDetail']['speed']['value']

            #send information to domoticz
            lastupdated=datetime.strptime(lastupdated,"%Y%m%d%H%M%S")
            print(lastupdated.strftime("%d-%m-%Y %H:%M:%S"))
            print('laatste update: ',lastupdated.strftime("%d/%m/%Y %H:%M:%S"))
            print('locatie en afstand: ',latitude,',',longitude, '/',distance(latitude,longitude,float(homelat),float(homelon)))
            print('rijrichting, snelheid en km-stand: ',heading,'/',speed,'/',odometer)
            print('bestuurdersportier open: ', driverdooropen)
            print('EV soc, opladen, range: ',soc,'% ',charging,'/',rangeLeft)
            print('12V accu SoC en status: ', soc12V, status12V)

            #send soc, temp, location to ABRP
            if carstatus != -1 and location !=-1: SendABRPtelemetry(soc,speed,latitude,longitude,charging,abrp_carmodel,abrp_token,DarkSkyApiKey)

            #TODO how to use this code in the onheartbeat of Domoticz
            #and now wait
            if soc12V < 30 or status12V !=0 :
                time.sleep(3600)
            elif ((rangeLeft == previousRangeLeft) and (charging == False) and (speed == 0)):
                #car is not moving and you are not charging
                pollCounter += 1
                if (pollCounter > 5):  # Car is not moving for 5 minutes so poll again in 10
                    time.sleep(10*pollUnit)
                else:
                    time.sleep(2*pollUnit)
            else: #car is moving or charging and battery > 30
                time.sleep(pollUnit)
                pollCounter = 0
            previousRangeLeft = rangeLeft
            print ("========================")
        except APIError as e:
            print (str(e))
            time.sleep(5 * pollUnit)
if __name__ == '__main__':
    main()