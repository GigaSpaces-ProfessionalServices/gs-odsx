echo "Installation starting..."
echo $1 "====" $3
gigalogs=$2

cd $1
logDir="$gigalogs/nginx"
if [ ! -d "/$logDir" ]; then
   mkdir -p /$logDir
   chmod 777 /$logDir
fi
pwd
./install_nb_infra.sh $3
echo "Setting NB_HOME"
cd
path="export NB_HOME="$1
sed -i '/export NB_HOME/d' .bashrc
#echo "">>setenv.sh
echo "$path">>.bashrc

setsebool -P httpd_read_user_content 1
chcon -Rt httpd_sys_rw_content_t $gigalogs/nginx/

echo "Setting NB_HOME -Done!"
