#!/bin/bash
# attact the directory on the pi
#mount -t cifs //pi@RPI._smb._tcp.local/pi /Volumes/pi

cd /Volumes/pi/Domoticz/plugins/bluvo/

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
  Echo "Restart Domoticz"
fi
if [[ "$RELOAD" == "True" ]]; then
  Echo "Restart Hardware"
fi




