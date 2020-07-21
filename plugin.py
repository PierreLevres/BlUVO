#           UVO Plugin
#
#           Author:     plips, 2020
#
"""
<plugin key="bluvo" name="Kia UVO and Hyundai Bluelink" author="plips" version="0.0.1">
    <params>
        <param field="Username" label="Email-address"           width="200px" required="true"  default="john.doe@gmail.com"                  />
        <param field="Password" label="Password"                width="200px" required="true"  default="myLittleSecret"   password="true"    />
        <param field="Port"     label="Pin"                     width=" 50px" required="true"  default="1234"                                />
        <param field="Mode1"    label="ABRP token"              width="300px" required="false" default="1234ab56-7cde-890f-a12b-3cde45678901"/>
        <param field="Mode2"    label="ABRP Car Type"           width="200px" required="true"                                                 >  
            <options>
                <option label="Ioniq 28kWh" value="hyundai:ioniq:17:28:other"/>
                <option label="Ioniq 38kWh" value="hyundai:ioniq:19:38:other"/>
                <option label="Kona 39kWh" value="hyundai:kona:19:39:other"/>
                <option label="Kona 64kWh" value="hyundai:kona:19:64:other"/>
                <option label="eNiro 39kWh" value="kia:niro:19:39:other"/>
                <option label="eNiro 64kWh" value="kia:niro:19:64:other" default="true"/>
                <option label="eSoul 39kWh" value="kia:soul:19:39"/>
                <option label="eSoul 64kWh" value="kia:soul:19:64:other"/>
             </options>
	    </param>
        <param field="Mode4"    label="Weather api key"     width="300px" required="false" default="0987a6b54c3de210123f456578901234"    />
        <param field="Mode5"    label="Weather provider"    width="300px" required="false"     >
            <options>
                <option label="DarkSky" value="DarkSky" default = "true"/>
                <option label="OpenWeather" value="OpenWeather"/>
             </options>
        </param>
        <param field="Mode6"    label="Debug"               width="75px"                                                                  >
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import sys
import json
from datetime import datetime


import binascii
import struct
import socket
import datetime
from datetime import datetime
from generic_lib import SendABRPtelemetry, distance
from bluvo_lib import APIError, getConstants, APIgetDeviceID, APIgetCookie, APIsetLanguage, APIgetAuthCode, APIgetToken, \
    APIgetVehicleId, APIsetWakeup, APIgetControlToken, APIgetStatus, APIgetOdometer, APIgetLocation

global previousRangeLeft, pollCounter, sleepCycles
global abrp_carmodel, abrp_token, WeatherApiKey, WeatherProvider, homelat, homelon, email, password, pin
global ServiceId, BasicToken, ApplicationId, ContentLengthToken, BaseHost, BaseURL, vehicleId, controlToken, controlTokenExpiresAt, accessToken, deviceId, car_brand

class BasePlugin:

    #just declare everything used as global
    global previousRangeLeft, pollCounter, sleepCycles
    global abrp_carmodel, abrp_token, WeatherApiKey, WeatherProvider, homelat, homelon, email, password, pin
    global ServiceId, BasicToken, ApplicationId, ContentLengthToken, BaseHost, BaseURL, vehicleId, controlToken, controlTokenExpiresAt, accessToken, deviceId, car_brand

    def onStart(self):
        global previousRangeLeft, pollCounter, sleepCycles
        global abrp_carmodel, abrp_token, WeatherApiKey, WeatherProvider, homelat, homelon, email, password, pin
        global ServiceId, BasicToken, ApplicationId, ContentLengthToken, BaseHost, BaseURL, vehicleId, controlToken, controlTokenExpiresAt, accessToken, deviceId, car_brand
        if Parameters["Mode6"] == "Debug":
            DumpConfigToLog()
        if (len(Devices) == 0):
            Domoticz.Device(Unit=1, TypeName="Visibility", Name="km-stand").Create()
            Domoticz.Device(Unit=2, TypeName="Visibility", Name="range").Create()
            Domoticz.Device(Unit=3, Type=244, Subtype=73, Switchtype=2, Name="charging").Create()
            Domoticz.Device(Unit=4, TypeName="Percentage", Name="soc").Create()
            Domoticz.Device(Unit=5, TypeName="Percentage", Name="soc 12v").Create()
            Domoticz.Device(Unit=6, TypeName="Custom", Name="status 12v").Create()
            Domoticz.Device(Unit=7, Type=244, Subtype=73, Switchtype=11, Name="kofferbak open").Create()
            Domoticz.Device(Unit=8, TypeName="Visibility", Name="afstand van huis").Create()
            Domoticz.Log("Devices created.")
            if Parameters["Mode6"] == "Debug":
                DumpConfigToLog()
        abrp_carmodel = Parameters["Mode2"]
        car_brand = (abrp_carmodel.split(":", 1)[0])
        abrp_token = Parameters["Mode1"]
        WeatherApiKey = Parameters["Mode4"]
        WeatherProvider = Parameters["Mode5"]

        loc = Settings["Location"].split(";")
        homelat = float(loc[0])
        homelon = float(loc[1])

        if homelat == None or homelon == None:
            Domoticz.Log("Unable to parse coordinates")
            return False

        email = Parameters["Username"]
        password = Parameters["Password"]
        pin = Parameters["Port"]

        ServiceId, BasicToken, ApplicationId, ContentLengthToken, BaseHost, BaseURL = getConstants(car_brand)

        controlTokenExpiresAt = datetime(1970, 1, 1, 0, 0, 0)
        previousRangeLeft = 0
        pollCounter = 0
        sleepCycles = 0
        Domoticz.Heartbeat(30)
        return True

    def onConnect(self, Connection, Status, Description):
        return True

    def onMessage(self, Connection, Data):
        return True

    def onCommand(self, Unit, Command, Level, Hue):
        return True

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        return True

    def onHeartbeat(self):
        global ServiceId, BasicToken, ApplicationId, ContentLengthToken #parameters defined by the constants
        global previousRangeLeft, pollCounter, sleepCycles # global since we use them for controlling on heartbeat
        global BaseURL, accessToken, BaseHost, deviceId, pin, controlTokenExpiresAt  # global since we use them in the statements enter-pincode every now and then
        global BaseURL, vehicleId, controlToken, deviceId #global since we use them in getting car status everynow and then

        #try:
        if True:
            # "sleepCycles" to not overload the car
            if sleepCycles != 0:
                sleepCycles -= 1
            else:
                if controlTokenExpiresAt == datetime(1970, 1, 1, 0, 0, 0): # since this is the first time connect to the car
                    if Parameters["Mode6"] == "Debug": Domoticz.Log("First Run, Connect to Car")
                    deviceId = APIgetDeviceID(BaseURL, ServiceId, BaseHost)
                    cookies = APIgetCookie(ServiceId, BaseURL)
                    APIsetLanguage(BaseURL, cookies)
                    authCode = APIgetAuthCode(BaseURL, email, password, cookies)
                    accessToken = APIgetToken(BaseURL, BasicToken, ContentLengthToken, BaseHost, authCode)
                    vehicleId = APIgetVehicleId(BaseURL, accessToken, deviceId, ApplicationId, BaseHost)
                    APIsetWakeup(BaseURL, vehicleId, accessToken, deviceId, ApplicationId, BaseHost)
                if (datetime.now() - controlTokenExpiresAt).total_seconds() / 60 > 10:  # enter pin if longer than 10 minutes ago
                    if Parameters["Mode6"] == "Debug": Domoticz.Log("Long time since pin, re-enter")
                    controlToken, controlTokenExpiresAt = APIgetControlToken(BaseURL, accessToken, BaseHost, deviceId, pin)
                # get values
                carstatus = APIgetStatus(BaseURL, vehicleId, controlToken, deviceId)
                odometer = round(APIgetOdometer(BaseURL, vehicleId, controlToken, deviceId),1)
                location = APIgetLocation(BaseURL, vehicleId, controlToken, deviceId)
                Domoticz.Log("polled car")
                # from car status
                trunkopen =1 if carstatus['trunkOpen'] else 0
                soc = carstatus['evStatus']['batteryStatus']
                charging = 1 if carstatus['evStatus']['batteryCharge'] else 0
                rangeLeft = round(carstatus['evStatus']['drvDistance'][0]['rangeByFuel']['totalAvailableRange']['value'],1)
                soc12V = carstatus['battery']['batSoc']
                status12V = carstatus['battery']['batState']
                latitude = location['gpsDetail']['coord']['lat']
                longitude = location['gpsDetail']['coord']['lon']
                speed = location['gpsDetail']['speed']['value']
                afstand = round(distance(latitude, longitude, float(homelat), float(homelon)),1)
                Domoticz.Log(str(rangeLeft))
                # send information to domoticz
                UpdateDevice(1, 0, odometer)  # kmstand
                UpdateDevice(2, 0, rangeLeft)  # kmstand
                UpdateDevice(3, charging, charging) #charging
                UpdateDevice(4, soc, soc) #soc
                UpdateDevice(5, soc12V, soc12V) #soc12v
                UpdateDevice(6, status12V, status12V) #status 12v
                UpdateDevice(7, trunkopen, trunkopen) #kofferbak
                UpdateDevice(8, 0, afstand) #afstand

                # send soc, temp, location to ABRP
                if carstatus != -1 and location != -1: SendABRPtelemetry(soc, speed, latitude, longitude, charging, abrp_carmodel, abrp_token, WeatherApiKey, WeatherProvider)

                # and now determine how long to wait before nextpoll
                if soc12V < 30 or status12V != 0:
                    sleepCycles = 120
                    if Parameters["Mode6"] == "Debug": Domoticz.Log("12V battery behaving strangely. Poll again in 1 hour")
                elif (rangeLeft == previousRangeLeft) and (charging == False) and (speed == 0): # car is not moving and you are not charging
                    pollCounter += 1
                    if Parameters["Mode6"] == "Debug": Domoticz.Log("Car is not moving and not charging")
                    if pollCounter > 10:
                        sleepCycles = 20 # Car is not moving for 5 minutes so poll again in 10
                        if Parameters["Mode6"] == "Debug": Domoticz.Log("Car hasnt moved in 5 minutes, poll again in 10 minutes")
                    else:sleepCycles = 4
                else:  # car is moving or charging and battery > 30
                    sleepCycles = 1
                    pollCounter = 0
                previousRangeLeft = rangeLeft
            return True
        #except APIError as e:
        #    Domoticz.Log(str(e))
        #    sleepCycles = 5
        #    return True
        return

    def onDisconnect(self, Connection):
        Domoticz.Log("Device has disconnected")
        return

    def onStop(self):
        Domoticz.Log("onStop called")
        return True

    def TurnOn(self):
        return

    def TurnOff(self):
        return

    def SyncDevices(self):
        return

    def ClearDevices(self):
        return


global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)


def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)


def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)


def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Settings count: " + str(len(Settings)))
    for x in Settings:
        Domoticz.Debug("'" + x + "':'" + str(Settings[x]) + "'")
    Domoticz.Debug("Image count: " + str(len(Images)))
    for x in Images:
        Domoticz.Debug("'" + x + "':'" + str(Images[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
        Domoticz.Debug("Device Image:     " + str(Devices[x].Image))
    return


def UpdateDevice(Unit, nValue, sValue):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
            Domoticz.Log("Update " + str(nValue) + ":'" + str(sValue) + "' (" + Devices[Unit].Name + ")")
    return


