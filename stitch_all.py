#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import
import subprocess as sp
import argparse
from commonlog import setup_logging
import os
import re

logger = setup_logging('stitch-all')

regex = re.compile(r'2015\d{4}-(?P<field>.+)-(?P<camera>80\d)$')

CHOSEN_FIELDS = {'wasp19b', 'k2_3b', 'ng2000'}
CHOSEN_CAMERAS = {802, 805, 806}


def valid(path):
    return regex.search(path)


def get_all_field_cameras():
    data_dir = os.path.join('/', 'ngts', 'pipedev', 'ParanalOutput',
                            'running-the-pipeline')
    cmd = map(str, ['find', data_dir, '-maxdepth', 1, '-type', 'd'])
    logger.debug('cmd: %s', cmd)
    for line in sp.check_output(cmd).split():
        yield line.strip()


def get_available_field_cameras():
    return (f for f in get_all_field_cameras() if valid(f))


def main(args):
    if args.verbose:
        logger.setLevel('DEBUG')
    for path in get_available_field_cameras():
        logger.info('Building {}'.format(path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    main(parser.parse_args())
