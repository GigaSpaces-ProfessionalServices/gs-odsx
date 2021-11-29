echo "Pausing Stream..."
#pwd
#sudo -s
#pwd
#su - dbsh
#su - testuser -p password
password=$3
if [ "$password" == "x" ] ; then
  final=${password//[x]/''}
fi
sudo -u $2 -H sh -c "/home/dbsh/cr8/latest_cr8/utils/CR8_Stream_ctl.sh stop $4"
