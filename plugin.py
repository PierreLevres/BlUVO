#           UVO Plugin
#
#           Author:     plips, 2020
#
"""
<plugin key="bluvo" name="Kia UVO and Hyundai Bluelink" author="plips" version="0.1.0">
    <description>
        <h2>BlUvo Plugin</h2>
        A plugin for Kia UVO and Hyundai Bluelink EV's (generally MY2020 and beyond). Use at own risk!
        <br/>
        This plugin will communicate with servers of Kia and Hyundai and through them with your car.
        Polling your car means draining battery and worst case, an empty battery.
        Educate yourself by googling "auxiliary battery drain Niro Kona Soul"
        <br/><br/>
        Email, Password, Pin are same as in you Bluelink or UVO app. VIN is optional, only needed if you have more than one car on your account.<br/>
        Cartype is mandatory, to distinguish Kia or Hyundai BlueLink operation. It is also used for ABRP integration. <br/><br/>
        <h3>ABRP (optional) and weather (even more optional) </h3>
        This plugin will send current state of charge (SoC) and local temperature to your ABRP account to have the most accurate route planning, even on the road. <br/>
        Your ABRP token can be found here: Settings - Car model, 
	Click on settings next to you car, 
	click on settings (arrow down) on the page of your car. 
	Scroll down a bit and click on Show live data instructions and next on the blue "Link Torque"-box.
        Click Next, Next, Next and see: "Set User Email Address to the following token". Click on the blue "Copy" box next to the token.
        <br/>
        If you omit your ABRP token, then no information will be sent to ABRP.
        <br/>
        If you want accurate weather information sent to ABRP enter either a DarkSky or OpenWeather api-key. If omitted, no weather info will be sent to ABRP.
        <br/><br/>
        <h3>12V auxiliary battery</h3>
        If you poll the car all the time, when not driving or not charging, your 12V battery may be drained, depending on the settings of your car to charge the auxiliary battery.
        There is no way for the plugin to determine if you start driving or charging other than polling the car. To save draining and yet to enable polling two mechanisms are implemented:
        <ul style="list-style-type:square">
            <li>Forced poll interval - Polls the car actively every x minutes. Default 60 (1 hour). You might want to change it to 999 (once a week approx.).</li>
            <li>Watching the domoticz "FlagInCar"-devices. Car will be polled if that flag is set to 1. You may want to define a timer on that flag to turn it off automatically.
                If you use iOS you can achieve enabling and disabling this flag by iOS Shortcuts when plugin in and out of Apple Carplay. In the following example 84.73.62.51:1234 is the external server and port of your Domoticz server, and 456 is the IDX of the FlagInCar device (see Domoticz devices tab): <br/>http://84.73.62.51:1234/json.htm?type=command&amp;param=udevice&amp;idx=456&amp;nvalue=1 : URL to open when you plug into Apple Carplay.
                <br/>http://84.73.62.51:1234/json.htm?type=command&amp;param=udevice&amp;idx=456&amp;nvalue=0 : URL to open when you remove it from Apple Carplay.</li>
        </ul>
        The active car polling stops when you are no longer driving or charging and the FlagInCar is not set.
        <br/>
    </description>
    <params>
        <param field="Username" label="Email-address"           width="200px" required="true"  default="john.doe@gmail.com"                  />
        <param field="Password" label="Password"                width="200px" required="true"  default="myLittleSecret" password="true"      />
        <param field="Port"     label="Pin"                     width=" 50px" required="true"  default="1234" password="true"                />
        <param field="Mode2"    label="Car Type"                width="125px" required="true"                                                 >
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
        <param field="Mode6"    label="VIN"                     width="150px" required="false" default="KNACC12ABC4567890"/>
        <param field="Mode1"    label="ABRP token"              width="300px" required="false" default="1234ab56-7cde-890f-a12b-3cde45678901"/>
        <param field="Mode5"    label="Weather provider"    width="150px" required="false"     >
            <options>
                <option label="DarkSky" value="DarkSky" default = "true"/>
                <option label="OpenWeather" value="OpenWeather"/>
             </options>
        </param>
        <param field="Mode4"    label="Weather api key"     width="300px" required="false" default="0987a6b54c3de210123f456578901234"    />
	    <param field="Mode3"    label="Forced poll interval (minutes)" width="100px"  required="true" default="60;15;2"                  />
        <param field="SerialPort"    label="Debug"               width="75px"                                                                  >
            <options>
                <option label="1. Debug" value="1"/>
                <option label="2. Info" value="2"/>
                <option label="3. Warning" value="3"/>
                <option label="4. Error" value="4" default = "true"/>
                <option label="5. Critical" value="5"/>
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz, logging
from datetime import datetime
from bluvo_main import initialise, pollcar

global email, password, pin, vin, abrp_token,abrp_carmodel, WeatherApiKey, WeatherProvider, homelocation, forcedpolltimer, logger, heartbeat, charginginterval, heartbeatinterval

class BasePlugin:
    global email, password, pin, vin, abrp_token,abrp_carmodel, WeatherApiKey, WeatherProvider, homelocation, forcedpolltimer, logger, heartbeat, charginginterval, heartbeatinterval
    def onStart(self):
        global heartbeat
        heartbeat = ""
        if Parameters["SerialPort"] == "1":
            Domoticz.Debugging(1)
            DumpConfigToLog()
            logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='bluvo.log',level=logging.DEBUG)
        else:
            Domoticz.Debugging(0)
            if Parameters["SerialPort"] == "2": logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='bluvo.log', level=logging.INFO)
            elif Parameters["SerialPort"] == "3": logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='bluvo.log', level=logging.WARNING)
            else: logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='bluvo.log', level=logging.ERROR)

        logging.info('started plugin')
        '''
        # add custom images
        CLOSED_ICON = "Closed"
        CHARGING_ICON = "Charging"
        AFSTAND_ICON = "Distance"
        # Dry Logo
        if self.CLOSED_ICON in Images:  Domoticz.Debug("ID: " + str(Images[self.CLOSED_ICON].ID))
        else:                           Domoticz.Image(CLOSED_ICON+".zip").Create()
        if self.CHARGING_ICON in Images:Domoticz.Debug("ID: " + str(Images[self.CHARGING_ICON].ID))
        else:                           Domoticz.Image(CHARGING_ICON+".zip").Create()
        if self.AFSTAND_ICON in Images: Domoticz.Debug("ID: " + str(Images[self.AFSTAND_ICON].ID))
        else:                           Domoticz.Image(AFSTAND_ICON+".zip").Create()
        '''
        if (len(Devices) == 0):
            Image = Images[self.HOMECONNECT_ICON].ID).Create()
            Domoticz.Device(Unit=1, Type=113, Subtype=0 , Switchtype=3 , Name="km-stand").Create()
            Domoticz.Device(Unit=2, Type=243, Subtype=31, Switchtype=0 , Name="range").Create()
            Domoticz.Device(Unit=3, Type=244, Subtype=73, Switchtype=2 , Name="charging",Image = Images[self.CHARGING_ICON].ID)).Create()
            Domoticz.Device(Unit=4, TypeName="Percentage"              , Name="soc").Create()
            Domoticz.Device(Unit=5, TypeName="Percentage"              , Name="soc 12v").Create()
            Domoticz.Device(Unit=6, Type=243, Subtype=31, Switchtype=0 , Name="status 12v").Create()
            Domoticz.Device(Unit=7, Type=244, Subtype=73, Switchtype=11, Name="kofferbak open",Image = Images[self.CLOSED_ICON].ID)).Create()
            Domoticz.Device(Unit=8, Type=243, Subtype=31, Switchtype=0 , Name="afstand van huis",Image = Images[self.AFSTAND_ICON].ID)).Create()
            Domoticz.Device(Unit=9, Type=244, Subtype=73, Switchtype=0 , Name="FlaginCar").Create()
            # TODO Create a scheme for turning off device 9 regularly (eg every 2 hours)
            Domoticz.Log("Devices created.")
            if Parameters["SerialPort"] == "1":
                Domoticz.Debugging(1)
                DumpConfigToLog()
        p_email = Parameters["Username"]
        p_password = Parameters["Password"]
        p_pin = Parameters["Port"]
        p_vin = Parameters["Mode6"]
        p_abrp_token = Parameters["Mode1"]
        p_abrp_carmodel = Parameters["Mode2"]
        # TODO see what weather API is running and get the data ..
        p_WeatherApiKey = Parameters["Mode4"]
        p_WeatherProvider = Parameters["Mode5"]
        p_homelocation = Settings["Location"]
        if p_homelocation == None:
            Domoticz.Log("Unable to parse coordinates")
            p_homelocation = "52.0930241;4.3423724,17"
            return False
        intervals = Parameters["Mode3"].split(";")
        p_forcepollinterval = float(intervals[0])
        p_charginginterval = float(intervals[1])
        p_heartbeatinterval = float(intervals[2])

        if initialise(p_email, p_password, p_pin, p_vin, p_abrp_token, p_abrp_carmodel, p_WeatherApiKey, p_WeatherProvider, p_homelocation, p_forcepollinterval, p_charginginterval, p_heartbeatinterval):
            Domoticz.Heartbeat(30)
        else: Domoticz.Log ("Initialisation failed")
        return True


    def onConnect(self, Connection, Status, Description):
        return True

    def onMessage(self, Connection, Data):
        return True

    def onCommand(self, Unit, Command, Level, Hue):
        if Unit==9:
            if Command == 'On': UpdateDevice(9, 1, 1)
            else: UpdateDevice(9, 0, 0)
        return True

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        return True

    def onHeartbeat(self):
        global heartbeat
        try:
            if (float((datetime.now() - heartbeat).total_seconds()) > (heartbeatinterval-10)):
                heartbeat = datetime.now()
                logging.debug("entering on heatbeat")
                oldphoneincarflag = (Devices[9].nValue==1)
                logging.debug("about to enter poll procedure phone in car? %s",oldphoneincarflag)
                phoneincarflag, updated, parsedStatus, afstand, googlelocation = pollcar(oldphoneincarflag)
#                phoneincarflag, updated, afstand, heading, speed, odometer, googlelocation, rangeleft, soc, charging, trunkopen, doorlock, driverdooropen, soc12v, status12v = pollcar(oldphoneincarflag)
                #if oldphoneincarflag != phoneincarflag: logging.info("exited poll procedure, phone in car? was %s and is %s", oldphoneincarflag, phoneincarflag)
                if oldphoneincarflag and not( phoneincarflag):
                    logging.debug("about to reset device phoneincarflag")
                    UpdateDevice(9, 0, 0)
                if updated:
                    logging.debug("about to update devices")
                    UpdateDevice(1, 0, parsedStatus['odometer'])  # kmstand
                    UpdateDevice(2, 0, parsedStatus['range'])  # kmstand
                    UpdateDevice(3, parsedStatus['charging'], parsedStatus['charging'])  # charging
                    UpdateDevice(4, parsedStatus['chargeHV'], parsedStatus['chargeHV')  # soc
                    UpdateDevice(5, parsedStatus['charge12V'], parsedStatus['charge12V'])  # soc12v
                    UpdateDevice(6, parsedStatus['status12V'], parsedStatus['status12V'])  # status 12v
                    UpdateDevice(7, parsedStatus['trunkopen'], parsedStatus['trunkopen'])  # kofferbak
                    logging.debug("devices 1-7 updates, now renameing 8")
                    if str(Devices[8].sValue) != str(afstand) or Devices[8].Name != googlelocation:
                        Devices[8].Update(nValue=0, sValue=str(afstand), Name=googlelocation)
                        Domoticz.Log("Update " +  str(afstand) + "' (" + Devices[8].Name + ")")
                    logging.debug("device 8 renamed")
        except:
            logging.debug("heartbeat wasnt set yet")
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


#TODO pushbuttons for lock/unlock start/stop charge start/stop ac start/stop heat
#TODO nicer buttons
#TODO button to change start and heat schedule
#TODO script, depending on outside temperature, to preheat the car depending on first destination of the day and the driving time to it
