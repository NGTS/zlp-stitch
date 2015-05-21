import numpy as np
from astropy.io import fits
import pytest


@pytest.fixture
def resultsfile():
    return 'out.fits'


def test_sorted_mjd_order(resultsfile):
    imagelist = fits.getdata(resultsfile, 'imagelist')
    tmid = imagelist['tmid']

    assert (tmid == np.sort(tmid)).all()

