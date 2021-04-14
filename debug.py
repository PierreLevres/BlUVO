import logging
import pickle
import pprint
import time

from consolemenu import *

from bluvo import bluvo
from generic_lib import georeverse, geolookup, distance, get_abrprouteplan
from interface import BluelinkyConfig
from params import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s', filename='bluvo.log',
                    level=logging.DEBUG)

mainmenuoptions = ['Status', 'Control', 'Reports']
statusmenuoptions = ['status cache raw', 'status cache formatted', 'Status refresh', 'location cache',
                     'location refresh', 'loop status', 'Get charge schedule', 'Get services', 'valet mode',
                     'get charge target', 'full status cache', 'full status refresh']
controlmenuoptions = ['Lock', 'Unlock', 'Navigate to', 'Set Charge Limits', 'Start heating', 'Stop heating',
                      'Start charge', 'Stop charge', 'Create ABRP plan (demo, no data send to car)']
reportmenuoptions = ['Monthly report', 'trips']

mainmenu = SelectionMenu(mainmenuoptions)
statusmenu = SelectionMenu(statusmenuoptions)
controlmenu = SelectionMenu(controlmenuoptions)
reportmenu = SelectionMenu(reportmenuoptions)

myConfig = BluelinkyConfig(p_email, p_password, ('0000' + (str(p_pin) if isinstance(p_pin, int) else p_pin))[-4:],
                           p_vin, (p_abrp_carmodel.split(":", 1)[0]))
client = bluvo(myConfig)
# vehicle = client._vehicles[0]
vehicle = client.getVehicle()
loc = p_homelocation.split(";")
homelat = float(loc[0])
homelon = float(loc[1])
while True:
    # try:
    if True:
        x = mainmenu.get_selection(mainmenuoptions)
        if x == 0:
            y = statusmenu.get_selection(statusmenuoptions)
            if y == 0: pprint.pprint(vehicle.api_get_status(False, False))
            if y == 1: pprint.pprint(vehicle.api_get_status(False, True))
            if y == 2: pprint.pprint(vehicle.api_get_status(True))
            if y == 3:
                locatie = vehicle.api_get_location(False)
                if locatie: pprint.pprint(georeverse(locatie.lat, locatie.lon))
            if y == 4:
                locatie = vehicle.api_get_location(True)
                if locatie: pprint.pprint(georeverse(locatie.lat, locatie.lon))
            if y == 5:
                vorigestatus = None
                while True:
                    # read semaphore flag
                    try:
                        with open('semaphore.pkl', 'rb') as f:
                            manualForcePoll = pickle.load(f)
                    except:
                        manualForcePoll = False
                    print(manualForcePoll)
                    status = vehicle.api_get_status(manualForcePoll, False)
                    print(status)
                    # clear semaphore flag
                    manualForcePoll = False
                    with open('semaphore.pkl', 'wb') as f:
                        pickle.dump(manualForcePoll, f)
                    if vorigestatus != status:
                        vorigestatus = status
                        afstand = round(
                            distance(status.vehicleLocation.coord.lat, status.vehicleLocation.coord.lon, float(homelat),
                                     float(homelon)), 1)
                        print(
                            '<a href="http://www.google.com/maps/search/?api=1&query=%s,%s">eNiro - Afstand van huis</a>',
                            str(status.vehicleLocation.coord.lat), str(status.vehicleLocation.coord.lon))
                        print('afstand van huis, rijrichting, snelheid en km-stand: %s / %s / %s / %s ',
                              round(distance(status.vehicleLocation.coord.lat, status.vehicleLocation.coord.lon,
                                             float(homelat), float(homelon)), 1),
                              status.vehicleLocation.head, status.vehicleLocation.speed, status.odometer.value)
                        print("range %s, soc %s", status.vehicleStatus.evStatus.drvDistance,
                              status.vehicleStatus.evStatus.batteryStatus)
                        if status.vehicleStatus.evStatus.batteryCharge: print("Laden")
                        if status.vehicleStatus.trunkOpen: print("kofferbak open")
                        if not status.vehicleStatus.doorLock: print("deuren van slot")
                        if status.vehicleStatus.doorOpen.frontLeft == 1: print("bestuurdersportier open")
                        print("soc12v %s, status 12V %s", status.vehicleStatus.battery.batSoc,
                              status.vehicleStatus.battery.batState)
                        print("=============")
                    time.sleep(120)
            if y == 6: pprint.pprint(vehicle.api_get_chargeschedule())
            if y == 7: pprint.pprint(vehicle.api_get_services())
            if y == 8: pprint.pprint(vehicle.api_get_valetmode())
            if y == 9: pprint.pprint(vehicle.api_get_chargetarget())
            if y == 10: pprint.pprint(vehicle.api_get_fullstatus(False))
            if y == 11: pprint.pprint(vehicle.api_get_fullstatus(True))
        if x == 1:
            y = controlmenu.get_selection(controlmenuoptions)
            if y == 0: vehicle.api_set_lock('on')
            if y == 1: vehicle.api_set_lock('off')
            if y == 2:
                poiInfoList = []
                while True:
                    i = 0
                    locatie = input(
                        "Press Enter address to navigate to, or add multiple locations (final destination comes first) on 1 line seperated by |, enter empty line to finish entering locations \n-> ")
                    if locatie is None or locatie == "": break
                    lijstlocaties = locatie.split('|')
                    print(lijstlocaties)
                    for locatie in lijstlocaties:
                        poiElement = geolookup(locatie)
                        poiElement['waypointID'] = i
                        i += 1
                        if poiElement is not False: poiInfoList.append(poiElement)
                pprint.pprint(poiInfoList)
                pprint.pprint(vehicle.api_set_navigation(poiInfoList))
            if y == 3:
                pprint.pprint(vehicle.api_get_chargetarget)
                invoer = input("Enter maximum for fast and slow charging seperated by space , : ; | \n-> ")
                for delim in ',;:|': invoer = invoer.replace(delim, ' ')
                pprint.pprint(vehicle.api_set_chargelimits(invoer.split()[0], invoer.split()[1]))
            if y == 4:
                invoer = input("temperature eg 20.0")
                pprint.pprint(vehicle.api_set_hvac('start', invoer))
            if y == 5:
                pprint.pprint(vehicle.api_set_hvac('stop'))
            if y == 6:
                invoer = input("temperature eg 20.0")
                pprint.pprint(vehicle.api_set_charge('start'))
            if y == 7:
                pprint.pprint(vehicle.api_set_charge('stop'))
            if y == 8:
                invoer = input("Press Enter address to navigate to \n-> ")
                arrive = geolookup(invoer)['coord']
                status = vehicle.api_get_fullstatus(False)

                destinations = [{"lat": status.vehicleLocation.coord.lat, "lon": status.vehicleLocation.coord.lon},
                                {"lat": arrive['lat'], "lon": arrive['lon']}]
                for step in get_abrprouteplan(destinations, p_abrp_carmodel,
                                              status.vehicleStatus.evStatus.batteryStatus):
                    print(
                        '%s,%s: %s %s' % (step['lat'], step['lon'], step['name'], georeverse(step['lat'], step['lon'])))
                    # todo Send This to Car9
        if x == 2:
            y = reportmenu.get_selection(reportmenuoptions)
            if y == 0:
                invoer = input(
                    "api_get_monthlyreport: Enter month in the form yyyymm or leave blank for current month \n-> ")
                pprint.pprint(vehicle.api_get_monthlyreport(invoer))
            if y == 1:
                invoer = input(
                    "api_get_tripinfo Enter day or month in the form yyyymmdd (report of that day) or yyyymm (report of that month) \n-> ")
                pprint.pprint(vehicle.api_get_tripinfo(invoer))
        if x == 3: break
    # except:
    #    print('Some error occured, see log for details')
    input("Press Enter to continue...")
