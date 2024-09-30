#!/usr/bin/expect -f

proc send_as_typing {str} {
    set delay 0.1  ; # Adjust the delay as needed
    foreach char [split $str ""] {
        send -- $char
        sleep $delay
    }
    send -- "\r"  ; # Simulate pressing Enter
}

cd /dbagiga/gs-odsx
#cd ~/gs-odsx
set timeout -1
set force_conservative 1
spawn ./odsx.py dataengine oracle-feeder schema-change
expect "Menu -> DataEngine -> Oracle-Feeder -> Schema change"
sleep .1
expect "DDL filename :"
sleep .1
#send -- "\r"
send_as_typing "STUD.TA_PERSON"
sleep .1
expect "modified ddl column (Ex. BZ00_TOKEN	DECIMAL(11, 0)	NOT NULL) :"
sleep .1
send_as_typing "test1 char(1)"
sleep .1
expect "Object is removed successfully!!"
sleep .1
expect "Object is registered successfully!!"
#send -- "\n"
sleep .1
expect -re ".*add index.*"
#expect "Do you want to add index (y/n) [n] ?"
sleep .1
send -- "\r"
sleep .1
expect eof
