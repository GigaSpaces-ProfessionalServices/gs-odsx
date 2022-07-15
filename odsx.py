#!/usr/bin/env python3
#eval "$(register-python-argcomplete odsx.py)"

import getopt, sys
import csv
import os.path
import signal
from os import path
import  pyfiglet
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cleanup import signal_handler
from utils.ods_cluster_config import discoverHostConfig
###############################
# For autocomplete
import argparse as ap
import argcomplete
import os
###############################
from scripts.ods_help import helpUsage

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

#clearing screen on each option selection render new screen.
def screen_clear():
    # for mac and linux(here, os.name is 'posix')
    if os.name == 'posix':
        _ = os.system('clear')
    else:
        # for windows platfrom
        _ = os.system('cls')
#Displaying logo before options
def displayOdsLogo():
    logger.info("Displaying logo")
    #screen_clear()
    result = pyfiglet.figlet_format("ODSX")
    print(result)
#To display main menu and respected submenu based on option selected.
def displayMainMenu(menu,currentMenu):
    logger.info("displaying main menu")
    displayOdsLogo()
    #print("MENU ")
    #print("\n")
    #print('menu',menu)
    #print('currentMenu',currentMenu)
    defaultMenu = currentMenu
    findExit ='exit'
    scriptsFolder='scripts'
    #print('defMenu1',defaultMenu)
    if(menu == '' or menu == 'menu'):
        #print('a')
        defaultMenu ="menu"
    elif(menu.count(findExit)):

        #print('b')
        defaultMenuExit =menu.replace('exit','')
        if str(defaultMenu).__contains__('_'):
            defaultMenu = defaultMenu[:defaultMenu.rindex('_')]
        #print('defMenu',defaultMenu)
    elif(menu != 'menu'):
        #print('c')
        defaultMenu=defaultMenu+'_'+menu
    else:
        defaultMenu='menu'
    #Dsisplay Tree stucture
    print(defaultMenu.upper().replace('_',' -> '))
    print('\n')
    env = str(readValuefromAppConfig("app.setup.env"))
    if path.exists('csv/'+defaultMenu+'.csv'):
        with open('csv/'+defaultMenu+'.csv','r') as menuFile:
            reader = csv.reader(menuFile, delimiter=",")
            stringRow =""
            for row in reader:
                stringRow+= str(row)
            if env=='dr':  # FOR DR envirounment DI is not applicable
                stringRow = stringRow.replace(" 'DI',","")
            stringRow =stringRow.replace('[',' ').replace('\'','').replace(']','')
            splittedRow = stringRow.split(',')
            #print(splittedRow[0])
            elementNumber=1
            for column in splittedRow:
                if (column.strip() =='EXIT'  or column.strip() == 'ESC' ):
                    print('[99]',column)
                else:
                    print('['+str(elementNumber)+'] '+column)
                elementNumber+=1
            try:
                optionMainMenu = int(input("Enter your option: "))
                screen_clear()
            except ValueError:
                print("Invalid input.")
                displayMainMenu(defaultMenu[defaultMenu.rindex('_')+1:],defaultMenu)
            #print('optionMenu:::',optionMainMenu)
            #print('defMenu',defaultMenu)
            #print('currMenu',currentMenu)
            #for i in range(0,len(splittedRow)):
            #    print(i)
            if(optionMainMenu !=99 and optionMainMenu > len(splittedRow)-1 ):
                print("")
                #break
            else:
                selectedOption=""
                if(optionMainMenu == 99):
                    selectedOption="EXIT"
                else:
                    #print("splittedRow:",splittedRow[optionMainMenu])
                    selectedOption = splittedRow[optionMainMenu-1]
                    selectedOption = selectedOption.replace(' ','')
                #print('selected Option',selectedOption)
                #print('selected current',defaultMenu)
                while True:
                    if(optionMainMenu == 99):

                        if(defaultMenu =='menu' and selectedOption.lower().strip() == findExit):
                            quit()
                        elif(menu != 'menu'):
                            displayMainMenu(selectedOption.lower().strip(),defaultMenu)
                        else:
                            break
                    else:
                        displayMainMenu(selectedOption.lower().strip(),defaultMenu)
                    #optionMainMenu = int(input("Enter your option: "))
    else:
        scriptMenu = defaultMenu.replace('menu','odsx')
        menuItems = str(readValuefromAppConfig("app.security.menu"))
        if profile=='security':
            for menu in menuItems.split(','):
                #skip for retention manager
                menu = str(menu).strip()
                if not(defaultMenu.__contains__('retentionmanager')) and defaultMenu.__contains__(menu):
                    scriptMenu = defaultMenu.replace('menu','odsx_security')

        #print(scriptsFolder+'/'+scriptMenu+'.py')
        logger.info("Finding file to execute selected command: "+scriptsFolder+'/'+scriptMenu+'.py')
        menuDrivenFlag='m' # To differentiate between CLI and Menudriven Argument handling help section
        #print("scriptsFolder:"+scriptsFolder)
        #print("scriptMenu:"+str(scriptMenu))
        try:
            if(path.exists(scriptsFolder+'/'+scriptMenu+'.py')):
                logger.info("File "+scriptsFolder+'/'+scriptMenu+'.py'+' exist.')
                #print('File Exist.....')
                #print(scriptsFolder+'/'+scriptMenu+'.py')
                screen_clear()
                #print(scriptsFolder+'/'+scriptMenu+'.py')
                os.system('python3 '+scriptsFolder+'/'+scriptMenu+'.py '+menuDrivenFlag)
                defaultMenu = defaultMenu[:defaultMenu.rindex('_')]
                displayMainMenu(defaultMenu[defaultMenu.rindex('_')+1:], defaultMenu[:defaultMenu.rindex('_')])
            else:
                logger.error("File "+scriptsFolder+'/'+scriptMenu+'.py'+' does not exist.')
                verboseHandle.printConsoleInfo("===================TBD==================")
                #Removing last cmd from filename hence its not part of menu
                defaultMenu = defaultMenu[:defaultMenu.rindex('_')]
                #passing Submenu and cuurentPath
                displayMainMenu(defaultMenu[defaultMenu.rindex('_')+1:], defaultMenu[:defaultMenu.rindex('_')])
                quit()
        except Exception as e:
            #print('defMennnu',defaultMenu)
            #print('currMennn',currentMenu)
            #print('scriptMenuuu',scriptMenu)
            logger.error("Invalid Option or file does not exist. : "+scriptsFolder+'/'+scriptMenu+'.py')
            displayMainMenu('','menu')
#To find command in file
def findArgumentInFile(currentArg,initialFileName):
    #logger.info("findArgumentInFile-currentArg : "+currentArg+ " initialFileName :"+initialFileName)
    fileSuffix ='.csv'
    directory='csv'
    #print('initialFilename:',initialFileName)
    try:
        with open(os.path.join(directory, initialFileName+fileSuffix),'r') as menuFile:
            reader = csv.reader(menuFile, delimiter=",")
            stringRow =""
            for row in reader:
                stringRow+= str(row)
            stringRow =stringRow.replace('[',' ').replace('\'','').replace(']','')
            splittedRow = stringRow.split(',')
            for column in splittedRow:
                column = column.replace(' ','')
                if(currentArg.casefold().strip()==column.casefold().strip()):
                    return True
    except Exception as e:
        #print(e)
        ""

def main(**args):
    # Discover hosts to be install for stateless cluster config
    discoverHostConfig()
    #check if command line arguments passed to check execution of CLI or Menu driven
    if len(sys.argv) > 1 :
        cmd=''
        cmdlist = list(cmd)
        initialCmdList = cmdlist
        initialFileName='menu'
        initialMenu = 'menu'
        requiredSuffix='.py'
        requiredPrefix='odsx'
        scriptsFolder ='scripts'
        n = len(sys.argv)
        for i in range(1, n):
            cmdlist.append(sys.argv[i])
            '''
            if(sys.argv[1] == 'odsx'):
                #cmdlist.append(sys.argv[i].replace('--',''))    
            else:
                print('Invalid command : ',sys.argv[1])
                quit()
            '''
        #cmdlist.remove(requiredPrefix)
        #print(cmdlist)
        #MainMenu
        for cmd in cmdlist:
            if(findArgumentInFile(cmd.replace('--',''),initialFileName)):
                initialFileName=initialFileName+'_'+cmd.replace('--','')
                cmdlist.remove(cmd)
        #SubMenu
        for cmd in cmdlist:
            if(findArgumentInFile(cmd.replace('--',''),initialFileName)):
                initialFileName=initialFileName+'_'+cmd.replace('--','')
                cmdlist.remove(cmd)
        #CommandMenu
        for cmd in cmdlist:
            if(findArgumentInFile(cmd.replace('--',''),initialFileName)):
                initialFileName=initialFileName+'_'+cmd.replace('--','')
                cmdlist.remove(cmd)

        if cmdlist.__contains__("--help") or cmdlist.__contains__("-h"):
            helpUsage(initialFileName)
        else:
            initialFileName = initialFileName.replace(initialMenu,requiredPrefix)
            initialFileName = initialFileName+requiredSuffix
            #print('FinalFileName:'+initialFileName)
            #print('Remaining Command: ',cmdlist)
            args = str(cmdlist)
            args =args.replace('[','').replace("'","").replace("]",'').replace(',','').strip()
            menuItems = str(readValuefromAppConfig("app.security.menu"))
            if profile=='security':
                for menu in menuItems.split(','):
                    #skip for retention manager
                    menu = str(menu).strip()
                    if not(initialFileName.__contains__('retentionmanager')) and initialFileName.__contains__(menu):
                        initialFileName = initialFileName.replace('odsx','odsx_security')
            #print('python3 '+scriptsFolder+'/'+initialFileName+' '+args)
            try:
                if(path.exists(scriptsFolder+'/'+initialFileName)):
                    #print('python3 '+scriptsFolder+'/'+initialFileName+' '+args)
                    #print(scriptsFolder+'/'+scriptMenu+'.py')
                    os.system('python3 '+scriptsFolder+'/'+initialFileName+' '+args)
                else:
                    verboseHandle.printConsoleInfo("===================TBD==================")
                    logger.error('File not exist. : '+scriptsFolder+'/'+initialFileName)
            except Exception as e:
                print(e)
    else:
        displayMainMenu('menu','')

if __name__== "__main__":
  parser = ap.ArgumentParser()
  subparser = parser.add_subparsers()
  signal.signal(signal.SIGINT, signal_handler)
  profile=str(readValuefromAppConfig("app.setup.profile"))
  #print("profile="+profile)
  logger.info("Profile :"+str(profile))

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
  validators = subparser.add_parser("validators", help="Validators")
  spaces = subparser.add_parser("space", help="Space")
  streams = subparser.add_parser("streams", help="Streams")
  wangateway = subparser.add_parser("wangateway", help="Wan Gateway")

############
# Settings
############
  settingsSubparser = settings.add_subparsers()
  snapshot = settingsSubparser.add_parser("snapshot", help="Settings for the space")
  snapshot.add_argument('--list', dest="settings_snapshot_list", action="store_true")
  snapshot.add_argument('--retention', dest="settings_snapshot_retention", action="store_true")
  snapshot.add_argument('--location', dest="settings_snapshot_location", action="store_true")
  snapshot.add_argument('--edit', dest="settings_snapshot_edit", action="store_true")
  snapshot.add_argument('-v', '--verbose', help='verbose', action='store_true')

  # backupSubparser = settings.add_subparsers()
  backup = settingsSubparser.add_parser("backup", help="Backup")
  backup.add_argument('--list', dest="settings_backup_list", action="store_true")
  backup.add_argument('--destination', dest="settings_backup_destination", action="store_true")
  backup.add_argument('--restore', dest="settings_backup_restore", action="store_true")
  backup.add_argument('--retention', dest="settings_backup_retention", action="store_true")
  backup.add_argument('-v', '--verbose', help='verbose', action='store_true')

  # scriptSubparser = settings.add_subparsers()
  script = settingsSubparser.add_parser("script", help="Script")
  script.add_argument('--versions', dest="settings_script_versions", action="store_true")
  script.add_argument('--upgrade', dest="settings_script_upgrade", action="store_true")
  script.add_argument('--rollback', dest="settings_script_rollback", action="store_true")
  script.add_argument('-v', '--verbose', help='verbose', action='store_true')

##########################################
# Servers - Space,Manager,CDC,NorthBound
##########################################
  serversSubparser = servers.add_subparsers()
  space = serversSubparser.add_parser("space", help="Space")
  #streams = serversSubparser.add_parser("streams", help="Streams")
  manager = serversSubparser.add_parser("manager", help="Manager")
  cdc = serversSubparser.add_parser("cdc", help="CDC")
  northbound = serversSubparser.add_parser("northbound", help="NorthBound")
 
 ##################################################
 # Servers - Space - Restore,Install,Stop,Remove
 ##################################################
  space.add_argument('--restore', dest="servers_space_restore", action="store_true")
  space.add_argument('--install', dest="servers_space_install", action="store_true")
  space.add_argument('--list', dest="servers_space_list", action="store_true")
  space.add_argument('--stop', dest="servers_space_stop", action="store_true")
  space.add_argument('--start', dest="servers_space_start", action="store_true")
  space.add_argument('--remove', dest="servers_space_remove", action="store_true")
  space.add_argument('-v', '--verbose', help='verbose', action='store_true')

 ##################################################
 # Servers - Manager - Restore,Install,Stop,Remove
 ##################################################
  manager.add_argument('--restore', dest="servers_manager_restore", action="store_true")
  manager.add_argument('--install', dest="servers_manager_install", action="store_true")
  manager.add_argument('--start', dest="servers_manager_start", action="store_true")
  manager.add_argument('--stop', dest="servers_manager_stop", action="store_true")
  manager.add_argument('--remove', dest="servers_manager_remove", action="store_true")
  manager.add_argument('--list', dest="servers_manager_list", action="store_true")
  manager.add_argument('-v', '--verbose', help='verbose', action='store_true')

  ##################################################
  # Servers - CDC - Restore,Install,Stop,Remove
  ##################################################
  cdc.add_argument('--restore', dest="servers_cdc_restore", action="store_true")
  cdc.add_argument('--install', dest="servers_cdc_install", action="store_true")
  cdc.add_argument('--start', dest="servers_cdc_start", action="store_true")
  cdc.add_argument('--stop', dest="servers_cdc_stop", action="store_true")
  cdc.add_argument('--remove', dest="servers_cdc_remove", action="store_true")
  cdc.add_argument('--list', dest="servers_cdc_list", action="store_true")
  cdc.add_argument('-v', '--verbose', help='verbose', action='store_true')

  ##################################################
  # Servers - CDC - Restore,Install,Stop,Remove
  ##################################################
  northbound.add_argument('--restore', dest="servers_northbound_restore", action="store_true")
  northbound.add_argument('--install', dest="servers_northbound_install", action="store_true")
  northbound.add_argument('--start', dest="servers_northbound_start", action="store_true")
  northbound.add_argument('--stop', dest="servers_northbound_stop", action="store_true")
  northbound.add_argument('--remove', dest="servers_northbound_remove", action="store_true")
  northbound.add_argument('--list', dest="servers_northbound_list", action="store_true")
  northbound.add_argument('-v', '--verbose', help='verbose', action='store_true')


  ##################################################
  # Streams - List,Show,Config,StartFullsync,Start online,Pause online,Resume online
  ##################################################
  streams.add_argument('--list', dest="streams_list", action="store_true")
  streams.add_argument('--show', dest="streams_show", action="store_true")
  streams.add_argument('--config', dest="streams_config", action="store_true")
  streams.add_argument('--startfullsync', dest="streams_startfullsync", action="store_true")
  streams.add_argument('--startonline', dest="streams_startonline", action="store_true")
  streams.add_argument('--resumeonline', dest="streams_resumeonline", action="store_true")
  streams.add_argument('--remove', dest="streams_remove", action="store_true")
  streams.add_argument('-v', '--verbose', help='verbose', action='store_true')

  ##################################################
  # Streams - List,Show,Config,StartFullsync,Start online,Pause online,Resume online
  ##################################################
  spaces.add_argument('--start', dest="space_start", action="store_true")
  spaces.add_argument('--stop', dest="space_stop", action="store_true")
  spaces.add_argument('-v', '--verbose', help='verbose', action='store_true')

  ##################################################
  # Streams - List,Show,Config,StartFullsync,Start online,Pause online,Resume online
  ##################################################
  wangateway.add_argument('--list', dest="wangateway_list", action="store_true")
  wangateway.add_argument('--show', dest="wangateway_show", action="store_true")
  wangateway.add_argument('--control', dest="wangateway_control", action="store_true")
  wangateway.add_argument('-v', '--verbose', help='verbose', action='store_true')

  argcomplete.autocomplete(parser)
  #args = parser.parse_args()
  args= sys.argv[1:]
  main()
