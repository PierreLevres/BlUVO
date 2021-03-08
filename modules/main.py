import logging


from vehicle import EUvehicle
from controller import EUcontroller
from interface import BluelinkyConfig

class bluvo:

    def __init__(self, myConfig: BluelinkyConfig):
        logging.debug(myConfig.username)
        if myConfig.brand == None: myConfig.brand = 'kia'
        logging.debug(myConfig.brand)
        self._controller = EUcontroller(myConfig)
        self.login()

    def login(self):
        response = self._controller.login()
        self._vehicles = self._controller.getvehicles()
