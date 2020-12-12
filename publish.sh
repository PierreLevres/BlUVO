#!/bin/bash
# attact the directory on the pi
FILE=~/pi/Domoticz/plugins/bluvo/plugin.py
if [ -f "$FILE" ]; then
    echo "already mounted"
else
  echo -n Password on pi:
  read -s password
  mount -t smbfs "//<pi-user>:$password@<pi_name>._smb._tcp.local/<homedir on pi>" ~/pi
fi

cd ~/pi/Domoticz/plugins/bluvo/

if [[ plugin.py -ot ~/Documents/GitHub/bluvo/plugin.py ]];
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
  if [[ $f -ot ~/Documents/GitHub/bluvo/$f ]];
  then
    RELOAD=True
    /bin/cp -rf ~/Documents/GitHub/bluvo/$f . 2>/dev/null
  fi
done
if [[ "$RESTART" == "True" ]]; then
  Echo "Please restart Domoticz"
fi
if [[ "$RELOAD" == "True" ]]; then
  Echo "Please restart Hardware"
fi




