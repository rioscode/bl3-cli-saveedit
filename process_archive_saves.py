#!/usr/bin/env python
# vim: set expandtab tabstop=4 shiftwidth=4:

# Copyright (c) 2020 CJ Kucera (cj@apocalyptech.com)
# 
# This software is provided 'as-is', without any express or implied warranty.
# In no event will the authors be held liable for any damages arising from
# the use of this software.
# 
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
# 
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software in a
#    product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 
# 3. This notice may not be removed or altered from any source distribution.

import os
import sys
import argparse
import bl3save
from bl3save.bl3save import BL3Save

# Set up args
parser = argparse.ArgumentParser(description='Process savegame archive saves')

group = parser.add_mutually_exclusive_group()

group.add_argument('-f', '--filename',
        type=str,
        help='Specific filename to process')

group.add_argument('-d', '--directory',
        type=str,
        help='Directory to process (defaults to "step")')

parser.add_argument('-i', '--info',
        type=str,
        help='HTML File to write output summary to')

parser.add_argument('-o', '--output',
        type=str,
        required=True,
        help='Output filename/directory to use')

parser.add_argument('-c', '--clobber',
        action='store_true',
        help='Clobber (overwrite) files without asking')

# Parse args
args = parser.parse_args()
if not args.filename and not args.directory:
    args.directory = 'step'

# Construct a list of filenames
targets = []
if args.directory:
    for filename in sorted(os.listdir(args.directory)):
        if '.sav' in filename:
            targets.append(os.path.join(args.directory, filename))
else:
    targets.append(args.filename)

# If we're a directory, make sure it exists
if not os.path.exists(args.output):
    os.mkdir(args.output)

# If we've been given an info file, check to see if it exists
if args.info and not args.clobber and os.path.exists(args.info):
    sys.stdout.write('WARNING: {} already exists.  Overwrite [y/N/a/q]? '.format(args.info))
    sys.stdout.flush()
    response = sys.stdin.readline().strip().lower()
    if response == 'y':
        pass
    elif response == 'n':
        args.info = None
    elif response == 'a':
        args.clobber = True
    elif response == 'q':
        sys.exit(1)
    else:
        # Default to No
        args.info = None

# Open the info file, if we have one.
if args.info:
    idf = open(args.info, 'w')

# Now loop through and process
files_written = 0
for filename in targets:

    # Figure out an output filename
    if args.filename:
        base_filename  = args.filename
        output_filename = args.output
    else:
        base_filename = filename.split('/')[-1]
        output_filename = os.path.join(args.output, base_filename)

    # See if the path already exists
    if os.path.exists(output_filename) and not args.clobber:
        sys.stdout.write('WARNING: {} already exists.  Overwrite [y/N/a/q]? '.format(output_filename))
        sys.stdout.flush()
        response = sys.stdin.readline().strip().lower()
        if response == 'y':
            pass
        elif response == 'n':
            continue
        elif response == 'a':
            args.clobber = True
        elif response == 'q':
            break
        else:
            # Default to No
            response = 'n'

    # Load!
    print('Processing: {}'.format(filename))
    save = BL3Save(filename)

    # Write to our info file, if we have it
    if args.info:

        # Write out the row
        print('<tr class="row{}">'.format(files_written % 2), file=idf)
        print('<td class="filename"><a href="bl3/{}">{}</a></td>'.format(base_filename, base_filename), file=idf)
        print('<td class="in_map">{}</td>'.format(save.get_pt_last_map(0, True)), file=idf)
        missions = save.get_pt_active_mission_list(0, True)
        if len(missions) == 0:
            print('<td class="empty_missions">&nbsp;</td>', file=idf)
        else:
            print('<td class="active_missions">', file=idf)
            print('<ul>', file=idf)
            for mission in sorted(missions):
                print('<li>{}</li>'.format(mission), file=idf)
            print('</ul>', file=idf)
            print('</td>', file=idf)
        print('</tr>', file=idf)

    # Max XP
    save.set_level(bl3save.max_level)

    # Max SDUs
    save.set_max_sdus()

    # Max Ammo
    save.set_max_ammo()

    # Unlock PT2
    # (In the original runthrough which I've already checked in, I'd accidentally set
    # this to 2.  Whoops!  Doesn't seem to matter, so whatever.)
    save.set_playthroughs_completed(1)

    # Copy mission/FT/location/mayhem status from PT1 to PT2
    save.copy_playthrough_data()

    # Inventory - force our testing gear
    # Gear data just taken from my modtest char.  Level 53.
    craders = b'\x03\xf9\x1e\xaa\x0f\xf21\xe2\xc0\x89\xd8\xb0O\x9f\xdbY\x0c*\x1bs\xae\xc5\xe1!\x0c~\x0bd\x03\xd6\x83V\xb6\x1cm\xa2\x99\xa0\x90'
    transformer = b'\x036"\x86"\xf8\xe8\xdae\x1ac\xe6\xf2,7;W\xea\xc2g\xfd\x93'
    save.overwrite_item_in_slot(bl3save.WEAPON1, craders)
    save.overwrite_item_in_slot(bl3save.SHIELD, transformer)

    # Write out
    save.save_to(output_filename)
    files_written += 1

if args.filename:
    if files_written == 1:
        print('Done!  Wrote to {}'.format(args.output))
else:
    if files_written == 1:
        plural = ''
    else:
        plural = 's'
    print('Done!  Wrote {} file{} to {}'.format(files_written, plural, args.output))

if args.info:
    print('Wrote HTML summary to {}'.format(args.info))
    idf.close()
