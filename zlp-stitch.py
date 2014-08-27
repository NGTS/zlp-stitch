#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import fitsio

def main(args):
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='+', help='Files to condense')
    parser.add_argument('-o', '--output', required=True, help='Output filename')
    main(parser.parse_args())
