import sys
import urllib
import requests
import uuid
import json
import urllib.parse as urlparse
from urllib.parse import parse_qs, urlencode, quote_plus

def APIgetDeviceID(BaseURL,ServiceId, BaseHost):
    # deviceID
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
    if response.status_code == 200:
        response = json.loads(response.text)
        deviceId = response['resMsg']['deviceId']
        return deviceId
    else:
        print('NOK deviceID')
        return -1


def APIgetCookie(ServiceId, BaseURL):
    # cookie for login
    session = requests.Session()
    response = session.get(
        BaseURL + '/api/v1/user/oauth2/authorize?response_type=code&state=test&client_id=' + ServiceId + '&redirect_uri=' + BaseURL + '/api/v1/user/oauth2/redirect')
    if response.status_code == 200:
        cookies = session.cookies.get_dict()
        return cookies
    else:
        print('NOK cookie for login')
        return -1


def APIsetLanguage(BaseURL, cookies):
    # set language
    url = BaseURL + '/api/v1/user/language'
    headers = {'Content-type': 'application/json'}
    data = {"lang": "en"}
    response = requests.post(url, json=data, headers=headers, cookies=cookies)
    return True


def APIgetAuthCode(BaseURL, email, password, cookies):
    url = BaseURL + '/api/v1/user/signin'
    headers = {'Content-type': 'application/json'}
    data = {"email": email, "password": password}
    response = requests.post(url, json=data, headers=headers, cookies=cookies)
    if response.status_code == 200:
        response = json.loads(response.text)
        response = response['redirectUrl']
        parsed = urlparse.urlparse(response)
        authCode = ''.join(parse_qs(parsed.query)['code'])
        return authCode
    else:
        print('NOK login')
        return -1


def APIgetToken(BaseURL, BasicToken, ContentLengthToken, BaseHost, authCode):
    # token
    url = BaseURL + '/api/v1/user/oauth2/token'
    headers = {
        'Authorization': BasicToken,
        'Content-type': 'application/x-www-form-urlencoded',
        'Content-Length': ContentLengthToken,
        'Host': BaseHost,
        'Connection': 'close',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'okhttp/3.10.0'}
    data = 'grant_type=authorization_code&redirect_uri=' + BaseURL + '/api/v1/user/oauth2/redirect&code=' + authCode
    response = requests.post(url, data=data, headers=headers)
    if response.status_code == 200:
        response = json.loads(response.text)
        access_token = response['token_type'] + ' ' + response['access_token']
        return access_token
    else:
        print('NOK token')
        return -1


def APIgetVehicleId(BaseURL, access_token, deviceId, ApplicationId, BaseHost):
    # vehicles
    url = BaseURL + '/api/v1/spa/vehicles'
    headers = {
        'Authorization': access_token,
        'ccsp-device-id': deviceId,
        'ccsp-application-id': ApplicationId,
        'offset': '1',
        'Host': BaseHost,
        'Connection': 'close',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'okhttp/3.10.0'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response = json.loads(response.text)
        vehicleId = response['resMsg']['vehicles'][0]['vehicleId']
        return vehicleId
    else:
        print('NOK vehicles')
        return -1


def APIsetWakeup(BaseURL, vehicleId, access_token, deviceId, ApplicationId, BaseHost):
    # prewakeup
    url = BaseURL + '/api/v1/spa/vehicles/' + vehicleId + '/control/engine'
    headers = {
        'Authorization': access_token,
        'ccsp-device-id': deviceId,
        'ccsp-application-id': ApplicationId,
        'offset': '1',
        'Content-Type': 'application/json;charset=UTF-8',
        'Content-Length': '72',
        'Host': BaseHost,
        'Connection': 'close',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'okhttp/3.10.0'}
    data = {"action": "prewakeup", "deviceId": deviceId}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return True
    else:
        print('NOK prewakeup')
        return -1


def APIgetControlToken(BaseURL, access_token, BaseHost, deviceId, pin):
    url = BaseURL + '/api/v1/user/pin'
    headers = {
        'Authorization': access_token,
        'Content-type': 'application/json;charset=UTF-8',
        'Content-Length': '64',
        'Host': BaseHost,
        'Connection': 'close',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'okhttp/3.10.0'}
    data = {"deviceId": deviceId, "pin": pin}
    response = requests.put(url, json=data, headers=headers)
    if response.status_code == 200:
        response = json.loads(response.text)
        controlToken = 'Bearer ' + response['controlToken']
        return controlToken
    else:
        print('NOK pin')
        return -1


def APIgetStatus(BaseURL, vehicleId, controlToken, deviceId):
    # status
    url = BaseURL + '/api/v2/spa/vehicles/' + vehicleId + '/status'
    headers = {
        'Authorization': controlToken,
        'ccsp-device-id': deviceId,
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response = json.loads(response.text)
        return response['resMsg']
    else:
        print('NOK status')
        return -1


def APIgetOdometer(BaseURL, vehicleId, controlToken, deviceId):
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
        odometer = response['resMsg']['vehicleStatusInfo']['odometer']['value']
        return odometer
    else:
        print('NOK odometer')
        return -1


def APIgetLocation(BaseURL, vehicleId, controlToken, deviceId):
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
        return response['resMsg']
    else:
        print('NOK location')
        return -1
