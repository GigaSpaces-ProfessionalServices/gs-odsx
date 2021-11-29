#!/usr/bin/env python3

import pandas as pd
from tabulate import tabulate
from colorama import Fore

# Below are all the styles that you can use:
# “plain”
# “simple”
# “github”
# “grid”
# “fancy_grid”
# “pipe”
# “orgtbl”
# “jira”
# “presto”
# “pretty”
# “psql”
# “rst”
# “mediawiki”
# “moinmoin”
# “youtrack”
# “html”
# “latex”
# “latex_raw”
# “latex_booktabs”
# “textile”

def printTabular(rowIndex, headers, data):
    if rowIndex == None:
        rowIndex = [""]*len(data)
    df = pd.DataFrame(data, rowIndex, headers)
    print(tabulate(df, showindex=False, headers=df.columns, tablefmt='psql',))

def printTabularGrid(rowIndex, headers, data):
    if rowIndex == None:
        rowIndex = [""]*len(data)
    df = pd.DataFrame(data, rowIndex, headers)
    print(tabulate(df, showindex=False, headers=df.columns, tablefmt='grid',))

def printTabularGridWrap(rowIndex, headers, data):
    if rowIndex == None:
        rowIndex = [""]*len(data)
    df = pd.DataFrame(data, rowIndex, headers)
    df[Fore.YELLOW+"Sr No."+Fore.RESET] = df[Fore.YELLOW+"Sr No."+Fore.RESET].str.wrap(70)
    df[ Fore.YELLOW+"ID"+Fore.RESET] = df[ Fore.YELLOW+"ID"+Fore.RESET].str.wrap(70)
    df[ Fore.YELLOW+"containerId"+Fore.RESET] = df[ Fore.YELLOW+"containerId"+Fore.RESET].str.wrap(70)
    df[ Fore.YELLOW+"mode"+Fore.RESET] = df[ Fore.YELLOW+"mode"+Fore.RESET].str.wrap(70)
    df[ Fore.YELLOW+"Status"+Fore.RESET] = df[ Fore.YELLOW+"Status"+Fore.RESET].str.wrap(70)
    df[ Fore.YELLOW+"Description"+Fore.RESET] = df[ Fore.YELLOW+"Description"+Fore.RESET].str.wrap(70)
    print(tabulate(df, showindex=False, headers=df.columns, tablefmt='grid',))

def printTabularStream(rowIndex, headers, data):
    if rowIndex == None:
        rowIndex = [""]*len(data)
    df = pd.DataFrame(data, rowIndex, headers)
    df[Fore.YELLOW+"ID"+Fore.RESET] = df[Fore.YELLOW+"ID"+Fore.RESET].str.wrap(20)
    df[Fore.YELLOW+"Name"+Fore.RESET] = df[Fore.YELLOW+"Name"+Fore.RESET].str.wrap(18)
    df[Fore.YELLOW+"Status"+Fore.RESET] = df[Fore.YELLOW+"Status"+Fore.RESET].str.wrap(18)
    df[Fore.YELLOW+"StreamType"+Fore.RESET] = df[Fore.YELLOW+"StreamType"+Fore.RESET].str.wrap(13)
    df[Fore.YELLOW+"Description"+Fore.RESET] = df[Fore.YELLOW+"Description"+Fore.RESET].str.wrap(20)
    df[Fore.YELLOW+"CreationDate"+Fore.RESET] = df[Fore.YELLOW+"CreationDate"+Fore.RESET].str.wrap(15)
    df[Fore.YELLOW+"ServerIP"+Fore.RESET] = df[Fore.YELLOW+"ServerIP"+Fore.RESET].str.wrap(30)
    df[Fore.YELLOW+"ServerJsonConfigPath"+Fore.RESET] = df[Fore.YELLOW+"ServerJsonConfigPath"+Fore.RESET].str.wrap(28)
    print(tabulate(df, showindex=False, headers=df.columns, tablefmt='grid',))

if __name__=="__main__":
    data = [[1, 'Liquid', 24, 12],
    [2, 'Virtus.pro', 19, 14],
    [3, 'PSG.LGD', 15, 19],
    [4,'Team Secret', 10, 20],
    [5,'This will be a real big data goes beyond format', 10000000000, 2000000000000000],
    [6,'Team Secret', 10, 20],
]

    headers = ["Pos", "Team", "Win", "Lose"]

    printTabular(None, headers, data)
