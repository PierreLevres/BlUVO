import requests
import json

# lists the cars brands and types from the ABRP API
url = "https://api.iternio.com/1/tlm/get_carmodels_list"
payload = headers = {}
response = requests.request("GET", url, headers=headers, data=payload)
try:
    cars = (json.loads(response.text)['result'])
    carlist = []
    for car in cars:
        for key, value in car.items():
            if 'kia' in value or 'hyundai' in value:
                carlist.append(value)
                print(len(carlist), ':', key, '==>', value)
    invoer = input('Pick a brand : ')
    try: print('add the following line to params.py\np_abrp_carmodel = \'' + carlist[int(invoer) - 1] + '\'')
    except: print('No valid choice given')
except: print('Could not get cars from ABRP')