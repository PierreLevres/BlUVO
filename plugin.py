#           UVO Plugin
#
#           Author:     plips, 2020
#
"""
<plugin key="bluvo" name="Kia UVO and Hyundai Bluelink" author="plips" version="0.0.2">
    <params>
        <param field="Username" label="Email-address"           width="200px" required="true"  default="john.doe@gmail.com"                  />
        <param field="Password" label="Password"                width="200px" required="true"  default="myLittleSecret" password="true"      />
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
	    <param field="Mode3"    label="polls every x secs" width="300px" required="true" default="600"                                   />
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

from bluvo_main import initialise, pollcar

global email, password, pin, abrp_token,abrp_carmodel, WeatherApiKey, WeatherProvider, homelocation, URLphoneincar, forcedpolltimer

class BasePlugin:
    global email, password, pin, abrp_token,abrp_carmodel, WeatherApiKey, WeatherProvider, homelocation, URLphoneincar, forcedpolltimer
    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
            DumpConfigToLog()
        if (len(Devices) == 0):
            Domoticz.Device(Unit=1, Type=113, Subtype=0 , Switchtype=3 , Name="km-stand").Create()
            Domoticz.Device(Unit=2, Type=243, Subtype=31, Switchtype=0 , Name="range").Create()
            Domoticz.Device(Unit=3, Type=244, Subtype=73, Switchtype=2 , Name="charging").Create()
            Domoticz.Device(Unit=4, TypeName="Percentage"              , Name="soc").Create()
            Domoticz.Device(Unit=5, TypeName="Percentage"              , Name="soc 12v").Create()
            Domoticz.Device(Unit=6, Type=243, Subtype=31, Switchtype=0 , Name="status 12v").Create()
            Domoticz.Device(Unit=7, Type=244, Subtype=73, Switchtype=11, Name="kofferbak open").Create()
            Domoticz.Device(Unit=8, Type=243, Subtype=31, Switchtype=0 , Name="afstand van huis").Create()
            Domoticz.Device(Unit=9, Type=244, Subtype=73, Switchtype=0 , Name="FlaginCar").Create()
            Domoticz.Log("Devices created.")
            if Parameters["Mode6"] == "Debug":
                Domoticz.Debugging(1)
                DumpConfigToLog()
        p_email = Parameters["Username"]
        p_password = Parameters["Password"]
        p_pin = Parameters["Port"]
        p_abrp_token = Parameters["Mode1"]
        p_abrp_carmodel = Parameters["Mode2"]
        # TODO see what weather API is running and get the data ..
        p_WeatherApiKey = Parameters["Mode4"]
        p_WeatherProvider = Parameters["Mode5"]
        p_homelocation = Settings["Location"]
        p_forcepollinterval = Parameters["Mode3"]
        if p_homelocation == None:
            Domoticz.Log("Unable to parse coordinates")
            return False
        logging.basicConfig(filename='bluvo-plugin.log', level=logging.INFO)
        initialise(p_email, p_password, p_pin, p_abrp_token, p_abrp_carmodel, p_WeatherApiKey, p_WeatherProvider, p_homelocation, "", p_forcepollinterval)
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
        updated,afstand, heading, speed, odometer, googlelocation, rangeleft, soc, charging, trunkopen, doorlock, driverdooropen, soc12v, status12v = pollcar()
        if updated:
            UpdateDevice(1, 0, odometer)  # kmstand
            UpdateDevice(2, 0, rangeleft)  # kmstand
            UpdateDevice(3, charging, charging)  # charging
            UpdateDevice(4, soc, soc)  # soc
            UpdateDevice(5, soc12v, soc12v)  # soc12v
            UpdateDevice(6, status12v, status12v)  # status 12v
            UpdateDevice(7, trunkopen, trunkopen)  # kofferbak
            if str(Devices[8].sValue) != str(afstand) or Devices[8].Name != googlelocation:
                Devices[8].Update(nValue=0, sValue=str(afstand), Name=googlelocation)
                Domoticz.Log("Update " +  str(afstand) + "' (" + Devices[8].Name + ")")
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
        if (Devices[Unit].nValue != nValue) or (str(Devices[Unit].sValue) != str(sValue)):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
            Domoticz.Log("Update " + str(nValue) + ":'" + str(sValue) + "' (" + Devices[Unit].Name + ")")
    return


