#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import

import argparse
import fitsio
import numpy as np

def main(args):
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='+', help='Files to condense')
    parser.add_argument('-o', '--output', required=True, help='Output filename')
    main(parser.parse_args())
