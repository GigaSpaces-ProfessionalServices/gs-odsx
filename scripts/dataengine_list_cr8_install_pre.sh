#!/bin/bash

cd /home/dbsh
#tar -xvf install.tar

home_dir=$(pwd)
installation_path=$home_dir/install/cr8

IS_CR8_INSTALL=0
if [ -d "/home/dbsh/cr8/latest_cr8/utils" ]
then
	cd /home/dbsh/cr8/latest_cr8/utils
	installation_file=$(find $installation_path -name *.rpm -printf "%f\n")

  INSTALLED_CR8_VER=$(echo $(./check_CR8jar_version.sh) |tr -dc '.''0-9' | cut -c 1-9)
	CR8_VER=$(echo $installation_file |tr -dc '.''0-9' | cut -c 2-9)
	INSTALLED_CR8_VER=$(echo $INSTALLED_CR8_VER | sed -e "s/\./${replace}/g")
	CR8_VER=$(echo $CR8_VER | sed -e "s/\./${replace}/g")

	cd

	if [[ "$INSTALLED_CR8_VER" = "$CR8_VER" ]]; then
     IS_CR8_INSTALL=4
	elif [[ "$INSTALLED_CR8_VER" > "$CR8_VER" ]]; then
	   IS_CR8_INSTALL=3
	elif [[ "$INSTALLED_CR8_VER" < "$CR8_VER" ]]; then
	   IS_CR8_INSTALL=2
	else
	   IS_CR8_INSTALL=1
	fi

else
  	 IS_CR8_INSTALL=1
fi

# IS_CR8_INSTALL= 1 -> install, 2-> installed version is lower, 3-> installed version is higher, 4-> installed version is same

echo "IS_CR8_INSTALL=" $IS_CR8_INSTALL
