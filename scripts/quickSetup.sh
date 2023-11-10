
ENV_CONFIG_PATH=$ENV_CONFIG
# Check if the environment variable is set
if [ -z "$ENV_CONFIG_PATH" ]; then
  echo "Error: $ENV_CONFIG_PATH is not set. Please set it before running this script."
  exit 1
else
  echo "$ENV_CONFIG_PATH is set to: $ENV_CONFIG_PATH"
fi
ENV_CONFIG_PATH="$ENV_CONFIG_PATH/app.config"

read_property() {
  local prop_name="$1"
  local prop_value

  prop_value=$(grep "^$prop_name=" "$ENV_CONFIG_PATH" | awk -F'=' '{print $2}')
  echo "$prop_value"
}

gigashare=$(read_property "app.gigashare.path")
gigalog=$(read_property "app.gigalog.path")
gigapath=$(read_property "app.giga.path")
gigainfluxpath=$(read_property "app.gigainfluxdata.path")

sed -i '/export PYTHONPATH=$(dirname $(pwd))/d' ~/.bash_profile
sed -i -e 's|/dbagigalogs/|'$gigalog'/|g' $gigapath/gs-odsx/config/logging.conf
sed -i -e 's|/dbagigalogs/|'$gigalog'/|g' $gigashare/current/gs/config/scripts/start_gsc.sh
sed -i -e 's|/dbagigalogs/|'$gigalog'/|g' $gigashare/current/gs/config/log/xap_logging.properties
sed -i -e 's|/dbagigalogs/|'$gigalog'/|g' $gigashare/current/telegraf/scripts/space/telegraf_wal-size.sh
sed -i -e 's|/dbagigalogs/|'$gigalog'/|g' $gigashare/current/mq-connector/adabas/config/application.yml
sed -i -e 's|/dbagigalogs/|'$gigalog'/|g' $gigashare/current/mq-connector/config/application.yml
sed -i -e 's|/dbagigainflaxdata/|'$gigainfluxpath'/|g' $gigashare/current/influx/config/influxdb.conf.template

#echo 'export PYTHONPATH=$(dirname $(pwd))' >> ~/.bashrc
project_home_dir=$(dirname $(pwd))
python_path="export PYTHONPATH="$project_home_dir
echo "$python_path" >> ~/.bash_profile
odsx_path="export ODSXARTIFACTS="$gigashare"/current/"
echo "$odsx_path" >> ~/.bash_profile
echo 'eval "$(register-python-argcomplete odsx.py)"' >> ~/.bash_profile
.  ~/.bash_profile