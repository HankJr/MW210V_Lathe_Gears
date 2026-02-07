#!/usr/bin/python3
#
# Program for working out feed gear ratios for the ubiquitous MW210V lathe.
# With a bit of doctoring it'll probably do for other lathes as well...
#
# For the paranoid and similarly encumbered:
# This code lives under the burden of the unlicense.
# This program should have reached you accompanied by a file with
# the name 'unlicense'. Read that if you wish.
# For more information, please refer to <https://unlicense.org/>
#
# This program was inspired by the one written by Matthias Wandel, see:
# <https://github.com/Matthias-Wandel/lathe-thread-gears>

# ------------------------------------------------------------------------------
# IMPORTANT:
# Data is read from the default input file 'lathe_data'.
# If none is available, call this program like: pyhton3 lathe_gears.py -e
# and a default data file 'lathe_data_example' will be created.
# Edit that to your heart's content.
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# For (a little) help call this program like: pyhton3 lathe_gears.py -h
# ------------------------------------------------------------------------------

import sys
import itertools
import argparse
import time
import math
import logging
import statistics

# We're logging our results into a file, grab a logger.
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Functions.

# For pretty runtime output.
def formatted_time(seconds, show_milli=False):
    milli = int(1000 * (seconds % 1))
    seconds = int(seconds)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if show_milli:
        return f'{hours}:{minutes:02d}:{seconds:02d}.{milli:04d}'
    else:
        return f'{hours}:{minutes:02d}:{seconds:02d}'

# Progress bar, ripped straight from the Wonderful Web World.
def print_progress_bar(index, total, label=""):
    n_bar = 20 # Progress bar width.
    progress = index / total
    sys.stdout.write('\r')
    sys.stdout.write(f"[{'=' * int(n_bar * progress):{n_bar}s}] {int(100 * progress)}% {label}")
    sys.stdout.flush()

# How many possible permutations of the gear combinations exist.
def possible_permutations(gears_available):
    total=0
    for p in [3,4,4,5]: # Configurations I through IV, see above.
        total = total + math.prod(list(range(gears_available, gears_available-p, -1))) * math.factorial(p)
    return total

# Create an example data file. Wouldn't it be a proper piss-off to get this
# program without its data/config file? So here's a sample one to start with.
# To create an example data file run:
# ~/this/file/path$ pyhton3 lathe_gears.py -e
def write_data_file(file_path):
    lines = [
        '# Lathe data listing. Data here is valid for my MW210V 8x39.',
        '# Parameter order doesn\'t matter, any parameters given on the command line',
        '# will override the ones provided here.',
        '#',
        '# DO NOT CHANGE THE VARIABLE NAMES.',
        '# DO NOT CHANGE THE FORMAT!',
        '# DO NOT PROVIDE \'EMPTY\' PARAMETERS (i.e., a name without a value).',
        '#',
        '# IMPORTANT: ALL THE PARAMETERS HERE ARE REQUIRED!!!',
        '#',
        '# NOTE: spindle_diameter, leadscrew_diameter, max_centers, min_out_dim, and',
        '# gear_clearance are \'equivalent sizes\', that is to say, they are the number',
        '# of teeth a gear of the same dimension as the desired dimension would have.',
        '# They SHOULD be given as integers--gears don\'t have fractional teeth.',
        '# The ONLY decimal figures here should be metric pitches. Yes, 2-4 1/2, I know.',
        '# If you know about modules and gears, you know what I\'m talking about.',
        '# If you don\'t, GTS, you\'re about to run a lathe, aren\'t you?',
        '# ------------------------------------------------------------------------------',
        '# There are four possible gear configurations on the MW210:',
        '#',
        '# \'H\' designates a spacer bushing, or just a small gear that won\'t interfere,',
        '# \'|\' designates meshing, \'-\' designates a gearpost, and \'=\' designates the',
        '# leadscrew. \'S\' is the (fixed) spindle gear.',
        '#',
        '#  I      II      III     IV',
        '#',
        '# S      S       S       S',
        '# |      |       |       |',
        '# A-H    A-B     A-H     A-B      There is only one possible population',
        '# |        |     |         |      with 3 or 5 gears (I and IV);there are two',
        '# C-H    H-D     C-D     C-D      possibilities with 4 (II and III).',
        '# |        |       |     |        I call II the \'dogleg\' and III the \'flash\'.',
        '# E=H    H=F     H=F     E=H',
        '# ------------------------------------------------------------------------------',
        '# LEGEND:',
        '# pitch_unit             -- Unit (\'mm\' or \'tpi\') of the desired pitches.',
        '# spindle_teeth          -- Fixed drive gear on spindle.',
        '# spindle_diameter       -- How much space is taken up by the spindle*.',
        '# leadscrew_pitch        -- Leadscrew pitch.',
        '# leadscrew_unit         -- mm, unless you found/made an imperial leadscrew...',
        '# leadscrew_diameter     -- How much space is taken up by the shaft**.',
        '# max_centers            -- Max center distance of gear mounting posts.',
        '# min_out_dim            -- Min outside dimension (so A touches the spindle).',
        '# gear_clearance         -- With both posts fully occupied, i.e. 5 gears used,',
        '#                           clearance between the non-meshing gears A and C.',
        '# gears_output_file      -- Output file name.',
        '# output_format          -- Output format, \'layout\' prints only the best gear',
        '#                           sets like on the lathe gear table, \'list\' prints',
        '#                           ALL zero-error gear sets in a more compact fashion,',
        '#                           as well as the nearset smaller and larger results',
        '#                           of pitches that cannot achieve zero error.',
        '# check_set_output_file  -- Output file name when using the -c option.',
        '#',
        '# NOTES:',
        '# *  The spindle limits the size of the \'B\' gear. This dimension is',
        '#    essentially the number of teeth a gear matching the diameter of the',
        '#    spindle would have. Ish. This value should include a safety margin.',
        '# ** The leadscrew limits the size of the gear paired with its meshing gear on',
        '#    the bottom gear post. This dimension is essentially the number of teeth a',
        '#    gear matching the diameter of the shaft would have. Ish. This value',
        '#    should include a safety margin.',
        '# ------------------------------------------------------------------------------',
        '# PARAMETERS:',
        '#',
        '# Some common Metric pitches are 0.8,1,1.5,1.75,2,2.5,3,3.5,4,4.5,5',
        '# Some common SAE pitches are 40,32,28,24,20,18,16,14,13,12,11,10,9,8,7,6',
        '#',
        '# 4,6,8, and 10 thou feedrates are 250,167,125, and 100 \'tpi\'.',
        '#',
        '# These gears came with my lathe; be careful, processing time increases',
        '# exponentially with gear numbers:',
        'gears_available=20,24,33,35,40,48,50,52,60,60,66,70,72,75,80,80,84',
        'pitches=250,167,125,100,40,32,28,24,20,18,16,14,13,12,11,10,9,8,7,6',
        'pitch_unit=tpi',
        'spindle_teeth=56',
        'spindle_diameter=56',
        'leadscrew_pitch=2',
        'leadscrew_unit=mm',
        'leadscrew_diameter=23',
        'max_centers=135',
        'min_out_dim=115',
        'gear_clearance=4',
        'gears_output_file=gears_result',
        'output_format=layout',
        'check_set_output_file=check_set_results'
    ]
    # Write the example file, warn if it already exists.
    try:
        with open(file_path, "x") as file:
            for line in lines:
                file.write(f"{line}\n")
    except FileExistsError:
        print(f"Error: The file \'{file_path}\' already exists.")

# Read and process a data file.
def read_data_file(file_path):
    try:
        with open(file_path, 'r') as f:
            file_lines = list(f.readlines())
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    # Scrub the comments and '\n' newline line endings.
    file_lines = [item[0:-1] for item in file_lines if item[0] != '#']
    return file_lines

# Generate all possible combinations of 3, 4,and 5 gears, in a single list.
def all_possible_sets(gears):
    return list(itertools.chain.from_iterable(itertools.combinations(gears, r) for r in [3,4,5]))

# Check linear fit ('A' gear reaches Spindle gear).
# 'item' is AACCE ABDDF AACDF ABDCE  for I through IV (above) respectively.
def check_reach_fit(item):
    if sum(item)/2 < min_out_dim:
        return False
    return True

# Check linear fit (total center distances leadscrew - bottom post - top post).
# 'item' is ACCE BDDF ACDF BDCE for I through IV (above) respectively.
def check_centers_fit(item):
    if sum(item)/2 > max_centers:
        return False
    return True

# Check 'A' gear shaft threads clear the belt drive.
def check_belt_cleared(a):
    if a < 33:
        return False
    return True

# Check 'B' gear clears spindle ('A' is the meshing gear) see II and IV above.
def check_spindle_cleared(a,b):
    if (b + spindle_diameter) >= (spindle_teeth + a):
        return False
    return True

# Check 'C' or 'D' (whichever may be the case, see III and IV above) gear
# clears spindle.
def check_lead_cleared(a,b,c):
    if (a + leadscrew_diameter) >= (b + c):
        return False
    return True

# Check 'A' gear clears 'C' gear, see IV above.
def check_gear_cleared(a,b,c,d):
    if (a + c + gear_clearance) >= (b + d):
        return False
    return True

# Check a gear set (from the command line) and report on fit and pitch.
# Population is in order ABCDEF,pitch. Pitch is optional.
def check_gear_set(check_set, check_pitch=0, output_file='check_set_results'):
    logging.basicConfig(
        filename=output_file,
        level=logging.DEBUG,
        format='%(message)s',
        filemode='a' # use 'a' to append, 'w' to overwrite each time
    )
    count = 0
    fits = ""
    if not check_belt_cleared(check_set[1]):
        fits = fits + "\n\'A\' gear post fouls Spindle pulley."
    for i in check_set:
        if i == 'H' or i == 1: # TODO remove 1
            count += 1
    if count == 3: # I - three gears.
        pitch = spindle_teeth*leadscrew_pitch/check_set[5]
        if not check_centers_fit([check_set[1],check_set[3],check_set[3],check_set[5]]):
            fits = fits + "\nTotal center distance too large"
        if not check_reach_fit([check_set[1],check_set[1],check_set[3],check_set[3],check_set[5]]):
            fits = fits + "\n\'A\' gear doesn\'t reach Spindle."
    if count == 2: # II or III - four gears.
        if check_set[3] == 'H': # II - 'dogleg'.
            pitch = spindle_teeth*leadscrew_pitch/check_set[1]*check_set[2]/check_set[6]
            if not check_centers_fit([check_set[2],check_set[4],check_set[4],check_set[6]]):
                fits = fits + "\nTotal center distance too large"
            if not check_reach_fit([check_set[1],check_set[2],check_set[4],check_set[4],check_set[6]]):
                fits = fits + "\n\'A\' gear doesn\'t reach Spindle."
            if not check_spindle_cleared(check_set[1],check_set[2]):
                fits = fits + "\nB gear fouls spindle"
        else: # III - 'flash'.
            pitch = spindle_teeth*leadscrew_pitch/check_set[3]*check_set[4]/check_set[6]
            if not check_centers_fit([check_set[1],check_set[3],check_set[4],check_set[6]]):
                fits = fits + "\nTotal center distance too large"
            if not check_reach_fit([check_set[1],check_set[1],check_set[3],check_set[4],check_set[6]]):
                fits = fits + "\n\'A\' gear doesn\'t reach Spindle."
            if not check_spindle_cleared(check_set[1]*2+check_set[3],check_set[4]):
                fits = fits + "\nB gear fouls spindle"
            if not check_lead_cleared(check_set[3],check_set[4],check_set[6]):
                fits = fits + "\nC gear fouls leadscrew"
    if count == 1: # IV - five gears.
        pitch = spindle_teeth*leadscrew_pitch/check_set[1]*check_set[2]/check_set[4]*check_set[3]/check_set[5]
        if not check_centers_fit([check_set[2],check_set[4],check_set[3],check_set[5]]):
            fits = fits + "\nTotal center distance too large"
        if not check_reach_fit([check_set[1],check_set[2],check_set[4],check_set[3],check_set[5]]):
            fits = fits + "\n\'A\' gear doesn\'t reach Spindle."
        if not check_lead_cleared(check_set[4],check_set[3],check_set[5]):
            fits = fits + "\nD gear fouls leadscrew"
        if not check_gear_cleared(check_set[1],check_set[2],check_set[3],check_set[4]):
            fits = fits + "\nA and C gears interfere"
    pitch = convert(pitch)
    check_set[0] = pitch
    fstring = f"\n-- {label} ------------------"
    if check_pitch != 0:
            fstring = f"\n-- {check_pitch} {label} ------------------"
    if fits == "":
        fits = "Gears fit."
    print(fstring);
    print(set_pattern(check_set, check_pitch))
    print(fits)
    logger.info(fstring)
    logger.info(set_pattern(check_set, check_pitch))
    logger.info(fits)

# Pretty output of a gear set.
def set_pattern(p, target):
    # There is no target with a single gear check (CLI option -c) so:
    if target == 0:
        err_str = ""
    else:
        err = (p[0]-target)/target*100
        if imperial:
            err_str = f"  Error: {err:.3f}% or {10*err:.1f} Thou per Inch"
        else:
            err_str = f"  Error: {err:.3f}% or {err/100*target:.2f} mm per thread"
    pp =("        "+f"{p[1]}".rjust(5)+f"{p[2]}".rjust(5)+"\n"+
        f"{p[0]:.4f}".rjust(8)+f"{p[3]}".rjust(5)+f"{p[4]}".rjust(5)+
        err_str+"\n"+
        "        "+f"{p[5]}".rjust(5)+f"{p[6]}".rjust(5))
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
parser.add_argument('-g', '--gears', metavar=('84,72,60 ...'), type=str, help="Comma separated list of available gears.")
parser.add_argument('-p', '--pitches', metavar=('28,20,19 ...'), type=str, help="Comma separated list of feedrate(s) of interest.")
parser.add_argument('-u', '--unit', choices=['mm','tpi'], type=str, help="Pitch unit.")
parser.add_argument('-c', '--check', nargs='+', metavar=('60,40,H,80,H,70',  'target-pitch'), type=str, help="Check a gear set--given as a comma separated list of 6(!) gear positions A,B,C,D,E,F--for fit and resulting pitch. Target-pitch is optional, if specified, an error percentage is also calculated; you _must_ use 'H' for empty gear positions as per the example.")
parser.add_argument('-i', '--input', default='lathe_data', metavar=('file_name'), type=str, help="Data file name when not using the default \'lathe_data\'; provide full path if it\'s not located in the program directory.")
parser.add_argument('-e', '--example', nargs='?', const='lathe_data_example', metavar=('file_name'), type=str, help="Create an example lathe data file and exit. The file name is optional and defaults to \'gear_data_example\'.")
parser.add_argument('-o', '--output', metavar=('file_name'), type=str, help="Non-default output file name; defaults are set in the data file.")
parser.add_argument('-f', '--format', choices=['list','layout'], type=str, help="Output format, \'list\' lists ALL working sets in a simple format, \'layout\' only gives the best* sets in a pretty layout. (*see README)")
args = parser.parse_args()

# ------------------------------------------------------------------------------
# Process CLI input.

# Save unnecessary processing: Do we want an example lathe data file?
# Exits the program to allow the user to edit the file.
if args.example:
    write_data_file(args.example)
    sys.exit(0)

# Read the data file now so CLI arguments can override file arguments.
if args.input:
    data_file = args.input
else:
    data_file = 'lathe_data'
print(f'\nReading data input file \'{data_file}\'.')
data = read_data_file(data_file)
for r in data:
    r = r.replace(" ", "")
    i = r.find('=')
    name = r[0:i]
    value = r[i+1:]
    match name:
        case 'gears_available':
            gears_available = [int(v) for v in value.split(',')]
        case 'pitches':
            if value.find('.') == -1:
                pitches = [int(v) for v in value.split(',')]
            else:
                pitches = [float(v) for v in value.split(',')]
        case 'pitch_unit':
            pitch_unit = str(value)
        case 'spindle_teeth':
            spindle_teeth = float(value)
        case 'spindle_diameter':
            spindle_diameter = int(value)
        case 'leadscrew_pitch':
            if value.find('.') == -1:
                leadscrew_pitch = int(value)
            else: # This shouldn't happen...
                leadscrew_pitch = float(value)
        case 'leadscrew_unit':
            leadscrew_unit = str(value)
        case 'leadscrew_diameter':
            leadscrew_diameter = int(value)
        case 'max_centers':
            max_centers = int(value)
        case 'min_out_dim':
            min_out_dim = int(value)
        case 'gear_clearance':
            gear_clearance = int(value)
        case 'gears_output_file':
            gears_output = str(value)
        case 'output_format':
            output_format = str(value)
        case 'check_set_output_file':
            check_set_output = str(value)

# Command line arguments override any already given above or in the data file.
if args.gears:
    gears_available = [int(v) for v in args.gears.split(',')]
if args.pitches:
    if args.pitches.find('.') == -1:
        pitches = [int(v) for v in args.pitches.split(',')]
    else:
        pitches = [float(v) for v in args.pitches.split(',')]
if args.unit:
    pitch_unit = args.unit
if args.format:
    output_format = args.format

# For pretty layout output.
label = pitch_unit.upper()
imperial = label == 'TPI'

# Function alias to simplify code.
if pitch_unit == leadscrew_unit:
    convert = no_conversion
else:
    convert = conversion

# Are we checking a single gear set?
# These results are logged in _append_ mode
if args.check:
    length = len(args.check)
    check_pitch = 0
    check_gears = args.check[0].split(',')
    if not len(check_gears) == 6:
        raise ValueError("Set must have 6 positions, ABCDEF plus optional pitch!")
    if args.output:
        check_set_output = args.output
    if length == 2:
        check_pitch = float(args.check[1])
    check_set=[0] # Place holder for resulting pitch value.
    for i in check_gears:
        if i == 'H' or i == 1: # TODO remove 1?
            check_set = check_set + [int(i)]
        else:
            check_set = check_set + [int(i)]
    check_gear_set(check_set, check_pitch, check_set_output)
    sys.exit(0)

# Were we given a custom output file name?
if args.output:
    gears_output = args.output
# Configure the logger (which writes our results to the output file).
logging.basicConfig(
    filename=gears_output,
    level=logging.DEBUG,
    format='%(message)s',
    filemode='w' # use 'a' to append, 'w' to overwrite each time
)

#-------------------------------------------------------------------------------
# MAIN This is where the 'hard work' is done.

# Record the start time
start_time = time.perf_counter()

# Get some numbers.
all_sets=all_possible_sets(gears_available)
total_sets = len(all_sets)
perms=possible_permutations(len(gears_available))
# Just in case the user was being funny...
pitches.sort()

# Start output file.
logger.info('Lathe feed/thread cutting gear populations.\n')
logger.info(f'Target feedrates: {pitches}\n')
logger.info(f'Available gears: {gears_available}\n')

# Inform the user.
print(f'\nTarget feedrates: {pitches}')
print(f'\nAvailable gears: {gears_available}')
print(f"\nGiving {len(all_sets):,} combinations with {perms:,} permutations..")
print(f"\nChecking for fit; this may take some time.")

# TODO change 1 back to H
# Turn combinations into populations ('place gears on the lathe'),
# discarding any that don't fit.
fitting_sets=[]
counter=0
for s in all_sets:
    counter = counter + 1
    # The progress bar takes a string comment like "Processing", wich seems
    # bit obvious, so, an empty string here, but, fill your boots... ;-)
    print_progress_bar(counter, total_sets)
    # Gears are 'placed' on the lathe along the mesh-line,
    # in the sequence of the set, see 'p = [A, ...] comments below.
    # Since the _order_ of the gears changes the ratio, we also want each
    # possible permutation of each set.
    # Sets that fit are stored with effective pitch as the first element.
    for p in list(itertools.permutations(s)):
        if len(p) == 3:
            # Configuration I (line) p = [A,C,E]
            if (check_belt_cleared(p[0]) and
                check_centers_fit([p[0],p[1],p[1],p[2]]) and
                check_reach_fit([p[0],p[0],p[1],p[1],p[2]])):
                pitch = convert(spindle_teeth*leadscrew_pitch/p[2])
                std=statistics.stdev([p[0],p[1],p[2]])
                fitting_sets = fitting_sets + [[ pitch, p[0], 1, p[1], 1, p[2], 1, std]]
        if len(p) == 4:
            # Configuration II (dogleg) p = [A,B,D,E]
            if (check_belt_cleared(p[0]) and
                check_centers_fit([p[1],p[2],p[2],p[3]]) and
                check_reach_fit([p[0],p[1],p[2],p[2],p[3]]) and
                check_spindle_cleared(p[0],p[1])):
                pitch = convert(spindle_teeth*leadscrew_pitch/p[0]*p[1]/p[3])
                std=statistics.stdev([p[0],p[1],p[2],p[3]])
                fitting_sets = fitting_sets + [[ pitch, p[0], p[1], 1, p[2], 1, p[3], std]]
            # Configuration III (flash) p = [A,C,D,F]
            if (check_belt_cleared(p[0]) and
                check_centers_fit([p[0],p[1],p[2],p[3]]) and
                check_reach_fit([p[0],p[0],p[1],p[2],p[3]]) and
                check_spindle_cleared(p[0]*2+p[1],p[2]) and
                check_lead_cleared(p[1],p[2],p[3])):
                pitch = convert(spindle_teeth*leadscrew_pitch/p[1]*p[2]/p[3])
                std=statistics.stdev([p[0],p[1],p[2],p[3]])
                fitting_sets = fitting_sets + [[ pitch, p[0], 1, p[1], p[2], 1, p[3], std]]
        if len(p) == 5:
            # Configuration IV (questionmark) p = [A,B,D,C,E]
            if (check_belt_cleared(p[0]) and
                check_centers_fit([p[1],p[2],p[3],p[4]]) and
                check_reach_fit([p[0],p[1],p[2],p[3],p[4]]) and
                check_spindle_cleared(p[0],p[1]) and
                check_lead_cleared(p[2],p[3],p[4]) and
                check_gear_cleared(p[0],p[1],p[3],p[2])):
                pitch = convert(spindle_teeth*leadscrew_pitch/p[0]*p[1]/p[2]*p[3]/p[4])
                std=statistics.stdev([p[0],p[1],p[2],p[3],p[4]])
                fitting_sets = fitting_sets + [[ pitch, p[0], p[1], p[3], p[2], p[4], 1, std]]

# Sort by effective pitch, then by std. deviation descending.
# This results in the sets with the smallest spread (most 'similar' gears)
# being published in the 'pretty layout' format.
fitting_sets.sort(key=lambda x: (x[0],-x[7],x[1],x[2],x[3],x[4],x[5],x[6]))
# Because sets have empty spaces, there are 'permutations' with the same gear
# order, but with 'different order' of the empty spaces... This of course
# results in duplicates. Remove them:
fitting_sets = list(map(list,list(dict.fromkeys(map(tuple, fitting_sets)))))

# Grab the first target from the pitches-list.
target = pitches.pop(0)
total_fitting_sets=len(fitting_sets)

# More user info.
print (f"\n\nFound {total_fitting_sets} sets fitting the lathe.")
print (f"\nWith the nearest matches to the target pitches being:\n")

# Search all populations for closest fit to target pitches, and publish
# either the best (lowest std. dev. of gear sizes) perfect fit, or the
# nearest smaller and nearest bigger result.
zero_error_exists = False
if output_format == 'layout':
    for i in range(total_fitting_sets-1):
        p = fitting_sets[i]
        if p[0] == target and not zero_error_exists:
            # First (lowest std. dev.) perfect pitch.
            zero_error_exists = True
            print(f"-- {target} {label} --------------");
            print(set_pattern(p, target))
            print ("")
            logger.info(f"-- {target} {label} --------------");
            logger.info(set_pattern(p, target))
            logger.info("")
        if p[0] > target:
            if not zero_error_exists:
                # We found no perfect matches; publish the closest smaller and larger ones.
                if i >0:
                    # There is a previous (nearest smaller) option.
                    prev_p = fitting_sets[i-1]
                    print(set_pattern(fitting_sets[i-1],target))
                    logger.info(set_pattern(fitting_sets[i-1],target))
                # The current (nearest larger) option.
                print(f"-- {target} {label} --------------");
                print(set_pattern(p, target))
                print ("")
                logger.info(f"-- {target} {label} --------------");
                logger.info(set_pattern(p, target))
                logger.info("")
            # Reset zero error flag.
            zero_error_exists = False
            # TODO potentially, p CAN be (but _likely_ is not) the next target lowest STD DEV solution, if we don't grab that here, we're off to evaluate the NEXT set, which may NOT be the optimal set for the next target (which we're about to pop next) probably not an issue though...
            if pitches:
                # There are more target pitches to check
                target = pitches.pop(0)
            else :
                # We're done
                break
else:
    # See previous for-loop for explanatory comments.
    for i in range(total_fitting_sets-1):
        p = fitting_sets[i]
        if p[0] == target:
            zero_error_exists = True
            print(p)
            logger.info(p)
        if p[0] > target:
            if not zero_error_exists:
                if i >0:
                    prev_p = fitting_sets[i-1]
                    print(f"{prev_p}, {(target-prev_p[0])/target*100:.3f} % error.")
                    logger.info(f"{prev_p}, {(target-prev_p[0])/target*100:.3f} % error.")
                print(f"{p}, {(target-p[0])/target*100:.3f} % error.")
                logger.info(f"{p}, {(target-p[0])/target*100:.3f} % error.")
            zero_error_exists = False
            if pitches:
                target = pitches.pop(0)
            else :
                break

# For proper interpretation of 'smallest' and 'biggest' pitches. For TPI, big numbers mean small pitch and v.v.
if pitch_unit == 'tpi':
    big_and_small = f'Smallest feedrate:\n{set_pattern(fitting_sets[total_fitting_sets-1],0)}\n\nBiggest feedrate:\n{set_pattern(fitting_sets[0],0)}'
else:
    big_and_small = f'Smallest feedrate:\n{set_pattern(fitting_sets[0],0)}\n\nBiggest feedrate:\n{set_pattern(fitting_sets[total_fitting_sets-1],0)}'
# Publish in both places.
logger.info(big_and_small)
print(big_and_small)

# Record the end time and publish total runtime.
end_time = time.perf_counter()
seconds=end_time - start_time
logger.info(f"\nTotal execution time: {formatted_time(seconds, False)}.")
print(f"\nTotal execution time: {formatted_time(seconds, False)}.")

