# s6.py
#!/usr/bin/python
import argparse
import os
import sys
from utils.ods_ssh import build_remote_bash_cmd


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

    for cmd in cmd_list:
        type = exe[cmd.split('.')[1]]
        if type == 'bash':
            # Bash scripts go through build_remote_bash_cmd so lib_app_config.sh
            # (read_property, validate_nonempty_paths, wait_for_user_bus) is in scope.
            full_cmd = build_remote_bash_cmd(host, user, cmd, '')
        else:
            # python/perl don't use the bash helpers — use plain SSH invocation.
            full_cmd = 'ssh ' + user + '@' + host + ' ' + type + ' < ' + cmd
        os.system(full_cmd)

if __name__ == '__main__':
    args = check_arg(sys.argv[1:])
    remote_run(args)