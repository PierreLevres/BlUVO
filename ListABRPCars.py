import requests
import json
#lists the cars brands and types from the ABRP API
url = "https://api.iternio.com/1/tlm/get_carmodels_list"
payload = {}
headers = {}
response = requests.request("GET", url, headers=headers, data=payload)
autos = (json.loads(response.text)['result'])
for car in autos:
    for key, value in car.items():
        model = value.split(":",1)[0]
        if model == "kia" or model == "hyundai": print (key, value)
