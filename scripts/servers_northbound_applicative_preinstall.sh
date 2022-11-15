echo "Starting pre Installation cofiguration."
echo "Extracting install.tar to "$targetDir
tar -xvf install.tar
targetDir=$1
sourceInstallerDirectory=$2
echo "TargetDir"$targetDir
echo "sourceInstallerDirectory:"$sourceInstallerDirectory
echo "getting installation file .gz"
home_dir=$(pwd)
echo "homedir: "$home_dir
installation_path=$sourceInstallerDirectory/nb/
installation_file=$(find $installation_path -name *.tar.gz -printf "%f\n")
echo $installation_path"/"$installation_file

echo "Extracting .tar.gz file from "$installation_path
tar -xzf $installation_path/*.tar.gz -C /dbagiga

dbagigashareApplicativePath=$sourceInstallerDirectory'/nb/applicative'

echo "Moving file from $installation_path/nb.conf.template To $targetDir/nb-infra/"
cp $dbagigashareApplicativePath/nb.conf.template $targetDir/nb-infra/

echo "copying ssl files to $targetDir/nb-infra/ssl"
pfxFiles=$(ls $$dbagigashareApplicativePath/ssl/*.pfx 2> /dev/null | wc -l)
echo "pemFiles:"$pfxFiles
if [[ $pfxFiles -gt 0 ]]
then
    echo "Copying .pfx file"
    cp $$dbagigashareApplicativePath/ssl/*.pfx $targetDir/nb-infra/ssl/
fi
crtFiles=$(ls $dbagigashareApplicativePath/ssl/*.crt 2> /dev/null | wc -l)
echo "crtFiles:"$crtFiles
if [[ $crtFiles -gt 0 ]]
then
    echo "Copying .crt file"
    cp $dbagigashareApplicativePath/ssl/*.crt $targetDir/nb-infra/ssl/
fi
pemFiles=$(ls $dbagigashareApplicativePath/ssl/*.pem 2> /dev/null | wc -l)
echo "pemFiles:"$pemFiles
if [[  $pemFiles -gt 0 ]]
then
    echo "Copying .pem file"
    cp $dbagigashareApplicativePath/ssl/*.pem $targetDir/nb-infra/ssl/
fi
keyFiles=$(ls $dbagigashareApplicativePath/ssl/*.key 2> /dev/null | wc -l)
echo "keyFiles:"$keyFiles
if [[ $keyFiles -gt 0 ]]
then
    echo "Copying .key file"
    cp $dbagigashareApplicativePath/ssl/*.key $targetDir/nb-infra/ssl/
fi