#TODO add versioning
import requests
import uuid
import json
import logging
import pickle
import urllib.parse as urlparse
from urllib.parse import parse_qs
from datetime import datetime, timedelta
from time import time

global ServiceId, BasicToken, ApplicationId, BaseHost, BaseURL, UserAgentPreLogon, UserAgent, ContentType, ContentJSON, AcceptLanguage, AcceptLanguageShort, AcceptEncoding, Connection, Accept, CcspApplicationId
global controlToken, controlTokenExpiresAt
global accessToken, accessTokenExpiresAt, refreshToken
global deviceId, vehicleId, cookies
global email, password, pin, vin
global stamp

def api_error(message):
    logger = logging.getLogger('root')
    logger.error(message)
    print(message)


def temp2hex(temp):
    if temp <= 14: return "00H"
    if temp >= 30: return "20H"
    return str.upper(hex(round(float(temp) * 2) - 28).split("x")[1]) + "H"  # rounds to .5 and transforms to Kia-hex (cut off 0x and add H at the end)


def hex2temp(hextemp):
    temp = int(hextemp[:2], 16) / 2 + 14
    if temp <= 14: return 14
    if temp >= 30: return 30
    return temp

def createStamp(carbrand):
    import random
    filename = carbrand+'list.txt'
    with open(carbrand+'list.txt') as f:
        lines = f.readlines()
    return random.choice(lines).rstrip("\n")

def get_constants(car_brand):
    global stamp, ServiceId, BasicToken, ApplicationId, BaseHost, BaseURL, UserAgentPreLogon, UserAgent, ContentType, ContentJSON, AcceptLanguage, AcceptLanguageShort, AcceptEncoding, Connection, Accept, CcspApplicationId
    if car_brand == 'kia':
        ServiceId = 'fdc85c00-0a2f-4c64-bcb4-2cfb1500730a'
        BasicToken = 'Basic ZmRjODVjMDAtMGEyZi00YzY0LWJjYjQtMmNmYjE1MDA3MzBhOnNlY3JldA=='
        ApplicationId = '693a33fa-c117-43f2-ae3b-61a02d24f417'
    elif car_brand == 'hyundai':
        ServiceId = '6d477c38-3ca4-4cf3-9557-2a1929a94654'
        BasicToken = 'Basic NmQ0NzdjMzgtM2NhNC00Y2YzLTk1NTctMmExOTI5YTk0NjU0OktVeTQ5WHhQekxwTHVvSzB4aEJDNzdXNlZYaG10UVI5aVFobUlGampvWTRJcHhzVg=='
        ApplicationId = '99cfff84-f4e2-4be8-a5ed-e5b755eb6581'
    else:
        api_error('Carbrand not OK.')
        return False
    stamp = createStamp(car_brand)
    BaseHost = 'prd.eu-ccapi.' + car_brand + '.com:8080'

    UserAgentPreLogon = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_1 like Mac OS X) AppleWebKit/604.3.5 (KHTML, like Gecko) Version/11.0 Mobile/15B92 Safari/604.1'
    UserAgent = 'UVO_REL/1.5.1 (iPhone; iOS 14.0.1; Scale/2.00)'
    UserAgent = 'UVO_Store/1.5.9 (iPhone; iOS 14.4; Scale/3.00)'
    Accept = '*/*'
    CcspApplicationId = '8464b0bf-4932-47b0-90ed-555fef8f143b'
    AcceptLanguageShort = 'nl-nl'
    AcceptLanguage = 'nl-NL;q=1, en-NL;q=0.9'
    AcceptEncoding = 'gzip, deflate, br'
    ContentType = 'application/x-www-form-urlencoded;charset=UTF-8'
    ContentJSON = 'application/json;charset=UTF-8'
    Connection = 'keep-alive'
    BaseURL = 'https://' + BaseHost
    return True


def check_control_token():
    if refresh_access_token():
        logging.debug('accesstoken OK')
        if controlTokenExpiresAt is not None:
            logging.debug('Check pin expiry on %s and now it is %s',controlTokenExpiresAt,datetime.now())
            if controlToken is None or datetime.now() > controlTokenExpiresAt:
                logging.debug('control token expired at %s, about to renew', controlTokenExpiresAt)
                return enter_pin()
    return True


def refresh_access_token():
    global accessToken, accessTokenExpiresAt
    if refreshToken is None:
        api_error('Need refresh token to refresh access token. Use login()')
        return False
    logging.debug('access token expires at %s', accessTokenExpiresAt)
    if (datetime.now() - accessTokenExpiresAt).total_seconds() > -3600: #one hour beforehand refresh the access token
        logging.debug('need to refresh access token')
        url = BaseURL + '/api/v1/user/oauth2/token'
        headers = {
            'Host': BaseHost,
            'Content-type': ContentType,
            'Accept-Encoding': AcceptEncoding,
            'Connection': Connection,
            'Accept': Accept,
            'User-Agent': UserAgent,
            'Accept-Language': AcceptLanguage,
            'Stamp': stamp,
            'Authorization': BasicToken
            }
        logging.debug(headers)
        data = 'redirect_uri=' + BaseURL + '/api/v1/user/oauth2/redirect&refresh_token=' + refreshToken + '&grant_type=refresh_token'
        # response = requests.post(url, data=data, headers=headers, throwHttpErrors=False)
        response = requests.post(url, data=data, headers=headers)
        logging.debug('refreshed access token %s',response)
        logging.debug('response text %s',json.loads(response.text))
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                accessToken = 'Bearer ' + response['access_token']
                accessTokenExpiresAt = datetime.now() + timedelta(seconds=response['expires_in'])
                logging.info('refreshed access token %s expires in %s seconds at %s',
                             accessToken[:40], response['expires_in'], accessTokenExpiresAt)
                with open('session.pkl', 'wb') as f:
                    pickle.dump(
                        [controlToken, accessToken, refreshToken, controlTokenExpiresAt, accessTokenExpiresAt, deviceId,
                         vehicleId, cookies, stamp], f)

                return True
            except:
                api_error('Refresh token failed: ' + response)
                return False
        else:
            api_error('Refresh token failed: ' + str(response.status_code) + response.text)
            return False
    return True


def enter_pin():
    global controlToken, controlTokenExpiresAt
    url = BaseURL + '/api/v1/user/pin'
    headers = {
        'Host': BaseHost,
        'Content-Type': ContentType,
        'Accept-Encoding': AcceptEncoding,
        'Connection': Connection,
        'Accept': Accept,
        'User-Agent': UserAgent,
        'Accept-Language': AcceptLanguage,
        'Stamp': stamp,
        'Authorization': accessToken
    }
    data = {"deviceId": deviceId, "pin": pin}
#    response = requests.put(url, json=data, headers=headers)
    response = requests.put(url, json=data, headers=headers, cookies=cookies)
    if response.status_code == 200:
        try:
            response = json.loads(response.text)
            controlToken = 'Bearer ' + response['controlToken']
            controlTokenExpiresAt = datetime.now() + timedelta(seconds=response['expiresTime'])
            logging.debug("Pin set, new control token %s, expires in %s seconds at %s",
                          controlToken[:40], response['expiresTime'], controlTokenExpiresAt)
            return True
        except:
            api_error('NOK pin. Error: ' + response)
            return False
    else:
        api_error('NOK pin. Error: ' + str(response.status_code) + response.text)
        return False


def login(car_brand, email2, password2, pin2, vin2):

    global controlToken, controlTokenExpiresAt
    global accessToken, accessTokenExpiresAt, refreshToken
    global deviceId, vehicleId, cookies
    global email, password, pin, vin, stamp
    email = email2
    password = password2
    pin = pin2
    vin = vin2
    url = "no URL set yet"
    logging.info('entering login %s %s', car_brand, email2)
    get_constants(car_brand)
    logging.debug('constants %s %s %s %s %s %s', ServiceId, BasicToken, ApplicationId, BaseHost, BaseURL, stamp)
    try:
        with open('session.pkl', 'rb') as f:
            controlToken, accessToken, refreshToken, controlTokenExpiresAt, accessTokenExpiresAt, deviceId, vehicleId, cookies, stamp = pickle.load(f)
            logging.info('session read %s',accessTokenExpiresAt)
    except:
        logging.info('session not read from file, full login')
        controlToken = accessToken = refreshToken = None
        controlTokenExpiresAt = accessTokenExpiresAt = datetime(1970, 1, 1, 0, 0, 0)

        try:
            # ---cookies----------------------------------
            url = BaseURL + '/api/v1/user/oauth2/authorize?response_type=code&client_id=' + ServiceId + '&redirect_uri=' + BaseURL + '/api/v1/user/oauth2/redirect&state=test&lang=en'
            session = requests.Session()
            response = session.get(url)
            if response.status_code != 200:
                api_error('NOK cookie for login. Error: ' + str(response.status_code) + response.text)
                return False

            cookies = session.cookies.get_dict()

            # https: // prd.eu - ccapi.kia.com: 8080 / web / v1 / user / authorize?lang = en & cache = reset
            # https: // prd.eu - ccapi.kia.com: 8080 / web / v1 / user / static / css / main.dbfc71fc.chunk.css
            # https: // prd.eu - ccapi.kia.com: 8080 / web / v1 / user / static / js / 2.cf048054.chunk.js
            # https: // prd.eu - ccapi.kia.com: 8080 / web / v1 / user / static / js / main.b922ef51.chunk.js

            # --- set language----------------------------------
            url = BaseURL + '/api/v1/user/language'
            headers = {
                'Host': BaseHost,
                'Content-Type': ContentJSON,
                'Origin': BaseURL,
                'Connection': Connection,
                'Accept': Accept,
                'User-Agent': UserAgentPreLogon,
                'Referer': BaseURL + '/web/v1/user/authorize?lang=en&cache=reset',
                'Accept-Language': AcceptLanguageShort,
                'Accept-Encoding': AcceptEncoding
            }
            data = {"lang": "en"}
            requests.post(url, json=data, headers=headers, cookies=cookies)

            # ---get deviceid----------------------------------
            url = BaseURL + '/api/v1/spa/notifications/register'
            headers = {
                'ccsp-service-id': ServiceId,
                'cssp-application-id': CcspApplicationId,
                'Content-Type': ContentJSON,
                'Host': BaseHost,
                'Connection': Connection,
                'Accept': Accept,
                'Accept-Encoding': AcceptEncoding,
                'Accept-Language': AcceptLanguage,
                'Stamp': stamp,
                'User-Agent': UserAgent}
            # what to do with the cookie? account=Nj<snip>>689c3
            # what to do with the right PushRegId
            data = {"pushRegId": "0827a4e6c94faa094fe20033ff7fdbbd3a7a789727546f2645a0f547f5db2a58", "pushType": "APNS", "uuid": str(uuid.uuid1())}
            logging.debug(headers)
            logging.debug(data)
            response = requests.post(url, json=data, headers=headers)
            if response.status_code != 200:
                api_error('NOK deviceID. Error: ' + str(response.status_code) + response.text)
                return False
            try:
                response = json.loads(response.text)
                deviceId = response['resMsg']['deviceId']
                logging.info("deviceId %s", deviceId)
            except:
                api_error('NOK login. Error in parsing /signing request' + response)
                return False


            # get session
            # delete session

            # ---signin----------------------------------
            url = BaseURL + '/api/v1/user/signin'
            headers = {
                'Host': BaseHost,
                'Content-Type': ContentJSON,
                'Origin': BaseURL,
                'Connection': Connection,
                'Accept': Accept,
                'User-Agent': UserAgentPreLogon,
                'Referer': BaseURL+'/web/v1/user/signin',
                'Accept-Language': AcceptLanguageShort,
                'Stamp': stamp,
                'Accept-Encoding': AcceptEncoding
            }
            data = {"email": email, "password": password}
            response = requests.post(url, json=data, headers=headers, cookies=cookies)
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
            url = BaseURL + '/api/v1/user/oauth2/token'
            headers = {
                'Host': BaseHost,
                'Content-Type': ContentType,
                'Accept-Encoding': AcceptEncoding,
                'Connection': Connection,
                'Accept': Accept,
                'User-Agent': UserAgent,
                'Accept-Language': AcceptLanguage,
                'Stamp': stamp,
                'Authorization': BasicToken
            }
            data = 'redirect_uri=' + BaseURL + '/api/v1/user/oauth2/redirect&code=' + authcode + '&grant_type=authorization_code'
            response = requests.post(url, data=data, headers=headers)
            if response.status_code != 200:
                api_error('NOK token. Error: ' + str(response.status_code) + response.text)
                return False
            try:
                response = json.loads(response.text)
                accessToken = 'Bearer ' + response['access_token']
                refreshToken = response['refresh_token']
                accessTokenExpiresAt = datetime.now() + timedelta(seconds=response['expires_in'])
                logging.info("accesstoken %s, refrestoken %s expiresAt %s", accessToken, refreshToken, accessTokenExpiresAt)
            except:
                api_error('NOK login. Error in parsing /token request' + response)
                return False
            # notification/register

            # user/profile    --> toevoegen bluelinky?
            # setting/language --> toevoegen bluelinky?
            # setting/service --> toevoegen bluelinky?

            # vehicles

            # ---get vehicles----------------------------------
            url = BaseURL + '/api/v1/spa/vehicles'
            headers = {
                'Host': BaseHost,
                'Accept': Accept,
                'Authorization': accessToken,
                'ccsp-application-id': CcspApplicationId,
                'Accept-Language': AcceptLanguage,
                'Accept-Encoding': AcceptEncoding,
                'offset': '2',
                'User-Agent': UserAgent,
                'Connection': Connection,
                'Content-Type': ContentJSON,
                'Stamp': stamp,
                'ccsp-device-id': deviceId
            }
            response = requests.get(url, headers=headers, cookies=cookies)
            if response.status_code != 200:
                api_error('NOK vehicles. Error: ' + str(response.status_code) + response.text)
                return False
            try:
                response = json.loads(response.text)
                logging.debug("response %s", response)
                vehicles = response['resMsg']['vehicles']
                logging.debug("%s vehicles found", len(vehicles))
            except:
                api_error('NOK login. Error in getting vehicles: ' + response)
                return False
            if len(vehicles) == 0:
                api_error('NOK login. No vehicles found')
                return False
            # ---get vehicleId----------------------------------
            vehicleId = None
            if len(vehicles) > 1:
                for vehicle in vehicles:
                    url = BaseURL + '/api/v1/spa/vehicles/' + vehicle['vehicleId'] + '/profile'
                    headers = {
                        'Host': BaseHost,
                        'Accept': Accept,
                        'Authorization': accessToken,
                        'ccsp-application-id': CcspApplicationId,
                        'Accept-Language': AcceptLanguage,
                        'Accept-Encoding': AcceptEncoding,
                        'offset': '2',
                        'User-Agent': UserAgent,
                        'Connection': Connection,
                        'Content-Type': ContentJSON,
                        'Stamp': stamp,
                        'ccsp-device-id': deviceId
                    }
                    response = requests.get(url, headers=headers, cookies=cookies)
                    try:
                        response = json.loads(response.text)
                        response = response['resMsg']['vinInfo'][0]['basic']
                        vehicle['vin'] = response['vin']
                        vehicle['generation'] = response['modelYear']
                    except:
                        api_error('NOK login. Error in getting profile of vehicle: ' + vehicle + response)
                        return False
                    if vehicle['vin'] == vin: vehicleId = vehicle['vehicleId']
                if vehicleId is None:
                    api_error('NOK login. The VIN you entered is not in the vehicle list ' + vin)
                    return False
            else: vehicleId = vehicles[0]['vehicleId']
            logging.info("vehicleID %s", vehicleId)
            with open('session.pkl', 'wb') as f:
                pickle.dump([controlToken, accessToken, refreshToken, controlTokenExpiresAt, accessTokenExpiresAt, deviceId, vehicleId, cookies, stamp],f)
        except:
            api_error('Login failed '+url + response.text)
            return False
        # the normal startup routine of the app is
        # profile
        # register
        # records
        # dezemoeten niet met de control token maar nog met de access token, te complex om te implementeren
        # api_get_services()
        # api_get_status(False)
        # api_get_parklocation()
        api_set_wakeup()
        # api_get_valetmode()
        # api_get_finaldestination()
        logging.debug("Finished successfull login procedure")
    return True


def api_get_valetmode():
    url = BaseURL + '/api/v1/spa/vehicles/' + vehicleId + '/status/valet'
    headers = {
        'Host': BaseHost,
        'Accept': Accept,
        'Authorization': accessToken,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage,
        'Accept-Encoding': AcceptEncoding,
        'offset': '2',
        'User-Agent': UserAgent,
        'Connection': Connection,
        'Content-Type': ContentJSON,
        'Stamp': stamp,
        'ccsp-device-id': deviceId
    }
    response = requests.get(url, headers=headers, cookies=cookies)
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


def api_get_parklocation():
    url = BaseURL + '/api/v1/spa/vehicles/' + vehicleId + '/location/park'
    headers = {
        'Host': BaseHost,
        'Accept': Accept,
        'Authorization': controlToken,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage,
        'Accept-Encoding': AcceptEncoding,
        'offset': '2',
        'User-Agent': UserAgent,
        'Connection': Connection,
        'Content-Type': ContentJSON,
        'Stamp': stamp,
        'ccsp-device-id': deviceId
    }
    response = requests.get(url, headers=headers, cookies=cookies)
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


def api_get_finaldestination():
    url = BaseURL + '/api/v1/spa/vehicles/' + vehicleId + '/finaldestionation'
    headers = {
        'Host': BaseHost,
        'Accept': Accept,
        'Authorization': controlToken,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage,
        'Accept-Encoding': AcceptEncoding,
        'offset': '2',
        'User-Agent': UserAgent,
        'Connection': Connection,
        'Content-Type': ContentJSON,
        'Stamp': stamp,
        'ccsp-device-id': deviceId
    }
    response = requests.get(url, headers=headers, cookies=cookies)
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


def api_set_wakeup():
    url = BaseURL + '/api/v1/spa/vehicles/' + vehicleId + '/control/engine'
    headers = {
        'Host': BaseHost,
        'Accept': Accept,
        'Authorization': accessToken,
        'Accept-Encoding': AcceptEncoding,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage,
        'offset': '2',
        'User-Agent': UserAgent,
        'Connection': Connection,
        'Content-Type': ContentJSON,
        'Stamp': stamp,
        'ccsp-device-id': deviceId
    }
    data = {"action": "prewakeup", "deviceId": deviceId}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return True
    else:
        api_error('NOK prewakeup. Error: ' + str(response.status_code) + response.text)
        return False


def api_get_status(refresh=False, raw=True):
    logging.debug('into get status')
    # get status either from cache or not
    if not check_control_token(): return False
    logging.debug('checked control token')
    cachestring = '' if refresh else '/latest'
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/status' + cachestring
    headers = {
        'Host': BaseHost, 'Accept': Accept, 'Authorization': controlToken,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
        'Stamp': stamp,
        'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': deviceId
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


def api_get_odometer():
    if not check_control_token(): return False
    # odometer
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/status/latest'
    headers = {
        'Host': BaseHost, 'Accept': Accept, 'Authorization': controlToken,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
        'Stamp': stamp,
        'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': deviceId
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


def api_get_location():
    if not check_control_token(): return False
    # location
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/location'
    headers = {
        'Host': BaseHost, 'Accept': Accept, 'Authorization': controlToken,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
        'Stamp': stamp,
        'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': deviceId
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


def api_set_lock(action='close'):
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

    if not check_control_token(): return False

    # location
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/control/door'
    headers = {
        'Host': BaseHost, 'Accept': Accept, 'Authorization': controlToken,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
        'Stamp': stamp,
        'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': deviceId
    }

    data = {"deviceId": deviceId, "action": action}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        logging.debug("Send (un)lock command to Vehicle")
        return True
    else:
        api_error('Error sending lock. Error: ' + str(response.status_code)  + response.text)
        return False


def api_set_charge(action='stop'):
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
    if not check_control_token(): return False
    # location
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/control/charge'
    headers = {
        'Host': BaseHost, 'Accept': Accept, 'Authorization': controlToken,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
        'Stamp': stamp,
        'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': deviceId
    }

    data = {"deviceId": deviceId, "action": action}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        logging.debug("Send (stop) charge command to Vehicle")
        return True
    else:
        api_error('Error sending start/stop charge. Error: ' + str(response.status_code) + response.text)
        return False


def api_set_hvac(action='stop', temp='21.0', bdefrost=False, bheating=False):
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

    if not check_control_token(): return False
    # location
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/control/temperature'
    headers = {
        'Host': BaseHost, 'Accept': Accept, 'Authorization': controlToken,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
        'Stamp': stamp,
        'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': deviceId
    }
    data = {
        "deviceId": deviceId,
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
def api_get_chargeschedule():
    if not check_control_token(): return False
    # location
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/reservation/charge'
    headers = {
        'Host': BaseHost, 'Accept': Accept, 'Authorization': controlToken,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
        'Stamp': stamp,
        'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': deviceId
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


def api_set_chargeschedule(schedule1, schedule2, tempset, chargeschedule):
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
    if not check_control_token(): return False

    # first get the currens settings
    data = api_get_chargeschedule()
    olddata = data
    if not (not data):
        try:
            # now enter the new settings

            if not (schedule1 is None or schedule1 is True):  # ignore it of True or None
                if schedule1 is False:  # turn the schedule off
                    data['reservChargeInfo']['reservChargeInfoDetail']['reservChargeSet'] = False
                else:
                    data['reservChargeInfo']['reservChargeInfoDetail']['reservChargeSet'] = True
                    schedule = {"day": schedule1[0], "time": {"time": str(schedule1[1][0]), "timeSection": int(schedule1[2][1])}}
                    data['reservChargeInfo']['reservChargeInfoDetail']['reservInfo'] = schedule
            if not (schedule2 is None or schedule2 is True):  # ignore it of True or None
                if schedule2 is False:  # turn the schedule off
                    data['reservChargeInfo2']['reservChargeInfoDetail']['reservChargeSet'] = False
                else:
                    data['reservChargeInfo2']['reservChargeInfoDetail']['reservChargeSet'] = True
                    schedule = {"day": schedule2[0], "time": {"time": str(schedule2[1][0]), "timeSection": int(schedule2[2][1])}}
                    data['reservChargeInfo2']['reservChargeInfoDetail']['reservInfo'] = schedule

            if not (tempset is None or tempset is True):  # ignore it of True or None
                if tempset is False:  # turn the schedule off
                    data['reservChargeInfo']['reservChargeInfoDetail']['reservFatcSet']['airCtrl'] = 0
                    data['reservChargeInfo2']['reservChargeInfoDetail']['reservFatcSet']['airCtrl'] = 0
                else:
                    data['reservChargeInfo']['reservChargeInfoDetail']['reservFatcSet']['airCtrl'] = 1
                    data['reservChargeInfo2']['reservChargeInfoDetail']['reservFatcSet']['airCtrl'] = 1
                    data['reservChargeInfo']['reservChargeInfoDetail']['reservFatcSet']['airTemp']['value'] = temp2hex(str(tempset[0]))
                    data['reservChargeInfo2']['reservChargeInfoDetail']['reservFatcSet']['airTemp']['value'] = temp2hex(str(tempset[0]))
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

            url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/reservation/charge'
            headers = {
                'Host': BaseHost, 'Accept': Accept, 'Authorization': controlToken,
                'ccsp-application-id': CcspApplicationId,
                'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
                'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON,
                'Stamp': stamp,
                'ccsp-device-id': deviceId
            }
            data['deviceId'] = deviceId
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200: return True
        except:
            api_error('NOK setting charge schedule.')
            return False
    api_error('NOK setting charge schedule.')
    return False


def api_set_chargelimits(limit_fast=80, limit_slow=100):
    if not check_control_token(): return False
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/charge/target'
    headers = {
        'Host': BaseHost, 'Accept': Accept, 'Authorization': controlToken,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
        'Stamp': stamp,
        'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': deviceId
    }
    data = {'targetSOClist': [{'plugType': 0, 'targetSOClevel': int(limit_fast)},
                              {'plugType': 1, 'targetSOClevel': int(limit_slow)}]}
    response = requests.post(url, json=data, headers=headers, cookies=cookies)
    if response.status_code == 200:
        return True
    else:
        api_error('NOK setting charge limits. Error: ' + str(response.status_code) + response.text)
        return False


def api_set_navigation(poi_info_list):
    if not check_control_token(): return False
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/location/routes'
    headers = {
        'Host': BaseHost, 'Accept': Accept, 'Authorization': controlToken,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
        'Stamp': stamp,
        'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': deviceId
    }
    data = poi_info_list
    poi_info_list['deviceID'] = deviceId
    response = requests.post(url, json=poi_info_list, headers=headers)
    if response.status_code == 200:
        return True
    else:
        api_error('NOK setting navigation. Error: ' + str(response.status_code) + response.text)
        return False
    #TODO test what will happen if you send an array of 2 or more POI's, will it behave like a route-plan ?


def api_get_userinfo():
    if not check_control_token(): return False
    # location
    url = BaseURL + '/api/v1/user/profile'
    headers = {
        'Host': BaseHost, 'Accept': Accept, 'Authorization': controlToken,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
        'Stamp': stamp,
        'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': deviceId
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


def api_get_services():
    if not check_control_token(): return False
    # location
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/setting/service'
    headers = {
        'Host': BaseHost, 'Accept': Accept, 'Authorization': controlToken,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
        'Stamp': stamp,
        'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': deviceId
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


def api_set_activeservices(servicesonoff=[]):
    # servicesonoff is array of booleans for each service in the list
    # 0= categoryname:1 = GIS
    # 1= categoryname:2 = Product and service improvements
    # 2= categoryname:3 = Alerts & security
    # 3= categoryname:4 = Vehicle Status (report, trips)
    # 4= categoryname:5 = Remote
    if not check_control_token(): return False
    # location
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/setting/service'
    headers = {
        'Host': BaseHost, 'Accept': Accept, 'Authorization': controlToken,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
        'Stamp': stamp,
        'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': deviceId
    }
    data=[]
    i = 0
    for service_on_off in servicesonoff:
        data['serviceCategorys'][i]['categoryName'] = i+1
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


def api_get_monthlyreport(month):
    if not check_control_token(): return False
    # location
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/monthlyreport'
    headers = {
        'Host': BaseHost, 'Accept': Accept, 'Authorization': controlToken,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
        'Stamp': stamp,
        'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': deviceId
    }
    data={'setRptMonth': "202006"}
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


def api_get_monthlyreportlist():
    if not check_control_token(): return False
    # location
    url = BaseURL + '/api/v1/spa/vehicles/' + vehicleId + '/monthlyreportlist'
    headers = {
        'Host': BaseHost, 'Accept': Accept, 'Authorization': controlToken,
        'ccsp-application-id': CcspApplicationId,
        'Accept-Language': AcceptLanguage, 'Accept-Encoding': AcceptEncoding, 'offset': '2',
        'Stamp': stamp,
        'User-Agent': UserAgent, 'Connection': Connection, 'Content-Type': ContentJSON, 'ccsp-device-id': deviceId
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

# TODO implement the other services
'''
api/v1/spa/vehicles/{carid}/monthlyreportlist —> doGetMVRInfoList    --> cant find it
api/v1/spa/vehicles/{carid}/drvhistory —> doPostECOInfo 
api/v1/spa/vehicles/{carid}/tripinfo —> doPostTripInfo --> 403 erorr unless i use V2 api
api/v1/spa/vehicles/{carid}/profile —> doUpdateVehicleName

api/v1/spa/vehicles/{carid}/location/park —>  doCarFinderLatestRequest

api/v2/spa/vehicles/{carid}/control/engine —> doEngine
api/v2/spa/vehicles/{carid}/control/horn —> doHorn
api/v2/spa/vehicles/{carid}/control/light —> doLights
'''