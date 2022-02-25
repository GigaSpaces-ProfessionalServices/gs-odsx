flag=$1
gsLogsConfigFile=$2
#echo ""$flag
#echo "parma2"$gsLogsConfigFile
if [ "$flag" == "enable" ]; then
    echo "Enabling"
    #cd $gsLogsConfigFile
    cp $gsLogsConfigFile $gsLogsConfigFile.reg
    #echo "Copying CEF file at :"$gsLogsConfigFile
    #Take xap prop file from source
    # backup /dbagiga/gs_config/xap.properties.cef
    #sed -i "/gaspaces.logger.GSSimpleFormatter.format = /ccom.gigaspaces.logger.GSSimpleFormatter.format = {0,date,yyyy-MM-dd HH:mm:ss} {11} CEF:0|gigaspaces|{12}|{13}|0|Legacy Message|{14}|{15}" xap_logging.properties
fi
if [ "$flag" == "disable" ]; then
    echo "Disabling"
    #cd $gsLogsConfigFile
    # backup /dbagiga/gs_config/xap.properties.reg
    cp $gsLogsConfigFile $gsLogsConfigFile.cef
    mv $gsLogsConfigFile.reg $gsLogsConfigFile
    #sed -i "/gaspaces.logger.GSSimpleFormatter.format = /ccom.gigaspaces.logger.GSSimpleFormatter.format = {0,date,yyyy-MM-dd HH:mm:ss,SSS} {6} {3} [{4}] - {5}" xap_logging.properties
fi
if [ "$flag" == "clean" ]; then
    echo "Cleaning logs from "$gsLogsConfigFile
    rm -rf $gsLogsConfigFile/*
    # backup /dbagiga/gs_config/xap.properties.reg
    #sed -i "/gaspaces.logger.GSSimpleFormatter.format = /ccom.gigaspaces.logger.GSSimpleFormatter.format = {0,date,yyyy-MM-dd HH:mm:ss,SSS} {6} {3} [{4}] - {5}" xap_logging.properties
fi