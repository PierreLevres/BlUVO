import sys
import urllib
import requests
import uuid
import json
import urllib.parse as urlparse
from urllib.parse import parse_qs, urlencode, quote_plus
from datetime import datetime
import time



# get the constants for this type of car
# parameters from parameter file or from domoticz
# email = from Uvo or Bluelink App'
# password = from Uvo or Bluelink App
# pin = from Uvo or Bluelink App
# abrp_token = Obtain from ABRP app by choosing live data from Torque Pro
# abrp_carmodel = 'kia:niro:19:64:other' Obtain from ABRP API site
# DarkSkyApiKey = obtain from Darksky, or rewrite function
# OpenWeatherApiKey = obtain from Darksky, or rewrite function
# homelat
# homelon

# global abrp_carmodel, abrp_token, DarkSkyApiKey, OpenWeatherApiKey, homelat, homelon, email, password, pin
from params import *
from generic_lib import SendABRPtelemetry, distance
from bluvo_lib import APIError, getConstants, APIgetDeviceID, APIgetCookie, APIsetLanguage, APIgetAuthCode, APIgetToken, \
    APIgetVehicleId, APIsetWakeup, APIgetControlToken, APIgetStatus, APIgetOdometer, APIgetLocation
from bluvo_main import initialise, doStuff


def main():
    initialise(abrp_carmodel, abrp_token, WeatherApiKey, WeatherProvider, homelat, homelon, email, password, pin)
    while True:
        someThingNew, carstatus, odometer, location = doStuff(abrp_carmodel, abrp_token, WeatherApiKey, WeatherProvider, homelat, homelon, email, password, pin)
        # from car status
        if someThingNew:
            lastupdated = carstatus['time']
            trunkopen = carstatus['trunkOpen']
            driverdooropen = carstatus['doorOpen']['frontLeft']
            soc = carstatus['evStatus']['batteryStatus']
            charging = carstatus['evStatus']['batteryCharge']
            rangeLeft = carstatus['evStatus']['drvDistance'][0]['rangeByFuel']['totalAvailableRange']['value']
            soc12V = carstatus['battery']['batSoc']
            status12V = carstatus['battery']['batState']
            # from location
            latitude = location['gpsDetail']['coord']['lat']
            longitude = location['gpsDetail']['coord']['lon']
            heading = location['gpsDetail']['head']
            speed = location['gpsDetail']['speed']['value']

            # send information to domoticz
            lastupdated = datetime.strptime(lastupdated, "%Y%m%d%H%M%S")
            print(lastupdated.strftime("%d-%m-%Y %H:%M:%S"))
            print('laatste update: ', lastupdated.strftime("%d/%m/%Y %H:%M:%S"))
            print('locatie en afstand: ', latitude, ',', longitude, '/',
                  distance(latitude, longitude, float(homelat), float(homelon)))
            print('rijrichting, snelheid en km-stand: ', heading, '/', speed, '/', odometer)
            print('bestuurdersportier en kofferbak open: ', driverdooropen, trunkopen)
            print('EV soc, opladen, range: ', soc, '% ', charging, '/', rangeLeft)
            print('12V accu SoC en status: ', soc12V, status12V)

            # send soc, temp, location to ABRP
            SendABRPtelemetry(soc, speed, latitude, longitude, charging, abrp_carmodel, abrp_token, WeatherApiKey)
        time.sleep(60)

if __name__ == '__main__':
    main()
