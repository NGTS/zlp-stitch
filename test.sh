#!/usr/bin/env bash

set -e

ensure_link() {
    if [[ ! -f $1 ]]; then
        ln -sv $2 $1
    fi
}

setup_test_files() {
    ensure_link /tmp/test1.fits /ngts/pipedev/ParanalOutput/old_runs/run01/03-wasp103b.fits
    ensure_link /tmp/test3.fits /ngts/pipedev/ParanalOutput/old_runs/run01/05-wasp103b.fits
    ensure_link /tmp/test2.fits /ngts/pipedev/ParanalOutput/old_runs/run01/08-wasp103b.fits
}

run_script() {
    test -f output.fits && rm output.fits
    python ./zlp-stitch.py /tmp/test1.fits /tmp/test2.fits /tmp/test3.fits -o /tmp/output.fits
}

main() {
    setup_test_files
    run_script
}

main
