from datetime import datetime

from generic_lib import SendABRPtelemetry, distance
from bluvo_lib import APIError, getConstants, APIgetDeviceID, APIgetCookie, APIsetLanguage, APIgetAuthCode, APIgetToken, \
    APIgetVehicleId, APIsetWakeup, APIgetControlToken, APIgetStatus, APIgetOdometer, APIgetLocation

def initialise(abrp_carmodel, abrp_token, DarkSkyApiKey, OpenWeatherApiKey, homelat, homelon, email, password, pin):
    # global abrp_carmodel, abrp_token, DarkSkyApiKey, OpenWeatherApiKey, homelat, homelon, email, password, pin
    global ServiceId, BasicToken, ApplicationId, ContentLengthToken, BaseHost, BaseURL,deviceId, cookies, authCode, accessToken, vehicleId, controlToken, controlTokenExpiresAt, car_brand
    global controlTokenExpiresAt, previousRangeLeft, pollCounter, sleepCycles
    car_brand = (abrp_carmodel.split(":", 1)[0])
    ServiceId, BasicToken, ApplicationId, ContentLengthToken, BaseHost, BaseURL = getConstants(car_brand)

    controlTokenExpiresAt = datetime (1970, 1, 1, 0, 0, 0)
    previousRangeLeft = 0
    pollCounter = 0
    sleepCycles = 0

def doStuff(abrp_carmodel, abrp_token, DarkSkyApiKey, OpenWeatherApiKey, homelat, homelon, email, password, pin):
    global ServiceId, BasicToken, ApplicationId, ContentLengthToken, BaseHost, BaseURL, deviceId, cookies, authCode, accessToken, vehicleId, controlToken, controlTokenExpiresAt, car_brand
    global previousRangeLeft, pollCounter, sleepCycles
    try:
        # "sleepCycles" to not overload the car
        if sleepCycles != 0:
            sleepCycles -= 1
        else:
            if controlTokenExpiresAt == datetime(1970, 1, 1, 0, 0, 0) : # since this is the first time connect to the car
                deviceId = APIgetDeviceID(BaseURL, ServiceId, BaseHost)
                cookies = APIgetCookie(ServiceId, BaseURL)
                APIsetLanguage(BaseURL, cookies)
                authCode = APIgetAuthCode(BaseURL, email, password, cookies)
                accessToken = APIgetToken(BaseURL, BasicToken, ContentLengthToken, BaseHost, authCode)
                vehicleId = APIgetVehicleId(BaseURL, accessToken, deviceId, ApplicationId, BaseHost)
                APIsetWakeup(BaseURL, vehicleId, accessToken, deviceId, ApplicationId, BaseHost)
            if (datetime.now() - controlTokenExpiresAt).total_seconds() / 60 > 10:  # enter pin if longer than 10 minutes ago
                controlToken, controlTokenExpiresAt = APIgetControlToken(BaseURL, accessToken, BaseHost, deviceId, pin)
            # get values
            carstatus = APIgetStatus(BaseURL, vehicleId, controlToken, deviceId)
            odometer = APIgetOdometer(BaseURL, vehicleId, controlToken, deviceId)
            location = APIgetLocation(BaseURL, vehicleId, controlToken, deviceId)

            rangeLeft = carstatus['evStatus']['drvDistance'][0]['rangeByFuel']['totalAvailableRange']['value']
            status12V = carstatus['battery']['batState']
            soc12V = carstatus['battery']['batSoc']
            speed = location['gpsDetail']['speed']['value']
            charging = carstatus['evStatus']['batteryCharge']

            # and now determine how long to wait before nextpoll
            if soc12V < 30 or status12V != 0:
                sleepCycles = 60
            elif ((rangeLeft == previousRangeLeft) and (charging == False) and (speed == 0)):
                # car is not moving and you are not charging
                pollCounter += 1
                if (pollCounter > 5):  # Car is not moving for 5 minutes so poll again in 10
                    sleepCycles = 10
                else:
                    sleepCycles = 2
            else:  # car is moving or charging and battery > 30
                sleepCycles = 0
                pollCounter = 0
            previousRangeLeft = rangeLeft
            return True,carstatus, odometer, location
        return False, 0,0,0
    except APIError as e:
        print(str(e))
        sleepCycles = 5
        return False, -1, -1, -1

