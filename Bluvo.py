import sys
import urllib
import requests
import uuid
import json
import urllib.parse as urlparse
from urllib.parse import parse_qs, urlencode, quote_plus


# we need the following params
# email = from Uvo or Bluelink App'
# password = from Uvo or Bluelink App
# pin = from Uvo or Bluelink App
# abrp_token = Obtain from ABRP app by choosing live data from Torque Pro
# abrp_carmodel = 'kia:niro:19:64:other' Obtain from ABRP API site
# DarkSkyApiKey = obtain from Darksky, or rewrite function
# car_brand = 'Kia' or ' Hyundai'
# parameters from parameter file or from domoticz
from params import *

def main():
    # constants, depending on Brand Kia or Hyundai
    if car_brand == 'kia':
        ServiceId = 'fdc85c00-0a2f-4c64-bcb4-2cfb1500730a'
        BasicToken = 'Basic ZmRjODVjMDAtMGEyZi00YzY0LWJjYjQtMmNmYjE1MDA3MzBhOnNlY3JldA=='
        ApplicationId= '693a33fa-c117-43f2-ae3b-61a02d24f417'
        ContentLengthToken = '150'
    elif car_brand == 'hyundai':
        ServiceId = '6d477c38-3ca4-4cf3-9557-2a1929a94654'
        BasicToken = 'Basic NmQ0NzdjMzgtM2NhNC00Y2YzLTk1NTctMmExOTI5YTk0NjU0OktVeTQ5WHhQekxwTHVvSzB4aEJDNzdXNlZYaG10UVI5aVFobUlGampvWTRJcHhzVg=='
        ApplicationId = '99cfff84-f4e2-4be8-a5ed-e5b755eb6581'
        ContentLengthToken = '154'
    else:return -1
    BaseHost = 'prd.eu-ccapi.'+car_brand+'.com:8080'
    BaseURL = 'https://'+BaseHost

    from generic_lib import SendABRPtelemetry, distance
    from BlUvo_lib import APIgetDeviceID, APIgetCookie, APIsetLanguage, APIgetAuthCode, APIgetToken, APIgetVehicleId, APIsetWakeup, APIgetControlToken, APIgetStatus, APIgetOdometer, APIgetLocation

    #connect to the car
    deviceId = APIgetDeviceID(BaseURL,ServiceId, BaseHost)
    cookies = APIgetCookie(ServiceId, BaseURL)
    APIsetLanguage(BaseURL, cookies)
    authCode = APIgetAuthCode(BaseURL, email, password, cookies)
    access_token = APIgetToken(BaseURL, BasicToken, ContentLengthToken, BaseHost, authCode)
    vehicleId = APIgetVehicleId(BaseURL, access_token, deviceId, ApplicationId, BaseHost)
    APIsetWakeup(BaseURL, vehicleId, access_token, deviceId, ApplicationId, BaseHost)
    controlToken = APIgetControlToken(BaseURL, access_token, BaseHost, deviceId, pin)

    #get values
    carstatus = APIgetStatus(BaseURL, vehicleId, controlToken, deviceId)
    odometer = APIgetOdometer(BaseURL, vehicleId, controlToken, deviceId)
    location = APIgetLocation(BaseURL, vehicleId, controlToken, deviceId)

    # from car status
    trunkopen = carstatus['trunkOpen']
    driverdooropen = carstatus['doorOpen']['frontLeft']
    soc = carstatus['evStatus']['batteryStatus']
    charging = carstatus['evStatus']['batteryCharge']
    rangeleft = carstatus['evStatus']['drvDistance'][0]['rangeByFuel']['totalAvailableRange']['value']
    soc12V = carstatus['battery']['batSoc']
    #from odometer
    #from location
    latitude = location['gpsDetail']['coord']['lat']
    longitude = location['gpsDetail']['coord']['lon']
    altitude = location['gpsDetail']['coord']['alt']
    heading = location['gpsDetail']['head']
    speed = location['gpsDetail']['speed']['value']

    #send information to domoticz
    print('locatie: ',latitude,',',longitude)
    print('afstand',distance(latitude,longitude,float(homelat),float(homelon)))
    print('rijrichting: ',heading)
    print('snelheid: ', speed)
    print('km-stand: ', odometer)
    print('trunk open: ',trunkopen)
    print('bestuurdersportier open: ', driverdooropen)
    print('soc: ',soc)
    print('charging: ', charging)
    print('range left: ', rangeleft)
    print('soc 12V: ', soc12V)

    #send soc, temp, location to ABRP
    SendABRPtelemetry(soc,speed,latitude,longitude,charging,abrp_carmodel,abrp_token,DarkSkyApiKey)

if __name__ == '__main__':
    main()