#!/bin/bash
passProperty=$(awk -F= '/app.manager.security.password.vault=/ {print $2}' ${ENV_CONFIG}/app.config)
dblocation=$(awk -F= '/app.vault.db.location=/ {print $2}' ${ENV_CONFIG}/app.config)
vaultJar=$(awk -F= '/app.vault.jar.location=/ {print $2}' ${ENV_CONFIG}/app.config)
export VAULT_MANAGER_PASS=$(java -Dapp.db.path=$dblocation -jar $vaultJar --get $passProperty)
echo $VAULT_MANAGER_PASS