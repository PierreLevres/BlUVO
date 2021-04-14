# generate the stamps needed for new authentication process
import subprocess

APP_IDS = {'hyundai': '99cfff84-f4e2-4be8-a5ed-e5b755eb6581', 'kia': '693a33fa-c117-43f2-ae3b-61a02d24f417'}
SIZE = 100


def generateStampsForBrand(brand):
    process = subprocess.run(['docker', 'run', 'hacksore/hks', brand, 'list', APP_IDS[brand]], capture_output=True,
                             text=True)
    stamps = process.stdout
    stamps = stamps.splitlines()  # split this lengthy string on \n
    stamps = stamps[
             1:SIZE + 1]  # select the first 1000 to work with, deleting the very first line "generating 100.000 stamps"
    with open('../' + brand + 'tokens.py', 'w') as f:
        f.write(brand + 'stamps = ')
        f.write(str(stamps))  # needs to be converted to string to be able to be read later on (in controller.py)


# if it is needed to pull a new docker, remove comment
# subprocess.run(['docker', 'pull', 'hacksore/hks'])
generateStampsForBrand('hyundai')
generateStampsForBrand('kia')
# TODO cleanup the containter subprocess.run(['docker', 'rm', 'hacksore/hks'])

