#!/usr/bin/python3

import tarfile
import os.path
import datetime
#import logManager

def makeTarfile(outputFilename, sourceDir):
    with tarfile.open(outputFilename, "w:gz") as tar:
        tar.add(sourceDir, arcname=os.path.basename(
            sourceDir), filter=excludeFunction)


def excludeFunction(filename, excludeName="/archive/"):
    if excludeName in filename.name:
        return None
    return filename


if __name__ == '__main__':
    currentDate = datetime.date.today()
    dateStr = currentDate.strftime("%Y%m%d")
    tarFileName = "../archive/" + os.path.basename(os.path.abspath("..") + dateStr + ".tar.gz")

    makeTarfile(tarFileName,  os.path.abspath(".."))

    #logManager = logManager.LogManager(os.path.basename(__file__))
    #logManager.printConsoleInfo("Archive created at " + tarFileName)
    print("Archive created at " + tarFileName)
