echo "Validating Stream..."

password=$2
if [ "$password" == "x" ] ; then
  final=${password//[x]/''}
fi
#echo ""$final | sudo -S sleep 1 && sudo su - $1 -c 'echo "$0" "$@"' -- "$3"
sudo -u $1 -H sh -c "/home/dbsh/cr8/latest_cr8/utils/updateCMDB.sh $4"
