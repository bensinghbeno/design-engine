#!/bin/bash 

for i in {1..100}
do
    ping -c1 192.168.2.156 >> /dev/null
    if [ $? -eq 0 ]
    then
        #echo success
         mplayer -really-quiet ~/engine/data/msg_tone.mp3 >> /dev/null &
         exit
    fi
done
