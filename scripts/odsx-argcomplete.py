#!/usr/bin/env python3
#eval "$(register-python-argcomplete odsx-argcomplete.py)"

import argparse as ap
import argcomplete
import os

def main(**args):
  for arg in args:
    if args.get(arg) == True:
      os.system("python3 odsx_" + arg + ".py")
      #print(arg)
            
  #print(args)
  pass

if __name__ == '__main__':
  parser = ap.ArgumentParser()
  subparser = parser.add_subparsers()

##############
# Main Menu
##############
  settings = subparser.add_parser("settings", help="Settings for the space")
  servers = subparser.add_parser("servers", help="Servers for the space")
  cdc = subparser.add_parser("cdc", help="CDC")
  northbound = subparser.add_parser("northbound", help="NorthBound")
  security = subparser.add_parser("security", help="Security")
  logs = subparser.add_parser("logs", help="Logs")
  object = subparser.add_parser("object", help="Object")
  velidators = subparser.add_parser("velidators", help="Velidators")

############
# Settings
############
  settingsSubparser = settings.add_subparsers()
  snapshot = settingsSubparser.add_parser("snapshot", help="Settings for the space")
  snapshot.add_argument('--list', dest="settings_snapshot_list", action="store_true")
  snapshot.add_argument('--retention', dest="settings_snapshot_retention", action="store_true")
  snapshot.add_argument('--location', dest="settings_snapshot_location", action="store_true")
  snapshot.add_argument('--edit', dest="settings_snapshot_edit", action="store_true")

  # backupSubparser = settings.add_subparsers()
  backup = settingsSubparser.add_parser("backup", help="Backup")
  backup.add_argument('--list', dest="settings_backup_list", action="store_true")
  backup.add_argument('--destination', dest="settings_backup_destination", action="store_true")
  backup.add_argument('--restore', dest="settings_backup_restore", action="store_true")
  backup.add_argument('--retention', dest="settings_backup_retention", action="store_true")

  # scriptSubparser = settings.add_subparsers()
  script = settingsSubparser.add_parser("script", help="Script")
  script.add_argument('--versions', dest="settings_script_versions", action="store_true")
  script.add_argument('--upgrade', dest="settings_script_upgrade", action="store_true")
  script.add_argument('--rollback', dest="settings_script_rollback", action="store_true")

##########################################
# Servers - Space,Manager,CDC,NorthBound
##########################################
  serversSubparser = servers.add_subparsers()
  space = serversSubparser.add_parser("space", help="Space")
  manager = serversSubparser.add_parser("manager", help="Manager")
  cdc = serversSubparser.add_parser("cdc", help="CDC")
  northbound = serversSubparser.add_parser("northbound", help="NorthBound")
 
 ##################################################
 # Servers - Space - Restore,Install,Stop,Remove
 ##################################################
  space.add_argument('--restore', dest="servers_space_restore", action="store_true")
  space.add_argument('--install', dest="servers_space_install", action="store_true")
  space.add_argument('--stop', dest="servers_space_stop", action="store_true")
  space.add_argument('--remove', dest="servers_space_remove", action="store_true")

 ##################################################
 # Servers - Manager - Restore,Install,Stop,Remove
 ##################################################
  manager.add_argument('--restore', dest="servers_manager_restore", action="store_true")
  manager.add_argument('--install', dest="servers_manager_install", action="store_true")
  manager.add_argument('--stop', dest="servers_manager_stop", action="store_true")
  manager.add_argument('--remove', dest="servers_manager_remove", action="store_true")

argcomplete.autocomplete(parser)
args = parser.parse_args()
main(**vars(args))
