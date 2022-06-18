#!/bin/bash
#source /home/dbsh/setenv.sh

systemctl stop odsxadabas.service
systemctl disable odsxadabas.service
systemctl daemon-reload

rm -rf install install.tar /home/dbsh/install /home/dbsh/install.tar /home/dbsh/setenv.sh /usr/local/bin/st*_adabasFeeder.sh /etc/systemd/system/odsxadabas.service /dbagiga/Adabas/* /dbagigalogs/Adabas/*
