# -*- coding: utf-8 -*-

"""Console script for msg_parser."""
import os.path
import sys
from argparse import Action
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from argparse import FileType
from pprint import pprint

from modules.app_email.lib.msg_parser import MsOxMessage


class FullPaths(Action):
    """Expand user- and relative-paths"""

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, os.path.abspath(os.path.expanduser(values)))


def is_dir(dir_name):
    """Checks if a path is an actual directory"""
    if not os.path.isdir(dir_name):
        msg = "{0} is not a directory".format(dir_name)
        raise ArgumentTypeError(msg)
    else:
        return dir_name


def create_parser(args):
    parser = ArgumentParser(description="Microsoft Message Parser")
    parser.add_argument(
        "-i",
        "--input",
        dest="input_file",
        required=True,
        help="msg file path",
        metavar="FILE",
        type=FileType(),
    )
    parser.add_argument(
        "-j",
        "--json",
        help="output parsed msg as json to console",
        dest="json_output",
        action="store_true",
    )
    parser.add_argument(
        "-e",
        "--eml",
        help="provide email file path to save as eml file.",
        dest="eml_file",
        action=FullPaths,
        type=is_dir,
    )
    return parser.parse_args(args)


def main():
    args = create_parser(sys.argv[1:])

    input_file = args.input_file

    json_output = args.json_output

    if json_output:
        ms_msg = MsOxMessage(input_file)
        pprint(ms_msg.get_message_as_json())

    eml_file = args.eml_file

    if eml_file:
        ms_msg = MsOxMessage(input_file)
        ms_msg.save_email_file(eml_file)


if __name__ == "__main__":
    sys.exit(main())
