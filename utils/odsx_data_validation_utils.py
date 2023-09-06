#!/usr/bin/env python3
import platform
import os
import socket, platform

def getPort(dataSource):
    if (dataSource == 'gigaspaces'):
        return '4174'

    if (dataSource == 'mysql'):
        return '3306'

    if (dataSource == 'db2'):
        return '446'

    if (dataSource == 'ms-sql'):
        return '1433'

    if (dataSource == 'oracle'):
        return '1521'