# s6.py
#!/usr/bin/python
import argparse
import os
import sys


def check_arg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('-h', '--host',
                        help='host ip',
                        required='True',
                        default='localhost')
    parser.add_argument('-u', '--user',
                        help='user name',
                        default='root')

    return parser.parse_args(args)

def remote_run(arguments):
    host = arguments.host
    user = arguments.user

    cmd_list = []
    with open('../csv/commands.txt', 'r') as f:
        for c in f:
            cmd_list.append(c.replace('\n','').replace('\r','').rstrip())

    exe = {'py':'python', 'sh':'bash', 'pl':'perl'}

    ssh = ''.join(['ssh ', user, '@',  host, ' '])
    for cmd in cmd_list:
        type = exe[cmd.split('.')[1]]
        cmd = ssh + type + ' < ' + cmd #+ '>> mylog.txt 2>&1'
        os.system(cmd)

if __name__ == '__main__':
    args = check_arg(sys.argv[1:])
    remote_run(args)