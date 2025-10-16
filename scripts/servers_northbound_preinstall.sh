echo "Starting pre Installation configuration."
echo "Extracting install.tar to "$targetDir
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

tar -xvf install.tar
targetDir=$1
echo "TargetDir"$targetDir

sslCert=$2
sslKey=$3
sslCaCert=$4


echo "getting installation file .gz"
home_dir=$(pwd)
echo "homedir: "$home_dir
installation_path=$home_dir/install/nb

installation_file=$(find $installation_path -name *.tar.gz -printf "%f\n")
nb_foldername=$(tar -ztvf $installation_path/$installation_file | head -1 | awk '{print $NF}' | cut -d/ -f1)

echo $installation_path"/"$installation_file

echo "Extracting .tar.gz file from "$installation_path
tar -xzf $installation_path/*.tar.gz -C $gigapath

echo "Moving file from $installation_path/nb.conf To $targetDir/$nb_foldername/"
mv $installation_path/nb.conf $targetDir/$nb_foldername/

echo "copying ssl files to $targetDir/$nb_foldername/ssl"

crtFiles=$(ls $dbagigashareApplicativePath/ssl/$sslCert 2> /dev/null | wc -l)
echo "crtFiles:"$crtFiles
if [[ $crtFiles -gt 0 ]]
then
    echo "Copying cert file"
    cp $dbagigashareApplicativePath/ssl/$sslCert $targetDir/$nb_foldername/ssl/
fi
cacertFiles=$(ls $dbagigashareApplicativePath/ssl/$sslCaCert 2> /dev/null | wc -l)
echo "cacertFiles:"$cacertFiles
if [[  $cacertFiles -gt 0 ]]
then
    echo "Copying cacert file"
    cp $dbagigashareApplicativePath/ssl/$sslCaCert $targetDir/$nb_foldername/ssl/
fi
keyFiles=$(ls $dbagigashareApplicativePath/ssl/$sslKey 2> /dev/null | wc -l)
echo "keyFiles:"$keyFiles
if [[ $keyFiles -gt 0 ]]
then
    echo "Copying key file"
    cp $dbagigashareApplicativePath/ssl/$sslKey $targetDir/$nb_foldername/ssl/
fi