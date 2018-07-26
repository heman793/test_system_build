# -*- coding: utf-8 -*-
from screenutils import Screen
from argparse import ArgumentParser


def parse_arguments():
    parser = ArgumentParser()

    parser.add_argument(
        "-s",
        "--screen_name",
        dest="screen_name",
        help='input screen name',
        default=''
    )

    parser.add_argument(
        "-c",
        "--command",
        dest="command",
        help='input your command',
        default='ls'
    )

    options = parser.parse_args()
    return options


def screen_manager(screen_name, command):
    print 'Enter screen_manager,screen_name:%s,command:%s.' % (screen_name, command)
    s = Screen(screen_name, True)
    s.enable_logs()
    s.send_commands(command)
    print next(s.logs)
    print 'Exit screen_manager,screen_name:%s.' % screen_name


if __name__ == '__main__':
    options = parse_arguments()
    screen_name = options.screen_name
    command = options.command
    screen_manager(screen_name, command)
