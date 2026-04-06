#!/bin/bash

function usage () {
  cat << EOF

  NAME

    $(basename $0) – Basic odsx setup

  USAGE:

    $(basename $0) <gigashare dir> <gigashare.tgz>

  EXAMPLE:

    $(basename $0) /gigashare /tmp/gigashare.tgz

EOF
exit
}

# Validate user root
if [[ "$(id -u)" -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

[[ $# -eq 0 || $1 == "-h" ]] && usage
[[ -z $1 ]] && { echo -e "\nMust provide a directory for gigashare as argument.\n" ; exit 1 ; } 
[[ ! -d $1 ]] & { echo -e "\nThe gigashare directory does not exist.\n" ; exit 1 ; }
[[ ! -s $2 ]] && { echo -e "\nThe gigashare.tgz is empty or does not exist.\n" ; exit 1 ; }
echo -e "Extracting gigashare"
tar xzf $2 -C $1
# Check if the environment variable is set
ENV_CONFIG_PATH="$1/env_config"
echo "ENV_CONFIG_PATH is set to: $ENV_CONFIG_PATH"
[[ ! -d "$ENV_CONFIG_PATH ]] && { echo -e "\nThe gigashare/env_config does not exist.\n" ; exit 1 ; }

# set app.config var
ENV_CONFIG_APP="$ENV_CONFIG_PATH/app.config"

read_property() {
  local prop_name="$1"
  local prop_value

  prop_value=$(grep "^$prop_name=" "$ENV_CONFIG_APP" | awk -F'=' '{print $2}')
  echo "$prop_value"
}

gigashare=$(read_property "app.gigashare.path")
gigawork=$(read_property "app.gigawork.path")
gigalog=$(read_property "app.gigalog.path")
gigapath=$(read_property "app.giga.path")
gigadatapath=$(read_property "app.gigadata.path")
gigainfluxpath=$(read_property "app.gigainfluxdata.path")

# Validate all required path keys are present in app.config
missing_paths=0
for key_var in "app.gigashare.path:$gigashare" "app.gigawork.path:$gigawork" "app.gigalog.path:$gigalog" "app.giga.path:$gigapath" "app.gigadata.path:$gigadatapath" "app.gigainfluxdata.path:$gigainfluxpath"; do
  key="${key_var%%:*}"
  val="${key_var#*:}"
  if [ -z "$val" ]; then
    echo "Error: '$key' is not set in $ENV_CONFIG_APP. All path keys are required."
    missing_paths=1
  fi
done
if [ "$missing_paths" -eq 1 ]; then
  exit 1
fi

mkdir $gigalog/
mkdir $gigashare
mkdir $gigawork
mkdir $gigapath
mkdir $gigadatapath
mkdir $gigainfluxpath
touch $gigalog/odsx.log

#SQLite - wget https://www.sqlite.org/2022/sqlite-tools-linux-x86-3380000.zip
mkdir $gigawork/sqlite
cd $gigawork/sqlite
cp /gigashare/current/sqlite3/* .

# Make sure gsods exists
if ! id "gsods" >/dev/null 2>&1; then
  useradd -m gsods
fi

chown gsods:gsods $gigapath
chown gsods:gsods $gigadatapath
chown gsods:gsods $gigalog
chown gsods:gsods $gigawork
chown gsods:gsods $gigashare
chown gsods:gsods $gigainfluxpath
chown -R gsods:gsods $gigashare/*
chown -R gsods:gsods $gigapath/*

# --- Non-root prerequisites ---

# Enable user-level systemd for gsods (persists after logout)
loginctl enable-linger gsods

# Create user-level systemd directory
gsods_home=$(eval echo ~gsods)
mkdir -p "$gsods_home/.config/systemd/user/"
chown -R gsods:gsods "$gsods_home/.config/"

# Create /giga/bin for start/stop scripts (replaces /usr/local/bin)
mkdir -p $gigapath/bin
chown gsods:gsods $gigapath/bin

# Set file descriptor limits for gsods
applicativeUser="gsods"
nofileLimitFile=$(read_property "app.user.nofile.limit")
if [ -z "$nofileLimitFile" ]; then
    nofileLimitFile=50000
fi
sed -i '/hard nofile/d' /etc/security/limits.conf
sed -i '/soft nofile/d' /etc/security/limits.conf
echo "" >> /etc/security/limits.conf
echo "$applicativeUser hard nofile $nofileLimitFile" >> /etc/security/limits.conf
echo "$applicativeUser soft nofile $nofileLimitFile" >> /etc/security/limits.conf

# Sudoers entries for third-party monitoring services (Grafana, InfluxDB, Telegraf)
cat > /etc/sudoers.d/odsx-monitoring << 'SUDOERS'
gsods ALL=(ALL) NOPASSWD: /bin/systemctl start grafana-server.service, /bin/systemctl stop grafana-server.service, /bin/systemctl restart grafana-server.service, /bin/systemctl status grafana-server.service, /bin/systemctl enable grafana-server.service
gsods ALL=(ALL) NOPASSWD: /bin/systemctl start influxdb.service, /bin/systemctl stop influxdb.service, /bin/systemctl restart influxdb.service, /bin/systemctl status influxdb.service, /bin/systemctl enable influxdb.service
gsods ALL=(ALL) NOPASSWD: /bin/systemctl start telegraf.service, /bin/systemctl stop telegraf.service, /bin/systemctl restart telegraf.service, /bin/systemctl status telegraf.service, /bin/systemctl enable telegraf.service
SUDOERS
chmod 0440 /etc/sudoers.d/odsx-monitoring

