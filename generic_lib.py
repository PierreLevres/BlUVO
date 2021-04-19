import time, uuid, requests, json
from math import cos, asin, sqrt, pi
from urllib.parse import urlencode, quote


def convert_if_bool(value):
    if type(value) == bool:
        if value:
            return 1
        else:
            return 0
    else:
        return value


def convert_to_bool(value):
    if type(value) == int:
        if value == 1:
            return True
        else:
            return False
    else:
        return value

def georeverse(lat, lon):
    get_address_url = 'https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=16&lat=' + str(lat) + '&lon=' + str(lon)
    response = requests.get(get_address_url)
    if response.status_code == 200:
        response = json.loads(response.text)
        return response['display_name']
    else:
        return False


def geolookup(locationtolookup):
    get_address_url = 'https://nominatim.openstreetmap.org/search?q='+quote(locationtolookup) + '&format=geocodejson&addressdetails=1&limit=1'
    response = requests.get(get_address_url)
    if response.status_code == 200:
        try:
            response = json.loads(response.text)
            response = response['features'][0]
            poi_info_element = {
                "coord": {
                    "lat": response['geometry']['coordinates'][1],
                    "alt": 0,
                    "lon": response['geometry']['coordinates'][0],
                    "type": 0
                },
                "addr": response['properties']['geocoding']['label'],
                "placeid": response['properties']['geocoding']['label'],
                "name": locationtolookup
            }
            return poi_info_element
        except: return False
    else: return False


def get_location_temperature(weather_api_key, weather_provider, lat, lon):
    if weather_provider == 'DarkSky':
        get_weather_url = 'https://api.darksky.net/forecast/' + weather_api_key + '/' + str(lat) + ',' + str(lon) + '?units=si'
        response = requests.get(get_weather_url)
        if response.status_code == 200:
            response = json.loads(response.text)
            return response['currently']['temperature']
        else: return False
    elif weather_provider == 'OpenWeather':
        get_weather_url = 'https://api.openweathermap.org/data/2.5/weather?lat=' + str(lat) + '&lon=' + str(lon) + '&appid=' + weather_api_key + '&type=accurate&units=metric'
        response = requests.get(get_weather_url)
        if response.status_code == 200:
            response = json.loads(response.text)
            return response['main']['temp']
        else: return False
    else: return False


def send_abr_ptelemetry(soc, speed, latitude, longitude, charging, abrp_carmodel, abrp_token, weather_api_key, weather_provider):
    # ABRP API information: https://documenter.getpostman.com/view/7396339/SWTK5a8w?version=latest
    # ABRP Telemetry API KEY - DO NOT CHANGE
    if abrp_token != "":
        abrp_apikey = '6f6a554f-d8c8-4c72-8914-d5895f58b1eb'
        data = {'utc': time.time(), 'soc': soc, 'speed': speed, 'is_charging': convert_if_bool(charging),
                'car_model': abrp_carmodel}
        if latitude is not None:    data['lat'] = latitude
        if longitude is not None:   data['lon'] = longitude
        if weather_provider is not None and weather_api_key is not None and latitude is not None and longitude is not None:
            ext_temp = get_location_temperature(weather_api_key, weather_provider, latitude, longitude)
            if ext_temp is not False: data['ext_temp'] = ext_temp
        params = {'token': abrp_token, 'api_key': abrp_apikey, 'tlm': json.dumps(data, separators=(',', ':'))}
        response = requests.get('https://api.iternio.com/1/tlm/send?' + urlencode(params))
        if response.status_code == 200: return json.loads(response.text)
        else: return -1


def distance(lat1, lon1, lat2, lon2):
    p = pi / 180
    a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return 12742 * asin(sqrt(a))


'''
destinations [{"address": "Lund, Sweden"}, {"address": "Berlin, Germany"}]
[Mandatory] A list of at exactly two destination (the start and final destination) of the plan.
Each destination object is has the following properties, in the order they will be used to identify the location:
    id: If given, this ID number corresponds to a charger in the Iternio database.
    lat/lon (numbers): If given, this is the coordinates of the waypoint
    address (string): If given, this address string will be used to look up the location of the waypoint. If id or lat/lon are given, this is only used to name the waypoint.
    bearing (number): If given, this is the bearing (heading) of the vehicle in degrees with zero being north.

carmodel, see list in ABRP
'''
def get_abrprouteplan(destinations, carmodel, startsoc):
    deviceId = str(uuid.uuid4()).replace('-', '')  # random 32-byte number is OK, no hyphens

    baseURL = "https://api.iternio.com/1/"
    headers = {'Authorization': 'APIKEY f4128c06-5e39-4852-95f9-3286712a9f3a',  # same for all instances
               'Accept': 'application/json, text/plain, */*',
               'content-type': 'application/json;charset=utf-8',
               'authority': 'api.iternio.com',
               'user-agent': 'ABRP/345 CFNetwork/1220.1 Darwin/20.3.0'}

    dataregister = {"platform": "ios", "device_id": deviceId}
    response = requests.post(baseURL + "session/new_session", json=dataregister, headers=headers)
    sessionID = json.loads(response.text)['result']
    cookies = response.cookies.get_dict()

#    datagetsession = {'session_id': sessionID, 'client': 'abrp-ios', 'version': 345, 'variant': 'default'}
#    response = requests.get(baseURL + "session/get_session", json=datagetsession, headers=headers, cookies=cookies)

    dataplanlite = {"destinations": destinations, "car_model": carmodel, "initial_soc_perc": startsoc}
    response = requests.post(baseURL + 'plan_light', headers=headers, json=dataplanlite, cookies=cookies)
    response = json.loads(response.text)
    response = response['result']['routes'][0]
    return response['steps'] if response['is_valid_route'] else False

#TODO google time from home
    #with google key calculate driving time from home