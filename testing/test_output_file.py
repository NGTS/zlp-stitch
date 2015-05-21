import numpy as np
from astropy.io import fits
import pytest
import os

TEST_FILENAME = 'out.fits'


@pytest.mark.skipif(not os.path.isfile(TEST_FILENAME),
        reason="cannot find test source file")
def test_sorted_mjd_order():
    imagelist = fits.getdata(TEST_FILENAME, 'imagelist')
    tmid = imagelist['tmid']

    assert (tmid == np.sort(tmid)).all()

