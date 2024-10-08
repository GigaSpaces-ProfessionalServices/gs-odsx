#!/bin/bash

INDEX_COLUMN_DETAIL=""
ADD_INDEX="n"
usage() {
  cat << EOF

  DESCRIPTION: Oracle Schema change.

  USAGE: $(basename $0) [<option>]

  OPTIONS:

  -d <ddlfilename>      ddlfilename without extension
  -c <column detail>       column detail
  -a <add index>       want to add index [y/n]
  -ic <index column detail>       batch index column detail
  -h <help>       help

  EXAMPLES:
  $(basename $0) -d "STUD.TA_PERSON" -c "test1 datetime"
  $(basename $0) -d "STUD.TA_PERSON" -c "test1 datetime" -a "n"
  $(basename $0) -d "STUD.TA_PERSON" -c "test1 datetime" -a "y" -ic "STUD.TA_PERSON  MUAMAD  ORDERED"
  $(basename $0) -d "STUD.TA_PERSON" -c "test1 datetime" -h

EOF
exit
}

while [[ $# -gt 0 ]]
do

key="$1"
case $key in
    -d|--ddlName)
      DDL_NAME="$2"
    shift # past argument
    ;;
    -c|--columnDetail)
      COLUMN_DETAIL="$2"
      shift # past argument
    ;;
    -a|--addindex)
      ADD_INDEX="$2"
      shift # past argument
    ;;
    -ic|--indexColumn)
      INDEX_COLUMN_DETAIL="$2"
      shift # past argument
    ;;
    -h|--help)
      usage
      #echo "Usage: cmd [-d ddlfilename without extension] [-c column detail] [-i want to add index [y/n]] [-ic index column detail]"
      exit 1
    ;;
    *)
            # unknown option
    ;;
esac
shift # past argument or value
done
ddl_name="${DDL_NAME}" column_detail="${COLUMN_DETAIL}" add_index="${ADD_INDEX}" index_column_detail="${INDEX_COLUMN_DETAIL}" /usr/bin/expect -c '
  set ddl_name "$env(ddl_name)"
  set column_detail "$env(column_detail)"
  set add_index "$env(add_index)"
  set index_column_detail "$env(index_column_detail)"
  # Function to send each character with a delay
  proc send_each_char {str} {
      set delay 0.1  ; # Adjust the delay as needed
      foreach char [split $str ""] {
          send -- $char
          sleep $delay
      }
      send -- "\r"  ; # Simulate pressing Enter
  }

  cd /dbagiga/gs-odsx
  # cd ~/gs-odsx
  set timeout -1
  set force_conservative 1
  spawn ./odsx.py dataengine oracle-feeder schema-change
  expect "Menu -> DataEngine -> Oracle-Feeder -> Schema change"
  sleep .1
  expect "DDL filename :"
  sleep .1

  # Send the DDL name
  send_each_char $ddl_name
  sleep .1
  expect -re ".*modified ddl column.*"
  sleep .1

  # Send the column detail
  send_each_char $column_detail
  sleep .1
  expect "Object is removed successfully!!"
  sleep .1
  expect "Object is registered successfully!!"
  sleep .1
  expect -re ".*add index.*"
  sleep .1
 # send -- "\r"
  send_each_char $add_index
  sleep .1
  if { $add_index == "y" } {
    expect -re ".*modified index.*"
    sleep .1
    send_each_char $index_column_detail
  }
  sleep .1
  expect eof
'
