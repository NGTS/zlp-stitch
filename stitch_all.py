#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import
import subprocess as sp
import argparse
from commonlog import setup_logging

logger = setup_logging('stitch-all')


def valid(x):
    return x % 2 == 0


def get_all_field_cameras():
    return xrange(10)


def get_available_field_cameras():
    return (f for f in get_all_field_cameras() if valid(f))


def main(args):
    for field_camera_combo in get_available_field_cameras():
        logger.info('Building {}'.format(field_camera_combo))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    main(parser.parse_args())
