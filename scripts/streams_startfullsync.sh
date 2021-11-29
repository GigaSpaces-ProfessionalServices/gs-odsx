echo "Starting full sync"

sudo -s
su - dbsh
cd /home/dbsh/cr8/latest_cr8/utils

echo ""$3 | sudo -S sleep 1 && sudo su - $2
#pwd
#cd /home/dbsh/cr8/latest_cr8/utils/
#pwd

./CR8_ctl.sh start

./CR8Sync.ctl start bll_db2_gs_segment
