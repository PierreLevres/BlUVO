import logging
from dacite import from_dict

from vehicle import EUvehicle
from controller import EUcontroller
from interface import BluelinkyConfig


class bluvo:

    def __init__(self, myConfig: BluelinkyConfig):
        logging.debug(myConfig.username)
        if myConfig.brand is None: myConfig.brand = 'kia'
        logging.debug(myConfig.brand)
        self._controller = EUcontroller(myConfig)
#        self.login()
#
#    def login(self):
        response = self._controller.login()
        result = self._controller.getvehicles()
        if result is not False:
            self._vehicles = result
            logging.debug('Found %s vehicles on the account', len(self._vehicles))
#        return response

    def getVehicles(self):
        return self._controller.vehicles

    def getVehicle(self, inputvin = ""):
        if len(self._vehicles) == 0:
            logging.debug('NOK login. No vehicles in the account')
            return False
        elif len(self._vehicles) == 1:
            return self._vehicles[0]
        else:
            vehicleId = None
            for vehicle in self._vehicles:
                if vehicle['vin'] == inputvin: return vehicle
            if vehicleId is None:
                logging.debug('NOK login. The VIN you entered is not in the vehicle list ' + inputvin)
            return False
