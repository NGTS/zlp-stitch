#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import
import subprocess as sp
import argparse
from commonlog import setup_logging
import os
import re
import joblib
from collections import defaultdict
from astropy.io import fits

logger = setup_logging('stitch-all')

regex = re.compile(r'2015\d{4}-(?P<field>.+)-(?P<camera_id>80\d)$')

CHOSEN_FIELDS = {'wasp19b', 'k2_3b', 'ng2000'}
CHOSEN_CAMERAS = {802, 805, 806}

memory = joblib.Memory(cachedir='.tmp')


@memory.cache
def photom_file_name(path):
    cmd = map(str, ['find', path, '-name', 'output.fits'])
    output = sp.check_output(cmd)
    return output.strip()


def has_detrended(root_path):
    photom_file = photom_file_name(root_path)
    try:
        with fits.open(photom_file) as infile:
            return 'casudet' in infile
    except IOError:
        logger.exception('Cannot open file %s', root_path)
        return False


def valid(path):
    if regex.search(path) and photom_file_name(path):
        logger.debug('photom file exists')
        if has_detrended(path):
            logger.debug('valid: %s', path)
            return True
        logger.debug('no detrended')
        return False
    else:
        logger.debug('invalid: %s', path)
        return False


def get_all_field_cameras():
    data_dir = os.path.join('/', 'ngts', 'pipedev', 'ParanalOutput',
                            'running-the-pipeline')
    cmd = map(str, ['find', data_dir, '-maxdepth', 1, '-type', 'd'])
    logger.debug('cmd: %s', cmd)
    for line in sp.check_output(cmd).split():
        path = line.strip()
        logger.debug('Available directory: %s', path)
        yield path


def get_available_field_cameras():
    return (f for f in get_all_field_cameras() if valid(f))


def summarise(mapping):
    logger.debug('Collected %s', mapping)
    for key in mapping:
        logger.info('%s => %d files', key, len(mapping[key]))


def main(args):
    if args.verbose:
        logger.setLevel('DEBUG')

    mapping = defaultdict(list)
    for path in get_available_field_cameras():
        logger.info('Building {}'.format(path))
        match = regex.search(path)
        field = match.group('field')
        camera_id = int(match.group('camera_id'))
        mapping[(field, camera_id)].append(path)

    summarise(mapping)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    main(parser.parse_args())
