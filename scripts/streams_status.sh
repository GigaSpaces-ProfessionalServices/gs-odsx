echo "Getting CR8 status..."
#sudo -s
#su - dbsh
#echo "user"$2
#echo "pass"$3
password=$2
if [ "$password" == "x" ] ; then
  final=${password//[x]/''}
fi
sudo -u $1 -H sh -c "/home/dbsh/cr8/latest_cr8/utils/CR8_Stream_ctl.sh status $3"
#echo ""$2 | sudo -S sleep 1 && sudo su - $1
#cd /home/dbsh/cr8/latest_cr8/utils
#./CR8_ctl.sh status
#./CR8_Stream_ctl.sh status demo