# TODO return values in the format defined in " Interfaces " and request input as defined in " Interfaces "
# to manage vehicle
import logging
import requests
import json
import pprint
from datetime import datetime
from dacite import from_dict

from interface import BluelinkyConfig, VehicleRegisterOptions
from interface import FullVehicleStatus, rawVehicleStatus, ParsedVehicleStatus, VehicleLocation, VehicleOdometer
# from controller import EUcontroller
from constants import *
from generic import api_error, ApiError, temp2hex, hex2temp
from generic_lib import convert_to_bool


class EUvehicle:
    userConfig: BluelinkyConfig
    _fullStatus: FullVehicleStatus
    _rawStatus: rawVehicleStatus
    _status: ParsedVehicleStatus
    _location: VehicleLocation
    _odometer: VehicleOdometer

    # def __init__(self, vehicleConfig: VehicleRegisterOptions, controller: EUcontroller):
    def __init__(self, vehicleConfig: VehicleRegisterOptions, controller):
        self.userConfig = controller.userconfig
        self.vehicleConfig = vehicleConfig
        self.controller = controller
        logging.debug('Vehicle %s created', self.vehicleConfig.id)

    def vin(self):
        return self.vehicleConfig.vin

    def name(self):
        return self.vehicleConfig.name

    def nickname(self):
        return self.vehicleConfig.nickname

    def public_id(self):
        return self.vehicleConfig.id

    def brandIndicator(self):
        return self.vehicleConfig.brandIndicator

    def check_control_token(self):
        logging.debug('about to check controlToken ')
        if self.controller.refresh_access_token():
            logging.debug('accessToken OK')
            if self.controller.session.controlTokenExpiresAt is not None or self.controller.session.controlToken is None or self.controller.session.controlToken == '':
                logging.debug('Check pin expiry on %s and now it is %s', self.controller.session.controlTokenExpiresAt,
                              datetime.now())
                if self.controller.session.controlToken is None or datetime.now() > self.controller.session.controlTokenExpiresAt:
                    logging.debug('control token expired at %s, about to renew',
                                  self.controller.session.controlTokenExpiresAt)
                    return self.controller.enter_pin()
        return True

    def api_get_valetmode(self):
        url = BaseURL[self.userConfig.brand] + '/api/v1/spa/vehicles/' + self.vehicleConfig.id + '/status/valet'
        headers = {
            'Host': BaseHost[self.userConfig.brand],
            'Accept': Accept,
            'Authorization': self.controller.session.accessToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage,
            'Accept-Encoding': AcceptEncoding,
            'offset': '1',
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
                # TODO Valet mode response
                return response['resMsg']['valetMode']
            except ValueError:
                raise ApiError('NOK Parsing valetmode: ' + response)
        else:
            raise ApiError('NOK requesting valetmode. Error: ' + str(response.status_code) + response.text)

    def api_get_parklocation(self):
        url = BaseURL[self.userConfig.brand] + '/api/v1/spa/vehicles/' + self.vehicleConfig.id + '/tripinfo'
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
                # TODO location park response
                return response['resMsg']
            except ValueError:
                raise ApiError('NOK Parsing location park: ' + response)
        else:
            raise ApiError('NOK requesting location park. Error: ' + str(response.status_code) + response.text)

    def api_get_finaldestination(self):
        url = BaseURL[self.userConfig.brand] + '/api/v1/spa/vehicles/' + self.vehicleConfig.id + '/finaldestination'
        headers = {
            'Host': BaseHost[self.userConfig.brand],
            'Accept': Accept,
            'Authorization': self.controller.session.accessToken,
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
                # TODO get destination response
                return response['resMsg']
            except ValueError:
                raise ApiError('NOK Parsing final destination: ' + response)
        else:
            raise ApiError('NOK requesting final destination. Error: ' + str(response.status_code) + response.text)

    def api_get_fullstatus(self, refresh=False):
        # first get cached status
        # if refresh
        #   get status refresh ==> put it in vehicle info part
        #   get location ==> put it in location part
        #   (odometer cant be forced to update)
        logging.debug('into get full status')
        if not self.check_control_token(): return False
        logging.debug('checked control token')

        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/status/latest'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
            'ccsp-device-id': self.controller.session.deviceId
        }
        logging.debug(headers)
        response = requests.get(url, headers=headers)
        logging.debug('got full status cached')
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                logging.debug(response['resMsg'])
                _fullstatus = from_dict(data_class=FullVehicleStatus, data=response['resMsg']['vehicleStatusInfo'])
            except:
                raise ApiError('NOK parsing status: ' + response)
        else:
            raise ApiError('NOK requesting status. Error: ' + str(response.status_code) + response.text)

        if refresh:
            url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/status'
            response = requests.get(url, headers=headers)
            logging.debug('got status refreshed')
            if response.status_code == 200:
                try:
                    response = json.loads(response.text)
                    logging.debug(response['resMsg'])
                    _fullstatus.vehicleStatus = from_dict(data_class=rawVehicleStatus, data=response['resMsg'])
                except:
                    raise ApiError('NOK parsing full status: ' + response)
            else:
                raise ApiError('NOK requesting status. Error: ' + str(response.status_code) + response.text)
            try:
                _fullstatus.vehicleLocation = self.api_get_location(True)
            except:
                api_error('could not fetch location from vehicle')
        return _fullstatus

    def api_get_status(self, refresh=False, parsed=False):
        logging.debug('into get status')
        # get status either from cache or not
        if not self.check_control_token(): return False
        logging.debug('checked control token')
        cachestring = '' if refresh else '/latest'
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/status' + cachestring
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
            'ccsp-device-id': self.controller.session.deviceId
        }
        logging.debug(headers)
        response = requests.get(url, headers=headers)
        logging.debug('got status')
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                # a refresh==True returns a short list, a refresh==False returns a long list.
                # So when not refreshed, select only the vehiclestatus part
                logging.debug(response['resMsg'])
                response = response['resMsg']
                if not refresh: response = response['vehicleStatusInfo']['vehicleStatus']
                if not parsed:
                    # status = rawVehicleStatus()
                    _status = from_dict(data_class=rawVehicleStatus, data=response)
                    return _status
                else:
                    # TODO # transform into ParsedStatus
                    _status = ParsedVehicleStatus()
                    _status.lastUpdated = datetime.strptime(response['time'], '%Y%m%d%H%M%S')
                    _status.chassis.hoodOpen = response['hoodOpen']
                    _status.chassis.trunkOpen = response['trunkOpen']
                    _status.chassis.locked = response['doorLock']
                    _status.chassis.openDoors.frontLeft = convert_to_bool(response['doorOpen']['frontLeft'])
                    _status.chassis.openDoors.backLeft = convert_to_bool(response['doorOpen']['backLeft'])
                    _status.chassis.openDoors.backRight = convert_to_bool(response['doorOpen']['backRight'])
                    _status.chassis.openDoors.frontRight = convert_to_bool(response['doorOpen']['frontRight'])
                    _status.chassis.tirePressureWarningLamp.frontRight = convert_to_bool(
                        response['tirePressureLamp']['tirePressureLampFR'])
                    _status.chassis.tirePressureWarningLamp.frontLeft = convert_to_bool(
                        response['tirePressureLamp']['tirePressureLampFL'])
                    _status.chassis.tirePressureWarningLamp.rearLeft = convert_to_bool(
                        response['tirePressureLamp']['tirePressureLampRL'])
                    _status.chassis.tirePressureWarningLamp.rearRight = convert_to_bool(
                        response['tirePressureLamp']['tirePressureLampRR'])
                    _status.chassis.tirePressureWarningLamp.all = convert_to_bool(
                        response['tirePressureLamp']['tirePressureLampAll'])
                    _status.climate.active = response['airCtrlOn']
                    _status.climate.steeringwheelHeat = convert_to_bool(response['steerWheelHeat'])
                    _status.climate.sideMirrorHeat = False
                    _status.climate.rearWindowHeat = convert_to_bool(response['sideBackWindowHeat'])
                    _status.climate.defrost = response['defrost']
                    _status.climate.temperatureSetpoint = hex2temp(response['airTemp']['value'])
                    _status.climate.temperatureUnit = response['airTemp']['unit']
                    _status.engine.ignition = response['engine']
                    _status.engine.accessory = response['acc']
                    try:
                        _status.engine.rangeGas = response['evStatus']['drvDistance'][0]['rangeByFuel']['gasModeRange'][
                            'value']
                    except KeyError as e:
                        _status.engine.rangeGas = 0
                    _status.engine.range = response['evStatus']['drvDistance'][0]['rangeByFuel']['totalAvailableRange'][
                        'value']
                    _status.engine.rangeEV = response['evStatus']['drvDistance'][0]['rangeByFuel']['evModeRange'][
                        'value']
                    _status.engine.pluggedTo = response['evStatus']['batteryPlugin']
                    _status.engine.charging = response['evStatus']['batteryCharge']
                    _status.engine.estimatedCurrentChargeDuration = response['evStatus']['remainTime2']['atc']['value']
                    _status.engine.estimatedFastChargeDuration = response['evStatus']['remainTime2']['etc1']['value']
                    _status.engine.estimatedPortableChargeDuration = response['evStatus']['remainTime2']['etc2'][
                        'value']
                    _status.engine.estimatedStationChargeDuration = response['evStatus']['remainTime2']['etc3']['value']
                    _status.engine.batteryCharge12v = response['battery']['batSoc']
                    _status.engine.batteryChargeHV = response['evStatus']['batteryStatus']
                    return _status
            except:
                raise ApiError('NOK parsing status: ' + response)
        else:
            raise ApiError('NOK requesting status. Error: ' + str(response.status_code) + response.text)

    def api_get_odometer(self):
        if not self.check_control_token(): return False
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/status/latest'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
            'ccsp-device-id': self.controller.session.deviceId
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return from_dict(data_class=VehicleOdometer, data=response)
            except ValueError:
                raise ApiError('NOK Parsing odometer: ' + response)
        else:
            raise ApiError('NOK requesting odometer. Error: ' + str(response.status_code) + response.text)

    def api_get_location(self, refresh=True):
        if not self.check_control_token(): return False
        _coord = ''
        # location
        if refresh:
            url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/location'
            headers = {
                'Host': BaseHost[self.userConfig.brand], 'Accept': Accept,
                'Authorization': self.controller.session.controlToken,
                'ccsp-application-id': CcspApplicationId,
                'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
                'stamp': self.controller.session.stamp,
                'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
                'ccsp-device-id': self.controller.session.deviceId
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                try:
                    response = json.loads(response.text)
                    _coord = response['resMsg']['gpsDetail']['coord']
                    _coord = from_dict(data_class=VehicleLocation, data=_coord)
                except ValueError:
                    raise ApiError('NOK Parsing location: ' + response)
            else:
                raise ApiError('NOK requesting location. Error: ' + str(response.status_code) + response.text)
        else:
            try:
                _coord: FullVehicleStatus() = self.api_get_fullstatus(False)
                _coord = _coord.vehicleLocation.coord
            except:
                api_error('could not fetch cached location')
        return _coord

    def api_set_lock(self, action='close'):
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
            raise ApiError('NOK Invalid locking parameter')

        if not self.check_control_token(): return False

        # location
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/control/door'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
            'ccsp-device-id': self.controller.session.deviceId
        }

        data = {"self.controller.session.deviceId": self.controller.session.deviceId, "action": action}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            logging.debug("Send (un)lock command to Vehicle")
            return True
        else:
            raise ApiError('Error sending lock. Error: ' + str(response.status_code) + response.text)

    def api_set_charge(self, action='stop'):
        if action == "":
            raise ApiError('NOK Emtpy charging parameter')
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
            raise ApiError('NOK Invalid charging parameter')
        if not self.check_control_token(): return False
        # location
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/control/charge'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
            'ccsp-device-id': self.controller.session.deviceId
        }

        data = {"self.controller.session.deviceId": self.controller.session.deviceId, "action": action}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            logging.debug("Send (stop) charge command to Vehicle")
            return True
        else:
            raise ApiError('Error sending start/stop charge. Error: ' + str(response.status_code) + response.text)

    def api_set_hvac(self, action='stop', temp='21.0', bdefrost=False, bheating=False):
        # todo get input from formatted @dataclass
        if action == "":
            raise ApiError('NOK Emtpy HVAC parameter')
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
            raise ApiError('NOK Invalid HVAC parameter')
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
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
            'ccsp-device-id': self.controller.session.deviceId
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
            raise ApiError('Error sending HVAC settings. Error: ' + str(response.status_code) + response.text)

    # ------------ tests -----------
    def api_get_chargeschedule(self):
        if not self.check_control_token(): return False
        # location
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/reservation/charge'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
            'ccsp-device-id': self.controller.session.deviceId
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                # TODO get schedule response
                return response['resMsg']
            except ValueError:
                raise ApiError('NOK Parsing charge schedule: ' + response)
        else:
            raise ApiError('NOK requesting charge schedule. Error: ' + str(response.status_code) + response.text)

    def api_set_chargeschedule(self, schedule1, schedule2, tempset, chargeschedule):
        # todo get input from formatted @dataclass
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
        data = self.api_get_chargeschedule()
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
                        data['reserveChargeInfo2']['reservChargeInfoDetail']['reservChargeSet'] = False
                    else:
                        data['reserveChargeInfo2']['reservChargeInfoDetail']['reservChargeSet'] = True
                        schedule = {"day": schedule2[0],
                                    "time": {"time": str(schedule2[1][0]), "timeSection": int(schedule2[2][1])}}
                        data['reserveChargeInfo2']['reservChargeInfoDetail']['reservInfo'] = schedule

                if not (tempset is None or tempset is True):  # ignore it of True or None
                    if tempset is False:  # turn the schedule off
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservFatcSet']['airCtrl'] = 0
                        data['reserveChargeInfo2']['reservChargeInfoDetail']['reservFatcSet']['airCtrl'] = 0
                    else:
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservFatcSet']['airCtrl'] = 1
                        data['reserveChargeInfo2']['reservChargeInfoDetail']['reservFatcSet']['airCtrl'] = 1
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservFatcSet']['airTemp'][
                            'value'] = temp2hex(str(tempset[0]))
                        data['reserveChargeInfo2']['reservChargeInfoDetail']['reservFatcSet']['airTemp'][
                            'value'] = temp2hex(str(tempset[0]))
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservFatcSet']['defrost'] = tempset[1]
                        data['reserveChargeInfo2']['reservChargeInfoDetail']['reservFatcSet']['defrost'] = tempset[1]

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

                url = BaseURL[
                          self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/reservation/charge'
                headers = {
                    'Host': BaseHost[self.userConfig.brand], 'Accept': Accept,
                    'Authorization': self.controller.session.controlToken,
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
                raise ApiError('NOK setting charge schedule.')
        raise ApiError('NOK setting charge schedule.')

    def api_set_chargelimits(self, limit_fast=80, limit_slow=100):
        # todo get input from formatted @dataclass
        if not self.check_control_token(): return False
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/charge/target'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
            'ccsp-device-id': self.controller.session.deviceId
        }
        data = {'targetSOClist': [{'plugType': 0, 'targetSOClevel': int(limit_fast)},
                                  {'plugType': 1, 'targetSOClevel': int(limit_slow)}]}
        response = requests.post(url, json=data, headers=headers, cookies=self.controller.session.cookies)
        if response.status_code == 200:
            return True
        else:
            raise ApiError('NOK setting charge limits. Error: ' + str(response.status_code) + response.text)

    def api_get_chargetarget(self):
        if not self.check_control_token(): return False
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/charge/target'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
            'ccsp-device-id': self.controller.session.deviceId
        }
        response = requests.get(url, headers=headers, cookies=self.controller.session.cookies)
        if response.status_code == 200:
            response = json.loads(response.text)
            response = response['resMsg']['targetSOClist']
            return response
        else:
            raise ApiError('NOK getting charge targets. Error: ' + str(response.status_code) + response.text)

    def api_set_navigation(self, poiinformations):
        print(poiinformations)
        if len(poiinformations) > 3:
            poiinformations[1] = poiinformations[-2]
            poiinformations[2] = poiinformations[-1]
            poiinformations = poiinformations[:3]
        i = 0
        for poiinformation in poiinformations:
            poiinformation['waypointID'] = i
            poiinformation["zip"] = poiinformation["phone"]= ""
            poiinformation["lang"]= 1
            poiinformation["src"]= "HERE"
            i += 1
        print(poiinformations)
        # todo get input from formatted @dataclass
        if not self.check_control_token(): return False
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/location/routes'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
            'ccsp-device-id': self.controller.session.deviceId
        }
        data = {'deviceId': self.controller.session.deviceId, 'poiInfoList': poiinformations}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return True
        else:
            raise ApiError('NOK setting navigation. Error: ' + str(response.status_code) + response.text)
        # TODO test what will happen if you send an array of 2 or more POI's, will it behave like a route-plan ?

    def api_get_userinfo(self):
        if not self.check_control_token(): return False
        # location
        url = BaseURL[self.userConfig.brand] + '/api/v1/user/profile'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
            'ccsp-device-id': self.controller.session.deviceId
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response
            except ValueError:
                raise ApiError('NOK Getting user info: ' + response)
        else:
            raise ApiError('NOK Getting user info. Error: ' + str(response.status_code) + response.text)

    def api_get_services(self):
        if not self.check_control_token(): return False
        # location
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/setting/service'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
            'ccsp-device-id': self.controller.session.deviceId
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                # TODO get categories response
                return response['resMsg']['serviceCategorys']
                # returns array of booleans for each service in the list
                # 0= categoryname:1 = GIS
                # 1= categoryname:2 = Product and service improvements
                # 2= categoryname:3 = Alerts & security
                # 3= categoryname:4 = Vehicle Status (report, trips)
                # 4= categoryname:5 = Remote
            except ValueError:
                raise ApiError('NOK Getting active services: ' + response)
        else:
            raise ApiError('NOK Getting active services. Error: ' + str(response.status_code) + response.text)

    def api_set_activeservices(self, servicesonoff):
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
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
            'ccsp-device-id': self.controller.session.deviceId
        }
        data = {'serviceCategorys': []}
        i = 0
        for service_on_off in servicesonoff:
            data['serviceCategorys'][i]['categoryName'] = i + 1
            data['serviceCategorys'][i]['categoryStatus'] = service_on_off
        response = requests.post(url, data=data, headers=headers)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                # TODO get services response
                return response['resMsg']
            except ValueError:
                raise ApiError('NOK Getting active services: ' + response)
        else:
            raise ApiError('NOK Getting active services. Error: ' + str(response.status_code) + response.text)

    def api_get_monthlyreport(self, yearmonth=None):
        # todo get input from formatted @dataclass
        if yearmonth is None: yearmonth = datetime.today().strftime('%Y%m')
        if not self.check_control_token(): return False
        # location
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/monthlyreport'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
            'ccsp-device-id': self.controller.session.deviceId
        }
        data = {'setRptMonth': yearmonth}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                # TODO get montlyreport response
                return response['resMsg']['monthlyReport']
            except ValueError:
                raise ApiError('NOK Getting montly report: ' + response)
        else:
            raise ApiError('NOK Getting monthlyreport. Error: ' + str(response.status_code) + response.text)

    # todo get input from formatted @dataclass
    def api_get_tripinfo(self, tripdate=datetime.today().strftime('%Y%m%d')):  # tripdate defaults to today, else yyyymmdd or yyyymm
        if len(tripdate) == 6: data = {'setTripMonth': tripdate, 'tripPeriodType': 0}
        else: data = {'setTripDay': tripdate, 'tripPeriodType': 1}
        url = BaseURL[self.userConfig.brand] + '/api/v1/spa/vehicles/' + self.vehicleConfig.id + '/tripinfo'
        headers = {
            'Authorization': self.controller.session.accessToken,
            'Content-Type': ContentJSON,
            'stamp': self.controller.session.stamp,
            'ccsp-device-id': self.controller.session.deviceId
        }
        response = requests.post(url, headers=headers, json=data, cookies=self.controller.session.cookies)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                # TODO get tripinfo response
                return response['resMsg']
            except ValueError:
                raise ApiError('NOK Parsing tripinfo: ' + response)
        else:
            raise ApiError('NOK requesting tripinfo. Error: ' + str(response.status_code) + response.text)

    def api_get_monthlyreportlist(self):  # is disallowed
        if not self.check_control_token(): return False
        # location
        url = BaseURL[self.userConfig.brand] + '/api/v2/spa/vehicles/' + self.vehicleConfig.id + '/monthlyreportlist'
        headers = {
            'Host': BaseHost[self.userConfig.brand], 'Accept': Accept,
            'Authorization': self.controller.session.controlToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
            'stamp': self.controller.session.stamp,
            'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
            'ccsp-device-id': self.controller.session.deviceId
        }
        response = requests.get(url, headers=headers)
        print(response.text)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                # TODO get monthlyreport response
                return response['resMsg']['monthlyReport']
            except ValueError:
                raise ApiError('NOK Getting montly reportlist: ' + response)
        else:
            raise ApiError('NOK Getting monthlyreportlist. Error: ' + str(response.status_code) + '\n' + response.text)


'''
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
            raise ApiError('NOK prewakeup. Error: ' + str(response.status_code) + response.text)
            return False
'''
