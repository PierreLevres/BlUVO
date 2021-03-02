import time
from math import cos, asin, sqrt, pi
import requests
import json
from urllib.parse import urlencode, quote


def convert_if_bool(value):
    if type(value) == bool:
        if value:
            return 1
        else:
            return 0
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
        response = json.loads(response.text)
        try:
            response = response['features'][0]
            poi_info = {
                "poiInfoList": [{
                    "phone": "",
                    "waypointID": 0,
                    "lang": 1,
                    "src": "HERE",
                    "coord": {
                        "lat": response['geometry']['coordinates'][0],
                        "alt": 0,
                        "lon": response['geometry']['coordinates'][1],
                        "type": 0
                    },
                    "addr": response['properties']['geocoding']['label'],
                    "zip": "",
                    "placeid": response['properties']['geocoding']['label'],
                    "name": lookup
                }],
            }
            return poi_info
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

#TODO google time from home
    #with google key calculate driving time from home