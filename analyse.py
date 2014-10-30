#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import numpy as np
import matplotlib.pyplot as plt
import fitsio
from scipy import stats


def find_night_breaks(mjd, gap_size):
    mjd_a = np.array(mjd)
    frames = np.arange(mjd_a.size)
    ind = np.diff(mjd_a) > gap_size
    return frames[ind]

def main(args):
    # np.random.seed(42)
    with fitsio.FITS(args.filename) as infile:
        hjd = infile['hjd'].read()
        flux = infile['flux'].read()
        fluxerr = infile['fluxerr'].read()

        imagelist = infile['imagelist']
        airmass = imagelist['airmass'].read()
        clouds = imagelist['clouds'].read()
        shift = imagelist['shift'].read()


    mean_flux = np.median(flux, axis=1)
    ind = (mean_flux >= 5E3) & (mean_flux <= 5E4)
    print(flux.shape)
    hjd, flux, fluxerr = [data[ind] for data in [hjd, flux, fluxerr]]

    chosen_ind = np.random.randint(0, hjd.shape[0])
    print(chosen_ind)
    print(flux.shape)
    hjd, flux, fluxerr = [data[chosen_ind] for data in [hjd, flux, fluxerr]]
    print(flux.shape)

    clouds_ind = clouds < 0.75
    hjd, flux, fluxerr, clouds, shift, airmass = [data[clouds_ind] for data in [
        hjd, flux, fluxerr, clouds, shift, airmass]]
    shift_ind = shift <= 3
    hjd, flux, fluxerr, clouds, shift, airmass = [data[shift_ind] for data in [
        hjd, flux, fluxerr, clouds, shift, airmass]]
    night_breaks = [0] + list(find_night_breaks(hjd, 0.1))

    corrected_lightcurve = []
    normalised_lightcurve = []
    for i in xrange(len(night_breaks)):
        l = night_breaks[i]
        try:
            r = night_breaks[i + 1]
        except IndexError:
            r = None

        chosen_flux, chosen_fluxerr, chosen_airmass = [
            flux[l:r], fluxerr[l:r], airmass[l:r]]

        chosen_magerr = 1.08 * chosen_fluxerr / chosen_flux
        chosen_mag = -2.5 * np.log10(chosen_flux)

        # plt.errorbar(chosen_airmass, chosen_mag, chosen_magerr,
        #              ls='None', marker='.', capsize=0., label=i)

        fit = np.poly1d(np.polyfit(chosen_airmass, chosen_mag, 1,
                                   w=1. / chosen_magerr ** 2))

        corrected = chosen_mag - fit(chosen_airmass)
        corrected_lightcurve.extend(corrected)

        normalised = chosen_mag - np.median(chosen_mag)
        normalised_lightcurve.extend(normalised)

    corrected_lightcurve, normalised_lightcurve = [np.array(data) for data in [
        corrected_lightcurve, normalised_lightcurve]]


    frame = np.arange(hjd.size)



    mag_error = 1.08 * fluxerr / flux
    offset = 0.25
    errorbar_alpha = 0.
    plt.errorbar(frame, normalised_lightcurve + offset, mag_error, ls='None', capsize=0.,
                 alpha=errorbar_alpha)
    plt.plot(frame, normalised_lightcurve + offset, ',', label='Raw')

    plt.errorbar(frame, corrected_lightcurve, mag_error, ls='None', capsize=0.,
                 alpha=errorbar_alpha)
    plt.plot(frame, corrected_lightcurve, ',', label='Airmass corrected')

    binned, ledges, _ = stats.binned_statistic(frame, corrected_lightcurve, bins=100,
                                               statistic='median')
    bin_centres = ledges[:-1] + np.diff(ledges)[0] / 2.
    plt.plot(bin_centres, binned, '.')


    for b in night_breaks:
        plt.axvline(b, zorder=-10, ls=':', color='k', alpha=0.3)

    plt.legend(loc='best')
    plt.grid(False)
    plt.tight_layout()
    plt.ylim(0.5, -0.25)

    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    main(parser.parse_args())
