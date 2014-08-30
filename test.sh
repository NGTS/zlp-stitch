#!/usr/bin/env bash

set -e

ensure_link() {
    if [[ ! -f $1 ]]; then
        ln -sv $2 $1
    fi
}

setup_test_files() {
    ensure_link test1.fits /ngts/pipedev/ParanalOutput/03-wasp103b.fits
    ensure_link test3.fits /ngts/pipedev/ParanalOutput/05-wasp103b.fits
    ensure_link test2.fits /ngts/pipedev/ParanalOutput/08-wasp103b.fits
}

run_script() {
    test -f output.fits && rm output.fits
    python ./zlp-stitch.py test1.fits test2.fits test3.fits -o output.fits
}

main() {
    setup_test_files
    run_script
}

main
