#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

#   Copyright (C) 2021  Andrew Bauer
#   Copyright (C) 2014  Enno Rodegerdts

#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License along
#   with this program.  If not, see <https://www.gnu.org/licenses/>.

# Standard library imports
import os
import sys
import time
import datetime

# Local application imports
import tables
import suntables 
import config
import increments
from alma_skyfield import init_sf


def makePDF(args, fn, msg = ""):
    command = 'pdflatex {}'.format(args + fn + ".tex")
    if args == "":
        os.system(command)
        print("finished" + msg)
    else:
        returned_value = os.system(command)
        if returned_value != 0:
            if msg != "":
                print("ERROR detected while" + msg)
            else:
                print("!!   ERROR detected while creating PDF file   !!")
                print("!! Append '-v' or '-log' for more information !!")
        else:
            if msg != "":
                print("finished" + msg)
            else:
                print("finished creating PDF")
    return

def tidy_up(fn):
    if not keeptex: os.remove(fn + ".tex")
    if not keeplog:
        if os.path.isfile(fn + ".log"):
            os.remove(fn + ".log")
    if os.path.isfile(fn + ".aux"):
        os.remove(fn + ".aux")
    return


##Main##
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

try:
    arg = sys.argv[1]
except IndexError:
    arg = ""
if len(sys.argv) > 2 or not (arg == "" or arg == "-v" or arg == "-log" or arg == "-tex"):
    print("One optional command line parameter is permitted:")
    print(" python -m skyalmanac -v")
    print(" ... to send pdfTeX output to the terminal")
    print(" python -m skyalmanac -log")
    print(" ... to keep the log file")
    print(" python -m skyalmanac -tex")
    print(" ... to keep the tex file")
    sys.exit(0)

args = "" if arg == "-v" else "-interaction=batchmode -halt-on-error "
keeplog = True if arg == "-log" else False
keeptex = True if arg == "-tex" else False

d = datetime.datetime.utcnow().date()
first_day = datetime.date(d.year, d.month, d.day)

# if this code runs locally (not in Docker), the settings in config.py are used.
# if this code runs in Docker without use of an environment file, the settings in config.py apply.
# if this code runs in Docker with an environment file ("--env-file ./.env"), then its values apply.
ageERR = False
ephERR = False
if config.dockerized:
    docker_main = os.getcwd()
    spad = docker_main + "/astro-data/"
    config.pgsz = os.getenv('PGSZ', config.pgsz)
    config.moonimg = os.getenv('MOONIMG', str(config.moonimg))
    config.ephndx = os.getenv('EPHNDX', str(config.ephndx))
    if config.ephndx not in set(['0', '1', '2', '3', '4']):
        ephERR = True
    else:
        config.ephndx = int(config.ephndx)
    config.useIERS = os.getenv('USEIERS', str(config.useIERS))
    config.ageIERS = os.getenv('AGEIERS', str(config.ageIERS))
    if not str(config.ageIERS).isnumeric():
        ageERR = True
    else:
        config.ageIERS = int(config.ageIERS)
        if config.ageIERS <= 0:
            ageERR = True
    stdt = os.getenv('SDATE', 'None')
    if stdt != 'None':      # for testing a specific date
        try:
            first_day = datetime.date(int(stdt[0:4]), int(stdt[5:7]), int(stdt[8:10]))
        except:
            print("Invalid date format for SDATE in .env: {}".format(stdt))
            sys.exit(0)
        d = first_day
    err1 = "the Docker .env file"
    err2 = "for MOONIMG in the Docker .env file"
    err3 = "for USEIERS in the Docker .env file"
    err4 = "for AGEIERS in the Docker .env file"
else:
    #first_day = datetime.date(2023, 6, 24)	# for testing a specific date
    #d = first_day							# for testing a specific date
    spad = "./"
    if config.ephndx not in set([0, 1, 2, 3, 4]):
        ephERR = True
    config.moonimg = str(config.moonimg)
    config.useIERS = str(config.useIERS)
    err1 = "config.py"
    err2 = "for 'moonimg' in config.py"
    err3 = "for 'useIERS' in config.py"
    err4 = "for 'ageIERS' in config.py"

if ephERR:
    print("Error - Please choose a valid ephemeris in {}".format(err1))
    sys.exit(0)

if config.pgsz not in set(['A4', 'Letter']):
    print("Please choose a valid paper size in {}".format(err1))
    sys.exit(0)

if config.moonimg.lower() not in set(['true', 'false']):
    print("Please choose a boolean value {}".format(err2))
    sys.exit(0)

if config.useIERS.lower() not in set(['true', 'false']):
    print("Please choose a boolean value {}".format(err3))
    sys.exit(0)

if ageERR:
    print("Please choose a positive non-zero numeric value {}".format(err4))
    sys.exit(0)

sday = "{:02d}".format(d.day)       # sday = "%02d" % d.day
smth = "{:02d}".format(d.month)     # smth = "%02d" % d.month
syr  = "{}".format(d.year)          # syr  = "%s" % d.year
symd = syr + smth + sday
sdmy = sday + "." + smth + "." + syr
yrmin = config.ephemeris[config.ephndx][1]
yrmax = config.ephemeris[config.ephndx][2]
config.moonimg = (config.moonimg.lower() == 'true') # to boolean
config.useIERS = (config.useIERS.lower() == 'true') # to boolean
f_prefix = config.docker_prefix
f_postfix = config.docker_postfix

ts = init_sf(spad)     # in alma_skyfield

s = input("""\nWhat do you want to create?:\n
    1   Nautical Almanac   (for a year)
    2   Sun tables only    (for a year)
    3   Nautical almanac   -  6 days from today
    4   Sun tables only    - 30 days from today
    5   "Increments and Corrections" tables (static data)
""")

if s in set(['1', '2', '3', '4', '5']):
    if int(s) < 3:
        print("Please enter the desired year")
        years = input("  as yyyy ... or the FIRST and LAST year as yyyy-yyyy\n")
        if len(years)== 4:
            yearfr = years
            yearto = years
        elif len(years) == 9 and years[4] == '-':
            yearfr = years[0:4]
            yearto = years[5:9]
        else:
            print("Error! Invalid format")
            sys.exit(0)
        
        if str(yearfr).isnumeric():
            if yrmin <= int(yearfr) <= yrmax:
                first_day = datetime.date(int(yearfr), 1, 1)
            else:
                print("!! Please pick a year between {} and {} !!".format(yrmin,yrmax))
                sys.exit(0)
        else:
            print("Error! First year is not numeric")
            sys.exit(0)

        if str(yearto).isnumeric():
            if yrmin <= int(yearto) <= yrmax:
                first_day_to = datetime.date(int(yearto), 1, 1)
            else:
                print("!! Please pick a year between {} and {} !!".format(yrmin,yrmax))
                sys.exit(0)
            if int(yearto) < int(yearfr):
                print("Error! The LAST year must be later than the FIRST year")
                sys.exit(0)
        else:
            print("Error! Last year is not numeric")
            sys.exit(0)

    if s != '5':
        tsin = input("""What table style is required?:\n
        t   Traditional
        m   Modern
""")
        ff = '_'
        DecFmt = ''
        config.tbls = tsin[0:1]	# table style
        config.decf = tsin[1:2]	# Declination format
        if config.tbls != 'm':
            config.tbls = ''		# anything other than 'm' is traditional
            ff = ''
        if config.decf != '+':		# Positive/Negative Declinations
            config.decf = ''		# USNO format for Declination
        else:
            DecFmt = '[old]'

    if s == '1':        # Nautical Almanac (for a year)
        print("Be patient - this may take a while.")
##        config.initLOG()		# initialize log file
        for yearint in range(int(yearfr),int(yearto)+1):
            start = time.time()
            year = "{:4d}".format(yearint)  # year = "%4d" %yearint
            msg = "\nCreating the nautical almanac for the year {}".format(year)
            print(msg)
##            config.writeLOG(msg)
            first_day = datetime.date(yearint, 1, 1)
            ff = "tradna_" if config.tbls != 'm' else "modna_"
            fn = "{}{}".format(ff,year+DecFmt)
            outfile = open(f_prefix + fn + ".tex", mode="w", encoding="utf8")
            outfile.write(tables.almanac(first_day,122))
            outfile.close()
            stop = time.time()
            msg = "execution time = {:0.2f} seconds".format(stop-start) # msg = "execution time = %0.2f seconds" %(stop-start)
            print(msg)
##            config.writeLOG("\n\n" + msg + "\n")
            print()
            if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
            makePDF(args, fn, " creating nautical almanac for {}".format(year))
            tidy_up(fn)
            if config.dockerized: os.chdir(docker_main)     # reset working folder to code folder
##        config.closeLOG()     # close log after the for-loop

    elif s == '2':      # Sun Tables (for a year)
        for yearint in range(int(yearfr),int(yearto)+1):
            year = "{:4d}".format(yearint)  # year = "%4d" %yearint
            msg = "\nCreating the sun tables for the year {}\n".format(year)
            print(msg)
            first_day = datetime.date(yearint, 1, 1)
            ff = "tradst_" if config.tbls != 'm' else "modst_"
            fn = "{}{}".format(ff,year+DecFmt)
            outfile = open(f_prefix + fn + ".tex", mode="w", encoding="utf8")
            outfile.write(suntables.almanac(first_day,25))
            outfile.close()
            if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
            makePDF(args, fn, " creating sun tables for {}".format(year))
            tidy_up(fn)
            if config.dockerized: os.chdir(docker_main)     # reset working folder to code folder

    elif s == '3':      # Nautical almanac   -  6 days from today
##        config.initLOG()		# initialize log file
        start = time.time()
        msg = "\nCreating nautical almanac tables - from {}\n".format(sdmy)
        print(msg)
        ff = "tradna_" if config.tbls != 'm' else "modna_"
        fn = "{}{}".format(ff,symd+DecFmt)
        outfile = open(f_prefix + fn + ".tex", mode="w", encoding="utf8")
        outfile.write(tables.almanac(first_day,2))
        outfile.close()
        stop = time.time()
        msg = "execution time = {:0.2f} seconds".format(stop-start) # msg = "execution time = %0.2f seconds" %(stop-start)
        print(msg)
##        config.writeLOG('\n\n' + msg)
##        config.closeLOG()
        print()
        if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
        makePDF(args, fn)
        tidy_up(fn)

    elif s == '4':      # Sun tables only    - 30 days from today
        msg = "\nCreating the sun tables - from {}\n".format(sdmy)
        print(msg)
        ff = "tradst_" if config.tbls != 'm' else "modst_"
        fn = "{}{}".format(ff,symd+DecFmt)
        outfile = open(f_prefix + fn + ".tex", mode="w", encoding="utf8")
        outfile.write(suntables.almanac(first_day,2))
        outfile.close()
        if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
        makePDF(args, fn)
        tidy_up(fn)

    elif s == '5':
        msg = "\nCreating the Increments and Corrections tables\n"
        print(msg)
        fn = "inc"
        outfile = open(f_prefix + fn + ".tex", mode="w", encoding="utf8")
        outfile.write(increments.makelatex())
        outfile.close()
        if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
        makePDF(args, fn)
        tidy_up(fn)

else:
    print("Error! Choose 1, 2, 3, 4 or 5")
