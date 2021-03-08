''' to manage vehicle'''
import logging, requests, json
from datetime import datetime, timedelta

from interface import BluelinkyConfig, VehicleRegisterOptions
from interface import FullVehicleStatus, VehicleStatus, VehicleLocation, VehicleOdometer
from controller import EUcontroller
from constants import *
from generic import api_error, temp2hex, hex2temp

class EUvehicle:
    userConfig: BluelinkyConfig
    _fullStatus: FullVehicleStatus
    _status: VehicleStatus
    _location: VehicleLocation
    _odometer: VehicleOdometer

    def __init__(self, vehicleConfig: VehicleRegisterOptions, controller: EUcontroller):
        self.userConfig = controller.userconfig
        self.vehicleConfig = vehicleConfig
        self.controller = controller
        logging.debug('Vehicle %s created', self.vehicleConfig.id)

    def vin(self): return self.vehicleConfig.vin
    def name(self): return self.vehicleConfig.name
    def nickname(self): return self.vehicleConfig.nickname
    def public_id(self): return self.vehicleConfig.id
    def brandIndicator(self): return self.vehicleConfig.brandIndicator

    def check_control_token(self):
        if self.controller.refresh_access_token():
            logging.debug('self.controller.session.controlToken OK')
            if self.controller.session.controlTokenExpiresAt is not None:
                logging.debug('Check pin expiry on %s and now it is %s', self.controller.session.controlTokenExpiresAt, datetime.now())
                if self.controller.session.controlToken is None or datetime.now() > self.controller.session.controlTokenExpiresAt:
                    logging.debug('control token expired at %s, about to renew', self.controller.session.controlTokenExpiresAt)
                    return self.controller.enter_pin()
        return True

    def api_get_valetmode(self):
        url = BaseURL[self.userConfig.brand] + '/api/v1/spa/vehicles/' + self.vehicleConfig.id + '/status/valet'
        headers = {
            'Host': BaseHost[self.userConfig.brand],
            'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage,
            'Accept-Encoding': AcceptEncoding,
            'offset': '2',
            'User-Agent': UserAgent,
            'Connection': Connection,
            'Content-Type': ContentJSON,
            'stamp': self.controller.session.stamp,
            'ccsp-device-id': self.controller.session.deviceId
        }
        response = requests.get(url, headers=headers, cookies=self.controller.session.cookies)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']['valetMode']
            except ValueError:
                api_error('NOK Parsing valetmode: ' + response)
                return False
        else:
            api_error('NOK requesting valetmode. Error: ' + str(response.status_code) + response.text)
            return False

    def api_get_parklocation(self):
        url = BaseURL[self.userConfig.brand] + '/api/v1/spa/vehicles/' + self.vehicleConfig.id + '/location/park'
        headers = {
            'Host': BaseHost[self.userConfig.brand],
            'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage,
            'Accept-Encoding': AcceptEncoding,
            'offset': '2',
            'User-Agent': UserAgent,
            'Connection': Connection,
            'Content-Type': ContentJSON,
            'stamp': self.controller.session.stamp,
            'ccsp-device-id': self.controller.session.deviceId
        }
        response = requests.get(url, headers=headers, cookies=self.controller.session.cookies)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']
            except ValueError:
                api_error('NOK Parsing location park: ' + response)
                return False
        else:
            api_error('NOK requesting location park. Error: ' + str(response.status_code) + response.text)
            return False

    def api_get_finaldestination(self):
        url = BaseURL[self.userConfig.brand] + '/api/v1/spa/vehicles/' + self.vehicleConfig.id + '/finaldestionation'
        headers = {
            'Host': BaseHost[self.userConfig.brand],
            'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage,
            'Accept-Encoding': AcceptEncoding,
            'offset': '2',
            'User-Agent': UserAgent,
            'Connection': Connection,
            'Content-Type': ContentJSON,
            'stamp': self.controller.session.stamp,
            'ccsp-device-id': self.controller.session.deviceId
        }
        response = requests.get(url, headers=headers, cookies=self.controller.session.cookies)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']
            except ValueError:
                api_error('NOK Parsing final destination: ' + response)
                return False
        else:
            api_error('NOK requesting final destination. Error: ' + str(response.status_code) + response.text)
            return False

    def api_set_wakeup(self):
        url = BaseURL[self.userConfig.brand] + '/api/v1/spa/vehicles/' + self.vehicleConfig.id + '/control/engine'
        headers = {
            'Host': BaseHost[self.userConfig.brand],
            'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'Accept-Encoding': AcceptEncoding,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage,
            'offset': '2',
            'User-Agent': UserAgent,
            'Connection': Connection,
            'Content-Type': ContentJSON,
            'stamp': self.controller.session.stamp,
            'ccsp-device-id': self.controller.session.deviceId
        }
        data = {"action": "prewakeup", "self.controller.session.deviceId": self.controller.session.deviceId}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return True
        else:
            api_error('NOK prewakeup. Error: ' + str(response.status_code) + response.text)
            return False

    def api_get_status(self,refresh=False, raw=True):
        logging.debug('into get status')
        # get status either from cache or not
        if not self.check_control_token(): return False
        logging.debug('checked control token')
        cachestring = '' if refresh else '/latest'
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/status' + cachestring
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept, 'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': self.controller.session.deviceId
        }
        response = requests.get(url, headers=headers)
        logging.debug('got status')
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                # a refresh==True returns a short list, a refresh==False returns a long list. If raw is true, return the entire string
                logging.debug(response['resMsg'])
                if raw: return response['resMsg']
                if not refresh: response = response['resMsg']['vehicleStatusInfo']['vehicleStatus']
                return response
            except:
                api_error('NOK parsing status: ' + response)
                return False
        else:
            api_error('NOK requesting status. Error: ' + str(response.status_code) + response.text)
            return False

    def api_get_odometer(self):
        if not self.check_control_token(): return False
        # odometer
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/status/latest'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept, 'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': self.controller.session.deviceId
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']['vehicleStatusInfo']['odometer']['value']
            except ValueError:
                api_error('NOK Parsing odometer: ' + response)
                return False
        else:
            api_error('NOK requesting odometer. Error: ' + str(response.status_code) + response.text)
            return False

    def api_get_location(self):
        if not self.check_control_token(): return False
        # location
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/location'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept, 'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': self.controller.session.deviceId
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']
            except ValueError:
                api_error('NOK Parsing location: ' + response)
                return False
        else:
            api_error('NOK requesting location. Error: ' + str(response.status_code) + response.text)
            return False

    def api_set_lock(self,action='close'):
        if action == "":
            api_error('NOK Emtpy lock parameter')
            return False
        if type(action) == bool:
            if action:
                action = 'close'
            else:
                action = 'open'
        else:
            action = str.lower(action)
            if action == 'on': action = 'close'
            if action == 'lock': action = 'close'
            if action == 'off': action = 'open'
        if not (action == 'close' or action == 'open'):
            api_error('NOK Invalid locking parameter')
            return False

        if not self.check_control_token(): return False

        # location
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/control/door'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept, 'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': self.controller.session.deviceId
        }

        data = {"self.controller.session.deviceId": self.controller.session.deviceId, "action": action}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            logging.debug("Send (un)lock command to Vehicle")
            return True
        else:
            api_error('Error sending lock. Error: ' + str(response.status_code) + response.text)
            return False

    def api_set_charge(self, action='stop'):
        if action == "":
            api_error('NOK Emtpy charging parameter')
            return False
        if type(action) == bool:
            if action:
                action = 'start'
            else:
                action = 'stop'
        else:
            action = str.lower(action)
            if action == 'on': action = 'start'
            if action == 'off': action = 'stop'
        if not (action == 'start' or action == 'stop'):
            api_error('NOK Invalid charging parameter')
            return False
        if not self.check_control_token(): return False
        # location
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/control/charge'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept, 'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': self.controller.session.deviceId
        }

        data = {"self.controller.session.deviceId": self.controller.session.deviceId, "action": action}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            logging.debug("Send (stop) charge command to Vehicle")
            return True
        else:
            api_error('Error sending start/stop charge. Error: ' + str(response.status_code) + response.text)
            return False

    def api_set_hvac(self,action='stop', temp='21.0', bdefrost=False, bheating=False):
        if action == "":
            api_error('NOK Emtpy HVAC parameter')
            return False
        if type(action) == bool:
            if action:
                action = 'start'
            else:
                action = 'stop'
        else:
            action = str.lower(action)
            if action == 'on': action = 'start'
            if action == 'off': action = 'stop'
        if not (action == 'stop' or action == 'start'):
            api_error('NOK Invalid HVAC parameter')
            return False
        try:
            tempcode = temp2hex(temp)
        except:
            tempcode = "0EH"  # default 21 celcius
        try:
            heating = 1 if bheating else 0
        except:
            heating = 1

        if not self.check_control_token(): return False
        # location
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/control/temperature'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept, 'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': self.controller.session.deviceId
        }
        data = {
            "self.controller.session.deviceId": self.controller.session.deviceId,
            "action": action,
            "hvacType": 1,
            "options": {
                "defrost": bdefrost,
                "heating1": heating
            },
            "unit": 'C',
            "tempCode": tempcode
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            logging.debug("Send HVAC setting to Vehicle")
            return True
        else:
            api_error('Error sending HVAC settings. Error: ' + str(response.status_code) + response.text)
            return False

    # ------------ tests -----------
    def api_get_chargeschedule(self):
        if not self.check_control_token(): return False
        # location
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/reservation/charge'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept, 'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': self.controller.session.deviceId
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']
            except ValueError:
                api_error('NOK Parsing charge schedule: ' + response)
        else:
            api_error('NOK requesting charge schedule. Error: ' + str(response.status_code) + response.text)
        return False

    def api_set_chargeschedule(self, schedule1, schedule2, tempset, chargeschedule):
        '''
         Parameters Schedule1, Schedule2 = timeschedules for the temperature set
           first array [x,y,z, etc] with x,y,z, days that need to be set, where sunday = 0 and saturday = 6
           second the time and timesection in 12h notation, int or string, plus 0 or 1 (=AM or PM), int or string
           eg [[2,5,6],["1040","0"]] means 10:40 AM on Tuesday, Friday, Saturday

         Param Tempset
          first the temp to be set (in celcius), float or string
          second True or False for defrost on or off
          [23.0, True] means a temperature of 23 celsius and defrosting on

         ChargeSchedule
           first starttime = array time (int or string) and timesection 0 or 1 (AM or PM)
           then  endtime = array time (int or string) and timesection 0 or 1 (AM or PM)
           prio = 1 (only off-peak times) or 2 (prio to off-peak times)
         [["1100","1"],["0700","0"], 1 ] means off peak times are from 23:00 to 07:00 and car should only charge during these off peak times

         if any parameter = True or None, then ignore values. If parameter = False then disable the schedule, else set the values.
        '''
        if not self.check_control_token(): return False

        # first get the currens settings
        data = self.api_get_chargeschedule(self)
        olddata = data
        if not (not data):
            try:
                # now enter the new settings

                if not (schedule1 is None or schedule1 is True):  # ignore it of True or None
                    if schedule1 is False:  # turn the schedule off
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservChargeSet'] = False
                    else:
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservChargeSet'] = True
                        schedule = {"day": schedule1[0],
                                    "time": {"time": str(schedule1[1][0]), "timeSection": int(schedule1[2][1])}}
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservInfo'] = schedule
                if not (schedule2 is None or schedule2 is True):  # ignore it of True or None
                    if schedule2 is False:  # turn the schedule off
                        data['reservChargeInfo2']['reservChargeInfoDetail']['reservChargeSet'] = False
                    else:
                        data['reservChargeInfo2']['reservChargeInfoDetail']['reservChargeSet'] = True
                        schedule = {"day": schedule2[0],
                                    "time": {"time": str(schedule2[1][0]), "timeSection": int(schedule2[2][1])}}
                        data['reservChargeInfo2']['reservChargeInfoDetail']['reservInfo'] = schedule

                if not (tempset is None or tempset is True):  # ignore it of True or None
                    if tempset is False:  # turn the schedule off
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservFatcSet']['airCtrl'] = 0
                        data['reservChargeInfo2']['reservChargeInfoDetail']['reservFatcSet']['airCtrl'] = 0
                    else:
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservFatcSet']['airCtrl'] = 1
                        data['reservChargeInfo2']['reservChargeInfoDetail']['reservFatcSet']['airCtrl'] = 1
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservFatcSet']['airTemp'][
                            'value'] = temp2hex(str(tempset[0]))
                        data['reservChargeInfo2']['reservChargeInfoDetail']['reservFatcSet']['airTemp'][
                            'value'] = temp2hex(str(tempset[0]))
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservFatcSet']['defrost'] = tempset[1]
                        data['reservChargeInfo2']['reservChargeInfoDetail']['reservFatcSet']['defrost'] = tempset[1]

                if not (chargeschedule is None or chargeschedule is True):  # ignore it of True or None
                    if chargeschedule is False:  # turn the schedule off
                        data['reservFlag'] = 0
                    else:
                        data['reservFlag'] = 1
                        data['offPeakPowerInfo']['offPeakPowerTime1'] = {
                            "starttime": {"time": str(chargeschedule[0][1]), "timeSection": int(chargeschedule[0][1])},
                            "endtime": {"time": str(chargeschedule[1][1]), "timeSection": int(chargeschedule[1][1])}}
                        data['offPeakPowerInfo']['offPeakPowerFlag'] = int(chargeschedule[2])
                if data == olddata: return True  # nothing changed

                url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/reservation/charge'
                headers = {
                    'Host': BaseHost[self.userConfig.brand], 'Accept': Accept, 'Authorization': self.controller.session.controlToken,
                    'ccsp-application-id': CcspApplicationId,
                    'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
                    'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
                    'stamp': self.controller.session.stamp,
                    'ccsp-device-id': self.controller.session.deviceId
                }
                data['self.controller.session.deviceId'] = self.controller.session.deviceId
                response = requests.post(url, json=data, headers=headers)
                if response.status_code == 200: return True
            except:
                api_error('NOK setting charge schedule.')
                return False
        api_error('NOK setting charge schedule.')
        return False

    def api_set_chargelimits(self, limit_fast=80, limit_slow=100):
        if not self.check_control_token(): return False
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/charge/target'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept, 'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': self.controller.session.deviceId
        }
        data = {'targetSOClist': [{'plugType': 0, 'targetSOClevel': int(limit_fast)},
                                  {'plugType': 1, 'targetSOClevel': int(limit_slow)}]}
        response = requests.post(url, json=data, headers=headers, cookies=self.controller.session.cookies)
        if response.status_code == 200:
            return True
        else:
            api_error('NOK setting charge limits. Error: ' + str(response.status_code) + response.text)
            return False

    def api_set_navigation(self, poi_info_list):
        if not self.check_control_token(): return False
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/location/routes'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept, 'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': self.controller.session.deviceId
        }
        data = poi_info_list
        poi_info_list['self.controller.session.deviceId'] = self.controller.session.deviceId
        response = requests.post(url, json=poi_info_list, headers=headers)
        if response.status_code == 200:
            return True
        else:
            api_error('NOK setting navigation. Error: ' + str(response.status_code) + response.text)
            return False
        # TODO test what will happen if you send an array of 2 or more POI's, will it behave like a route-plan ?

    def api_get_userinfo(self):
        if not self.check_control_token(): return False
        # location
        url = BaseURL[self.userConfig.brand] + '/api/v1/user/profile'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept, 'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': self.controller.session.deviceId
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response
            except ValueError:
                api_error('NOK Getting user info: ' + response)
                return False
        else:
            api_error('NOK Getting user info. Error: ' + str(response.status_code) + response.text)
            return False

    def api_get_services(self):
        if not self.check_control_token(): return False
        # location
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/setting/service'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept, 'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': self.controller.session.deviceId
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']['serviceCategorys']
                # returns array of booleans for each service in the list
                # 0= categoryname:1 = GIS
                # 1= categoryname:2 = Product and service improvements
                # 2= categoryname:3 = Alerts & security
                # 3= categoryname:4 = Vehicle Status (report, trips)
                # 4= categoryname:5 = Remote
            except ValueError:
                api_error('NOK Getting active services: ' + response)
                return False
        else:
            api_error('NOK Getting active services. Error: ' + str(response.status_code) + response.text)
            return False

    def api_set_activeservices(self, servicesonoff=[]):
        # servicesonoff is array of booleans for each service in the list
        # 0= categoryname:1 = GIS
        # 1= categoryname:2 = Product and service improvements
        # 2= categoryname:3 = Alerts & security
        # 3= categoryname:4 = Vehicle Status (report, trips)
        # 4= categoryname:5 = Remote
        if not self.check_control_token(): return False
        # location
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/setting/service'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept, 'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': self.controller.session.deviceId
        }
        data = []
        i = 0
        for service_on_off in servicesonoff:
            data['serviceCategorys'][i]['categoryName'] = i + 1
            data['serviceCategorys'][i]['categoryStatus'] = service_on_off
        response = requests.post(url, data=data, headers=headers)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']
            except ValueError:
                api_error('NOK Getting active services: ' + response)
                return False
        else:
            api_error('NOK Getting active services. Error: ' + str(response.status_code) + response.text)
            return False

    def api_get_monthlyreport(self, month):
        if not self.check_control_token(): return False
        # location
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/monthlyreport'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept, 'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': self.controller.session.deviceId
        }
        data = {'setRptMonth': "202006"}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']['monthlyReport']
            except ValueError:
                api_error('NOK Getting montly report: ' + response)
                return False
        else:
            api_error('NOK Getting monthlyreport. Error: ' + str(response.status_code) + response.text)
            return False

    def api_get_monthlyreportlist(self):
        if not self.check_control_token(): return False
        # location
        url = BaseURL[self.userConfig.brand] + '/api/v1/spa/vehicles/' + self.vehicleConfig.id + '/monthlyreportlist'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept, 'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': self.controller.session.deviceId
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']['monthlyReport']
            except ValueError:
                api_error('NOK Getting montly reportlist: ' + response)
                return False
        else:
            api_error('NOK Getting monthlyreportlist. Error: ' + str(response.status_code) + response.text)
            return False
