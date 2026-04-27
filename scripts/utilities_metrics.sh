# Load shared read_property helper (no-op when piped over SSH; see lib_app_config.sh).
[ -r "$(dirname "$0")/lib_app_config.sh" ] && source "$(dirname "$0")/lib_app_config.sh"

echo "Start configuring metrics.xml.. "
ENV_CONFIG_PATH=$ENV_CONFIG
# Check if the environment variable is set
if [ -z "$ENV_CONFIG_PATH" ]; then
  echo "Error: $ENV_CONFIG_PATH is not set. Please set it before running this script."
  exit 1
else
  echo "$ENV_CONFIG_PATH is set to: $ENV_CONFIG_PATH"
fi
ENV_CONFIG_PATH="$ENV_CONFIG_PATH/app.config"


gigapath=$(read_property "app.giga.path")
gigainfluxpath=$(read_property "app.gigainfluxdata.path")
gigasharepath=$(read_property "app.gigashare.path")
gigadatapath=$(read_property "app.gigadata.path")
gigalogpath=$(read_property "app.gigalog.path")
gigaworkPath=$(read_property "app.gigawork.path")

sed -i '/^\s*<!--/!b;N;/<reporter name="influxdb">/s/.*\n//;T;:a;n;/^\s*-->/!ba;d' $gigapath/gs_config/metrics.xml
sed -i '/^\s*<!--/!b;N;/<grafana url="http:\/\/localhost:3000" api-key="" user="admin" password="admin">/s/.*\n//;T;:a;n;/^\s*-->/!ba;d' $gigapath/gs_config/metrics.xml

grafanaHost=$1
influxdbHost=$2
#echo "grafana:"$grafanaHost
#echo "influxdb:"$influxdbHost

sed -i "s|value=\"localhost\"|value=\"$influxdbHost\"|g" $gigapath/gs_config/metrics.xml
sed -i "s|localhost:3000|$grafanaHost:3000|g" $gigapath/gs_config/metrics.xml
sed -i "s|localhost:8086|$influxdbHost:8086|g" $gigapath/gs_config/metrics.xml
