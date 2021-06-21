#/bin/bash

#scp -r ubuntu@192.168.0.200:/home/ubuntu/C-023/ /home/pi/
gcc main.c data.c git_data.c utf_8_to_gb3212.c -o lcd_server -lwiringPi -lpthread

./lcd_server
