import requests
import uuid
import json
import logging
import urllib.parse as urlparse
from urllib.parse import parse_qs
from datetime import datetime, timedelta

global ServiceId, BasicToken, ApplicationId, BaseHost, BaseURL
global controlToken, controlTokenExpiresAt
global accessToken, accessTokenExpiresAt
global deviceId, vehicleId, cookies
global email, password, pin


def api_error(message):
    logger = logging.getLogger('root')
    logger.error(message)
    print(message)


def temp2hex(temp):
    if temp<14: temp = 14
    if temp>32: temp = 30
    return str.upper(hex(round(float(temp) * 2) - 28).split("x")[1]) + "H"  # rounds to .5 and transforms to hex


def hex2temp(hex):
    return int(hex[:2], 16) / 2 + 14


def get_constants(car_brand):
    global ServiceId, BasicToken, ApplicationId, BaseHost, BaseURL
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
    BaseHost = 'prd.eu-ccapi.' + car_brand + '.com:8080'
    BaseURL = 'https://' + BaseHost
    return True


def check_control_token():
    if refresh_access_token():
        if controlTokenExpiresAt != None:
            # logging.debug('Check pin expiry on %s and now it is %s',controlTokenExpiresAt,datetime.now())
            if controlToken == None or datetime.now() >  controlTokenExpiresAt:
                return enter_pin()
    return True


def refresh_access_token():
    global accessToken, accessTokenExpiresAt
    if refreshToken == None:
        api_error('Need refresh token to refresh access token. Use login()')
        return False
    if (datetime.now() - accessTokenExpiresAt).total_seconds() > -0.1:
        url = BaseURL + '/api/v1/user/oauth2/token'
        headers = {
            'Authorization': BasicToken,
            'Content-type': 'application/x-www-form-urlencoded',
            'Host': BaseHost,
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'okhttp/3.10.0'}
        data = 'grant_type=refresh_token&redirect_uri=https://www.getpostman.com/oauth2/callback&refresh_token=' + refreshToken
        response = requests.post(url, data=data, headers=headers, throwHttpErrors = False)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                accessToken = 'Bearer ' + response['access_token']
                accessTokenExpiresAt = datetime.now() + timedelta(seconds=response['expires_in'])
                return True
            except:
                api_error('Refresh token failed: ' + str(response.status_code))
                return False
        else:
            api_error('Refresh token failed: ' + str(response.status_code))
            return False
    return True


def enter_pin():
    global controlToken, controlTokenExpiresAt
    url = BaseURL + '/api/v1/user/pin'
    headers = {
        'Authorization': accessToken,
        'Content-type': 'application/json;charset=UTF-8',
        'Content-Length': '64',
        'Host': BaseHost,
        'Connection': 'close',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'okhttp/3.10.0'}
    data = {"deviceId": deviceId, "pin": pin}
    response = requests.put(url, json=data, headers=headers)
    if response.status_code == 200:
        try:
            response = json.loads(response.text)
            controlToken = 'Bearer ' + response['controlToken']
            controlTokenExpiresAt = datetime.now()+timedelta(seconds=response['expiresTime'])
            logging.debug ("Pin set, control token expires at %s and is %s", controlTokenExpiresAt, controlToken)
            return True
        except:
            api_error('NOK pin. Error: ' + str(response.status_code))
            return False
    else:
        api_error('NOK pin. Error: ' + str(response.status_code))
        return False


def login(car_brand, email2, password2, pin2, vin2):
    global controlToken, controlTokenExpiresAt
    global accessToken, accessTokenExpiresAt, refreshToken
    global deviceId, vehicleId, cookies
    global email, password, pin, vin
    email = email2
    password = password2
    pin = pin2
    vin = vin2

    logging.info('entering login %s %s', car_brand, email2)
    get_constants(car_brand)
    logging.debug('constants %s %s %s %s %s', ServiceId, BasicToken, ApplicationId, BaseHost, BaseURL)

    controlToken = accessToken = refreshToken = None
    controlTokenExpiresAt = accessTokenExpiresAt = datetime(1970, 1, 1, 0, 0, 0)

    try:
        #---cookies----------------------------------
        session = requests.Session()
        url = BaseURL + '/api/v1/user/oauth2/authorize?response_type=code&state=test&client_id=' + ServiceId + '&redirect_uri=' + BaseURL + '/api/v1/user/oauth2/redirect'
        response = session.get(url)
        if response.status_code != 200:
            api_error('NOK cookie for login. Error: ' + str(response.status_code))
            return False
        cookies = session.cookies.get_dict()
        #--- set language----------------------------------
        url = BaseURL + '/api/v1/user/language'
        headers = {'Content-type': 'application/json'}
        data = {"lang": "en"}
        response = requests.post(url, json=data, headers=headers, cookies=cookies)
        #---signin----------------------------------
        url = BaseURL + '/api/v1/user/signin'
        headers = {'Content-type': 'application/json'}
        data = {"email": email, "password": password}
        response = requests.post(url, json=data, headers=headers, cookies=cookies)
        if response.status_code != 200:
            api_error('NOK login. Error: ' + str(response.status_code))
            return False
        try:
            response = json.loads(response.text)
            response = response['redirectUrl']
            parsed = urlparse.urlparse(response)
            authcode = ''.join(parse_qs(parsed.query)['code'])
        except:
            api_error('NOK login. Error in parsing /signing request')
            return False
        #---get deviceid----------------------------------
        url = BaseURL + '/api/v1/spa/notifications/register'
        headers = {
            'ccsp-service-id': ServiceId,
            'Content-type': 'application/json;charset=UTF-8',
            'Content-Length': '80',
            'Host': BaseHost,
            'Connection': 'close',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'okhttp/3.10.0'}
        data = {"pushRegId": "1", "pushType": "GCM", "uuid": str(uuid.uuid1())}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 200:
            api_error('NOK deviceID. Error: ' + str(response.status_code))
            return False
        try:
            response = json.loads(response.text)
            deviceId = response['resMsg']['deviceId']
            logging.info("deviceId %s", deviceId)
        except:
            api_error('NOK login. Error in parsing /signing request')
            return False
        #---get accesstoken----------------------------------
        url = BaseURL + '/api/v1/user/oauth2/token'
        headers = {
            'Authorization': BasicToken,
            'Content-type': 'application/x-www-form-urlencoded',
            'Host': BaseHost,
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'okhttp/3.10.0',
            'grant_type': 'authorization_code'
        }
        data = 'grant_type=authorization_code&redirect_uri=' + BaseURL + '/api/v1/user/oauth2/redirect&code=' + authcode
        response = requests.post(url, data=data, headers=headers)
        if response.status_code != 200:
            api_error('NOK token. Error: ' + str(response.status_code))
            return False
        try:
            response = json.loads(response.text)
            accessToken = 'Bearer ' + response['access_token']
            refreshToken = response['refresh_token']
            accessTokenExpiresAt = datetime.now() + timedelta(seconds=response['expires_in'])
            logging.info("accesstoken %s, refrestoken %s expiresAt %s", accessToken, refreshToken, accessTokenExpiresAt)
        except:
            api_error('NOK login. Error in parsing /token request')
            return False
        #---get vehicles----------------------------------
        url = BaseURL + '/api/v1/spa/vehicles'
        headers = {'Authorization': accessToken, 'ccsp-device-id': deviceId}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            api_error('NOK vehicles. Error: ' + str(response.status_code))
            return False
        try:
            response = json.loads(response.text)
            logging.debug("response %s", response)
            vehicles = response['resMsg']['vehicles']
            logging.debug("%s vehicles found", len(vehicles))
        except:
            api_error('NOK login. Error in getting vehicles: '+response)
            return False
        if len(vehicles) == 0:
            api_error('NOK login. No vehicles found')
            return False
        #---get vehicleId----------------------------------
        vehicleId = None
        if len(vehicles) > 1:
            for vehicle in vehicles:
                url = BaseURL + '/api/v1/spa/vehicles/'+vehicle['vehicleId']+'/profile'
                headers = {'Authorization': accessToken,'ccsp-device-id': deviceId}
                response = requests.get(url, headers=headers)
                try:
                    response = json.loads(response.text)
                    response = response['resMsg']['vinInfo'][0]['basic']
                    vehicle['vin'] = response['vin']
                    vehicle['generation'] = response['modelYear']
                except:
                    api_error('NOK login. Error in getting profile of vehicle: '+vehicle)
                    return False
                if vehicle['vin'] == vin: vehicleId=vehicle['vehicleId']
            if vehicleId == None:
                api_error('NOK login. The VIN you entered is not in the vehicle list ' + vin)
                return False
        else:
            vehicleId = vehicles[0]['vehicleId']
        logging.info("vehicleID %s", vehicleId)
    except:
        api_error('Login failed')
        return False
    logging.debug("Finished successfull login procedure")
    return True


def api_set_wakeup(base_url, vehicle_id, access_token, device_id, application_id, base_host):
    url = base_url + '/api/v1/spa/vehicles/' + vehicle_id + '/control/engine'
    headers = {
        'Authorization': access_token,
        'ccsp-device-id': device_id,
        'ccsp-application-id': application_id,
        'offset': '1',
        'Content-Type': 'application/json;charset=UTF-8',
        'Content-Length': '72',
        'Host': base_host,
        'Connection': 'close',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'okhttp/3.10.0'}
    data = {"action": "prewakeup", "deviceId": device_id}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return True
    else:
        api_error('NOK prewakeup. Error: ' + str(response.status_code))
        return False

def api_get_status(refresh = False, raw = True):
    global BaseURL, vehicleId, controlToken, deviceId
    if not check_control_token(): return False
    # get status either from cache or not

    cachestring = '' if refresh else '/latest'
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/status' + cachestring
    headers = {
        'Authorization': controlToken,
        'ccsp-device-id': deviceId,
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response = json.loads(response.text)
        # a refresh==True returns a short list, a refresh==False returns a long list. If raw is true, return the entire string
        try:
            if raw: return response['resMsg']
            if not refresh: response = response['resMsg']['vehicleStatusInfo']['vehicleStatus']
            return response
        except:
            api_error('NOK parsing status: ' + str(response))
            return False
    else:
        api_error('NOK requesting status. Error: ' + str(response.status_code))
        return False


def api_get_odometer():
    global BaseURL, vehicleId, controlToken, deviceId
    if not check_control_token(): return False
    # odometer
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/status/latest'
    headers = {
        'Authorization': controlToken,
        'ccsp-device-id': deviceId,
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response = json.loads(response.text)
        try:
            return response['resMsg']['vehicleStatusInfo']['odometer']['value']
        except ValueError:
            api_error('NOK Parsing odometer: ' + str(response))
            return False
    else:
        api_error('NOK requesting odometer. Error: ' + str(response.status_code))
        return False


def api_get_location():
    global BaseURL, vehicleId, controlToken, deviceId
    if not check_control_token(): return False
    # location
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/location'
    headers = {
        'Authorization': controlToken,
        'ccsp-device-id': deviceId,
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response = json.loads(response.text)
        try:
            return response['resMsg']
        except ValueError:
            api_error('NOK Parsing location: ' + str(response))
            return False
    else:
        api_error('NOK requesting location. Error: ' + str(response.status_code))
        return False


def api_set_lock(action = 'close'):
    if action == "":
        api_error('NOK Emtpy lock parameter')
        return False
    if type(action) == bool:
        if action: action = 'close'
        else: action = 'open'
    else:
        action = str.lower(action)
        if action == 'on': action = 'close'
        if action == 'off': action = 'open'
    if not (action == 'close' or action == 'open'):
        api_error('NOK Invalid locking parameter')
        return False

    if not check_control_token(): return False

    # location
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/control/door'
    headers = {
        'Authorization': controlToken,
        'ccsp-device-id': deviceId,
        'Content-Type': 'application/json'
    }
    data = {"deviceId": deviceId, "action": action}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        logging.debug("Send (un)lock command to Vehicle")
        return True
    else:
        api_error('Error sending lock. Error: ' + str(response.status_code) + url)
        return False


def api_set_charge(action = 'stop'):
    if action == "":
        api_error('NOK Emtpy charging parameter')
        return False
    if type(action) == bool:
        if action: action = 'start'
        else: action = 'stop'
    else:
        action = str.lower(action)
        if action == 'on' : action = 'start'
        if action == 'off': action = 'stop'
    if not (action == 'start' or action == 'stop'):
        api_error('NOK Invalid charging parameter')
        return False
    if not check_control_token(): return False
    # location
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/control/charge'
    headers = {
        'Authorization': controlToken,
        'ccsp-device-id': deviceId,
        'Content-Type': 'application/json'
    }
    data = {"deviceId": deviceId, "action": action}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        logging.debug("Send (stop) charge command to Vehicle")
        return True
    else:
        api_error('Error sending start/stop charge. Error: ' + str(response.status_code))
        return False


def api_set_HVAC(action = 'stop', temp='21.0', bdefrost = False, bheating = False):
    if action == "":
        api_error('NOK Emtpy HVAC parameter')
        return False
    if type(action) == bool:
        if action: action = 'start'
        else: action = 'stop'
    else:
        action = str.lower(action)
        if action == 'on' : action = 'start'
        if action == 'off': action = 'stop'
    if not (action == 'stop' or action == 'start'):
        api_error('NOK Invalid HVAC parameter')
        return False
    try:
        tempcode = temp2hex(temp)
    except:
        tempcode = "0EH"  #default 21 celcius
    try:
        heating = 1 if bheating else 0
    except:
        heating = 1

    if not check_control_token(): return False
    # location
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/control/temperature'
    headers = {
        'Authorization': controlToken,
        'ccsp-device-id': deviceId,
        'Content-Type': 'application/json'
    }
    data = {
        "deviceId": deviceId,
        "action": action,
        "hvacType": 0,
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
        api_error('Error sending HVAC settings. Error: ' + str(response.status_code))
        return False


#------------ tests -----------
def api_get_chargeschedule():
    global BaseURL, vehicleId, controlToken, deviceId
    if not check_control_token(): return False
    # location
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/reservation/charge'
    headers = {
        'Authorization': controlToken,
        'ccsp-device-id': deviceId,
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response = json.loads(response.text)
        try:
            return response['resMsg']
        except ValueError:
            api_error('NOK Parsing charge schedule: ' + str(response))
            return False
    else:
        api_error('NOK requesting charge schedule. Error: ' + str(response.status_code))
        return False


def api_set_chargeschedule(Schedule1, Schedule2, TempSet, ChargeSchedule):
    # Params Schedule1, Schedule2 = timeschedules for the temperature set
    #   ["day"] is array [x,y,z, etc] with x,y,z, days that need to be set, where sunday =1 and saturday = 6
    #   ["time"] is a list of time and timeSection ['time']:hhmm and ['timeSection']:0 or 1 (AM or PM)
    # Param Tempset
    #   ["temperature"] = the temp (in celcius)
    #   ["defrost"] = true of false (on or off)
    # ChargeSchedule
    #   ['starttime'] = list of time and timeSection ['time']:hhmm and ['timeSection']:0 or 1 (AM or PM)
    #   ['endtime'] = list of time and timeSection ['time']:hhmm and ['timeSection']:0 or 1 (AM or PM)
    #   ['prio'] = True if it has prio, False if off peak Only
    # if any parameter = True or None, then ignore values. If parameter = False then disable the schedule, else set the values.


    global BaseURL, vehicleId, controlToken, deviceId
    if not check_control_token(): return False

    # first get the currens settings
    data = api_get_chargeschedule()
    if not (not data):
        try:
            # now enter the new settings
            url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/reservation/charge'
            headers = {
                'Authorization': controlToken,
                'ccsp-device-id': deviceId,
                'Content-Type': 'application/json'
            }
            data['deviceId'] = deviceId
            if not (Schedule1 == None or Schedule1 == True): # ignore it of True or None
                if Schedule1 == False: #turn the schedule off
                    data['reservChargeInfo']['reservChargeSet']=False
                else:
                    data['reservChargeInfo']['reservChargeSet']=True
                    data['reservChargeInfo']['reservInfo']=Schedule1
            if not (Schedule2 == None or Schedule2 == True): # ignore it of True or None
                if Schedule2 == False: #turn the schedule off
                    data['reservChargeInfo2']['reservChargeSet']=False
                else:
                    data['reservChargeInfo2']['reservChargeSet']=True
                    data['reservChargeInfo2']['reservInfo']=Schedule2

            if not (TempSet == None or TempSet == True): # ignore it of True or None
                if TempSet == False: #turn the schedule off
                    data['reservChargeInfo']['reservFatcSet']['airCtrl'] = 0
                    data['reservChargeInfo2']['reservFatcSet']['airCtrl'] = 0
                else:
                    data['reservChargeInfo']['reservFatcSet']['airCtrl'] = 1
                    data['reservChargeInfo2']['reservFatcSet']['airCtrl'] = 1
                    data['reservChargeInfo']['reservFatcSet']['airTemp']['value'] = temp2hex(TempSet['Temperature'])
                    data['reservChargeInfo2']['reservFatcSet']['airTemp']['value'] = temp2hex(TempSet['Temperature'])

            if not (ChargeSchedule == None or ChargeSchedule == True): # ignore it of True or None
                if ChargeSchedule == False: #turn the schedule off
                    data['reservFlag'] = 0
                else:
                    data['reservFlag'] = 1
                    data['offPeakPowerInfo'] = ChargeSchedule

            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200: return True
        except:
            api_error('NOK setting charge schedule.' )
            return False
    api_error('NOK setting charge schedule.')
    return False

def api_set_chargelimits(LimitFast = 80, LimitSlow = 100):
    global BaseURL, vehicleId, controlToken, deviceId
    if not check_control_token(): return False
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/charge/target'
    headers = {
        'Authorization': controlToken,
        'ccsp-device-id': deviceId,
        'Connection': 'keep-alive',
        'offset': '2',
        'Content-Type': 'application/json;charset=UTF-8',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'okhttp/3.10.0'
    }
    data = {'targetSOClist' : [{'plugType': 0,'targetSOClevel': int(LimitFast) },{'plugType': 1,'targetSOClevel': int(LimitSlow)}]}
    response = requests.post(url, json=data, headers=headers, cookies=cookies)
    if response.status_code == 200: return True
    else:
        api_error('NOK setting charge limits. Error: ' + response.text['resMsg']+str(response.status_code))
        return False

def api_set_navigation(poiInfoList):
    global BaseURL, vehicleId, controlToken, deviceId
    if not check_control_token(): return False
    data = {}
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/location/routes'
    headers = {
        'Authorization': controlToken,
        'ccsp-device-id': deviceId,
        'Content-Type': 'application/json'
    }
    data=poiInfoList
    data['deviceID']=deviceId
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return True
    else:
        api_error('NOK setting navigation. Error: ' + str(response.status_code))
        return False