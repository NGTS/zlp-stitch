#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import
import subprocess as sp
import argparse
from commonlog import setup_logging
import os
import re
from collections import defaultdict
from astropy.io import fits
import sys
import joblib
import json

logger = setup_logging('stitch-all')

regex = re.compile(r'2015\d{4}-(?P<field>.+)-(?P<camera_id>80\d)$')

CHOSEN_FIELDS = {'wasp19b', 'k2_3b', 'ng2000'}
CHOSEN_CAMERAS = {802, 805, 806}

LOGDIR = os.environ.get('LOGDIR', os.path.expanduser('~/var/log'))

memory = joblib.Memory(cachedir='.tmp')


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


def build_zlp_stitch_command(field, camera_id, files):
    binary_path = os.path.realpath(os.path.join(os.path.dirname(__file__), 'zlp-stitch'))
    output_path = os.path.join('/', 'ngts', 'pipedev', 'ParanalOutput', 'per_field')
    output_stub = '{field}-{camera_id}.fits'.format(field=field, camera_id=camera_id)
    output_path = os.path.join(output_path, output_stub)
    cmd = [binary_path, '-o', output_path]
    cmd.extend(files)
    logger.debug('cmd: %s', ' '.join(cmd))
    return map(str, cmd)


def build_qsub_command(field, camera_id):
    name = 'stitch-{field}-{camera_id}'.format(field=field, camera_id=camera_id)
    log_name = os.path.join(LOGDIR, '{}.log'.format(name))
    return map(str, ['/usr/local/sge/bin/lx-amd64/qsub', '-N', name, '-j', 'yes', '-o',
                     log_name, '-b', 'y', '-pe', 'parallel', 1])


def spawn_job(field, camera_id, files):
    zlp_stitch_command = build_zlp_stitch_command(field=field,
                                                  camera_id=camera_id,
                                                  files=files)

    qsub_command_string = build_qsub_command(field, camera_id)
    command_string = qsub_command_string + zlp_stitch_command
    qsub_env = {'SGE_ROOT': '/usr/local/sge'}
    sp.check_call(command_string, env=qsub_env)


class Mapping(object):

    join_char = '@'

    def __init__(self):
        self._data = defaultdict(list)

    def append(self, key, value):
        self._data[key].append(value)

    def summarise(self):
        logger.debug('Collected %s', self._data)
        for key in self._data:
            logger.info('%s => %d files', key, len(self._data[key]))

    def to_file(self, filename):
        out = {}
        for key in self._data:
            key_str = self.join_char.join(map(str, key))
            out[key_str] = self._data[key]

        with open(filename, 'w') as outfile:
            json.dump(out, outfile, indent=2)

    @classmethod
    def from_file(cls, filename):
        data = {}

        with open(filename) as infile:
            raw = json.load(infile)

        for key in raw:
            field, camera_id = key.split(cls.join_char)
            camera_id = int(camera_id)
            data[(field, camera_id)] = raw[key]

        self = cls()
        self._data.update(data)
        return self

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, key):
        return self._data[key]


def build_field_camera_mapping():
    mapping = Mapping()
    for path in get_available_field_cameras():
        logger.info('Building {}'.format(path))
        match = regex.search(path)
        field = match.group('field')
        camera_id = int(match.group('camera_id'))
        mapping.append(key=(field, camera_id), value=photom_file_name(path))

    return mapping


def main(args):
    if args.verbose:
        logger.setLevel('DEBUG')

    if args.mapping is not None:
        mapping = Mapping.from_file(args.mapping)
    else:
        mapping = build_field_camera_mapping()

    mapping.summarise()

    if args.save_mapping is not None:
        logger.debug('Rendering mapping to file %s', args.save_mapping)
        mapping.to_file(args.save_mapping)

    if args.run:
        for key in mapping:
            field, camera_id = key
            spawn_job(field=field, camera_id=camera_id, files=sorted(mapping[key]))


if __name__ == '__main__':
    description = '''Stitch all available NGTS observations together for a single
    field and camera'''

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-m', '--mapping', required=False, help='Pre-computed mapping')
    parser.add_argument('-r', '--run', action='store_true', help='Spawn jobs')
    parser.add_argument('-s', '--save-mapping',
                        required=False,
                        help='Save mapping information')
    main(parser.parse_args())
