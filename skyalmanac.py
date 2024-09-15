#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

#   Copyright (C) 2024  Andrew Bauer
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

###### Standard library imports ######
import os
import sys, site
import time
from sysconfig import get_path  # new in python 3.2
from datetime import date, datetime, timedelta
from multiprocessing import cpu_count

###### Local application imports ######
import config
# !! execute the next 3 lines before importing from nautical/eventtables !!
config.WINpf = True if sys.platform.startswith('win') else False
config.LINUXpf = True if sys.platform.startswith('linux') else False
config.MACOSpf = True if sys.platform == 'darwin' else False
config.FANCYhd = False  # default for TeX Live <= "TeX Live 2019/Debian"
config.CPUcores = cpu_count()
# NOTE: Multiprocessing on Windows using 'spawn' requires all variables modified
#       and stored in config.py to be re-calculated for every spawned process!
# NOTE: multiprocessing is supported in modules: nautical, eventtables
#       Hence these can only be imported *after* we know if '-sp' is specified
from alma_skyfield import init_sf
from ld_skyfield import ld_init_sf
#from nautical import almanac            # multiprocessing supported
from suntables import sunalmanac
#from eventtables import makeEVtables    # multiprocessing supported
from ld_tables import makeLDtables
from ld_charts import makeLDcharts
from increments import makelatex

#   Some modules in Skyalmanac have been ported from the original source code ...
#   this may explain why sections of code are not consolidated. Furthermore two
#   separate Skyfield modules are used with obvious repetition of code. This
#   simplifies porting from the original code for development and testing.

def toUnix(fn):
    # replacing parentheses with square brackets in Ubuntu works, but is not required.
    if squarebr and (config.LINUXpf or config.MACOSpf):
        fn = fn.replace("(","[").replace(")","]")
    return fn

def toUNIX(fn):
    if not squarebr and (config.LINUXpf or config.MACOSpf):
        # either of the following commands work in Ubuntu:
        if True:
            fn = "'" + fn + "'"
        else:
            fn = fn.replace("(","\(").replace(")","\)")
    return fn

def deletePDF(filename):
    if os.path.exists(filename + ".pdf"):
        try:
            os.remove(filename + ".pdf")
        except PermissionError:
            print("ERROR: please close '{}' so it can be re-created".format(filename + ".pdf"))
            sys.exit(0)
    if os.path.exists(filename + ".tex"):
        os.remove(filename + ".tex")

def makePDF(pdfcmd, fn, msg = ""):
    command = r'pdflatex {}'.format(pdfcmd + toUNIX(fn + ".tex"))
    print()     # blank line before "This is pdfTex, Version 3.141592653...
    if pdfcmd == "":
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
                print("finished creating '{}'".format(fn + ".pdf"))
    return

def tidy_up(fn):
    if not keeptex: os.remove(fn + ".tex")
    if not keeplog:
        if os.path.isfile(fn + ".log"):
            os.remove(fn + ".log")
    if os.path.isfile(fn + ".aux"):
        os.remove(fn + ".aux")
    return

def check_mth(mm):
    if not 1 <= int(mm) <= 12:
        print("ERROR: Enter month between 01 and 12")
        sys.exit(0)

def check_exists(fn):
    # check a required file exist to avoid a more obscure error in pdfTeX if "-v" not used...
    if not os.path.exists(fn):
        print("Error - missing file: {}".format(fn))
        sys.exit(0)

def check_date(year, month, day):
    yy = int(year)
    mm = int(month)
    day_count_for_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if yy%4==0 and (yy%100 != 0 or yy%400==0):
        day_count_for_month[2] = 29
    if not (1 <= mm <= 12 and 1 <= int(day) <= day_count_for_month[mm]):
        print("ERROR: Enter a valid date")
        sys.exit(0)

def check_years(yearfr, yearto):
    global yrmin, yrmax

    if str(yearfr).isnumeric():
        if yrmin <= int(yearfr) <= yrmax:
            first_day = date(int(yearfr), 1, 1)
        else:
            print("!! Please pick a year between {} and {} !!".format(yrmin,yrmax))
            sys.exit(0)
    else:
        print("Error! First year is not numeric")
        sys.exit(0)

    if str(yearto).isnumeric():
        if yrmin <= int(yearto) <= yrmax:
            first_day_to = date(int(yearto), 1, 1)
        else:
            print("!! Please pick a year between {} and {} !!".format(yrmin,yrmax))
            sys.exit(0)
        if int(yearto) < int(yearfr):
            print("Error! The LAST year must be later than the FIRST year")
            sys.exit(0)
    else:
        print("Error! Last year is not numeric")
        sys.exit(0)

def timer_start():
    # initialize these counts before processing the next year (Almanac or Event Tables)
    config.stopwatch  = 0.0     # 00000
    config.stopwatch2 = 0.0     # 00000
    config.moonDaysCount = 0
    config.moonDataSeeks = 0
    config.moonDataFound = 0
    config.moonHorizonSeeks = 0
    config.moonHorizonFound = 0
    return time.time()

def timer_end(start, x = 0):
    stop = time.time()
    #print("start = {}".format(time.localtime(start)))
    #print("stop  = {}".format(time.localtime(stop)))
    msg = "execution time = {:0.2f} seconds".format(stop-start)
    if x < 0:
        msg += "\n"     # newline after "execution time = ..."
        x = abs(x)
    print(msg)
    if config.logfileopen: config.writeLOG("\n\n" + msg)
    if x == 0: return

    pct = 100 * config.stopwatch/(stop-start)
    msg4 = " ({:0.1f}%)".format(pct) if not config.MULTIpr else ""
    msg2 = "stopwatch      = {:0.2f} seconds".format(config.stopwatch) + msg4
    print(msg2)                 # 00000
    if config.logfileopen: config.writeLOG(msg2 + "\n")
    msg3 = "(stopwatch = time spent getting moonrise and/or moonset times)"
    #if x == 2: msg3 += "\n"
    if config.logfileopen: config.writeLOG(msg3 + "\n")
    print(msg3)                 # 00000

    if x == 1: return   # following is not required for Event Time tables
    msg5 = "stopwatch2     = {:0.2f} seconds".format(config.stopwatch2)
    print(msg5)                 # 00000
    msg6 = "(stopwatch2 = time spent searching if moon above/below horizon)"
    if x == 2: msg6 += "\n"
    print(msg6)
    return

def search_stats():
    if config.MULTIpr:
        msg4 = "Moonrise/moonset time seeks  = {}".format(config.moonDataSeeks)
        print(msg4)
        msg5 = "Above/below horizon searches = {}".format(config.moonHorizonSeeks)
        print(msg5)
    else:
        msg4 = "Moonrise/moonset times found in transient store = {} of {}".format(config.moonDataFound, config.moonDataSeeks)
        print(msg4)
        msg5 = "Moon continuously above/below horizon state found in transient store = {} of {}".format(config.moonHorizonFound, config.moonHorizonSeeks)
        print(msg5)
    return

def checkCoreCount():       # only called when config.MULTIpr == True
    if not (config.WINpf or config.LINUXpf or config.MACOSpf):
        print("Unsupported OS for multi-processing.")
        sys.exit(0)
    if not sys.version_info.major > 3:
        if not (sys.version_info.major == 3 and sys.version_info.minor >= 4):
            print("Python 3.4 or higher is required for multi-processing.")
            sys.exit(0)
    if config.CPUcores == 1:
        config.MULTIpr = False
        print("\nERROR: 2 logical processors minimum are required for parallel processessing")
        print("       defaulting to single processessing")
    if config.CPUcores < 12 or (config.WINpf and config.CPUcores < 8):
        print("\nNOTE: only {} logical processors are available for parallel processessing".format(config.CPUcores))


###### Main Program ######

if __name__ == '__main__':      # required for Windows multiprocessing compatibility
    if sys.version_info[0] < 3:
        print("This runs only with Python 3")
        sys.exit(0)

    # check if TeX Live is compatible with the 'fancyhdr' package...
    process = os.popen("tex --version")
    returned_value = process.read()
    process.close()
    if returned_value == "":
        print("- - - Neither TeX Live nor MiKTeX is installed - - -")
        sys.exit(0)
    pos1 = returned_value.find("(") 
    pos2 = returned_value.find(")")
    if pos1 != -1 and pos2 != -1:
        texver = returned_value[pos1+1:pos2]
        # e.g. "TeX Live 2019/Debian", "TeX Live 2022/dev/Debian", "MiKTeX 22.7.30"
        if texver[:8] == "TeX Live":
            yrtxt = texver[9:13]
            if yrtxt.isnumeric():
                yr = int(yrtxt)
                if yr >= 2020:
                    config.FANCYhd = True  # TeX Live can handle the 'fancyhdr' package
#                if yr < 2020:
#                    print("TeX version = '" + texver + "'")
#                    print("Upgrade TeX Live to 'TeX Live 2020' at least")
#                    sys.exit(0)
        else:
            config.FANCYhd = True  # assume MiKTeX can handle the 'fancyhdr' package

    # command line arguments...
    validargs = ['-v', '-q', '-log', '-tex', '-sky', '-old', '-a4', '-let', '-nao', '-dtr', '-dpo', '-sbr', '-sp', '-nmg', '-d1', '-d2', '-d3', '-d4']
    # (the 4 dummy arguments d1 d2 d3 d4 are specified in 'dockerfile')
    for i in list(range(1, len(sys.argv))):
        if sys.argv[i] not in validargs:
            print("Invalid argument: {}".format(sys.argv[i]))
            print("\nValid command line arguments are:")
            print(" -v   ... 'verbose': to send pdfTeX output to the terminal")
            print(" -q   ... quiet mode for LD charts")
            print(" -log ... to keep the log file")
            print(" -tex ... to keep the tex file")
            print(" -sky ... stars only in LD charts")
            print(" -old ... old formatting without the 'fancyhdr' package")
            print(" -a4  ... A4 papersize")
            print(" -let ... Letter papersize")
            print(" -nao ... HMNAO style hourly Moon d-values")
            print(" -dtr ... 'difference-then-round' style hourly Moon d-values")
            print(" -dpo ... data pages only")
            print(" -sbr ... square brackets in Unix filenames")
            print(" -sp  ... execute in single-processing mode (slower)")
            sys.exit(0)

    # NOTE: pdfTeX 3.14159265-2.6-1.40.21 (TeX Live 2020/Debian), as used in the Docker
    #       Image, does not have the options "-quiet" or "-verbose".
    listarg = "" if "-v" in set(sys.argv[1:]) else "-interaction=batchmode -halt-on-error "
    keeplog = True if "-log" in set(sys.argv[1:]) else False
    keeptex = True if "-tex" in set(sys.argv[1:]) else False
    quietmode = True if "-q" in set(sys.argv[1:]) else False
    onlystars = True if "-sky" in set(sys.argv[1:]) else False
    squarebr = True if "-sbr" in set(sys.argv[1:]) else False
    #
    # !! CHANGES TO VARIABLES IN config.py ARE NOT MAINTAINED WHEN MULTIPROCESSING !!
    #
    if "-nmg" in set(sys.argv[1:]): config.moonimg = False  # only for debugging
    config.DPonly = True if "-dpo" in set(sys.argv[1:]) else False
    if "-old" in set(sys.argv[1:]): config.FANCYhd = False  # don't use the 'fancyhdr' package

    if "-sp" in set(sys.argv[1:]):
        config.MULTIpr = False

    # NOTE: multiprocessing is supported in modules: nautical, eventtables
    #       Hence these can only be imported *after* we know if '-sp' is specified
    from nautical import almanac            # multiprocessing supported
    from eventtables import makeEVtables    # multiprocessing supported

    if not("-a4" in set(sys.argv[1:]) and "-let" in set(sys.argv[1:])):
        if "-a4" in set(sys.argv[1:]): config.pgsz = "A4"
        if "-let" in set(sys.argv[1:]): config.pgsz = "Letter"

    if not("-nao" in set(sys.argv[1:]) and "-dtr" in set(sys.argv[1:])):
        if "-nao" in set(sys.argv[1:]): config.d_valNA = True
        if "-dtr" in set(sys.argv[1:]): config.d_valNA = False

    d = datetime.utcnow().date()
    first_day = date(d.year, d.month, d.day)
    yy = "%s" % d.year

    # if this code runs locally (not in Docker), the settings in config.py are used.
    # if this code runs in Docker without use of an environment file, the settings in config.py apply.
    # if this code runs in Docker with an environment file ("--env-file ./.env"), then its values apply.
    ageERR = False
    ephERR = False
    if config.dockerized:
        docker_main = os.getcwd()
        spad = docker_main + "/astro-data/" # path to bsp/all/dat in the Docker Image
        spdf = docker_main + "/"            # path to pdf/png/jpg in the Docker Image
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
        err1 = "the Docker .env file"
        err2 = "for MOONIMG in the Docker .env file"
        err3 = "for USEIERS in the Docker .env file"
        err4 = "for AGEIERS in the Docker .env file"
    else:
        spad = spdf = "./"   # path when executing the GitHub files in a folder
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

    global yrmin, yrmax
    yrmin = config.ephemeris[config.ephndx][1]
    yrmax = config.ephemeris[config.ephndx][2]
    config.moonimg = (config.moonimg.lower() == 'true') # to boolean
    config.useIERS = (config.useIERS.lower() == 'true') # to boolean
    f_prefix = config.docker_prefix
    f_postfix = config.docker_postfix

    # ------------ process user input ------------

    s = input("""\n  What do you want to create?:\n
    1   Nautical Almanac      (for a day/month/year)
    2   Sun tables only       (for a day/month/year)
    3   Event Time tables     (for a day/month/year)
    4   Lunar Distance tables (for a day/month/year)
    5   Lunar Distance charts (for a day/month)
    6   "Increments and Corrections" tables (static data)
""")

    if s in set(['1', '3', '4']): dnum = 6
    elif s == '2': dnum = 30
    else: dnum = 0
    smalltxt = " (or 'x' for a brief sample)" if dnum > 0 else ""
    smallmsg = "\n    - or 'x' for {} days from today".format(dnum) if dnum > 0 else ""

    if s in set(['1', '2', '3', '4', '5', '6']):
        if int(s) < 5:
            daystoprocess = 0
            ss = input("""  Enter as numeric digits{}:\n
    - starting date as 'DDMMYYYY'
    - or just 'YYYY' (for a whole year)
    - or 'YYYY-YYYY' (for first and last year)
    - or just 'MM' (01 - 12) for the current or a future month
    - or '-MM' for a previous month (e.g. '-02' is last February){}
    - nothing for the current day
""".format(smalltxt,smallmsg))

            sErr = False    # syntax error
            entireMth = False
            entireYr  = False

            if len(ss) <= 1:
                daystoprocess = 1
                if d.year > yrmax:
                    print("!! Only years up to {} are valid!!".format(yrmax))
                    sys.exit(0)
                if len(ss) == 1:
                    daystoprocess = dnum
                    if dnum == 0: sErr = True
                    if ss.lower() != 'x': sErr = True
                if sErr:
                    print("ERROR: Incorrect data or format")
                    sys.exit(0)

            else:
                if len(ss) not in [2,3,4,8,9]: sErr = True
                if len(ss) == 3:
                    if ss[0] != '-': sErr = True
                    if not ss[1:].isnumeric(): sErr = True
                elif len(ss) == 9:
                    if ss[4] != '-': sErr = True
                    if not (ss[:4].isnumeric() and ss[5:].isnumeric()): sErr = True
                elif not ss.isnumeric(): sErr = True

                if sErr:
                    print("ERROR: Incorrect data or format")
                    sys.exit(0)

                if len(ss) == 2:
                    dd = "01"
                    mm = ss[0:2]
                    check_mth(mm)
                    if int(mm) < d.month: yy = str(d.year + 1)
                elif len(ss) == 3:
                    dd = "01"
                    mm = ss[1:3]
                    check_mth(mm)
                    if int(mm) >= d.month: yy = str(d.year - 1)
                elif len(ss) == 4:
                    entireYr = True
                    dd = "01"
                    mm = "01"
                    yy = ss
                    yearfr = ss
                    yearto = ss
                    check_years(yearfr, yearto)
                elif len(ss) == 9 and ss[4] == '-':
                    entireYr = True
                    dd = "01"
                    mm = "01"
                    yy = ss[0:4]
                    yearfr = ss[0:4]
                    yearto = ss[5:]
                    check_years(yearfr, yearto)
                elif len(ss) == 8:
                    dd = ss[:2]
                    mm = ss[2:4]
                    check_mth(mm)
                    yy = ss[4:]
                    check_date(yy,mm,dd)
                
                first_day = date(int(yy), int(mm), int(dd))
                d = first_day

                if len(ss) in [2,3]:    # process entire month
                    entireMth = True
                    daystoprocess = (d.replace(month = d.month%12 + 1, day = 1)-timedelta(days=1)).day

                if not entireYr and not entireMth and daystoprocess == 0:
                    daystoprocess = 1       # default
                    nn = input("""  Enter number of days to process from starting date:
""")
                    if len(nn) > 0:
                        if not nn.isnumeric():
                            print("ERROR: Not a number")
                            sys.exit(0)
                        daystoprocess = int(nn)
                        if daystoprocess > 300:
                            print("ERROR: 'Days to process' not <= 300")
                            sys.exit(0)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        elif int(s) == 5:   # for Lunar Distance charts only
#   Due to the lengthy calculations LD charts for a whole year is not supported.
            daystoprocess = 0
            ss = input("""
  Enter as numeric digits:
    - starting date as 'DDMMYYYY'
    - or just 'DDMM' (YYYY = current year)
    - or just 'MM' (01 - 12) for the current or a future month
    - or '-MM' for a previous month (e.g. '-02' is last February)
    - nothing for the current day
""")
            sErr = False    # syntax error
            entireMth = False
            entireYr  = False

            if len(ss) == 0:
                daystoprocess = 1
                if d.year > yrmax:
                    print("!! Only years up to {} are valid!!".format(yrmax))
                    sys.exit(0)
            else:
                if len(ss) not in [2,3,4,8]: sErr = True
                if len(ss) == 3 and ss[0] != '-': sErr = True
                if len(ss) == 3:
                    if not ss[1:].isnumeric(): sErr = True
                elif not ss.isnumeric(): sErr = True
                if sErr:
                    print("ERROR: Enter numeric digits in the correct format")
                    sys.exit(0)
                if len(ss) == 2:
                    dd = "01"
                    mm = ss[0:2]
                    if int(mm) < d.month: yy = str(d.year + 1)
                if len(ss) == 3:
                    dd = "01"
                    mm = ss[1:3]
                    if int(mm) >= d.month: yy = str(d.year - 1)
                elif len(ss) >= 4:
                    dd = ss[0:2]
                    mm = ss[2:4]
                if len(ss) == 8: yy = ss[4:]
                check_mth(mm)
                check_date(yy,mm,dd)

                if not (yrmin <= int(yy) <= yrmax):
                    print("!! Please pick a year between {} and {} !!".format(yrmin,yrmax))
                    sys.exit(0)

                first_day = date(int(yy), int(mm), int(dd))
                d = first_day

                if len(ss) in [2,3]:     # process entire month
                    entireMth = True
                    daystoprocess = (d.replace(month = d.month%12 + 1, day = 1)-timedelta(days=1)).day

                if daystoprocess == 0:
                    daystoprocess = 1       # default
                    nn = input("""  Enter number of days to process from starting date:
""")
                    if len(nn) > 0:
                        if not nn.isnumeric():
                            print("ERROR: Not a number")
                            sys.exit(0)
                        daystoprocess = int(nn)
                        if daystoprocess > 50:
                            print("ERROR: 'Days to process' not <= 50")
                            sys.exit(0)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        if s in set(['1', '2']):
            tsin = input("""  What table style is required?:\n
    t   Traditional
    m   Modern
""")
            ff = '_'
            DecFmt = ''
            config.tbls = tsin[0:1]	# table style
            config.decf = tsin[1:2]	# Declination format ('+' or nothing)
            if config.tbls != 'm':
                config.tbls = ''		# anything other than 'm' is traditional
                ff = ''
            if config.decf != '+':		# Positive/Negative Declinations
                config.decf = ''		# USNO format for Declination
            else:
                DecFmt = '[old]'

        sday = "{:02d}".format(d.day)
        smth = "{:02d}".format(d.month)
        syr  = "{}".format(d.year)
        symd = syr + smth + sday
        sdmy = sday + "." + smth + "." + syr

        if s in set(['4', '5']):
            strat = config.defaultLDstrategy
            if strat == '':
                strat = input("""  Select a strategy for choosing celestial bodies:\n
    A   objects closest to the Moon
    B   with highest hourly LD delta
    C   with brightest navigational stars
""")

            strat = strat.upper()
            if len(strat) == 0:
                strat = 'B'        # pick a default
            if not strat in ["A", "B", "C"]:
                print("Error! Invalid selection")
                sys.exit(0)

# ------------ create the desired tables/charts ------------

        if int(s) <= 3:
            ts = init_sf(spad)      # in alma_skyfield (almanac-based)
        elif int(s) in set([4, 5]):
            ts = ld_init_sf(spad)   # in ld_skyfield ('Lunar Distance'-based)
        papersize = config.pgsz

        if s == '1' and entireYr:        # Nautical Almanac (for a year/years)
            check_exists(spdf + "A4chart0-180_P.pdf")
            check_exists(spdf + "A4chart180-360_P.pdf")
            print("Take a break - this computer needs some time for cosmic meditation.")
    ##        config.initLOG()		# initialize log file
            for yearint in range(int(yearfr),int(yearto)+1):
                if config.MULTIpr: checkCoreCount()
                start = timer_start()
                config.moonDataSeeks = 0
                config.moonDataFound = 0
                config.moonHorizonSeeks = 0
                config.moonHorizonFound = 0
                year = "{:4d}".format(yearint)  # year = "%4d" %yearint
                msg = "\nCreating the nautical almanac for the year {}".format(year)
                print(msg)
    ##            config.writeLOG(msg)
                first_day = date(yearint, 1, 1)
                ff = "NAtrad" if config.tbls != 'm' else "NAmod"
                fn = toUnix("{}({})_{}".format(ff,papersize,year+DecFmt))
                deletePDF(f_prefix + fn)
                # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                outfile = open(f_prefix + fn + ".tex", mode="w", encoding="utf8")
                outfile.write(almanac(first_day,0,ts))
                outfile.close()
                # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                timer_end(start, 1)
                search_stats()
                if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
                makePDF(listarg, fn)
                tidy_up(fn)
                if config.dockerized: os.chdir(docker_main)     # reset working folder to code folder
    ##        config.closeLOG()     # close log after the for-loop

        elif s == '1' and entireMth:        # Nautical Almanac (for a month)
            check_exists(spdf + "A4chart0-180_P.pdf")
            check_exists(spdf + "A4chart180-360_P.pdf")
    ##        config.initLOG()		# initialize log file
            if config.MULTIpr: checkCoreCount()
            start = timer_start()
            config.moonDataSeeks = 0
            config.moonDataFound = 0
            config.moonHorizonSeeks = 0
            config.moonHorizonFound = 0
            msg = "\nCreating the nautical almanac for {}".format(first_day.strftime("%B %Y"))
            print(msg)
    ##            config.writeLOG(msg)
            ff = "NAtrad" if config.tbls != 'm' else "NAmod"
            fn = toUnix("{}({})_{}".format(ff,papersize,syr + '-' + smth + DecFmt))
            deletePDF(f_prefix + fn)
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            outfile = open(f_prefix + fn + ".tex", mode="w", encoding="utf8")
            outfile.write(almanac(first_day,-1,ts))
            outfile.close()
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            timer_end(start, 1)
            search_stats()
            if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
            makePDF(listarg, fn)
            tidy_up(fn)
            if config.dockerized: os.chdir(docker_main)     # reset working folder to code folder
    ##        config.closeLOG()     # close log after the for-loop

        elif s == '1' and not entireYr and not entireMth:       # Nautical Almanac (for a few days)
            check_exists(spdf + "A4chart0-180_P.pdf")
            check_exists(spdf + "A4chart180-360_P.pdf")
    ##        config.initLOG()		# initialize log file
            if config.MULTIpr: checkCoreCount()
            start = timer_start()
            config.moonDataSeeks = 0
            config.moonDataFound = 0
            config.moonHorizonSeeks = 0
            config.moonHorizonFound = 0
            txt = "from" if daystoprocess > 1 else "for"
            msg = "\nCreating the nautical almanac {} {}".format(txt,first_day.strftime("%d %B %Y"))
            print(msg)
    ##            config.writeLOG(msg)
            ff = "NAtrad" if config.tbls != 'm' else "NAmod"
            dto = ""
            if daystoprocess > 1:   # filename as 'from date'-'to date'
                lastdate = d + timedelta(days=daystoprocess-1)
                dto = lastdate.strftime("-%Y%m%d")
            fn = toUnix("{}({})_{}".format(ff,papersize,symd+dto+DecFmt))
            deletePDF(f_prefix + fn)
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            outfile = open(f_prefix + fn + ".tex", mode="w", encoding="utf8")
            outfile.write(almanac(first_day,daystoprocess,ts))
            outfile.close()
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            timer_end(start, 1)
            search_stats()
            if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
            makePDF(listarg, fn)
            tidy_up(fn)
            if config.dockerized: os.chdir(docker_main)     # reset working folder to code folder
    ##        config.closeLOG()     # close log after the for-loop

        elif s == '2' and entireYr:     # Sun Tables (for a year/years)
            check_exists(spdf + "Ra.jpg")
            for yearint in range(int(yearfr),int(yearto)+1):
                year = "{:4d}".format(yearint)  # year = "%4d" %yearint
                msg = "\nCreating the sun tables for the year {}".format(year)
                print(msg)
                first_day = date(yearint, 1, 1)
                ff = "STtrad" if config.tbls != 'm' else "STmod"
                fn = toUnix("{}({})_{}".format(ff,papersize,year+DecFmt))
                deletePDF(f_prefix + fn)
                # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                outfile = open(f_prefix + fn + ".tex", mode="w", encoding="utf8")
                outfile.write(sunalmanac(first_day,0))
                outfile.close()
                # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
                makePDF(listarg, fn)
                tidy_up(fn)
                if config.dockerized: os.chdir(docker_main)     # reset working folder to code folder

        elif s == '2' and entireMth:     # Sun Tables (for a month)
            check_exists(spdf + "Ra.jpg")
            msg = "\nCreating the sun tables for {}".format(first_day.strftime("%B %Y"))
            print(msg)
            ff = "STtrad" if config.tbls != 'm' else "STmod"
            fn = toUnix("{}({})_{}".format(ff,papersize,syr + '-' + smth + DecFmt))
            deletePDF(f_prefix + fn)
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            outfile = open(f_prefix + fn + ".tex", mode="w", encoding="utf8")
            outfile.write(sunalmanac(first_day,-1))
            outfile.close()
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
            makePDF(listarg, fn)
            tidy_up(fn)
            if config.dockerized: os.chdir(docker_main)     # reset working folder to code folder

        elif s == '2' and not entireYr and not entireMth:   # Sun Tables (for a few days)
            check_exists(spdf + "Ra.jpg")
            txt = "from" if daystoprocess > 1 else "for"
            msg = "\nCreating the sun tables {} {}".format(txt,first_day.strftime("%d %B %Y"))
            print(msg)
            ff = "STtrad" if config.tbls != 'm' else "STmod"
            dto = ""
            if daystoprocess > 1:   # filename as 'from date'-'to date'
                lastdate = d + timedelta(days=daystoprocess-1)
                dto = lastdate.strftime("-%Y%m%d")
            fn = toUnix("{}({})_{}".format(ff,papersize,symd+dto+DecFmt))
            deletePDF(f_prefix + fn)
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            outfile = open(f_prefix + fn + ".tex", mode="w", encoding="utf8")
            outfile.write(sunalmanac(first_day,daystoprocess))
            outfile.close()
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
            makePDF(listarg, fn)
            tidy_up(fn)
            if config.dockerized: os.chdir(docker_main)     # reset working folder to code folder

        elif s == '3' and entireYr:      # Event Time tables  (for a year/years)
            check_exists(spdf + "A4chart0-180_P.pdf")
            check_exists(spdf + "A4chart180-360_P.pdf")
            print("Take a break - this computer needs some time for cosmic meditation.")
            for yearint in range(int(yearfr),int(yearto)+1):
                if config.MULTIpr: checkCoreCount()
                start = timer_start()
                year = "{:4d}".format(yearint)  # year = "%4d" %yearint
                msg = "\nCreating the event time tables for the year {}".format(year)
                print(msg)
                first_day = date(yearint, 1, 1)
                fn = toUnix("Event-Times({})_{}".format(papersize,year))
                deletePDF(f_prefix + fn)
                # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                outfile = open(f_prefix + fn + ".tex", mode="w", encoding="utf8")
                outfile.write(makeEVtables(first_day,0,ts))
                outfile.close()
                # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                timer_end(start, 1)
                if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
                makePDF(listarg, fn)
                tidy_up(fn)
                if config.dockerized: os.chdir(docker_main)     # reset working folder to code folder

        elif s == '3' and entireMth:      # Event Time tables  (for a month)
            check_exists(spdf + "A4chart0-180_P.pdf")
            check_exists(spdf + "A4chart180-360_P.pdf")
            if config.MULTIpr: checkCoreCount()
            start = timer_start()
            msg = "\nCreating the event time tables for {}".format(first_day.strftime("%B %Y"))
            print(msg)
            fn = toUnix("Event-Times({})_{}".format(papersize,syr + '-' + smth))
            deletePDF(f_prefix + fn)
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            outfile = open(f_prefix + fn + ".tex", mode="w", encoding="utf8")
            outfile.write(makeEVtables(first_day,-1,ts))
            outfile.close()
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            timer_end(start, 1)
            if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
            makePDF(listarg, fn)
            tidy_up(fn)
            if config.dockerized: os.chdir(docker_main)     # reset working folder to code folder

        elif s == '3' and not entireYr and not entireMth:   # Event Time tables (for a few days)
            check_exists(spdf + "A4chart0-180_P.pdf")
            check_exists(spdf + "A4chart180-360_P.pdf")
            if config.MULTIpr: checkCoreCount()
            start = timer_start()
            txt = "from" if daystoprocess > 1 else "for"
            msg = "\nCreating the event time tables {} {}".format(txt,first_day.strftime("%d %B %Y"))
            print(msg)
            fn = toUnix("Event-Times({})_{}".format(papersize,symd))
            if daystoprocess > 1:   # filename as 'from date'-'to date'
                lastdate = d + timedelta(days=daystoprocess-1)
                fn += lastdate.strftime("-%Y%m%d")
            deletePDF(f_prefix + fn)
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            outfile = open(f_prefix + fn + ".tex", mode="w", encoding="utf8")
            outfile.write(makeEVtables(first_day,daystoprocess,ts))
            outfile.close()
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            timer_end(start, 1)
            if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
            makePDF(listarg, fn)
            tidy_up(fn)
            if config.dockerized: os.chdir(docker_main)     # reset working folder to code folder

        elif s == '4':  # Lunar Distance tables
            check_exists(spdf + "A4chart0-180_P.pdf")
            check_exists(spdf + "A4chart180-360_P.pdf")
            if entireYr: # Lunar Distance tables (for a year/years)
                for yearint in range(int(yearfr),int(yearto)+1):
                    start = time.time()
                    year = "{:4d}".format(yearint)  # year = "%4d" %yearint
                    msg = "\nCreating the lunar distance tables for the year {}".format(year)
                    print(msg)
                    daystoprocess = (date(yearint+1, 1, 1) - date(yearint, 1, 1)).days
                    fn = toUnix("LDtable({})_{}".format(papersize,year))
                    first_day = date(yearint, 1, 1)
                    # ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                    outfile = open(fn + ".tex", mode="w", encoding="utf8")
                    outfile.write(makeLDtables(first_day,0,strat))
                    outfile.close()
                    # ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                    if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
                    stop = time.time()
                    msg2 = "execution time = {:0.2f} seconds".format(stop-start)
                    print(msg2)
                    makePDF(listarg, fn)
                    tidy_up(fn)
            else:
                start = time.time()
                if entireMth:
                    fn = toUnix("LDtable({})_{}".format(papersize,syr + '-' + smth))
                    msg = "\nCreating the lunar distance tables for {}".format(first_day.strftime("%B %Y"))
                    daystoprocess = -1
                else:
                    fn = toUnix("LDtable({})_{}".format(papersize,symd))
                    if daystoprocess > 1:   # filename as 'from date'-'to date'
                        lastdate = first_day + timedelta(days=daystoprocess-1)
                        fn += lastdate.strftime("-%Y%m%d")
                    txt = "from" if daystoprocess > 1 else "for"
                    msg = "\nCreating the lunar distance tables {} {}".format(txt,symd)
                print(msg)
                deletePDF(f_prefix + fn)
                # ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                outfile = open(f_prefix + fn + ".tex", mode="w", encoding="utf8")
                outfile.write(makeLDtables(first_day,daystoprocess,strat))
                outfile.close()
                # ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
                stop = time.time()
                msg2 = "execution time = {:0.2f} seconds".format(stop-start)
                print(msg2)
                makePDF(listarg, fn)
                tidy_up(fn)

        elif s == '5':  # Lunar Distance charts
            if entireMth:
                fn = toUnix("LDchart({})_{}".format(papersize,syr + '-' + smth))
            else:
                fn = toUnix("LDchart({})_{}".format(papersize,symd))
                if daystoprocess > 1:   # filename as 'from date'-'to date'
                    lastdate = first_day + timedelta(days=daystoprocess-1)
                    fn += lastdate.strftime("-%Y%m%d")
            deletePDF(f_prefix + fn)

            start = time.time()
            if entireYr: msg = "\nCreating the lunar distance charts for the year {}".format(syr)
            elif entireMth: msg = "\nCreating the lunar distance charts for {}".format(syr + '-' + smth)
            elif daystoprocess > 1: msg = "\nCreating the lunar distance charts from {}".format(symd)
            else: msg = "\nCreating the lunar distance chart for {}".format(symd)
            print(msg)
            # ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            outfile = open(f_prefix + fn + ".tex", mode="w", encoding="utf8")
            makeLDcharts(first_day,strat,daystoprocess,outfile,ts,onlystars,quietmode)
            outfile.close()
            # ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
            stop = time.time()
            msg2 = "\nexecution time = {:0.2f} seconds".format(stop-start)
            print(msg2)
            makePDF(listarg, fn)
            tidy_up(fn)

        elif s == '6':  # Increments and Corrections tables
            msg = "\nCreating the Increments and Corrections tables"
            print(msg)
            fn = toUnix("Inc({})").format(papersize)
            deletePDF(f_prefix + fn)
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            outfile = open(f_prefix + fn + ".tex", mode="w", encoding="utf8")
            outfile.write(makelatex())
            outfile.close()
            # :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            if config.dockerized: os.chdir(os.getcwd() + f_postfix)     # DOCKER ONLY
            makePDF(listarg, fn)
            tidy_up(fn)

    else:
        print("Error! Choose 1, 2, 3, 4, 5 or 6")