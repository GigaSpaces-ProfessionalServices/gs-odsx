ENV_CONFIG_PATH=$ENV_CONFIG
# Check if the environment variable is set
if [ -z "$ENV_CONFIG_PATH" ]; then
  echo "Error: $ENV_CONFIG_PATH is not set. Please set it before running this script."
  exit 1
else
  echo "$ENV_CONFIG_PATH is set to: $ENV_CONFIG_PATH"
fi
ENV_CONFIG_APP="$ENV_CONFIG_PATH/app.config"

read_property() {
  local prop_name="$1"
  local prop_value

  prop_value=$(grep "^$prop_name=" "$ENV_CONFIG_APP" | awk -F'=' '{print $2}')
  echo "$prop_value"
}

gigapath=$(read_property "app.giga.path")
gigainfluxpath=$(read_property "app.gigainfluxdata.path")
gigasharepath=$(read_property "app.gigashare.path")
gigadatapath=$(read_property "app.gigadata.path")
gigalogpath=$(read_property "app.gigalog.path")
gigaworkPath=$(read_property "app.gigawork.path")

sed -i '/export PYTHONPATH=$(dirname $(pwd))/d' ~/.bash_profile

#echo 'export PYTHONPATH=$(dirname $(pwd))' >> ~/.bashrc
project_home_dir=$(dirname $(pwd))
python_path="export PYTHONPATH="$project_home_dir
echo "$python_path" >> ~/.bash_profile
odsx_path="export ODSXARTIFACTS="$gigasharepath"/current/"
echo "$odsx_path" >> ~/.bash_profile
echo 'eval "$(register-python-argcomplete odsx.py)"' >> ~/.bash_profile

sed -i '/eval "$(register-python-argcomplete odsx.py)"/d' ~/.bash_profile
echo 'eval "$(register-python-argcomplete odsx.py)"' >> ~/.bash_profile
.  ~/.bash_profile
pip3 install -r requirements.txt
