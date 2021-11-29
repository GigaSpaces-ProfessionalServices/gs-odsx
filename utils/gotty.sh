#!/bin/bash

PROCESS_NAME=gotty

pid_list() {
        process=`ps auxwww | egrep -v -e "(ps|grep)" | egrep -e "$1" | awk '{print $2}'`
}

# To start the server
start() {
    ./gotty_linux_amd64/gotty --config ./gotty_linux_amd64/gotty.conf bash &
}

# To stop the server
stop() {
        pid_list "($PROCESS_NAME)"
        if [ "$process" ]; then
                echo "Sending wakeup signal for graceful exit"
                kill $process > /dev/null 2>&1
                sleep 20
                pid_list "($PROCESS_NAME)"
                if [ "$process" ]; then
                        echo "Killing $PROCESS_NAME running with PID $process"
                        kill -9 $process > /dev/null 2>&1
                fi
        fi
}

while [[ $# -ge 1 ]]
do

    key="$1"
    case $key in
        -e|--enable)
        start
        shift # past argument
        ;;
        -d|--disable)
        stop
        shift # past argument
        ;;
        *)
                # unknown option
        ;;
    esac
    shift # past argument or value
done
