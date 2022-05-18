echo "Starting pre Installation cofiguration."
echo "Extracting install.tar to "$targetDir
tar -xvf install.tar
targetDir=$1
echo "TargetDir"$targetDir

echo "getting installation file .gz"
home_dir=$(pwd)
echo "homedir: "$home_dir
installation_path=$home_dir/dbagigashare/current/NB
installation_file=$(find $installation_path -name *.tar.gz -printf "%f\n")
echo $installation_path"/"$installation_file

echo "Extracting .tar.gz file from "$installation_path
tar -xzf $installation_path/*.tar.gz -C /dbagiga

echo "Moving file from $installation_path/nb.conf To $targetDir/nb-infra/"
mv $installation_path/MANAGEMENT/nb.conf $targetDir/

echo "copying ssl files to $targetDir/nb-infra/ssl"
pfxFiles=$(ls install/nb/ssl/*.pfx 2> /dev/null | wc -l)
echo "pemFiles:"$pfxFiles
if [[ $pfxFiles -gt 0 ]]
then
    echo "Copying .pfx file"
    cp $installation_path/MANAGEMENT/SSL/*.pfx $targetDir/nb-infra/ssl/
fi
crtFiles=$(ls $installation_path/MANAGEMENT/SSL/*.crt 2> /dev/null | wc -l)
echo "crtFiles:"$crtFiles
if [[ $crtFiles -gt 0 ]]
then
    echo "Copying .crt file"
    cp $installation_path/MANAGEMENT/SSL/*.crt $targetDir/nb-infra/ssl/
fi
pemFiles=$(ls $installation_path/MANAGEMENT/SSL/*.pem 2> /dev/null | wc -l)
echo "pemFiles:"$pemFiles
if [[  $pemFiles -gt 0 ]]
then
    echo "Copying .pem file"
    cp $installation_path/MANAGEMENT/SSL/*.pem $targetDir/nb-infra/ssl/
fi
keyFiles=$(ls $installation_path/MANAGEMENT/SSL/*.key 2> /dev/null | wc -l)
echo "keyFiles:"$keyFiles
if [[ $keyFiles -gt 0 ]]
then
    echo "Copying .key file"
    cp $installation_path/MANAGEMENT/SSL/*.key $targetDir/nb-infra/ssl/
fi