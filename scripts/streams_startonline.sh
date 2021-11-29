echo "Starting Stream..."
#pwd
#sudo -s
#pwd
#su - dbsh
#su - testuser -p password
password=$2
if [ "$password" == "x" ] ; then
  final=${password//[x]/''}
fi
sudo -u $1 -H sh -c "/home/dbsh/cr8/latest_cr8/utils/CR8_Stream_ctl.sh start $3"
#whoami
#echo "param:"$3
#cd /home/dbsh/cr8/latest_cr8/utils/
#source ~/.bash_profile
#echo "StreamName:"$streamName
#pwd
#./CR8_ctl.sh start
#./CR8_Stream_ctl.sh start demo
