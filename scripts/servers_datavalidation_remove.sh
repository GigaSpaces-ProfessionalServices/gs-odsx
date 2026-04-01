# Set XDG_RUNTIME_DIR for systemctl --user over SSH
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

source setenv.sh

systemctl --user stop odsxdatavalidation.service
sleep 2

#yum -y remove java*
#yum -y remove jdk*

rm -rf /home/gsods/install/data-validation /giga/bin/st*_data_validation.sh $HOME/.config/systemd/user/odsxdatavalidation.service
