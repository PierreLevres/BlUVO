#           BlUVO n Plugin for Domoticz
#
#           Dev. Platform : Py 
#
#           Author:     plips
#           0.0.1:  initial release
#
# sources

# https://www.domoticz.com/wiki/Developing_a_Python_plugin

# Below is what will be displayed in Domoticz GUI under HW
#
"""
<plugin key="Heatpump" name="Alpha Innotec Luktronik" author="plips" version="0.0.3" >
    <params>
        <param field="email" label="Email-address (from UVO/Bluelink app)" width="200px" required="true" default="john.doe@gmail.com"/>
        <param field="password" label="Password (from UVO/Bluelink app)" width="200px" required="true" default="1234"/>
        <param field="pin" label="Pin (from UVO/Bluelink app)" width="40px" required="true" default="1234"/>
        <param field="abrp_token" label="ABRP token (from ABRP after selecting Torque Pro)" width="400px" required="false" default="1234ab56-7cde-890f-a12b-3cde45678901"/>
        <param field="car_type" label="ABRP Car Type" width="200px" required="true">
            <options>
                <option label="Ioniq 28kWh" value= "hyundai:ioniq:17:28:other"/>
                <option label="Ioniq 38kWh" value= "hyundai:ioniq:19:38:other"/>
                <option label="Kona 39kWh" value="hyundai:kona:19:39:other"/>
                <option label="Kona 64kWh" value="hyundai:kona:19:64:other"/>
                <option label="eNiro 39kWh" value="kia:niro:19:39:other"/>
                <option label="eNiro 64kWh" value="kia:niro:19:64:other" default="true"/>
                <option label="eSoul 39kWh" value="kia:soul:19:39"/>
                <option label="eSoul 64kWh" value="kia:soul:19:64:other"/>
             </options>
        </param>
        <param field="DarkSkyApiKey" label="Darksky api-key" width="400px" required="false" default="0987a6b54c3de210123f456578901234"/>
        <param field="car_brand" label="Pin (from UVO/Bluelink app)" width="80px" required="true">
            <options>
                <option label="Kia" value="kia" default="true"/>
                <option label="Hyundai" value="hyundai"/>
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
import binascii
import struct
import socket
import datetime

class BasePlugin:
    enabled = False

    def __init__(self):
        return

    def onStart(self):
        #from the selected car types get the left part to determine car brand
        #get homelat and homelon from domoticz
        if len(Devices) == 0:
        # create devices
            Domoticz.Device(Unit=21, TypeName="Text", Name="status").Create()
            Domoticz.Log("Devices created.")
        DumpConfigToLog()
        # connect to car
        Domoticz.Log("Plugin is started.")
        # slower hearbeat
        Domoticz.Heartbeat(300)

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        #Domoticz.Log("onHeartbeat called")
        #read values from car
        #make calculations
        #send to domoticz
        #send to ABRP
        UpdateDevice(device_index, n, s)

global _plugin
_plugin = BasePlugin()

#global functions


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
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return


def UpdateDevice(Unit, nValue, sValue):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
    #        Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return
