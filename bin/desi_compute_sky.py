#!/usr/bin/env python
#
# See top-level LICENSE file for Copyright information
#
# -*- coding: utf-8 -*-

"""
This script computes the fiber flat field correction from a DESI continuum lamp frame.
"""

from desispec.io import read_frame
from desispec.io import read_fibermap
from desispec.io import read_fiberflat
from desispec.io import write_sky
from desispec.io import write_qa_exposure
from desispec.io import read_qa_exposure
from desispec.fiberflat import apply_fiberflat
from desispec.sky import compute_sky
from desispec.sky import qa_skysub
from desispec.qa.qa_exposure import QA_Exposure
from desispec.log import get_logger
import argparse
import numpy as np
import sys, glob

def main() :

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--infile', type = str, default = None, required=True,
                        help = 'path of DESI exposure frame fits file')
    parser.add_argument('--fibermap', type = str, default = None, required=True,
                        help = 'path of DESI exposure frame fits file')
    parser.add_argument('--fiberflat', type = str, default = None, required=True,
                        help = 'path of DESI fiberflat fits file')
    parser.add_argument('--outfile', type = str, default = None, required=True,
                        help = 'path of DESI sky fits file')
    parser.add_argument('--qafile', type = str, default = None, required=False,
                        help = 'path of QA file. Will calculate for Sky Subtraction')
    #parser.add_argument('--qafig', type = str, default = None, required=False)

    args = parser.parse_args()
    log=get_logger()

    log.info("starting")

    # read exposure to load data and get range of spectra
    frame = read_frame(args.infile)
    specmin, specmax = np.min(frame.fibers), np.max(frame.fibers)

    # read fibermap to locate sky fibers
    fibermap = read_fibermap(args.fibermap)
    selection=np.where((fibermap["OBJTYPE"]=="SKY")&(fibermap["FIBER"]>=specmin)&(fibermap["FIBER"]<=specmax))[0]
    if selection.size == 0 :
        log.error("no sky fiber in fibermap %s"%args.fibermap)
        sys.exit(12)

    # read fiberflat
    fiberflat = read_fiberflat(args.fiberflat)

    # apply fiberflat to sky fibers
    apply_fiberflat(frame, fiberflat)

    # compute sky model
    skymodel = compute_sky(frame, fibermap)

    # QA
    if args.qafile is not None: 
        log.info("performing skysub QA")
        # Load (read, if it exists)
        if len(glob.glob(args.qafile)) == 1:
            qaexp = read_qa_exposure(args.qafile)
        else:
            qaexp = QA_Exposure('science') # Include expid too if we can
        # Init SkySub
        qaexp.init_skysub(frame.meta['camera'])
        # Run
        qa_skysub(qaexp, frame, fibermap, skymodel)
        # Write
        write_qa_exposure(args.qafile, qaexp)
        log.info("successfully wrote {:s}".format(args.qafile))

    # write result
    write_sky(args.outfile, skymodel, frame.meta)
    log.info("successfully wrote %s"%args.outfile)


if __name__ == '__main__':
    main()
