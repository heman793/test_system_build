# -*- coding: utf-8 -*-
from argparse import ArgumentParser


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument(
        "-d",
        "--date",
        dest="date",
        help='input filter date',
        default=''
    )
    options = parser.parse_args()
    return options