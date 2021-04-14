import logging


class ApiError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
        logger = logging.getLogger('root')
        logger.error(self.message)

def api_error(message):
    logger = logging.getLogger('root')
    logger.error(message)
    print(message)


def temp2hex(temp):
    if temp <= 14: return "00H"
    if temp >= 30: return "20H"
    return str.upper(hex(round(float(temp) * 2) - 28).split("x")[1]) + "H"  # rounds to .5 and transforms to Kia-hex (cut off 0x and add H at the end)


def hex2temp(hextemp):
    temp = int(hextemp[:2], 16) / 2 + 14
    if temp <= 14: return 14
    if temp >= 30: return 30
    return temp