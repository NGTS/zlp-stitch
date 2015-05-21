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

def test_resort_data(tmpdir, fname):
    assert not is_sorted(fname)
    resort(fname)
    assert is_sorted(fname)

