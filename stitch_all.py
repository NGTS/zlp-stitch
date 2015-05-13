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
import sys

logger = setup_logging('stitch-all')

regex = re.compile(r'2015\d{4}-(?P<field>.+)-(?P<camera_id>80\d)$')

CHOSEN_FIELDS = {'wasp19b', 'k2_3b', 'ng2000'}
CHOSEN_CAMERAS = {802, 805, 806}

memory = joblib.Memory(cachedir='.tmp')
LOGDIR = os.environ.get('LOGDIR', os.path.expanduser('~/var/log'))


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


def build_zlp_stitch_command(field, camera_id, files):
    python_path = os.path.realpath(os.path.join(os.path.dirname(__file__), 'venv', 'bin',
                                                'python'))
    script_path = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                'zlp-stitch.py'))
    output_path = os.path.join('/', 'ngts', 'pipedev', 'ParanalOutput', 'per_field')
    output_stub = '{field}-{camera_id}.fits'.format(field=field, camera_id=camera_id)
    output_path = os.path.join(output_path, output_stub)
    cmd = [python_path, script_path, '-o', output_path]
    cmd.extend(files)
    logger.debug('cmd: %s', ' '.join(cmd))
    return map(str, cmd)


def build_qsub_command(field, camera_id):
    name = 'stitch-{field}-{camera_id}'.format(field=field, camera_id=camera_id)
    log_name = os.path.join(LOGDIR, '{}.log'.format(name))
    return map(str, ['/usr/local/sge/bin/lx-amd64/qsub', '-N', name, '-j', 'yes', '-o',
                     log_name, '-S', '/bin/bash', '-pe', 'parallel', 1])


def spawn_job(field, camera_id, files):
    zlp_stitch_command = build_zlp_stitch_command(field=field,
                                                  camera_id=camera_id,
                                                  files=files)
    command_string = ['echo',] + zlp_stitch_command
    submit_command = sp.Popen(command_string, stdout=sp.PIPE)

    qsub_command_string = build_qsub_command(field, camera_id)
    qsub_env = {'SGE_ROOT': '/usr/local/sge'}
    sp.check_call(qsub_command_string, stdin=submit_command.stdout, env=qsub_env)
    submit_command.wait()


@memory.cache
def build_field_camera_mapping():
    mapping = defaultdict(list)
    for path in get_available_field_cameras():
        logger.info('Building {}'.format(path))
        match = regex.search(path)
        field = match.group('field')
        camera_id = int(match.group('camera_id'))
        mapping[(field, camera_id)].append(photom_file_name(path))

    summarise(mapping)
    return mapping


def main(args):
    if args.verbose:
        logger.setLevel('DEBUG')

    mapping = build_field_camera_mapping()
    for key in mapping:
        field, camera_id = key
        spawn_job(field=field, camera_id=camera_id, files=mapping[key])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    main(parser.parse_args())
