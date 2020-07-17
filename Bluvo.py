import sys
import urllib
import requests
import uuid
import json
import time
import urllib.parse as urlparse
from urllib.parse import parse_qs, urlencode, quote_plus

# we need the following params
# email = from Uvo or Bluelink App'
# password = from Uvo or Bluelink App
# pin = from Uvo or Bluelink App
# abrp_token = Obtain from ABRP app by choosing live data from Torque Pro
# abrp_carmodel = 'kia:niro:19:64:other' Obtain from ABRP API site
# DarkSkyApiKey = obtain from Darksky, or rewrite function
# car_brand = 'Kia' or ' Hyundai'
# parameters from parameter file or from domoticz
from params import *

def main():
    #logging or not?
    logging = False

    # constants, depending on Brand Kia or Hyundai
    if car_brand == 'kia':
        ServiceId = 'fdc85c00-0a2f-4c64-bcb4-2cfb1500730a'
        BasicToken = 'Basic ZmRjODVjMDAtMGEyZi00YzY0LWJjYjQtMmNmYjE1MDA3MzBhOnNlY3JldA=='
        ApplicationId= '693a33fa-c117-43f2-ae3b-61a02d24f417'
        ContentLengthToken = '150'
    elif car_brand == 'hyundai':
        ServiceId = '6d477c38-3ca4-4cf3-9557-2a1929a94654'
        BasicToken = 'Basic NmQ0NzdjMzgtM2NhNC00Y2YzLTk1NTctMmExOTI5YTk0NjU0OktVeTQ5WHhQekxwTHVvSzB4aEJDNzdXNlZYaG10UVI5aVFobUlGampvWTRJcHhzVg=='
        ApplicationId = '99cfff84-f4e2-4be8-a5ed-e5b755eb6581'
        ContentLengthToken = '154'
    else:
        return
    BaseHost = 'prd.eu-ccapi.'+car_brand+'.com:8080'
    BaseURL = 'https://'+BaseHost

    def log(value):
        if logging: print(value)

    def ConvertIfBool(value):
        if type(value) == bool:
            if value:
                return 1
            else:
                return 0
        else:
            return value

    def GetLocationTemperature(lat,lon):
        # TODO general: error handling with try and except / raise
        # todo change Darksky
        getDarkSkyURL = 'https://api.darksky.net/forecast/' + DarkSkyApiKey +'/'+str(lat)+','+str(lon)+'?units=si'
        response = requests.get(getDarkSkyURL)
        if response.status_code == 200:
            response = json.loads(response.text)
            return response['currently']['temperature']
        else:
            print('NOK Weather')
            return

    def SendABRPtelemetry():
        # ABRP API information: https://documenter.getpostman.com/view/7396339/SWTK5a8w?version=latest
        # ABRP Telemetry API KEY - DO NOT CHANGE
        abrp_apikey = '6f6a554f-d8c8-4c72-8914-d5895f58b1eb'
        data = {}
        data['utc'] = time.time()
        data['soc'] = soc
        data['speed'] = speed
        data['lat'] = latitude
        data['lon'] = longitude
        data['is_charging'] = ConvertIfBool(charging)
        data['car_model'] = abrp_carmodel
        data['ext_temp']= GetLocationTemperature(latitude, longitude)
        params = {'token': abrp_token, 'api_key': abrp_apikey,'tlm': json.dumps(data, separators=(',', ':'))}
        response = requests.get('https://api.iternio.com/1/tlm/send?' + urlencode(params))
        if response.status_code == 200:
            response = json.loads(response.text)
            log(response)
            return response
        else:
            print('NOK ABRP')
            return


    #deviceID
    url = BaseURL+'/api/v1/spa/notifications/register'
    log(url)
    headers = {
        'ccsp-service-id': ServiceId,
        'Content-type': 'application/json;charset=UTF-8',
        'Content-Length': '80',
        'Host': BaseHost,
        'Connection': 'close',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'okhttp/3.10.0'}
    data = {"pushRegId":"1","pushType":"GCM","uuid": str(uuid.uuid1())}
    response = requests.post(url, json = data, headers = headers)
    if response.status_code == 200:
        response = json.loads(response.text)
        deviceId = response['resMsg']['deviceId']
        log(deviceId)
    else:
        print('NOK deviceID')
        return

    #cookie for login
    session = requests.Session()
    response = session.get(BaseURL+'/api/v1/user/oauth2/authorize?response_type=code&state=test&client_id='+ServiceId+'&redirect_uri='+BaseURL+'/api/v1/user/oauth2/redirect')
    if response.status_code == 200:
        cookies = session.cookies.get_dict()
        log(cookies)
    else:
        print('NOK cookie for login')
        return
        # cookie for login

    #set language
    url = BaseURL+'/api/v1/user/language'
    log(url)
    headers = {'Content-type': 'application/json'}
    data = {"lang": "en"}
    response = requests.post(url, json=data, headers=headers, cookies=cookies)
    log(response)

    #login
    url = BaseURL+'/api/v1/user/signin'
    log(url)
    headers = {'Content-type': 'application/json'}
    data = {"email": email,"password": password}
    response = requests.post(url, json = data, headers = headers, cookies = cookies)
    if response.status_code == 200:
        response = json.loads(response.text)
        response = response['redirectUrl']
        parsed = urlparse.urlparse(response)
        authCode = ''.join(parse_qs(parsed.query)['code'])
        log(authCode)
    else:
        print('NOK login')
        return

    #token
    url = BaseURL+'/api/v1/user/oauth2/token'
    log(url)
    headers = {
        'Authorization': BasicToken,
        'Content-type': 'application/x-www-form-urlencoded',
        'Content-Length': ContentLengthToken,
        'Host': BaseHost,
        'Connection': 'close',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'okhttp/3.10.0'}
    data = 'grant_type=authorization_code&redirect_uri='+BaseURL+'/api/v1/user/oauth2/redirect&code=' + authCode
    #data = 'grant_type=authorization_code&redirect_uri=https%3A%2F%2Fprd.eu-ccapi.kia.com%3A8080%2Fapi%2Fv1%2Fuser%2Foauth2%2Fredirect&code=' + authCode
    response = requests.post(url, data = data, headers = headers)
    log(response)
    if response.status_code == 200:
        response = json.loads(response.text)
        access_token = response['token_type'] + ' ' + response['access_token']
        log(access_token)
    else:
        print('NOK token')
        return

    #vehicles
    url = BaseURL+'/api/v1/spa/vehicles'
    log(url)
    headers = {
        'Authorization': access_token,
        'ccsp-device-id': deviceId,
        'ccsp-application-id': ApplicationId,
        'offset': '1',
        'Host': BaseHost,
        'Connection': 'close',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'okhttp/3.10.0'}
    response = requests.get(url, headers = headers)
    log(response)
    if response.status_code == 200:
        response = json.loads(response.text)
        vehicleId = response['resMsg']['vehicles'][0]['vehicleId']
        log(vehicleId)
    else:
        print('NOK vehicles')
        return

    #vehicles/profile

    #prewakeup
    url = BaseURL+'/api/v1/spa/vehicles/' + vehicleId + '/control/engine'
    log(url)
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
    data = {"action":"prewakeup","deviceId": deviceId}
    response = requests.post(url, json = data, headers = headers)
    log(response.content)
    if response.status_code == 200:
        log(response.text)
        response = ''
    else:
        print('NOK prewakeup')
        return

    #pin
    url = BaseURL+'/api/v1/user/pin'
    log(url)
    headers = {
        'Authorization': access_token,
        'Content-type': 'application/json;charset=UTF-8',
        'Content-Length': '64',
        'Host': BaseHost,
        'Connection': 'close',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'okhttp/3.10.0'}
    data = {"deviceId": deviceId,"pin": pin}
    response = requests.put(url, json = data, headers = headers)
    if response.status_code == 200:
        response = json.loads(response.text)
        controlToken = 'Bearer ' + response['controlToken']
        log(controlToken)
    else:
        print('NOK pin')
        return

    # status
    url = BaseURL+'/api/v2/spa/vehicles/' + vehicleId + '/status'
    headers = {
        'Authorization': controlToken,
        'ccsp-device-id': deviceId,
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        statusresponse = json.loads(response.text)
        log(statusresponse['resMsg'])
        trunkopen = statusresponse['resMsg']['trunkOpen']
        evStatus = statusresponse['resMsg']['evStatus']
        soc = evStatus['batteryStatus']
        charging = evStatus['batteryCharge']
        rangeleft = evStatus['drvDistance'][0]['rangeByFuel']['totalAvailableRange']['value']
    else:
        print('NOK status')
        return

    #odometer
    url = BaseURL+'/api/v2/spa/vehicles/' + vehicleId + '/status/latest'
    headers = {
        'Authorization': controlToken,
        'ccsp-device-id': deviceId,
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        statusresponse = json.loads(response.text)
        odometer=statusresponse['resMsg']['vehicleStatusInfo']['odometer']['value']
    else:
        print('NOK status')
        return

    # location
    url = BaseURL+'/api/v2/spa/vehicles/' + vehicleId + '/location'
    headers = {
        'Authorization': controlToken,
        'ccsp-device-id': deviceId,
        'Content-Type': 'application/json'
        }
    response = requests.get(url, headers = headers)
    if response.status_code == 200:
        statusresponse = json.loads(response.text)
        log (statusresponse['resMsg'])
        latitude=statusresponse['resMsg']['gpsDetail']['coord']['lat']
        longitude=statusresponse['resMsg']['gpsDetail']['coord']['lon']
        altitude=statusresponse['resMsg']['gpsDetail']['coord']['alt']
        heading=statusresponse['resMsg']['gpsDetail']['head']
        speed=statusresponse['resMsg']['gpsDetail']['speed']['value']
    else:
        print('NOK status')
        return

    #send information to domoticz
    print('locatie: ',latitude,',',longitude)
    print('rijrichting: ',heading)
    print('snelheid: ', speed)
    print('km-stand: ', odometer)
    print('trunk open: ',trunkopen)
    print('soc: ',soc)
    print('charging: ', charging)
    print('range left: ', rangeleft)

    #send soc, temp, location to ABRP
    SendABRPtelemetry()

if __name__ == '__main__':
    main()