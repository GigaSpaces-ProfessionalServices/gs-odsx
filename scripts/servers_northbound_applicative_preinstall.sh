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

dbagigashareApplicativePath=$sourceInstallerDirectory'/nb/applicative'

echo "Moving file from $installation_path/nb.conf To $targetDir/$nb_foldername/"
cp $dbagigashareApplicativePath/nb.conf $targetDir/$nb_foldername/

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