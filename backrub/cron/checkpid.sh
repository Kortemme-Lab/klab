#!/bin/bash

if [ ! -f /tmp/daemon-example.pid ] 
then
  echo "The backrub webserver daemon needs to be rebooted." | mail -s "Backrub failure" spiderbaby@gmail.com
  echo "The backrub webserver daemon needs to be rebooted." | mail -s "Backrub failure" shane.oconnor@ucsf.edu
fi

#echo "The backrub webserver daemon needs to be rebooted" | mail -s "Backrub failure" shane.oconnor@ucsf.edu
#if [ ! -f /tmp/daemon-example.pid ] then
# echo "The backrub webserver daemon needs to be rebooted" | mail -s "Backrub failure" spiderbaby@gmail.com
#fi
