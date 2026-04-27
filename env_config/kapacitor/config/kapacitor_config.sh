#!/bin/bash

function edit_toml() {
    # change tables / vaules in TOML (configuration) files
    element=$1      # the element to target
    table_name=$2   # the table name to target
    if [[ $element == "table" ]]; then
        # enable or disable a toml table
        [[ $# -ne 4 ]] && (echo "error: missing parameters!" ; return)
        action=$3          # operation: enable | disable
        file=$4         # the TOML file
        case $action in
            "enable") sed -i "/\[${table_name}\]/s/#/ /g" $file ;;
            "disable") sed -i "/\[${table_name}\]/s/ /#/" $file ;;
        esac
    elif [[ $element == "value" ]]; then
        # change the value of a key
        [[ $# -ne 5 ]] && (echo "error: missing parameters!" ; return)
        key=$3          # the key to change
        value=$4        # the new value to set
        file=$5         # the TOML file
        sed -i "/^\[$table_name\]/,/^[[]/ s/\($key =\).*/\1 $value/" $file
    else
        echo "Error: bad parameter!"
    fi
}

KAPACITOR_CONF="/etc/kapacitor/kapacitor.conf"

# save default kapacitor.conf
[[ ! -f "${KAPACITOR_CONF}.default" ]] && cp "${KAPACITOR_CONF}" "${KAPACITOR_CONF}.default"

# set kapacitor url
sed -i '/KAPACITOR_URL/d' /root/.bashrc
echo -e "export KAPACITOR_URL=http://$(hostname -I | awk '{print $1}'):9992\n" >> /root/.bashrc

source /root/.bashrc

# set http parameters
edit_toml "value" "http" "bind-address" ":9992" "$KAPACITOR_CONF"
edit_toml "value" "http" "log-enabled" "false" "$KAPACITOR_CONF"

# set smtp parameters
edit_toml "value" "smtp" "enabled" "true" "$KAPACITOR_CONF"
edit_toml "value" "smtp" "global" "true" "$KAPACITOR_CONF"
edit_toml "value" "smtp" "from" "kapacitor-alerts@tau.ac.il" "$KAPACITOR_CONF"
edit_toml "value" "smtp" "to" '["tau-alerts@gigaspaces.com"]' "$KAPACITOR_CONF"
edit_toml "value" "smtp" "state-changes-only" "true" "$KAPACITOR_CONF"

# # setup shob alerts file
# alerts_log="/gigalogs/shob_alerts.log"
# touch $alerts_log
# chown kapacitor:kapacitor $alerts_log

# set endpoint parameters according to environment
# cat >> $KAPACITOR_CONF << EOL
# [[httppost]]
#     endpoint = "debug"
#     url = "http://localhost:4242"
#     alert-template-file = "/etc/kapacitor/templates/debug.json"

# [[httppost]]
#     endpoint = "common-alert"
#     url = "https://servicenow-preprod-itom/api/global/em/jsonv2"
#     headers = { Accept = "application/json" , Content-Type = "application/json" }
#     basic-auth = { username = "", password = "" }
#     alert-template-file = "/etc/kapacitor/templates/common-alert.json"

# [[httppost]]
#     endpoint = "nginx-load-raw"
#     url = "https://servicenow-preprod-itom/api/global/em/jsonv2"
#     headers = { Accept = "application/json" , Content-Type = "application/json" }
#     basic-auth = { username = "", password = "" }
#     row-template-file = "/etc/kapacitor/templates/nginx-load-raw.json"

# EOL

exit
