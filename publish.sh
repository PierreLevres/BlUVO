#!/bin/bash
# attact the directory on the pi
FILE=~/pi/Domoticz/plugins/bluvo/plugin.py
if [ -f "$FILE" ]; then
    echo "al gemount"
else
  echo -n Password voor de pi:
  read -s password
  mount -t smbfs "//pi:$password@RPI._smb._tcp.local/pi" ~/pi
fi

cd ~/pi/Domoticz/plugins/bluvo/

if [[ plugin.py -ot /Users/peter/Documents/GitHub/bluvo/plugin.py ]];
then
  RESTART=True
else
  RESTART=False
fi

RELOAD=False
FILES=*.py

for f in $FILES
do
  # take action on each file. $f store current file name
  if [[ $f -ot /Users/peter/Documents/GitHub/bluvo/$f ]];
  then
    RELOAD=True
    /bin/cp -rf /Users/peter/Documents/GitHub/bluvo/$f . 2>/dev/null
  fi
done
if [[ "$RESTART" == "True" ]]; then
  Echo "Please restart Domoticz"
fi
if [[ "$RELOAD" == "True" ]]; then
  Echo "Please restart Hardware"
fi




