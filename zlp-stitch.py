#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import

import argparse
import fitsio
import numpy as np

def compute_final_statistics(fname):
  '''
  Given a filename, for each aperture in the file compute the number of points in the lightcurve
  which are not NaNs

  This function is destructive - it changes the output file
  '''
  with fitsio.FITS(fname, 'rw') as outfile:
      flux = outfile['flux'].read()
      fluxerr = outfile['fluxerr'].read()
      original_catalogue = outfile['catalogue']
      keys = original_catalogue.get_colnames()
      original_catalogue_data = original_catalogue.read()

      out_catalogue_data = []
      for (lc, lcerr, cat_row) in zip(flux, fluxerr, original_catalogue_data):
          ind = np.isfinite(lc)
          npts = lc[ind].size

          new_data = { key: value for (key, value) in zip(keys, cat_row) }
          new_data['NPTS'] = npts

          if npts > 0:
              flux_mean = np.average(lc[ind], weights=1. / lcerr[ind] ** 2)
              new_data['FLUX_MEAN'] = flux_mean
          else:
              new_data['FLUX_MEAN'] = np.nan

          out_catalogue_data.append(new_data)

      out_catalogue_data = { key: np.array([row[key] for row in out_catalogue_data])
                            for key in keys }
      original_catalogue.write(out_catalogue_data)


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
    file_handles = [fitsio.FITS(fname) for fname in args.file]

    with fitsio.FITS(args.output, 'rw', clobber=True) as outfile:
        outfile.write(file_handles[0]['catalogue'].read(),
                      header={'extname': 'CATALOGUE'})

        for hdu in file_handles[0]:
            hdu_name = hdu.get_extname()
            exttype = hdu.get_exttype()

            if not hdu_name:
                continue

            print('{}: {}'.format(hdu_name, exttype))

            if hdu_name == 'PRIMARY':
                continue

            if exttype == 'IMAGE_HDU':
                print("Found image {}".format(hdu_name))

                for fitsfile, name in zip(file_handles, args.file):
                    print("Reading data from file {}".format(name))
                    in_data = fitsfile[hdu_name].read()
                    in_data = filter_by_exposure_time(in_data, fitsfile, args.exptime,
                                                      axis=1)
                    print('in_data.shape: {}'.format(in_data.shape))
                    try:
                        out_data = np.concatenate([out_data, in_data], axis=1)
                    except NameError:
                        out_data = in_data
                    print('out_data.shape: {}'.format(out_data.shape))

                outfile.write(out_data, header={'extname': hdu_name})
                del out_data

            else:
                print("Found catalogue {}".format(hdu_name))

                if hdu_name == 'IMAGELIST':
                    for fitsfile in file_handles:
                        in_data = fitsfile[hdu_name].read()
                        in_data = filter_by_exposure_time(in_data, fitsfile, args.exptime)
                        print(in_data.shape)
                        try:
                            out_data = np.concatenate([out_data, in_data])
                        except NameError:
                            out_data = in_data

                    outfile.write(out_data, header={'extname': hdu_name})
                    del out_data
                elif hdu_name != 'CATALOGUE':
                    raise RuntimeError("Unknown hdu catalogue: {}".format(hdu_name))

    compute_final_statistics(args.output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='+', help='Files to condense')
    parser.add_argument('-e', '--exptime', help='Pick a specific exposure time',
                        required=False, type=float)
    parser.add_argument('-o', '--output', required=True, help='Output filename')
    main(parser.parse_args())
