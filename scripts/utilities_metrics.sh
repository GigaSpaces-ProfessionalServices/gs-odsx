echo "Start configuring metrics.xml.. "
sed -i '/^\s*<!--/!b;N;/<reporter name="influxdb">/s/.*\n//;T;:a;n;/^\s*-->/!ba;d' /dbagiga/gs_config/metrics.xml
sed -i '/^\s*<!--/!b;N;/<grafana url="http:\/\/localhost:3000" api-key="" user="admin" password="admin">/s/.*\n//;T;:a;n;/^\s*-->/!ba;d' /dbagiga/gs_config/metrics.xml

grafanaHost=$1
influxdbHost=$2
#echo "grafana:"$grafanaHost
#echo "influxdb:"$influxdbHost

sed -i "s|value=\"localhost\"|value=\"$influxdbHost\"|g" /dbagiga/gs_config/metrics.xml
sed -i "s|localhost:3000|$grafanaHost:3000|g" /dbagiga/gs_config/metrics.xml
sed -i "s|localhost:8086|$influxdbHost:8086|g" /dbagiga/gs_config/metrics.xml
