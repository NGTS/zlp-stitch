import numpy as np
import sys
sys.path.insert(0, 'scripts')
from astropy.io import fits
import shutil
import pytest

from resort_by_mjd import resort


@pytest.fixture
def fname(tmpdir):
    fname = str(tmpdir.join('test.fits'))
    shutil.copyfile('testing/data/smaller.fits', fname)
    return fname


def is_sorted(fname):
    tmid = fits.getdata(fname, 'imagelist')['tmid']
    return (tmid == np.sort(tmid)).all()


def test_resort_imagelist(fname):
    assert not is_sorted(fname)
    resort(fname)
    assert is_sorted(fname)


def test_flux_is_sorted(fname):
    assert not is_sorted(fname)
    with fits.open(fname) as infile:
        tmid = infile['imagelist'].data['tmid']
        flux = infile['flux'].data[0]
        zipped = zip(tmid, flux)

    expected = sorted(zipped, key=lambda row: row[0])
    resort(fname)

    with fits.open(fname) as infile:
        tmid = infile['imagelist'].data['tmid']
        flux = infile['flux'].data[0]
        zipped = zip(tmid, flux)

    assert zipped == expected


def test_casudet_is_unchanged(fname):
    assert not is_sorted(fname)
    with fits.open(fname) as infile:
        expected = infile['casudet'].data[0]

    resort(fname)

    with fits.open(fname) as infile:
        flux = infile['casudet'].data[0]

    assert (flux == expected).all()
