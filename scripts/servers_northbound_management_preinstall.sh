echo "Starting pre Installation configuration."
echo "Extracting install.tar to "$targetDir
tar -xvf install.tar
targetDir=$1
sourceInstallerDirectory=$2
sourceInstallerDirectoryTar=$3

sslCert=$4
sslKey=$5
sslCaCert=$6

echo "TargetDir"$targetDir
echo "sourceInstallerDirectory:"$sourceInstallerDirectory
echo "getting installation file .gz"
home_dir=$(pwd)
echo "homedir: "$home_dir
installation_path=$sourceInstallerDirectory/nb/
installation_path_tar=$sourceInstallerDirectoryTar/nb
installation_file=$(find $installation_path_tar -name *.tar.gz -printf "%f\n")
nb_foldername=$(tar -ztvf $installation_path_tar/$installation_file | head -1 | awk '{print $NF}' | cut -d/ -f1)

echo $installation_path_tar"/"$installation_file

echo "Extracting .tar.gz file from "$installation_path_tar
tar -xzf $installation_path_tar/*.tar.gz -C /dbagiga

dbagigashareManagementPath=$sourceInstallerDirectory'/nb/management'

echo "Moving file from $installation_path/nb.conf To $targetDir/$nb_foldername/"
cp $dbagigashareManagementPath/nb.conf $targetDir/$nb_foldername/

echo "copying ssl files to $targetDir/$nb_foldername/ssl"

crtFiles=$(ls $dbagigashareManagementPath/ssl/$sslCert 2> /dev/null | wc -l)
echo "crtFiles:"$crtFiles
if [[ $crtFiles -gt 0 ]]
then
    echo "Copying cert file"
    cp $dbagigashareManagementPath/ssl/$sslCert $targetDir/$nb_foldername/ssl/
else
    echo "Copying cert file from pkg"
    cp $targetDir/$nb_foldername/ssl/management/$sslCert $targetDir/$nb_foldername/ssl/
fi
cacertFiles=$(ls $dbagigashareManagementPath/ssl/$sslCaCert 2> /dev/null | wc -l)
echo "cacertFiles:"$cacertFiles
if [[  $cacertFiles -gt 0 ]]
then
    echo "Copying cacert file"
    cp $dbagigashareManagementPath/ssl/$sslCaCert $targetDir/$nb_foldername/ssl/
else
    echo "Copying cacert file from pkg"
    cp $targetDir/$nb_foldername/ssl/management/$sslCaCert $targetDir/$nb_foldername/ssl/
fi
keyFiles=$(ls $dbagigashareManagementPath/ssl/$sslKey 2> /dev/null | wc -l)
echo "keyFiles:"$keyFiles
if [[ $keyFiles -gt 0 ]]
then
    echo "Copying key file"
    cp $dbagigashareManagementPath/ssl/$sslKey $targetDir/$nb_foldername/ssl/
else
    echo "Copying key file from pkg"
    cp $targetDir/$nb_foldername/ssl/management/$sslKey $targetDir/$nb_foldername/ssl/
fi