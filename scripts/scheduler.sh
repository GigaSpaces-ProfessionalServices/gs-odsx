#!/bin/bash
# chkconfig: 2345 93 80
# description: Elastic Search Service

# Source function library.
#. /etc/rc.d/init.d/functions


# Set script Home Folder

# nohup ./scripts/ods_scheduler.py > odsx_scheduler.log &
# echo "Launched ods_scheduler.py in background"

SCRIPT_HOME=scripts
SCRIPT_NAME=scripts/ods_scheduler.py
PROCESS_NAME=ods_scheduler.py
USER="ubuntu"
LOG_FILE="scheduler.log"

pid_list() {
        process=`ps auxwww | egrep -v -e "(ps|grep)" | egrep -e "$1" | awk '{print $2}'`
}

# To start the server
start() {
    if [[ $EUID -ne 0 ]]; then
        nohup ./scripts/ods_scheduler.py > $LOG_FILE &
    else
        daemon --user=$USER -r $SCRIPT_NAME
        ret=$?
        if [ $ret -eq 0 ]; then
                echo "Starting $SCRIPT_NAME as a daemon"
        else
                echo "Unable to start $SCRIPT_NAME as a daemon"
        fi
        return $ret
    fi
    ret=$?
    if [ $ret -eq 0 ]; then
            echo "Started $SCRIPT_NAME in background"
    else
            echo "Unable to start $SCRIPT_NAME in background"
    fi
    return $ret
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

# Get server status
status() {
        pid_list "($PROCESS_NAME)"
        if [ "$process" ]; then
                echo "$PROCESS_NAME is running with PID $process"
        else
                echo "$PROCESS_NAME is not running"
        fi
}

### main logic ###
case "$1" in
  start)
        start
        ;;
  stop)
        stop
        ;;
  status)
        status
        ;;
  restart)
        stop
        sleep 1s
        start
        ;;
  *)
        echo $"Usage: $0 {start|stop|restart|status}"
        exit 1
esac

exit 0
