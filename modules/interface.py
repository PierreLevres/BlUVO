# interface between vehicle and calling app
from dataclasses import dataclass
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


class EVPlugTypes(Enum):
  UNPLUGED = 0,
  FAST = 1,
  PORTABLE = 2,
  STATION = 3

@dataclass
class nested_subfeature:
  subFeatureName: str
  subFeatureValue: str

@dataclass
class nested_feature:
  featureName: str
  features: List[nested_subfeature]

@dataclass
class VehicleFeatureEntry:
  category: str
  features: List[nested_feature]

@dataclass #unit and value is used for speed, odometer, estmatedtime: nested_soe
class nested_soe:
  unit: int
  value: float

@dataclass
class nested_rangeByFuel:
  #gasModeRange: Optional[nested_soe]
  evModeRange: nested_soe
  totalAvailableRange: nested_soe

@dataclass
class nested_drvDistance:
  rangeByFuel: nested_rangeByFuel
  type: int

@dataclass
class nested_remainTime2:
  etc1: nested_soe
  etc2: nested_soe
  etc3: nested_soe
  atc: nested_soe

@dataclass
class nested_time:
  time: str
  timeSection: int

@dataclass
class nested_offPeakPowerTime1:
  starttime: nested_time
  endtime: nested_time

@dataclass
class nested_offpeakPowerInfo:
  offPeakPowerTime1: nested_offPeakPowerTime1
  offPeakPowerFlag: int

@dataclass
class nested_reservInfo:
  day: List[int]
  time: nested_time

@dataclass
class nested_airTemp:
  value: str
  unit: int
  hvacTempType: int

@dataclass
class nested_reservFatcSet:
  defrost: bool
  airTemp: nested_airTemp
  airCtrl: int
  heating1: int

@dataclass
class nested_reservChargeInfoDetail:
  reservInfo: nested_reservInfo
  reservChargeSet: bool
  reservFatcSet: nested_reservFatcSet

@dataclass
class nested_reservChargeInfo:
  reservChargeInfoDetail: nested_reservChargeInfoDetail

@dataclass
class nested_reserveChargeInfo2:
  reservChargeInfoDetail: nested_reservChargeInfoDetail

@dataclass
class nested_datetime:
  day: int
  time: nested_time

@dataclass
class nested_ect:
  start: nested_datetime
  end: nested_datetime

@dataclass
class nested_dte:
  rangeByFuel: nested_rangeByFuel
  type: int

@dataclass
class nested_targetSOClistelement:
  targetSOClevel: int
  dte: nested_dte
  plugType: int

@dataclass
class nested_targetSOClist:
  List[nested_targetSOClistelement]

@dataclass
class nested_reservChargeInfos:
  reservChargeInfo: nested_reservChargeInfo
  offpeakPowerInfo: nested_offpeakPowerInfo
  reserveChargeInfo2: nested_reserveChargeInfo2
  reservFlag: int
  ect: nested_ect
  targetSOClist: List[nested_targetSOClistelement]

@dataclass
class nested_evStatus:
  batteryCharge: bool
  batteryStatus: int
  batteryPlugin: int
  remainTime2: nested_remainTime2
  drvDistance: List[nested_drvDistance]
  reservChargeInfos: nested_reservChargeInfos

@dataclass
class nested_battery:
  batSoc: int
  batState: int

@dataclass
class nested_climate:
    active: bool
    steeringwheelHeat: bool
    sideMirrorHeat: bool
    rearWindowHeat: bool
    temperatureSetpoint: int
    temperatureUnit: int
    defrost: bool

@dataclass
class nested_engine:
    ignition: bool
    batteryCharge: Optional[int]
    charging: Optional[bool]
    timeToFullCharge: Optional[int]
    range: int
    rangeGas: Optional[int]
    rangeEV: Optional[int]
    plugedTo : Optional[EVPlugTypes]
    estimatedCurrentChargeDuration: Optional[int]
    estimatedFastChargeDuration: Optional[int]
    estimatedPortableChargeDuration: Optional[int]
    estimatedStationChargeDuration: Optional[int]
    batteryCharge12v: Optional[int]
    batteryChargeHV: Optional[int]
    adaptiveCruiseControl: bool

@dataclass
class nested_coord:
      lat: float
      lon: float
      alt: int
      type: int

@dataclass
class nested_doorOpen:
    frontLeft: int
    frontRight: int
    backLeft: int
    backRight: int

@dataclass
class nested_openDoors:
    frontLeft: bool
    frontRight: bool
    backLeft: bool
    backRight: bool

@dataclass
class nested_tirePressureLamp:
  tirePressureLampAll: int
  tirePressureLampFL: int
  tirePressureLampFR: int
  tirePressureLampRL: int
  tirePressureLampRR: int

@dataclass
class nested_tirePressureWarningLamp:
    rearLeft: bool
    frontLeft: bool
    frontRight: bool
    rearRight: bool
    all: bool

@dataclass
class nested_chassis:
  hoodOpen: bool
  trunkOpen: bool
  locked: bool
  openDoors: nested_openDoors
  tirePressureWarningLamp: nested_tirePressureWarningLamp

@dataclass
class nested_accuracy:
    hdop: int
    pdop: int


@dataclass
class nested_vehicleLocation:
    coord: nested_coord
    head: int
    speed: nested_soe
    accuracy: nested_accuracy
    time: str

@dataclass
class VehicleLocation:
  latitude: float
  longitude: float
  altitude: float
  heading: int

@dataclass
class VehicleOdometer:
  unit: int
  value: int
  speed: nested_soe

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



# Statusses
@dataclass
class VehicleStatus:
  engine: nested_engine
  climate: nested_climate
  chassis: nested_chassis

@dataclass
class nested_vehicleStatus:
    airCtrlOn: bool
    engine: bool
    doorLock: bool
    doorOpen: nested_doorOpen
    trunkOpen: bool
    airTemp: nested_airTemp
    defrost: bool
    acc: bool
    evStatus: nested_evStatus
    ign3: bool
    hoodOpen: bool
    transCond: bool
    steerWheelHeat: int
    sideBackWindowHeat: int
    tirePressureLamp: nested_tirePressureLamp
    battery: nested_battery
    time: str

@dataclass
class FullVehicleStatus:
  vehicleLocation: nested_vehicleLocation
  vehicleStatus: nested_vehicleStatus
  odometer: nested_soe

@dataclass
class RawVehicleStatus:
  lastStatusDate: str
  dateTime: str
  acc: bool
  trunkOpen: bool
  doorLock: bool
  defrostStatus: str
  transCond: bool
  doorLockStatus: str
  doorOpen: nested_doorOpen
  airCtrlOn: bool
  airTempUnit: str
  airTemp: nested_airTemp
  battery: nested_battery
  ign3: bool
  ignitionStatus: str
  lowFuelLight: bool
  sideBackWindowHeat: int
  dte: nested_soe
  engine: bool
  defrost: bool
  hoodOpen: bool
  airConditionStatus: str
  steerWheelHeat: int
  tirePressureLamp: nested_tirePressureLamp
  trunkOpenStatus: str
  evStatus: nested_evStatus
  drvDistance: List[nested_drvDistance]

