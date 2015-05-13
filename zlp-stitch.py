#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import

import argparse
import fitsio
import numpy as np
import logging
import os
from commonlog import setup_logging

logger = setup_logging('zlp-stitch')


def perform_post_processing(outfile):
    sort_by_hjd(outfile)
    compute_final_statistics(outfile)


def sort_by_hjd(filename):
    ignore_list = ['catalogue', 'primary', '']
    logger.info('Sorting by hjd')

    with fitsio.FITS(filename, 'rw') as infile:
        tmid = infile['imagelist']['tmid'].read()
        ind = np.argsort(tmid)
        for hdu in infile:
            logger.debug('Found hdu: %s', hdu.get_extname())
            if hdu.get_extname().strip().lower() == 'imagelist':
                data = hdu.read()
                data = data[ind]
                hdu.write(data)
                del data

            elif hdu.get_extname().strip().lower() not in ignore_list:
                data = hdu.read()
                data = data[:, ind]
                hdu.write(data)
                del data

    logger.info('File sorted')


def compute_final_statistics(fname):
    '''
    Given a filename, for each aperture in the file compute the number of points
    in the lightcurve which are not NaNs

    This function is destructive - it changes the output file
    '''
    logger.info('Computing final statistics')
    with fitsio.FITS(fname, 'rw') as outfile:
        flux = outfile['flux'].read()
        fluxerr = outfile['fluxerr'].read()
        original_catalogue = outfile['catalogue']
        keys = original_catalogue.get_colnames()
        original_catalogue_data = original_catalogue.read()
        logger.debug('Data read')

        out_catalogue_data = []
        for (lc, lcerr, cat_row) in zip(flux, fluxerr, original_catalogue_data):
            ind = np.isfinite(lc)
            npts = lc[ind].size

            new_data = {key: value for (key, value) in zip(keys, cat_row)}
            new_data['NPTS'] = npts

            if npts > 0:
                flux_mean = np.average(lc[ind], weights=1. / lcerr[ind] ** 2)
                new_data['FLUX_MEAN'] = flux_mean
            else:
                new_data['FLUX_MEAN'] = np.nan

            out_catalogue_data.append(new_data)

        out_catalogue_data = {
            key: np.array([row[key] for row in out_catalogue_data])
            for key in keys
        }
        original_catalogue.write(out_catalogue_data)

    logger.info('Statistics computed')


def get_exposure_time_indices(file_handle, exptime):
    exptime_data = file_handle['imagelist']['exposure'].read()
    return exptime_data == exptime


def filter_by_exposure_time(data, file_handle, exptime, axis=0):
    if exptime is not None:
        ind = get_exposure_time_indices(file_handle, exptime)
        if axis == 0:
            return data[ind]
        else:
            return data[:, ind]
    else:
        return data


def main(args):
    if args.verbose:
        logger.setLevel('DEBUG')
    logger.debug(args)
    logger.info('Merging %s files', len(args.file))
    file_handles = [fitsio.FITS(fname) for fname in args.file]

    with fitsio.FITS(args.output, 'rw', clobber=True) as outfile:
        outfile.write(file_handles[0]['catalogue'].read(),
                      header={'extname': 'CATALOGUE'})
        logger.debug('Catalogue written')

        for hdu in file_handles[0]:
            hdu_name = hdu.get_extname()
            exttype = hdu.get_exttype()

            if hdu_name in {'', 'PRIMARY'}:
                logger.debug('Found Primary HDU, skipping')
                continue

            logger.debug('Stacking hdu %s: %s', hdu_name, exttype)

            if exttype == 'IMAGE_HDU':
                logger.debug("Found image")

                for fitsfile, name in zip(file_handles, args.file):
                    logger.info("{filename}:{hdu}".format(filename=name, hdu=hdu_name))
                    in_data = fitsfile[hdu_name].read()
                    in_data = filter_by_exposure_time(in_data, fitsfile, args.exptime,
                                                      axis=1)
                    logger.debug('in_data.shape: %s', in_data.shape)
                    try:
                        out_data = np.concatenate([out_data, in_data], axis=1)
                    except NameError:
                        out_data = in_data
                    logger.debug('out_data.shape: %s', out_data.shape)

                outfile.write(out_data, header={'extname': hdu_name})
                del out_data

            else:
                logger.info("Found catalogue")

                if hdu_name == 'IMAGELIST':
                    for fitsfile in file_handles:
                        in_data = fitsfile[hdu_name].read()
                        in_data = filter_by_exposure_time(in_data, fitsfile, args.exptime)
                        logger.debug('in_data.shape: %s', in_data.shape)
                        try:
                            out_data = np.concatenate([out_data, in_data])
                        except NameError:
                            out_data = in_data
                        logger.debug('out_data.shape: %s', out_data.shape)

                    outfile.write(out_data, header={'extname': hdu_name})
                    del out_data
                elif hdu_name != 'CATALOGUE':
                    raise RuntimeError("Unknown hdu catalogue: {}".format(hdu_name))

    perform_post_processing(args.output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='+', help='Files to condense')
    parser.add_argument('-e', '--exptime',
                        help='Pick a specific exposure time',
                        required=False,
                        type=float)
    parser.add_argument('-o', '--output', required=True, help='Output filename')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    main(parser.parse_args())
