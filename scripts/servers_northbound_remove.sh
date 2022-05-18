echo "Removing north bound started..."
source ~/.bashrc
echo "NB"$NB_HOME
pwd
echo $1 "====" $2
#source setenv.sh
cd $NB_HOME
pwd
./install_nb_infra.sh $2
cd
#source setenv.sh
sed -i '/export NB_HOME/d' .bashrc
rm -rf $NB_HOME install install.tar dbagigashare
echo "Removing north bound -Done!"