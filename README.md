# BlUVO
 
BlUvo Plugin
An application or Domoticz plugin for Kia UVO and Hyundai Bluelink EV's (generally MY2020 and beyond). Use at own risk!

This plugin will communicate with servers of Kia and Hyundai and through them with your car. Polling your car means draining battery and worst case, an empty battery. Educate yourself by googling "auxiliary battery drain Niro Kona Soul"

Email, Password, Pin are same as in you Bluelink or UVO app. Cartype is mandatory, to distinguish Kia or Hyundai BlueLink operation. It is also used for ABRP integration.

ABRP (optional) and weather (even more optional)
This plugin will send current state of charge (SoC) and local temperature to your ABRP account to have the most accurate route planning, even on the road.
Your ABRP token can be found here: Settings - Car model, Click on settings next to you car, click on settings (arrow down) on the page of your car. Scroll down a bit and click on Show live data instructions and next on the blue "Link Torque"-box. Click Next, Next, Next and see: "Set User Email Address to the following token". Click on the blue "Copy" box next to the token.
If you omit your ABRP token, then no information will be sent to ABRP.
If you want accurate weather information sent to ABRP enter either a DarkSky or OpenWeather api-key. If omitted, no weather info will be sent to ABRP.

12V auxiliary battery
If you poll the car all the time, when not driving or not charging, your 12V battery may be drained, depending on the settings of your car to charge the auxiliary battery. There is no way for the plugin to determine if you start driving or charging other than polling the car. To save draining and yet to enable polling two mechanisms are implemented:
Forced poll interval - Polls the car actively every x minutes. Default 60 (1 hour). You might want to change it to 999 (once a week approx.)
Watching an external flag, eg in domoticz. Car will be polled if that flag is set to 1. You may want to define a timer on that flag to turn it off automatically. If you use iOS you can achieve enabling and disabling this flag by iOS Shortcuts when plugin in and out of Apple Carplay. 
The active car polling stops when you are no longer driving or charging and the FlagInCar is not set.

If session.pkl is removed or not present, the app is 'installed' as if it were a mobile phone app, session parameters are saved to disk. If it is present, existing session parameters are used.

Fill params.py with the parameters.

p_email = 'your email address from bluelinky or UVO app'

p_password = 'your password from the app'

p_pin = 'your pin from the app'

p_vin = vin of car you want to manage, not relevant if only 1 car is in your profile

p_abrp_token = 'abrp token (find in ABRP Torque Pro setup instructions)'

p_abrp_carmodel = 'ABRP car type, find in ABRP API'

p_WeatherApiKey = 'api key if you want actual weather uploaded to ABRP'

p_WeatherProvider = 'weather provider Darksky or OpenWeather if you want actual weather uploaded to ABRP'

p_homelocation="homelatitude;homelongitude"

p_forcepollinterval = 120 # forces application to poll actively every so many minutes

p_charginginterval = 60 # forces application to poll actively every so many minutes while charging

p_heartbeatinterval = 30 # forces application to read from cache every so many minutes

p_URLphoneincar= 'url to return information to an external server if eg your phone is plugged into the car or unplugged'

