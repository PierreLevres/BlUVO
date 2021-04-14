# interface between vehicle and calling app
from dataclasses import dataclass, field
from typing import Optional, List
import datetime
from enum import Enum


@dataclass
class BluelinkyConfig:
    username: str
    password: str
    pin: str
    vin: Optional[str]
    brand: str


@dataclass
class EuropeanEndpoints:
    session: str
    login: str
    redirect_uri: str
    token: str


@dataclass
class BluelinkVehicle:
    name: str
    vin: str
    type: str


@dataclass
class Session:
    accessToken: str
    refreshToken: str
    controlToken: str
    deviceId: str
    accessTokenExpiresAt: datetime
    controlTokenExpiresAt: datetime
    stamp: str
    cookies: str


@dataclass
class VehicleRegisterOptions:
    nickname: str
    name: str
    vin: str
    regDate: str
    brandIndicator: str
    regId: str
    id: str
    generation: str


@dataclass
class VehicleInfo:
    vehicleId: str
    nickName: str
    modelCode: str
    modelName: str
    modelYear: str
    fuelKindCode: str
    trim: str
    engine: str
    exteriorColor: str
    dtcCount: int
    subscriptionStatus: str
    subscriptionEndDate: str
    overviewMessage: str
    odometer: float
    odometerunit: int
    defaultVehicle: bool
    enrollmentStatus: str
    genType: str
    transmissionType: str
    vin: str


@dataclass
class object_subfeature:
    subFeatureName: str
    subFeatureValue: str


@dataclass
class object_feature:
    featureName: str
    features: List[object_subfeature]


@dataclass
class VehicleFeatureEntry:
    category: str
    features: List[object_feature]


# from here: all stuff for controlling the vehicle
class EVPlugTypes(Enum):
    UNPLUGGED = 0,
    FAST = 1,
    PORTABLE = 2,
    STATION = 3


# unit and value is used for speed, odometer, estmatedtime: object_unit_value
@dataclass
class object_unit_value:
    value: float = 1.0
    unit: int = 1


@dataclass
class object_rangeByFuel:
    gasModeRange: object_unit_value = field(default_factory=object_unit_value)
    evModeRange: object_unit_value = field(default_factory=object_unit_value)
    totalAvailableRange: object_unit_value = field(default_factory=object_unit_value)


@dataclass
class object_drvDistance:
    rangeByFuel: object_rangeByFuel = field(default_factory=object_rangeByFuel)
    type: int = 1


@dataclass
class object_remainTime2:
    etc1: object_unit_value = field(default_factory=object_unit_value)
    etc2: object_unit_value = field(default_factory=object_unit_value)
    etc3: object_unit_value = field(default_factory=object_unit_value)
    atc: object_unit_value = field(default_factory=object_unit_value)


@dataclass
class object_time:
    time: str = "20200101000000"
    timeSection: int = 0


@dataclass
class object_offPeakPowerTime1:
    starttime: object_time = field(default_factory=object_time)
    endtime: object_time = field(default_factory=object_time)


@dataclass
class object_offpeakPowerInfo:
    offPeakPowerTime1: object_offPeakPowerTime1 = field(default_factory=object_offPeakPowerTime1)
    offPeakPowerFlag: int = 0


@dataclass
class object_reservInfo:
    day: List[int]
    time: object_time = field(default_factory=object_time)


@dataclass
class object_airTemp:
    value: str = "0FH"
    unit: int = 0
    hvacTempType: int = 1


@dataclass
class object_reservFatcSet:
    airTemp: object_airTemp = field(default_factory=object_airTemp)
    defrost: bool = False
    airCtrl: int = 0
    heating1: int = 0


@dataclass
class object_reservChargeInfoDetail:
    reservInfo: object_reservInfo = field(default_factory=object_reservInfo)
    reservFatcSet: object_reservFatcSet = field(default_factory=object_reservFatcSet)
    reservChargeSet: bool = False


@dataclass
class object_reservChargeInfo:
    reservChargeInfoDetail: object_reservChargeInfoDetail = field(default_factory=object_reservChargeInfoDetail)


@dataclass
class object_reserveChargeInfo2:
    reservChargeInfoDetail: object_reservChargeInfoDetail = field(default_factory=object_reservChargeInfoDetail)


@dataclass
class object_datetime:
    time: object_time = field(default_factory=object_time)
    day: int = 0


@dataclass
class object_ect:
    start: object_datetime = field(default_factory=object_datetime)
    end: object_datetime = field(default_factory=object_datetime)


@dataclass
class object_dte:
    rangeByFuel: object_rangeByFuel = field(default_factory=object_rangeByFuel)
    type: int = 1


@dataclass
class object_targetSOClistelement:
    dte: object_dte = field(default_factory=object_dte)
    targetSOClevel: int = 100
    plugType: int = 1


# @dataclass
# class object_targetSOClist:
#  List[object_targetSOClistelement]

# making a mess Hyundai/Kia: reserveChargeInfo2 and reservChargeInfo   -> see how an 'e' is added in nr2
@dataclass
class object_reservChargeInfos:
    targetSOClist: List[object_targetSOClistelement]
    offpeakPowerInfo: object_offpeakPowerInfo = field(default_factory=object_offpeakPowerInfo)
    reservChargeInfo: object_reservChargeInfo = field(default_factory=object_reservChargeInfo)
    reserveChargeInfo2: object_reserveChargeInfo2 = field(default_factory=object_reserveChargeInfo2)
    reservFlag: int = 0
    ect: object_ect = field(default_factory=object_ect)


@dataclass
class object_battery:
    batSoc: int
    batState: int


@dataclass
class object_climate:
    active: bool = False
    steeringwheelHeat: bool = False
    sideMirrorHeat: bool = False
    rearWindowHeat: bool = False
    temperatureSetpoint: int = 20
    temperatureUnit: int = 1
    defrost: bool = False


@dataclass
class object_engine:
    ignition: bool = False
    batteryCharge: int = 0
    charging: bool = False
    range: int = 0
    rangeGas: int = 0
    rangeEV: int = 0
    pluggedTo: int = 0
    estimatedCurrentChargeDuration: int = 0
    estimatedFastChargeDuration: int = 0
    estimatedPortableChargeDuration: int = 0
    estimatedStationChargeDuration: int = 0
    batteryCharge12v: int = 0
    batteryChargeHV: int = 0
    accessory: bool = True


@dataclass
class VehicleLocation:
    lat: float = 52.000000
    lon: float = 4.350000
    alt: float = 0
    type: int = 0


@dataclass
class object_doorOpen:
    frontLeft: int = 0
    frontRight: int = 0
    backLeft: int = 0
    backRight: int = 0


@dataclass
class object_tirePressureLamp:
    tirePressureLampAll: int = 0
    tirePressureLampFL: int = 0
    tirePressureLampFR: int = 0
    tirePressureLampRL: int = 0
    tirePressureLampRR: int = 0


# for parsed statusses
@dataclass
class object_openDoors:
    frontLeft: bool = False
    frontRight: bool = False
    backLeft: bool = False
    backRight: bool = False


@dataclass
class object_tirePressureWarningLamp:
    rearLeft: bool = False
    frontLeft: bool = False
    frontRight: bool = False
    rearRight: bool = False
    all: bool = False


@dataclass
class object_chassis:
    openDoors: object_openDoors = field(default_factory=object_openDoors)
    tirePressureWarningLamp: object_tirePressureWarningLamp = field(default_factory=object_tirePressureWarningLamp)
    hoodOpen: bool = False
    trunkOpen: bool = False
    locked: bool = False


# generic types
@dataclass
class object_accuracy:
    hdop: int = 10
    pdop: int = 10


@dataclass
class object_vehicleLocation:
    coord: VehicleLocation = field(default_factory=VehicleLocation)
    speed: object_unit_value = field(default_factory=object_unit_value)
    accuracy: object_accuracy = field(default_factory=object_accuracy)
    head: int = 0
    time: str = "20210101000000"


# location call returns
# {'gpsDetail':
#   {'coord': {'lat': 52.004478, 'lon': 4.3545, 'alt': 0, 'type': 0},
#    'head': 165,
#    'speed': {'value': 0, 'unit': 1},
#    'accuracy': {'hdop': 10, 'pdop': 10},
#    'time': '20210314160435'},
#    'drvDistance': {'rangeByFuel': {'evModeRange': {'value': 0, 'unit': 1}, 'totalAvailableRange': {'value': 0, 'unit': 1}}, 'type': 2}}


@dataclass
class VehicleOdometer:
    unit: int
    value: float


@dataclass
class object_battery:
    batSoc: int = 84
    batState: int = 0


@dataclass
class object_evStatus:
    drvDistance: List[object_drvDistance]
    remainTime2: object_remainTime2 = field(default_factory=object_remainTime2)
    reservChargeInfos: object_reservChargeInfos = field(default_factory=object_reservChargeInfos)
    batteryCharge: bool = False
    batteryStatus: int = 100
    batteryPlugin: int = 0


@dataclass
class ParsedVehicleStatus:  # short
    lastUpdated: datetime = datetime.datetime.now()
    engine: object_engine = field(default_factory=object_engine)
    climate: object_climate = field(default_factory=object_climate)
    chassis: object_chassis = field(default_factory=object_chassis)


@dataclass
class rawVehicleStatus:  # short, unparsed
    airTemp: object_airTemp = field(default_factory=object_climate)
    evStatus: object_evStatus = field(default_factory=object_evStatus)
    doorOpen: object_doorOpen = field(default_factory=object_doorOpen)
    tirePressureLamp: object_tirePressureLamp = field(default_factory=object_tirePressureLamp)
    battery: object_battery = field(default_factory=object_battery)
    airCtrlOn: bool = False
    engine: bool = False
    doorLock: bool = True
    trunkOpen: bool = False
    defrost: bool = False
    acc: bool = False
    ign3: bool = True
    hoodOpen: bool = False
    transCond: bool = True
    steerWheelHeat: int = 0
    sideBackWindowHeat: int = 0
    time: str = "20210101000000"


@dataclass
class FullVehicleStatus:  # long
    vehicleLocation: object_vehicleLocation = field(default_factory=object_vehicleLocation)
    vehicleStatus: rawVehicleStatus = field(default_factory=rawVehicleStatus)
    odometer: object_unit_value = field(default_factory=object_unit_value)


# input classes for commands
@dataclass
class VehicleStatusOptions:
    refresh: bool
    parsed: bool


@dataclass
class VehicleCommandResponse:
    responseCode: int
    responseDesc: str


@dataclass
class VehicleStartOptions:
    airCtrl: Optional[bool]
    igniOnDuration: int
    airTempvalue: Optional[str]
    defrost: Optional[bool]
    heating1: Optional[bool]


@dataclass
class VehicleClimateOptions:
    defrost: bool
    windscreenHeating: bool
    temperature: int
    unit: str

@dataclass
class PoiInfo:
    addr: str
    placeid: str
    name: str
    coord: VehicleLocation = field(default_factory=VehicleLocation)
    phone: str = ""
    waypointID: int = 0
    lang: int = 1
    src: str = 'HERE'
    zip: str = ""
