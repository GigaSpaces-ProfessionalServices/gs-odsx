echo "Installation starting..."
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

gigapath=$(read_property "app.giga.path")
gigainfluxpath=$(read_property "app.gigainfluxdata.path")
gigasharepath=$(read_property "app.gigashare.path")
gigadatapath=$(read_property "app.gigadata.path")
gigalogpath=$(read_property "app.gigalog.path")
gigaworkPath=$(read_property "app.gigawork.path")

echo $1 "====" $2
cd $1
logDir=$gigalogpath"/nginx"
if [ ! -d "/$logDir" ]; then
   mkdir -p /$logDir
   chmod 755 /$logDir
fi
pwd
./install_nb_infra.sh $2
echo "Setting NB_HOME"
cd
path="export NB_HOME="$1
sed -i '/export NB_HOME/d' .bashrc
#echo "">>setenv.sh
echo "$path">>.bashrc

setsebool -P httpd_read_user_content 1
chcon -Rt httpd_sys_rw_content_t $gigalogpath/nginx/

echo "Setting NB_HOME -Done!"
