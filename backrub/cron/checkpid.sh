#!/bin/bash

if [ ! -f /tmp/rosettaweb-rosettadaemon.pid ] 
then
  echo "The backrub webserver daemon needs to be rebooted." | mail -s "Backrub webserver daemon failure" spiderbaby@gmail.com
  echo "The backrub webserver daemon needs to be rebooted." | mail -s "Backrub webserver daemon failure" shane.oconnor@ucsf.edu
fi

if [ ! -f /tmp/rosettaweb-clusterdaemon.pid ]
then
  echo "The backrub cluster daemon needs to be rebooted" | mail -s "Backrub cluster daemon failure" shane.oconnor@ucsf.edu
  echo "The backrub cluster daemon needs to be rebooted" | mail -s "Backrub cluster daemon failure" spiderbaby@gmail.com
fi
