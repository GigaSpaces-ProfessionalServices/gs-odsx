#!/usr/bin/env python3
import os.path
from utils.ods_discovery import discoveryManager,discoverySpace,discoverStreams, discoverCDC
from scripts.logManager import LogManager

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

def discover():
    answer = input("Do you want to discover CDC Server? (yes(y)/no(n)/cancel(c): ")
    logger.info("Selected answer cdc:"+str(answer))
    if(answer.lower() == "y"):
        discoverCDC()
    elif(answer.lower() == "c"):
        return

    answer = input("Do you want to discover Northbound Server? (yes(y)/no(n)/cancel(c): ")
    logger.info("Selected answer nb :"+str(answer))
    if(answer.lower() == "y"):
        ip = input("Please, enter IP or host of Northbound server:")
        discoverNB(ip)
    elif(answer.lower() == "c"):
        return

    answer = input("Do you want to discover WAN Gateway? (yes(y)/no(n)/cancel(c): ")
    logger.info("Selected answer wan:"+str(answer))
    if(answer.lower() == "y"):
        ip = input("Please, enter IP or host of WAN Gateway:")
        discoverWanGateway(ip)
    elif(answer.lower() == "c"):
        return

    answer = input("Do you want to discover Streams? (yes(y)/no(n)/cancel(c): ")
    logger.info("Selected answer streams:"+str(answer))
    if(answer.lower() == "y"):
        #ip = input("Please, enter IP or host of Streams:")
        #discoverStreams(ip)
        discoverStreams()
    elif(answer.lower() == "c"):
        return

    answer = input("Do you want to discover Manager? (yes(y)/no(n)/cancel(c): ")
    logger.info("Selected answer : manager"+str(answer))
    if(answer.lower() == "y"):
        discoveryManager()
    elif(answer.lower() == "c"):
        return

    answer = input("Do you want to discover Space? (yes(y)/no(n)/cancel(c): ")
    logger.info("Selected answer space:"+str(answer))
    if(answer.lower() == "y"):
        ip = input("Please, enter IP or host of Space:")
        discoverySpace(ip)
    elif(answer.lower() == "c"):
        return


def discoverNB(ip):
    print("Discovering Northbound at " + ip)

def discoverWanGateway(ip):
    print("Discovering WAN Gateway at " + ip)

if __name__=="__main__":
    discover()
