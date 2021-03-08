from enum import Enum
from string import Template
#enumerates constants
BaseHost = { 'hyundai':'prd.eu-ccapi.hyundai.com:8080','kia':'prd.eu-ccapi.kia.com:8080'}
BaseURL = { 'hyundai':'https://prd.eu-ccapi.hyundai.com:8080','kia':'https://prd.eu-ccapi.kia.com:8080'}
ServiceId = { 'hyundai':'6d477c38-3ca4-4cf3-9557-2a1929a94654','kia':'fdc85c00-0a2f-4c64-bcb4-2cfb1500730a'}
BasicToken =  {'hyundai': 'Basic NmQ0NzdjMzgtM2NhNC00Y2YzLTk1NTctMmExOTI5YTk0NjU0OktVeTQ5WHhQekxwTHVvSzB4aEJDNzdXNlZYaG10UVI5aVFobUlGampvWTRJcHhzVg==', 'kia': 'Basic ZmRjODVjMDAtMGEyZi00YzY0LWJjYjQtMmNmYjE1MDA3MzBhOnNlY3JldA=='}
GCMSenderID  = { 'hyundai': '199360397125', 'kia': '199360397125',} #doesnt seem to be used on iOS
ApplicationId = { 'hyundai':'99cfff84-f4e2-4be8-a5ed-e5b755eb6581','kia':'693a33fa-c117-43f2-ae3b-61a02d24f417'} #doesnt seem to be used

UserAgentPreLogon = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_1 like Mac OS X) AppleWebKit/604.3.5 (KHTML, like Gecko) Version/11.0 Mobile/15B92 Safari/604.1'
UserAgent = 'UVO_Store/1.5.9 (iPhone; iOS 14.4; Scale/3.00)'
Accept = '*/*'
CcspApplicationId = '8464b0bf-4932-47b0-90ed-555fef8f143b'
AcceptLanguageShort = 'nl-nl'
AcceptLanguage = 'nl-NL;q=1, en-NL;q=0.9'
AcceptEncoding = 'gzip, deflate, br'
ContentType = 'application/x-www-form-urlencoded;charset=UTF-8'
ContentJSON = 'application/json;charset=UTF-8'
Connection = 'keep-alive'

