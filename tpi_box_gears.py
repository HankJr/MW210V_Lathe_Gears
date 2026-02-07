#!/usr/bin/python3

import sys
import itertools
import argparse
import time
import math
import logging
import decimal

# TPI-box to get perfect tpi gear ratios on a MW210V lathe.
# The gears hang behind the spindle, and are arranged as depicted below.
# The output gear 'O' is wider so as to engage the 'B' gear on the lathe;
# the 'Q' gear therefore needs to be larger than the 'I' gear to prevent
# fouling. The 'O' gear needs to be larger than the spindle gear 'S',
# because it runs ON the bushing between 'S' and the spindle bearing.
#
#                            OOO
#                            OOO   S
#            chuck ----------OOO---S----- spindle free end ---
#                            OOO   S
#                            OOO   |
#                            |     P
#                            Q     P
#                            Q  I  P
#  Legend:                  -Q--I==P-
#    - shaft                 Q  I  P
#    = keyed (connected)     Q  |  P
#    | meshing gears         |  M  P
#                            N  M
#                           -N==M----
#                            N  M
#                               M
#
# This is not a scale drawing... ;-)

# Some physical limits, names refer to the gears depicted above...
no_snag = 4 # Gear size difference to prevent overlapping teeth snagging.
S = 56      # Spindle gear teeth; manufacturer imposed.
I = 127     # Smallest integer 'inch-fold'; 5*25.4=127,
            # which is--obviously--a prime...
max_O = 71  # This could be a bit more, but would quickly start to
            # inhibit metric gearing, fouling the B gear on the lathe.
max_P = 171 # If you're happy with a big 'back-bulge', feel free to grow this.
max_M = 100 # Seems a good limit, see previous comment.
min_N = 20  # Ought perhaps to be a bit more? Dunno, maybe, maybe not...

# We're logging our results into a file, grab a logger.
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# CLI arguments parsing.

parser = argparse.ArgumentParser(description="Determine gear sets for feed-rates on a lathe, written with the MW210V in mind.")
parser.add_argument('-o', '--output', nargs=1, metavar=('file_name'), type=str, help="Non-default output file name; defaults are set in the data file.")
args = parser.parse_args()

# ------------------------------------------------------------------------------
# Process CLI input.

output_file = 'tpi_box_rationals'

# Were we given a custom output file name? Override the default.
if args.output:
    output_file = args.output

# Configure the logger (which writes our results to the output file).
logging.basicConfig(
    filename=output_file,
    level=logging.DEBUG,    # Write ALL messages.
    format='%(message)s',   # No need for timestamps &c.
    filemode='w'            # Overwrite each time, 'a' for append, but why?
)

#-------------------------------------------------------------------------------
# MAIN This is where the 'hard work' is done.

# Say 'hello'.
print('\nTPI gearbox calculation for MW21V lathe.')
# Output file 'title'.
logger.info('Lathe TPI box inch-fractional gear combinations.\n')

all_sets=[]
counter=0
# The next two minima are physical constraints.
for O in range(S+no_snag, max_O):
    for P in range((I+O+no_snag-S), max_P):
        # Q follows.
        Q=S+P-O
        # But has a physical minimum constraint.
        if Q < I+no_snag:
            continue
        # M also has a minimum constraint.
        for M in range((Q+min_N-I),max_M):
            counter += 1
            # And N follows.
            N=M+I-Q
            # Calculate effective teeth; Q and O are just intermediary gears;
            # they have no ratio effect.
            Z_effective=S/P*I/M*N
            # Abs tol is 1 order of magnitude larger than smallest float.
            # If Z_effective is divisible by 1/1024 inch, it's usable.
            if math.isclose(Z_effective % (25.4/1024), 0, abs_tol = 1e-8):
                all_sets = all_sets + [[P, I, M, N, Q, O, float(f"{Z_effective:.6f}")]]

# Inform the user.
print (f"\nFound {counter} sets.")

# Sort by primary 'P' gear diameter (smaller is better), and descending
# effective teeth count of the output gear 'O'.
all_sets.sort(key=lambda x: (x[0], -x[6]))
for i in all_sets:
    logger.info(f'{i}')

# More user info.
print (f"\nOf which {len(all_sets)} are inch-fractional.")
print (f"\nSmallest primary gear: {all_sets[0]}.")
