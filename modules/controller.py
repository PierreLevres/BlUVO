''' to control account and vehicle'''

import requests, uuid, json, logging, pickle
import urllib.parse as urlparse
from urllib.parse import parse_qs
from datetime import datetime, timedelta

from interface import BluelinkyConfig, Session, VehicleRegisterOptions
from generic import api_error
from constants import *
from vehicle import EUvehicle
class EUcontroller:

    session : Session
    session = {'accesstoken':'','refreshToken': None, 'controlToken': '', 'deviceId': '', 'accessTokenExpiresAt': 0, 'stamp': ""}
    userconfig : BluelinkyConfig
    vehicles: []

    def __init__(self, userconfig: BluelinkyConfig):
        self.userconfig = userconfig
        self.session.deviceId = uuid.uuid4()
        import random
        with open(self.userconfig.brand + 'list.txt') as f: lines = f.readlines()
        self.session.stamp = random.choice(lines).rstrip("\n")
        logging.debug("controller created")
        logging.debug(self.session)


        #todo make async and wait until IO error / timeout
        # async def
        #try:
        # await call...
        #except errors
        
    def refreshAccessToken(self):
        if self.session.refreshToken is None:
            api_error('Need refresh token to refresh access token. Use login()')
            return False
        logging.debug('access token expires at %s', self.session.accessTokenExpiresAt)
        if (datetime.now() - self.session.accessTokenExpiresAt).total_seconds() < -60:  # 1 minutes beforehand refresh the access token
            logging.debug('no need to refresh access token')
            return False
        else:
            logging.debug('need to refresh access token')
            url = BaseURL[self.userconfig.brand] + '/api/v1/user/oauth2/token'
            headers = {
                'Host': BaseHost[self.userconfig.brand],
                'Content-type': ContentType,
                'Accept-Encoding': AcceptEncoding,
                'Connection': Connection,
                'Accept': Accept,
                'User-Agent': UserAgent,
                'Accept-Language': AcceptLanguage,
                'Stamp': self.session.stamp,
                'Authorization': BasicToken[self.userconfig.brand]
            }
            logging.debug(headers)
            data = 'redirect_uri=' + BaseURL[self.userconfig.brand] + '/api/v1/user/oauth2/redirect&refresh_token=' + self.session.refreshToken + '&grant_type=refresh_token'
            response = requests.post(url, data=data, headers=headers)
            logging.debug('refreshed access token %s', response)
            logging.debug('response text %s', json.loads(response.text))
            if response.status_code == 200:
                try:
                    response = json.loads(response.text)
                    self.session.accessToken = 'Bearer ' + response['access_token']
                    self.session.accessTokenExpiresAt = datetime.now() + timedelta(seconds=response['expires_in'])
                    logging.info('refreshed access token %s expires in %s seconds at %s', self.session.accessToken[:40], response['expires_in'], self.session.accessTokenExpiresAt)
                    with open('session.pkl', 'wb') as f: pickle.dump(self.session, f)
                    return True
                except:
                    api_error('Refresh token failed: ' + response)
                    return False
            else:
                api_error('Refresh token failed: ' + str(response.status_code) + response.text)
                return False


    def enter_pin(self):
        url = BaseURL[self.userconfig.brand] + '/api/v1/user/pin'
        headers = {
            'Host': BaseHost[self.userconfig.brand],
            'Content-Type': ContentType,
            'Accept-Encoding': AcceptEncoding,
            'Connection': Connection,
            'Accept': Accept,
            'User-Agent': UserAgent,
            'Accept-Language': AcceptLanguage,
            'Stamp': self.session.stamp,
            'Authorization': self.session.accessToken
        }
        data = {"deviceId": self.session.deviceId, "pin": self.userconfig.pin}
        #    response = requests.put(url, json=data, headers=headers)
        response = requests.put(url, json=data, headers=headers, cookies=self.session.cookies)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                self.session.controlToken = 'Bearer ' + response['controlToken']
                self.session.controlTokenExpiresAt = datetime.now() + timedelta(seconds=response['expiresTime'])
                logging.debug("Pin set, new control token %s, expires in %s seconds at %s",
                              self.session.controlToken[:40], response['expiresTime'], self.session.controlTokenExpiresAt)
                return True
            except:
                api_error('NOK pin. Error: ' + response)
                return False
        else:
            api_error('NOK pin. Error: ' + str(response.status_code) + response.text)
            return False

    def logout(self):
        return True


    def login(self):
        logging.info('entering login %s %s', self.userconfig.brand, self.userconfig.username)
        logging.debug('login with service id:%s | basictoken: %s | applicationid: %s | basehost: %s | baseurl: %s | stamp: %s', ServiceId[self.userconfig.brand], BasicToken[self.userconfig.brand], ApplicationId[self.userconfig.brand], BaseHost[self.userconfig.brand], BaseURL[self.userconfig.brand], self.session.stamp)
        try:
            with open('session.pkl', 'rb') as f: self.session = pickle.load(f)
            logging.info('session read %s',self.session.accessTokenExpiresAt)
            logging.debug("Read session parameters from pickls")
        except:
            logging.info('session not read from file, full login')
            self.session.controlToken = self.session.accessToken = self.session.refreshToken = None
            self.session.controlTokenExpiresAt = self.session.accessTokenExpiresAt = datetime(1970, 1, 1, 0, 0, 0)
            try:
                # ---cookies----------------------------------
                url = BaseURL[self.userconfig.brand] + '/api/v1/user/oauth2/authorize?response_type=code&client_id=' + ServiceId[self.userconfig.brand] + '&redirect_uri=' + BaseURL[self.userconfig.brand] + '/api/v1/user/oauth2/redirect&state=test&lang=en'
                session = requests.Session()
                response = session.get(url)
                if response.status_code != 200:
                    api_error('NOK cookie for login. Error: ' + str(response.status_code) + response.text)
                    return False
                self.session.cookies = session.cookies.get_dict()
    
                # --- set language----------------------------------
                url = BaseURL[self.userconfig.brand] + '/api/v1/user/language'
                headers = {
                    'Host': BaseHost[self.userconfig.brand],
                    'Content-Type': ContentJSON,
                    'Origin': BaseURL[self.userconfig.brand],
                    'Connection': Connection,
                    'Accept': Accept,
                    'User-Agent': UserAgentPreLogon,
                    'Referer': BaseURL[self.userconfig.brand] + '/web/v1/user/authorize?lang=en&cache=reset',
                    'Accept-Language': AcceptLanguageShort,
                    'Accept-Encoding': AcceptEncoding,
                    'Stamp': self.session.stamp,
                }
                data = {"lang": "en"}
                requests.post(url, json=data, headers=headers, cookies=self.session.cookies)
    
                # ---get deviceid----------------------------------
                url = BaseURL[self.userconfig.brand] + '/api/v1/spa/notifications/register'
                headers = {
                    'ccsp-service-id': ServiceId[self.userconfig.brand],
                    'cssp-application-id': CcspApplicationId,
                    'Content-Type': ContentJSON,
                    'Host': BaseHost[self.userconfig.brand],
                    'Connection': Connection,
                    'Accept': Accept,
                    'Accept-Encoding': AcceptEncoding,
                    'Accept-Language': AcceptLanguage,
                    'Stamp': self.session.stamp,
                    'User-Agent': UserAgent}
                # what to do with the cookie? account=Nj<snip>>689c3
                # what to do with the right PushRegId
                data = {"pushRegId": "0827a4e6c94faa094fe20033ff7fdbbd3a7a789727546f2645a0f547f5db2a58", "pushType": "APNS", "uuid": str(uuid.uuid1())}
                response = requests.post(url, json=data, headers=headers)
                if response.status_code != 200:
                    api_error('NOK deviceID. Error: ' + str(response.status_code) + response.text)
                    return False
                try:
                    response = json.loads(response.text)
                    self.session.deviceId = response['resMsg']['deviceId']
                    logging.info("deviceId %s", self.session.deviceId)
                except:
                    api_error('NOK login. Error in parsing /signing request' + response)
                    return False
                # ---signin----------------------------------
                url = BaseURL[self.userconfig.brand] + '/api/v1/user/signin'
                headers = {
                    'Host': BaseHost[self.userconfig.brand],
                    'Content-Type': ContentJSON,
                    'Origin': BaseURL[self.userconfig.brand],
                    'Connection': Connection,
                    'Accept': Accept,
                    'User-Agent': UserAgentPreLogon,
                    'Referer': BaseURL[self.userconfig.brand]+'/web/v1/user/signin',
                    'Accept-Language': AcceptLanguageShort,
                    'Stamp': self.session.stamp,
                    'Accept-Encoding': AcceptEncoding
                }
                data = {"email":self.userconfig.username, "password": self.userconfig.password}
                response = requests.post(url, json=data, headers=headers, cookies=self.session.cookies)
                if response.status_code != 200:
                    api_error('NOK login. Error: ' + str(response.status_code) + response.text)
                    return False
                try:
                    response = json.loads(response.text)
                    response = response['redirectUrl']
                    parsed = urlparse.urlparse(response)
                    authcode = ''.join(parse_qs(parsed.query)['code'])
                    logging.info("authCode %s", authcode)
                except:
                    api_error('NOK login. Error in parsing /signing request' + response)
                    return False
    
                # ---get accesstoken----------------------------------
                url = BaseURL[self.userconfig.brand] + '/api/v1/user/oauth2/token'
                headers = {
                    'Host': BaseHost[self.userconfig.brand],
                    'Content-Type': ContentType,
                    'Accept-Encoding': AcceptEncoding,
                    'Connection': Connection,
                    'Accept': Accept,
                    'User-Agent': UserAgent,
                    'Accept-Language': AcceptLanguage,
                    'Stamp': self.session.stamp,
                    'Authorization': BasicToken[self.userconfig.brand]
                }
                data = 'redirect_uri=' + BaseURL[self.userconfig.brand] + '/api/v1/user/oauth2/redirect&code=' + authcode + '&grant_type=authorization_code'
                response = requests.post(url, data=data, headers=headers)
                if response.status_code != 200:
                    api_error('NOK token. Error: ' + str(response.status_code) + response.text)
                    return False
                try:
                    response = json.loads(response.text)
                    self.session.accessToken = 'Bearer ' + response['access_token']
                    self.session.refreshToken = response['refresh_token']
                    self.session.accessTokenExpiresAt = datetime.now() + timedelta(seconds=response['expires_in'])
                    logging.info("accesstoken %s, refrestoken %s expiresAt %s", self.session.accessToken, self.session.refreshToken, self.session.accessTokenExpiresAt)
                except:
                    api_error('NOK login. Error in parsing /token request' + response)
                    return False
                with open('session.pkl', 'wb') as f:
                    pickle.dump(self.session, f)
                logging.debug("Finished successfull login procedure")
            except:
                api_error('NOK login. Somewhere strange and unforseen. Good luck!')
                return False
        return True

    def getvehicles(self):
        if self.session.accessToken == '':
            api_error('NOK token. Token not set: ')
            return False
        # ---get vehicles----------------------------------
        url = BaseURL[self.userconfig.brand] + '/api/v1/spa/vehicles'
        headers = {
            'Host': BaseHost[self.userconfig.brand],
            'Accept': Accept,
            'Authorization': self.session.accessToken,
            'ccsp-application-id': CcspApplicationId,
            'Accept-Language': AcceptLanguage,
            'Accept-Encoding': AcceptEncoding,
            'offset': '2',
            'User-Agent': UserAgent,
            'Connection': Connection,
            'Content-Type': ContentJSON,
            'Stamp': self.session.stamp,
            'ccsp-device-id': self.session.deviceId
        }
        response = requests.get(url, headers=headers, cookies=self.session.cookies)
        if response.status_code != 200:
            api_error('NOK vehicles. Error: ' + str(response.status_code) + response.text)
            return False

        try:
            response = json.loads(response.text)
            logging.debug("response %s", response)
            vehiclesonaccount = response['resMsg']['vehicles']
            logging.debug("%s vehicles found", len(vehiclesonaccount))
        except:
            api_error('NOK login. Error in getting vehicles: ' + response)
            return False

        if len(vehiclesonaccount) == 0:
            api_error('NOK login. No vehicles found')
            return False

        # not we got a list of vehicles on the account, gather the data of all of them
        self.vehicles = []
        for v in vehiclesonaccount:
            url = BaseURL[self.userconfig.brand] + '/api/v1/spa/vehicles/' + v['vehicleId'] + '/profile'
            headers = {
                'Host': BaseHost[self.userconfig.brand],
                'Accept': Accept,
                'Authorization': self.session.accessToken,
                'ccsp-application-id': CcspApplicationId,
                'Accept-Language': AcceptLanguage,
                'Accept-Encoding': AcceptEncoding,
                'offset': '2',
                'User-Agent': UserAgent,
                'Connection': Connection,
                'Content-Type': ContentJSON,
                'Stamp': self.session.stamp,
                'ccsp-device-id': self.session.deviceId
            }
            response = requests.get(url, headers=headers, cookies=self.session.cookies)
            try:
                response = json.loads(response.text)
                vehicleProfile = response['resMsg']
                vehicleConfig = VehicleRegisterOptions(v['nickname'], v['vehicleName'],vehicleProfile.vinInfo[0].basic.vin, v['regDate'], 'kia', '', v['vehicleId'], vehicleProfile.vinInfo[0].basic.modelYear)
                anothervehicle = EUvehicle(vehicleConfig, self)
                self.vehicles.append(anothervehicle)
                logging.debug('Added vehicle %s', vehicleConfig.id)
            except:
                api_error('NOK login. Error in getting profile of vehicle: ' + v + response)
                return False
        return self.vehicles


#snippet:
# loop through all vehicles and pick the right one to manage
#if vehicleId is None:
#    api_error('NOK login. The VIN you entered is not in the vehicle list ' + vin)
#    return False
#else:
#    vehicleId = vehicles[0]['vehicleId']
#logging.info("vehicleID %s", vehicleId)
#            if vehicle['vin'] == vin: vehicleId = vehicle['vehicleId']


def api_wakeup(self):
    url = BaseURL[self.userconfig.brand] + '/api/v1/spa/vehicles/' + vehicleId + '/control/engine'
    headers = {
        'Host': BaseHost[self.userconfig.brand],
        'Accept': Accept,
        'Authorization': self.session.accessToken,
        'Accept-Encoding': AcceptEncoding,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage,
        'offset': '2',
        'User-Agent': UserAgent,
        'Connection': Connection,
        'Content-Type': ContentJSON,
        'Stamp': self.session.stamp,
        'ccsp-device-id': self.session.deviceId
    }
    data = {"action": "prewakeup", "deviceId": self.session.deviceId}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return True
    else:
        api_error('NOK prewakeup. Error: ' + str(response.status_code) + response.text)
        return False

