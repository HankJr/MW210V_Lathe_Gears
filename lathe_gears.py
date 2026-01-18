#!/usr/bin/python3
#
# Program for working out feed gear ratios for the ubiquitous MW210V lathe.
# With a bit of doctoring it'll probably do for other lathes as well...
#
# For the paranoid and similarly encumbered:
# This code lives under the burden of the un-license.
# This program should have reached you with accompanied by a file with
# the name 'un-license'. Read that if you wish.
# For more information, please refer to <https://unlicense.org/>
#
# This program was inspired by the one written by Matthias Wandel, see:
# <https://github.com/Matthias-Wandel/lathe-thread-gears>

# ------------------------------------------------------------------------------
# For (a little) help try: ~/this/file/path$ pyhton3 lathe_gears.py -h
# ------------------------------------------------------------------------------

import sys
import itertools
import argparse
import time
import math
import logging

# We're logging our results into a file, default is 'lathe_gears_result'.
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# There are four possible gear configurations on the MW210:
#
# 'H' designates a spacer bushing, '|' designates meshing, '-' designates a
# gearpost, and '=' designates the leadscrew. 'S' is the (fixed) spindle gear.
#
#  I      II      III     IV
#
# S      S       S       S
# |      |       |       |
# A-H    A-B     A-H     A-B      There is only one possible population
# |        |     |         |      with 3 or 5 gears (I and IV);there are two
# C-H    H-D     C-D     C-D      possibilities with 4 (II and III).
# |        |       |     |        I call II the 'dogleg' and III the 'flash'.
# E=H    H=F     H=F     E=H

# ------------------------------------------------------------------------------
# Lathe Settings, these are OVERRIDDEN by values from the data file--if
# used--which in turn are OVERRIDDEN by command line arguments--if given.
# Pick your poison.
spindle_teeth = 56       # Fixed drive gear on spindle.
spindle_diameter = 56    # How much space is taken up by the spindle*.
leadscrew_pitch = 2      # Leadscrew pitch.
leadscrew_unit = 'mm'    # Unless you found/made an imperial leadscrew...
leadscrew_diameter = 23  # How much space is taken up by the shaft**.
max_centers = 135        # Max center distance of gear mounting posts.
reach_dimension = 110        # Min outside dimension (so A touches the spindle).
gear_clearance = 4       # With both posts fully occupied, i.e. 5 gears used,
                         # clearance between the non-meshing gears A and C.
# ------------------------------------------------------------------------------
# User Settings
gears_available = [24,30,40,48,50,52,60,60,66,70,72,75]
#pitches = [0.8,1,1.5,1.75,2,2.5,3,3.5,4,4.5,5] # Metric
pitches = [44,40,32,28,24,22,20,19,14,11,10,9,8,7,6] # SAE
#pitch_unit = 'mm'       # Or 'tpi'.
pitch_unit = 'tpi'       # Or 'mm'.

# Inch gears that come with the lathe, this takes seconds.
#gears_available = [24,30,40,48,50,52,60,60,66,70,72,75]

# Inch gears plus optional mm gears, this takes 28 minutes on an older laptop.
#gears_available = [84,80,80,72,60,50,40,33,20,24,30,40,48,50,52,60,60,66,70,72,75]

# ------------------------------------------------------------------------------
# Functions.

# For pretty runtime output.
def format_seconds(seconds):
    milli = int(1000 * (seconds % 1))
    seconds = int(seconds)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f'{hours}:{minutes:02d}:{seconds:02d}.{milli:04d}'

# Progress bar, ripped straight from the Wonderful Web World.
def print_progress_bar(index, total, label):
    n_bar = 20 # Progress bar width.
    progress = index / total
    sys.stdout.write('\r')
    sys.stdout.write(f"[{'=' * int(n_bar * progress):{n_bar}s}] {int(100 * progress)}% {label}")
    sys.stdout.flush()

# How many possible permutations of the gear combinations exist.
def possible_permutations(gears_available):
    total=0
    for p in [3,4,4,5]: # Configurations I through IV, see above.
        total = total + math.factorial(gears_available) / math.factorial(gears_available - p)
    return int(total)

# Parse 'list' item from the command line. See the ArgParser below.
# The 'list' is a single 'comma separated' string.
def csv_to_list(value):
    value = value.split(",")
    return value

# Parse 'list' item from the data file. See the ArgParser below.
# The 'list' is a single 'comma separated' string, it's plit into a list,
# and the individual values cast as float.
def csv_to_floatlist(value):
    value = value.split(",")
    return [float(item) for item in value]

# Create an example data file.
def write_data_file(file_path):
    lines = [
        '# Lathe data listing. Data here is valid for my MW210V 8x39.',
        '# Be careful adding gears, possibilities grow exponentially,',
        '# 25 gears give about 1.25 BILLION possibilities...',
        '# Here\'s a graph. <https://www.desmos.com/calculator/cpiettwsy2>',
        '# Parameter order doesn\'t matter. Not all parameters need',
        '# to be here, but those that are will override the ones in',
        '# the program file. Any parameters given on the command line',
        '# will override both the ones in the program file, as well as',
        '# the ones provided here.',
        '#',
        '# DO NOT CHANGE THE VARIABLE NAMES.',
        '# DO NOT CHANGE THE FORMAT!',
        '# DO NOT PROVIDE \'EMPTY\' PARAMETERS (i.e., a name without a value).',
        '#',
        '# Pitch and leadscrew unit options are: mm, tpi.',
        '#',
        '# NOTE: spindle_diameter, leadscrew_diameter, max_centers, and',
        '# gear_clearance are \'equivalent sizes\', that is to say, they are',
        '# the number of teeth a gear of the same dimension as the desired',
        '# dimension would have. If you know about modules and gears you know',
        '# what I\'m talking about. If you don\'t, GTS, you\'re about to run',
        '# a lathe, aren\'t you?',
        '# ',
        'gears_available=24,30,40,48,50,52,60,60,66,70,72,75',
        'pitches=40,32,28,24,20,18,16,14,13,12,11,10,9,8,7,6',
        'pitch_unit=tpi',
        'spindle_teeth=56',
        'spindle_diameter=56',
        'leadscrew_pitch=2',
        'leadscrew_unit=mm',
        'leadscrew_diameter=23',
        'max_centers=135',
        'reach_dimension=115',
        'gear_clearance=4'
    ]
    # Write the example file, warn if it already exists.
    try:
        with open(file_path, "x") as file:
            for line in lines:
                file.write(f"{line}\n")
    except FileExistsError:
        print(f"Error: The file \'{file_path}\' already exists.")
    # Give the user opportunity to edit the file.
    sys.exit(0)

# Read and process a data file.
def read_data_file(file_path):
    try:
        with open(file_path, 'r') as file:
            file_lines = list(file.readlines())
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    # Scrub the comments.
    while file_lines :
        if file_lines[0][0] == '#':
            foo=file_lines.pop(0)
        else:
            break
    # Scrub the '\n' newline line endings.
    file_lines = [item[0:-1] for item in file_lines]
    return file_lines

# Check linear fit ('A' gear reaches Spindle gear).
# 'item' is AACCE ABDDF AACDF ABDCE  for I through IV (above) respectively.
def reach_fit(item):
    if sum(item)/2 < reach_dimension:
        return False
    return True

# Check linear fit (total center distances leadscrew - bottom post - top post).
# 'item' is ACCE BDDF ACDF BDCE for I through IV (above) respectively.
def centers_fit(item):
    if sum(item)/2 > max_centers:
        return False
    return True

# Check 'B' gear clears spindle ('A' is the meshing gear) see II and IV above.
def spindle_cleared(a,b):
    if (b + spindle_diameter) >= (spindle_teeth + a):
        return False
    return True

# Check 'C' or 'D' (whichever may be the case, see III and IV above) gear
# clears spindle.
def lead_cleared(a,b,c):
    if (a + leadscrew_diameter) >= (b + c):
        return False
    return True

# Check 'A' gear clears 'C' gear, see IV above.
def gear_cleared(a,b,c,d):
    if (a + c + gear_clearance) >= (b + d):
        return False
    return True

# Check a gear set (from the command line) and report on fit and pitch.
# Population is in order ABCDEF
def check_gear_set(p):
    count = 0
    fits = ""
    for i in p:
        if i == 'H':
            count += 1
    if count == 3: # I - three gears.
        pitch = spindle_teeth*leadscrew_pitch/p[5]
        if not centers_fit([p[1],p[3],p[3],p[5]]):
            fits = fits + "\nTotal center distance too large"
        if not reach_fit([p[1],p[1],p[3],p[3],p[5]]):
            fits = fits + "\n\'A\' gear doesn\'t reach Spindle."
    if count == 2: # II or III - four gears.
        if p[3] == 'H': # II - 'dogleg'.
            pitch = spindle_teeth*leadscrew_pitch/p[1]*p[2]/p[6]
            if not centers_fit([p[2],p[4],p[4],p[6]]):
                fits = fits + "\nTotal center distance too large"
            if not reach_fit([p[1],p[2],p[4],p[4],p[6]]):
                fits = fits + "\n\'A\' gear doesn\'t reach Spindle."
            if not spindle_cleared(p[1],p[2]):
                fits = fits + "\nB gear fouls spindle"
        else: # III - 'flash'.
            pitch = spindle_teeth*leadscrew_pitch/p[3]*p[4]/p[6]
            if not centers_fit([p[1],p[3],p[4],p[6]]):
                fits = fits + "\nTotal center distance too large"
            if not reach_fit([p[1],p[1],p[3],p[4],p[6]]):
                fits = fits + "\n\'A\' gear doesn\'t reach Spindle."
            if not spindle_cleared(p[1]*2+p[3],p[4]):
                fits = fits + "\nB gear fouls spindle"
            if not lead_cleared(p[3],p[4],p[6]):
                fits = fits + "\nC gear fouls leadscrew"
    if count == 1: # IV - five gears.
        pitch = spindle_teeth*leadscrew_pitch/p[1]*p[2]/p[4]*p[3]/p[5]
        if not centers_fit([p[2],p[4],p[3],p[5]]):
            fits = fits + "\nTotal center distance too large"
        if not reach_fit([p[1],p[2],p[4],p[3],p[5]]):
            fits = fits + "\n\'A\' gear doesn\'t reach Spindle."
        if not lead_cleared(p[4],p[3],p[5]):
            fits = fits + "\nD gear fouls leadscrew"
        if not gear_cleared(p[1],p[2],p[3],p[4]):
            fits = fits + "\nA and C gears interfere"
    pitch = convert(pitch)
    p[0] = pitch
    if fits == "":
        fits = "Gears fit."
    print(f"---------- {label} ----------");
    print(set_layout(p, 0))
    print(fits)
    logger.info(f"---------- {label} ----------")
    logger.info(set_layout(p, 0))
    logger.info(fits)

# Pretty output of a gear set.
def set_layout(p, target):
    # There is no target with a single gear check (CLI option -c) so:
    if target == 0:
        err_str = ""
    else:
        err = (p[0]-target)/target*100
        err_str = f"  Error: {err:.3f}%"
    pp =(f"{p[1]}".rjust(15)+f"{p[2]}".rjust(5)+"\n"+
        f"{p[0]:.5f}".rjust(10)+f"{p[3]}".rjust(5)+f"{p[4]}".rjust(5)+
        err_str+"\n"+
        f"{p[5]}".rjust(15)+f"{p[6]}".rjust(5))
    return pp

# convert() becomes an alias (below) for one of these two:
# Leadscrew and pitches have the same units, either mm or tpi.
def no_conversion(value):
    return value
# Leadscrew and pitches have different units, either mm or tpi.
# Since A/b=c <=> A/c=b...
def conversion(value):
    return 25.4/value

# ------------------------------------------------------------------------------
# CLI arguments parsing.

parser = argparse.ArgumentParser(description="Determine gear sets for feed-rates on a lathe, written with the MW210V in mind.")
parser.add_argument('-g', '--gears', type=csv_to_list, help="Comma separated list of vailable gears, e.g. -g=84,72,60,42")
parser.add_argument('-p', '--pitches', type=csv_to_list, help="Comma separated list of feedrate(s) of interest, e.g. -p=8,12,16,24")
parser.add_argument('-u', '--unit', choices=['mm','tpi'], help="Pitch unit, mm is the default.")
parser.add_argument('-c', '--check',  type=csv_to_list, help="Check a gear set, given as a comma separated list of 6(!) gear positions A B C D E F, e.g. -c=60,40,H,80,H,56 ('H' for empty positions) for fit and resulting pitch.")
parser.add_argument('-f', '--file', nargs='*', type=str, help="Use data from file, provide full path if it\'s not located in the program directory, default is local file \'lathe_data\'.")
parser.add_argument('-e', '--example', nargs='*', type=str, help="Create an example lathe data file and exit, file name is optional.")
parser.add_argument('-o', '--output', type=str, help="Output file name, default is \'lathe_gears_result\'.")
args = parser.parse_args()

# ------------------------------------------------------------------------------
# Process CLI input.

# Do we want an example lathe data file?
# This exits the program to allow the user to edit the file.
if args.example or args.example == []:
    if args.example:
        write_data_file(args.example[0])
    else:
        write_data_file('lathe_data_example')

# Are we using a lathe data file?
# read it now so CLI arguments can override file arguments.
if args.file or args.file == []:
    if args.file:
        data = read_data_file(args.file[0])
    else:
        data = read_data_file('lathe_data')
    print('Reading data.')
    for r in data:
        i = r.find('=')
        name = r[0:i]
        value = r[i+1:]
        # 'list' values are actually strings; turn them into a list of floats.
        if value.find(',') >= 0:
            value = csv_to_floatlist(value)
        match name:
            case 'gears_available':
                gears_available = value
            case 'pitches':
                pitches = value
            case 'pitch_unit':
                pitch_unit = value
            case 'spindle_teeth':
                spindle_teeth = int(value)
            case 'spindle_diameter':
                spindle_diameter = float(value)
            case 'leadscrew_pitch':
                leadscrew_pitch = float(value)
            case 'leadscrew_unit':
                leadscrew_unit = value
            case 'leadscrew_diameter':
                leadscrew_diameter = float(value)
            case 'max_centers':
                max_centers = float(value)
            case 'gear_clearance':
                gear_clearance = float(value)

# Were we given a custom output file name?
output_file = 'lathe_gears_result'
if args.output:
    output_file = args.output
# Configure the logger (which writes our results to the output file).
logging.basicConfig(
    filename=output_file,
    level=logging.DEBUG,
    format='%(message)s',
    filemode='w' # use 'a' to append, 'w' to overwrite each time
)

# Command line arguments override any already given above or in the data file.
if args.gears:
    gears_available = args.gears
if args.pitches:
    pitches = args.pitches
if args.unit:
    pitch_unit = args.unit
# For pretty output.
label = pitch_unit.upper()

# Function alias to simplify code.
if pitch_unit == leadscrew_unit:
    convert = no_conversion
else:
    convert = conversion

# Are we checking a single gear set?
if args.check:
    if not len(args.check) == 6:
        raise ValueError("Set must have 6 positions, ABCDEF!")
    checkset=[0] # Place holder for resulting pitch value.
    for i in args.check:
        if i == 'H':
            checkset = checkset + ['H']
        else:
            checkset = checkset + [int(i)]
    check_gear_set(checkset)
    sys.exit(0)

#-------------------------------------------------------------------------------
# MAIN

#-------------------------------------------------------------------------------
# This is where the 'hard work' is done.

# Record the start time
start_time = time.perf_counter()

# Get some numbers.
all_sets=list(itertools.chain.from_iterable(itertools.combinations(gears_available, r) for r in [3,4,5]))
total_sets = len(all_sets)
total_permutations=possible_permutations(len(gears_available))
# Just in case the user was being funny...
pitches.sort()

# Inform the user.
print('Lathe feedrate and thread cutting gear set layouts for MW210V lathe.\n')
print(f'Available gears: {gears_available}\n')
print(f'Target feedrates: {pitches}\n')
print(f"Found {total_sets} combinations.\n")
print(f"Checking {total_permutations} possible permutations. This may take some time.")

# And log some info.
logger.info('Lathe feedrate and thread cutting gear set layouts for MW210V lathe.\n')
logger.info(f'Available gears: {gears_available}\n')
logger.info(f'Target feedrates: {pitches}\n')

# All permutations of each possible gear combination is 'placed on the lathe',
# discarding any that don't fit.
fitting_sets=[]
counter=0
for s in all_sets:
    counter = counter + 1
    # The progress bar takes a string comment like "Processing", wich seems
    # bit obvious, so, an empty string here, but, fill your boots... ;-)
    print_progress_bar(counter, total_sets, "")
    # Gears are 'placed' on the lathe along the mesh-line,
    # in the sequence of the set, see 'p = [A, ...] comments below.
    # Since the _order_ of the gears changes the ratio, we also want each
    # possible permutation of each set.
    # Sets that fit are stored with effective pitch as the first element.
    for p in list(itertools.permutations(s)):
        if len(p) == 3:
            # Configuration I (line) p = [A,C,E]
            if (centers_fit([p[0],p[1],p[1],p[2]]) and
                reach_fit([p[0],p[0],p[1],p[1],p[2]])):
                pitch = convert(spindle_teeth*leadscrew_pitch/p[2])
                fitting_sets = fitting_sets + [[ pitch, p[0], "H", p[1], "H", p[2], "H"]]
        if len(p) == 4:
            # Configuration II (dogleg) p = [A,B,D,E]
            if (centers_fit([p[1],p[2],p[2],p[3]]) and
                reach_fit([p[0],p[1],p[2],p[2],p[3]]) and
                spindle_cleared(p[0],p[1])):
                pitch = convert(spindle_teeth*leadscrew_pitch/p[0]*p[1]/p[3])
                fitting_sets = fitting_sets + [[ pitch, p[0], p[1], "H", p[2], "H", p[3]]]
            # Configuration III (flash) p = [A,C,D,F]
            if (centers_fit([p[0],p[1],p[2],p[3]]) and
                reach_fit([p[0],p[0],p[1],p[2],p[3]]) and
                spindle_cleared(p[0]*2+p[1],p[2]) and
                lead_cleared(p[1],p[2],p[3])):
                pitch = convert(spindle_teeth*leadscrew_pitch/p[1]*p[2]/p[3])
                fitting_sets = fitting_sets + [[ pitch, p[0], "H", p[1], p[2], "H", p[3]]]
        if len(p) == 5:
            # Configuration IV (questionmark) p = [A,B,D,C,E]
            if (centers_fit([p[1],p[2],p[3],p[4]]) and
                reach_fit([p[0],p[1],p[2],p[3],p[4]]) and
                spindle_cleared(p[0],p[1]) and
                lead_cleared(p[2],p[3],p[4]) and
                gear_cleared(p[0],p[1],p[3],p[2])):
                pitch = convert(spindle_teeth*leadscrew_pitch/p[0]*p[1]/p[2]*p[3]/p[4])
                fitting_sets = fitting_sets + [[ pitch, p[0], p[1], p[3], p[2], p[4], "H"]]

# Prepare for 'search'.
fitting_sets.sort(key=lambda x: x[0])
total_fitting_sets=len(fitting_sets)

# More user info.
print (f"\n\nDiscarded {total_permutations-total_fitting_sets}, which do not fit on the lathe.\n")
print (f"From the remaining {total_fitting_sets} the nearest matches to the target pitches are:\n")

# Search all populations for closest fit to target pitches,
# and publish nearest smaller and nearest bigger result.
# Grab the first target.
target = pitches.pop(0)
for i in range(total_fitting_sets-1):
    p = fitting_sets[i]
    if p[0] > target:
        if i > 0:
            print(set_layout(fitting_sets[i-1],target))
            print(f"{target}".rjust(4)+f"{label}".rjust(4)+" ".ljust(12,"-"));
            print(set_layout(p, target))
            print ("")
            logger.info(set_layout(fitting_sets[i-1],target))
            logger.info(f"{target}".rjust(4)+f"{label}".rjust(4)+" ".ljust(12,"-"));
            logger.info(set_layout(p, target))
            logger.info("")
        # If there are unsolved pitches left:
        if pitches:
            # grab the next one.
            target = pitches.pop(0)
        else:
            # If not, set the target to a 'huge' value, this will
            # get us to the end of the list without any more matches.
            target = 100000

# For proper interpretation of 'smallest' and 'biggest' pitches;
# for TPI, big numbers mean small pitch and v.v....
if pitch_unit == 'tpi':
    big_and_small = f'Smallest feedrate:\n{set_layout(fitting_sets[total_fitting_sets-1],0)}\n\nBiggest feedrate:\n{set_layout(fitting_sets[0],0)}'
else:
    big_and_small = f'Smallest feedrate:\n{set_layout(fitting_sets[0],0)}\n\nBiggest feedrate:\n{set_layout(fitting_sets[total_fitting_sets-1],0)}'
# Publish in both places.
logger.info(big_and_small)
print(big_and_small)

# Record the end time and publish total runtime.
end_time = time.perf_counter()
total_time=end_time - start_time
logger.info(f"\nTotal execution time: {format_seconds(total_time)}.")
print(f"\nTotal execution time: {format_seconds(total_time)}.")

# ------------------------------------------------------------------------------
# NOTES
# *  The spindle limits the size of the 'B' gear. This dimension is
#    essentially the number of teeth a gear matching the diameter of the
#    spindle would have. Ish; this value should include a safety margin.
# ** The leadscrew limits the size of the gear paired with its meshing gear on
#    the bottom gear post. This dimension is essentially the number of teeth a
#    gear matching the diameter of the shaft would have. Ish; this value
#    should include a safety margin.
