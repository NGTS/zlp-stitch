#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import
import argparse
import logging
from astropy.io import fits
import numpy as np

logging.basicConfig(level='INFO', format='%(levelname)7s %(message)s')
logger = logging.getLogger(__name__)

IGNORE_HDUS = {'PRIMARY', 'CASUDET'}


def resort(filename):
    with fits.open(filename, mode='update') as infile:
        imagelist = infile['imagelist'].data
        tmid = imagelist['tmid']
        ind = np.argsort(tmid)

        infile['imagelist'].data[:] = imagelist[ind]

        images = (hdu for hdu in infile if hdu.is_image)
        for image in images:
            name = image.name
            if name.upper() in IGNORE_HDUS:
                continue

            sorted_data = image.data[:, ind]
            infile[name].data = sorted_data[:]


def main(args):
    if args.verbose:
        logger.setLevel('DEBUG')
    logger.debug(args)

    if not args.force:
        raise RuntimeError(
            'To actually change the file, the -f/--force argument is required')


if __name__ == '__main__':
    description = 'Sort a summary file in place'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('filename')
    parser.add_argument('-f', '--force', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    main(parser.parse_args())