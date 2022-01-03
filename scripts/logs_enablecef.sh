flag=$1
gsLogsConfigFile=$2
echo "parma1"$flag
echo "parma2"$gsLogsConfigFile
if [ "$flag" == "enable" ]; then
    echo "Enabling"
    cd $gsLogsConfigFile
    echo "curr Dir:"$(pwd)
    sed -i "/gaspaces.logger.GSSimpleFormatter.format = /ccom.gigaspaces.logger.GSSimpleFormatter.format = {0,date,yyyy-MM-dd HH:mm:ss} {11} CEF:0|gigaspaces|{12}|{13}|0|Legacy Message|{14}|{15}" xap_logging.properties
fi
if [ "$flag" == "disable" ]; then
    echo "Disabling"
    cd $gsLogsConfigFile
    sed -i "/gaspaces.logger.GSSimpleFormatter.format = /ccom.gigaspaces.logger.GSSimpleFormatter.format = {0,date,yyyy-MM-dd HH:mm:ss,SSS} {6} {3} [{4}] - {5}" xap_logging.properties
fi