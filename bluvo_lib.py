import sys
import urllib
import requests
import uuid
import json
import urllib.parse as urlparse
from urllib.parse import parse_qs, urlencode, quote_plus

class APIError(Exception):
    pass


def getConstants(car_brand):
    if car_brand == 'kia':
        ServiceId = 'fdc85c00-0a2f-4c64-bcb4-2cfb1500730a'
        BasicToken = 'Basic ZmRjODVjMDAtMGEyZi00YzY0LWJjYjQtMmNmYjE1MDA3MzBhOnNlY3JldA=='
        ApplicationId = '693a33fa-c117-43f2-ae3b-61a02d24f417'
        ContentLengthToken = '150'
    elif car_brand == 'hyundai':
        ServiceId = '6d477c38-3ca4-4cf3-9557-2a1929a94654'
        BasicToken = 'Basic NmQ0NzdjMzgtM2NhNC00Y2YzLTk1NTctMmExOTI5YTk0NjU0OktVeTQ5WHhQekxwTHVvSzB4aEJDNzdXNlZYaG10UVI5aVFobUlGampvWTRJcHhzVg=='
        ApplicationId = '99cfff84-f4e2-4be8-a5ed-e5b755eb6581'
        ContentLengthToken = '154'
    else:
        raise APIError('Carbrand not OK.')
    BaseHost = 'prd.eu-ccapi.' + car_brand + '.com:8080'
    BaseURL = 'https://' + BaseHost
    return ServiceId, BasicToken, ApplicationId, ContentLengthToken, BaseHost, BaseURL


def APIgetDeviceID(BaseURL,ServiceId, BaseHost):
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
        raise APIError('NOK deviceID. Error: '+str(response.status_code))


def APIgetCookie(ServiceId, BaseURL):
    session = requests.Session()
    response = session.get(
        BaseURL + '/api/v1/user/oauth2/authorize?response_type=code&state=test&client_id=' + ServiceId + '&redirect_uri=' + BaseURL + '/api/v1/user/oauth2/redirect')
    if response.status_code == 200:
        cookies = session.cookies.get_dict()
        return cookies
    else:
        raise APIError('NOK cookie for login. Error: '+str(response.status_code))


def APIsetLanguage(BaseURL, cookies):
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
        raise APIError('NOK login. Error: '+str(response.status_code))


def APIgetToken(BaseURL, BasicToken, ContentLengthToken, BaseHost, authCode):
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
        raise APIError('NOK token. Error: '+str(response.status_code))


def APIgetVehicleId(BaseURL, access_token, deviceId, ApplicationId, BaseHost):
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
        raise APIError('NOK vehicles. Error: '+str(response.status_code))


def APIsetWakeup(BaseURL, vehicleId, access_token, deviceId, ApplicationId, BaseHost):
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
        raise APIError('NOK prewakeup. Error: '+str(response.status_code))


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
        raise APIError('NOK pin. Error: '+str(response.status_code))


def APIgetStatus(BaseURL, vehicleId, controlToken, deviceId):
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
        raise APIError('NOK status. Error: '+str(response.status_code))


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
        #print ('status/latest output')
        #print(response['resMsg'])
        odometer = response['resMsg']['vehicleStatusInfo']['odometer']['value']
        return odometer
    else:
        raise APIError('NOK odometer. Error: '+str(response.status_code))


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
        raise APIError('NOK location. Error: '+str(response.status_code))
