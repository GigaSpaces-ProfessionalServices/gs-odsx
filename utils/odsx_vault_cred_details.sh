#!/bin/bash
source ~/.bashrc
export ENV_CONFIG=$ENV_CONFIG
# Load shared read_property helper.
source "$(dirname "$0")/../scripts/lib_app_config.sh"
passProperty=$(read_property app.manager.security.password.vault)
dblocation=$(read_property app.vault.db.location)
vaultJar=$(read_property app.vault.jar.location)
export VAULT_MANAGER_PASS=$(java -Dapp.db.path=$dblocation -jar $vaultJar --get $passProperty)
echo $VAULT_MANAGER_PASS