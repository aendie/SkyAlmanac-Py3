#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   Copyright (C) 2023  Andrew Bauer

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

# This contains the majority of functions that calculate values for the Nautical Almanac

###### Standard library imports ######
# don't confuse the 'date' method with the 'Date' variable!
#   the following line includes 'datetime.combine' class method:
from datetime import date, time, datetime, timedelta
# don't confuse the 'time' instance method in the 'datetime' object with the 'Time' module:
import time as Time # 00000 - stopwatch elements
from math import pi, cos, tan, atan, degrees, copysign
import os
import errno
import socket
import sys			# required for .stdout.write()
import urllib.error # used in 'download_EOP' function
from urllib.request import urlopen
from collections import deque

###### Third party imports ######
from skyfield import VERSION
from skyfield.api import Loader
from skyfield.api import Topos, Star
from skyfield import almanac
from skyfield.nutationlib import iau2000b
from skyfield.data import hipparcos
from skyfield.magnitudelib import planetary_magnitude
import numpy as np

###### Local application imports ######
import config

#---------------------------
#   Module initialization
#---------------------------

urlIERS = "ftp://ftp.iers.org/products/eop/rapid/standard/"
urlUSNO = "https://maia.usno.navy.mil/ser7/"        # alternate location
urlDCIERS = "https://datacenter.iers.org/data/9/"   # alternate location

hour_of_day = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
next_hour_of_day = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
degree_sign= u'\N{DEGREE SIGN}'

def compareVersion(versions1, version2):
    #versions1 = [int(v) for v in version1.split(".")]
    versions2 = [int(v) for v in version2.split(".")]
    for i in range(max(len(versions1),len(versions2))):
        v1 = versions1[i] if i < len(versions1) else 0
        v2 = versions2[i] if i < len(versions2) else 0
        if v1 > v2:
            return 1
        elif v1 < v2:
            return -1
    return 0

def isConnected():
    try:
        # connect to the host -- tells us if the host is actually reachable
        sock = socket.create_connection(("www.iers.org", 80))
        if sock is not None: sock.close
        return True
    except OSError:
        pass
    # try alternate source if above server is down ...
    try:
        # connect to the host -- tells us if the host is actually reachable
        sock = socket.create_connection(("maia.usno.navy.mil", 80))
        if sock is not None: sock.close
        return True
    except OSError:
        pass
    return False    # if neither is reachable

# NOTE: the IERS server is unavailable (due to maintenance work in the first 3 weeks, at least, of April 2022)
#       however, although the USNO server currently works, it was previously down for 2.5 years!
#       So it is still best to try using the IERS server as first oprion, and USNO as second.

def testServer(filename, url):
    url += filename
    try:
        connection2 = urlopen(url)
    except Exception as e:
        e2 = IOError('cannot download {0} because {1}'.format(url, e))
        e2.__cause__ = None
#        raise e2
        return False
    return True     # server works

def download_EOP(path, filename, url, loc):
    # NOTE: the following 'print' statement does not print immediately in Linux!
    #print("Downloading EOP data from USNO...", end ="")
    sys.stdout.write("Downloading EOP data from {}...".format(loc))
    sys.stdout.flush()
    filepath = os.path.join(path, filename)
    url += filename
    try:
        connection = urlopen(url)
    except urllib.error.URLError as e:
        #raise IOError('error getting {0} - {1}'.format(url, e))
        print('\nError getting {0} - {1}'.format(url, e))
        sys.exit(0)
    blocksize = 128*1024

    # Claim our own unique download filename.

    tempbase = tempname = path + filename + '.download'
    flags = getattr(os, 'O_BINARY', 0) | os.O_CREAT | os.O_EXCL | os.O_RDWR
    i = 1
    while True:
        try:
            fd = os.open(tempname, flags, 0o666)
        except OSError as e:  # "FileExistsError" is not supported by Python 2
            if e.errno != errno.EEXIST:
                raise
            i += 1
            tempname = '{0}{1}'.format(tempbase, i)
        else:
            break

    # Download to the temporary filename.

    with os.fdopen(fd, 'wb') as w:
        try:
            length = 0
            while True:
                data = connection.read(blocksize)
                if not data:
                    break
                w.write(data)
                length += len(data)
            w.flush()
        except Exception as e:
            raise IOError('error getting {0} - {1}'.format(url, e))

    # Rename the temporary file to the destination name.

    if os.path.exists(filepath):
        os.remove(filepath)
    try:
        os.rename(tempname, filepath)
    except Exception as e:
        raise IOError('error renaming {0} to {1} - {2}'.format(tempname, filepath, e))

    sys.stdout.write("done.\n")
    sys.stdout.flush()

def init_sf(spad):
    global ts, eph, earth, moon, sun, venus, mars, jupiter, saturn, df
    load = Loader(spad)         # spad = folder to store the downloaded files
    EOPdf  = "finals2000A.all"  # Earth Orientation Parameters data file
    dfIERS = spad + EOPdf
    config.useIERSEOP = False
    config.txtIERSEOP = ""

    if config.useIERS:
        if compareVersion(VERSION, "1.31") >= 0:
            if os.path.isfile(dfIERS):
                if load.days_old(EOPdf) > float(config.ageIERS):
                    if isConnected():
                        if testServer(EOPdf, urlIERS):  # first try downloading via FTP
                            load.download(EOPdf)
                        elif testServer(EOPdf, urlUSNO):# then try the USNO server
                            download_EOP(spad,EOPdf,urlUSNO,"USNO")
                        else:   # finally try the IERS datacenter (available in more countries)
                            download_EOP(spad,EOPdf,urlDCIERS,"IERS datacenter")
                    else: print("NOTE: no Internet connection... using existing '{}'".format(EOPdf))
                ts = load.timescale(builtin=False)	# timescale object
                config.useIERSEOP = True
            else:
                if isConnected():
                    if testServer(EOPdf, urlIERS):  # first try downloading via FTP
                        load.download(EOPdf)
                    elif testServer(EOPdf, urlUSNO):# then try the USNO server
                        download_EOP(spad,EOPdf,urlUSNO,"USNO")
                    else:   # finally try the IERS datacenter (available in more countries)
                        download_EOP(spad,EOPdf,urlDCIERS,"IERS datacenter")
                    ts = load.timescale(builtin=False)	# timescale object
                    config.useIERSEOP = True
                else:
                    print("NOTE: no Internet connection... using built-in UT1-tables")
                    ts = load.timescale()	# timescale object with built-in UT1-tables
        else:
            ts = load.timescale()	# timescale object with built-in UT1-tables
    else:
        ts = load.timescale()	# timescale object with built-in UT1-tables

    if config.useIERSEOP and os.path.isfile(dfIERS):
# get the IERS EOP data "release date" according to these rules:
#   - begin searching within this millenium (ignoring data from 02 Jan 1973 to 31 Dec 1999)
#   - halt when the following value is "P", i.e. predicted as opposed to measured:
#       - flag for Bull. A UT1-UTC values
#   - step back one day to the record that has "I", i.e. measured data.
#
# the date of this record is the last date with IERS measured data.
#   [the more recent the date, the more accurate/reliable are both the past IERS
#   Earth Orientation Parameters as well as the future (predicted) EOP data values.]

# IERS EOP data format definition:
# https://maia.usno.navy.mil/ser7/readme.finals2000A

        queue = deque(["a", "b", "c", "d"])
        PredData = False    # True when Prediction data flagged
        PredEnd  = False    # True when Prediction data no longer flagged

        iers = ""
        with open(dfIERS) as file:
            for line in file:
                mjd = int(line[7:12])

                if not PredData and mjd >= 51544:    # skip data in previous  millenium
                    queue.append(line)
                    queue.popleft()
                    c1 = line[16:17]    # IERS (I) or Prediction (P) flag for Bull. A polar motion values
                    c2 = line[57:58]    # IERS (I) or Prediction (P) flag for Bull. A UT1-UTC values
                    c3 = line[95:96]    # IERS (I) or Prediction (P) flag for Bull. A nutation values
                    if not PredData and c2 == "P":
                        PredData = True
                        iers = ""
                        while queue:
                            iersdata = queue.pop()
                            if iersdata[57:58] == "I":
                                iers = iersdata
                                break
                        if iers == "": iers = iersdata
                        year = int(iers[0:2]) + 2000
                        mth  = int(iers[2:4])
                        day  = int(iers[4:6])
                        dt = date(year, mth, day)
                        config.txtIERSEOP = "IERS Earth Orientation data as of " + dt.strftime("%d-%b-%Y")
                elif PredData:    # search for end of Prediction data
                    c2 = line[57:58]    # IERS (I) or Prediction (P) flag for Bull. A UT1-UTC values
                    if c2 == "P":
                        iers = line
                    else:
                        PredEnd = True
                        break

        if iers == "":
            print("Error: IERS Earth Orientation Parameters data file is incomplete...")
            print("       most likely the download did not finish properly.")
            print("       Please delete the 'finals2000A.all' data file and")
            print("       rerun this program - it will be downloaded anew.")
            sys.exit(0)

        # detect end of Prediction data even if file ends with c2 == "P" ...
        year = int(iers[0:2]) + 2000
        mth  = int(iers[2:4])
        day  = int(iers[4:6])
        dt2 = date(year, mth, day)
        config.endIERSEOP = "IERS Earth Orientation predictions end " + dt2.strftime("%d-%b-%Y")
        config.dt_IERSEOP = dt2

    if config.ephndx in set([0, 1, 2, 3, 4]):
    
        eph = load(config.ephemeris[config.ephndx][0])	# load chosen ephemeris
        earth   = eph['earth']
        moon    = eph['moon']
        sun     = eph['sun']
        venus   = eph['venus']
        jupiter = eph['jupiter barycenter']
        saturn  = eph['saturn barycenter']
        if config.ephndx >= 3:
            mars    = eph['mars barycenter']
        else:
            mars    = eph['mars']

    # load the Hipparcos catalog as a 118,218 row Pandas dataframe.
    with load.open(hipparcos.URL) as f:
        #hipparcos_epoch = ts.tt(1991.25)
        df = hipparcos.load_dataframe(f)

    return ts

#------------------------
#   internal functions
#------------------------

def norm(delta):
    # normalize the angle between 0° and 360°
    # (usually delta is roughly 15 degrees)
    while delta < 0:
        delta += 360.0
    while delta >= 360.0:
        delta -= 360.0
    return delta

def GHAcolong(gha):
    # return the colongitude, e.g. 270° returns 90°
    coGHA = gha + 180
    while coGHA > 360:
        coGHA = coGHA - 360
    return coGHA

def fmtgha(gst, ra):
    # formats angle (hours) to that used in the nautical almanac. (ddd°mm.m)
    sha = (gst - ra) * 15
    if sha < 0:
        sha = sha + 360
    return fmtdeg(sha)

def gha2deg(gst, ra):
    # convert GHA (hours) to degrees of arc
    sha = (gst - ra) * 15
    while sha < 0:
        sha = sha + 360
    return sha

def fmtdeg(deg, fixedwidth=1):
    # formats the angle (deg) to that used in the nautical almanac (ddd°mm.m)
	# the optional argument specifies the minimum width for the degrees
    theminus = ""
    if deg < 0:
    	theminus = '-'
    df = abs(deg)
    di = int(df)
    mf = round((df-di)*60, 1)	# minutes (float), rounded to 1 decimal place
    mi = int(mf)			# minutes (integer)
    if mi == 60:
        mf -= 60
        di += 1
        if di == 360:
            di = 0
    if fixedwidth == 2:
        gm = "{}{:02d}$^\circ${:04.1f}".format(theminus,di,mf)
    else:
        if fixedwidth == 3:
            gm = "{}{:03d}$^\circ${:04.1f}".format(theminus,di,mf)
        else:
            gm = "{}{}$^\circ${:04.1f}".format(theminus,di,mf)
    return gm

def time2text(t, round2seconds):
    if round2seconds:
        return t.ut1_strftime('%H:%M:%S')
    else:
        return t.ut1_strftime('%H:%M')

def rise_set(t, y, lats, round2seconds = False):
    # analyse the return values from the 'find_discrete' method...
    # get sun/moon rise/set values (if any) rounded to nearest minute
    rise = '--:--'
    sett = '--:--'
    ris2 = '--:--'
    set2 = '--:--'
    # 'finalstate' is True if above horizon; False if below horizon; None if unknown
    finalstate = None
    if len(t) == 2:		# this happens most often
        dt0 = t[0].utc_datetime()
        sec0 = dt0.second + int(dt0.microsecond)/1000000.
        t0 = ts.ut1(dt0.year, dt0.month, dt0.day, dt0.hour, dt0.minute, sec0)
        dt1 = t[1].utc_datetime()
        sec1 = dt1.second + int(dt1.microsecond)/1000000.
        t1 = ts.ut1(dt1.year, dt1.month, dt1.day, dt1.hour, dt1.minute, sec1)
        if y[0] and not(y[1]):
            # get the UT1 time rounded to minutes OR seconds ...
            rise = time2text(t0, round2seconds)
            sett = time2text(t1, round2seconds)
            finalstate = False
        else:
            if not(y[0]) and y[1]:
                # get the UT1 time rounded to minutes OR seconds ...
                sett = time2text(t0, round2seconds)
                rise = time2text(t1, round2seconds)
                finalstate = True
            else:
                # this should never get here!
                rise_set_error(y,lats,ts.utc(t[0].utc_datetime()))
    else:
        if len(t) == 1:		# this happens ocassionally
            dt0 = t[0].utc_datetime()
            sec0 = dt0.second + int(dt0.microsecond)/1000000.
            t0 = ts.ut1(dt0.year, dt0.month, dt0.day, dt0.hour, dt0.minute, sec0)
            if y[0]:
                # get the UT1 time rounded to minutes OR seconds ...
                rise = time2text(t0, round2seconds)
                finalstate = True
            else:
                # get the UT1 time rounded to minutes OR seconds ...
                sett = time2text(t0, round2seconds)
                finalstate = False
        else:
            if len(t) == 3:		# this happens rarely (in high latitudes mid-year)
                dt0 = t[0].utc_datetime()
                sec0 = dt0.second + int(dt0.microsecond)/1000000.
                t0 = ts.ut1(dt0.year, dt0.month, dt0.day, dt0.hour, dt0.minute, sec0)
                dt1 = t[1].utc_datetime()
                sec1 = dt1.second + int(dt1.microsecond)/1000000.
                t1 = ts.ut1(dt1.year, dt1.month, dt1.day, dt1.hour, dt1.minute, sec1)
                dt2 = t[2].utc_datetime()
                sec2 = dt2.second + int(dt2.microsecond)/1000000.
                t2 = ts.ut1(dt2.year, dt2.month, dt2.day, dt2.hour, dt2.minute, sec2)
                if y[0] and not(y[1]) and y[2]:
                    # get the UT1 time rounded to minutes OR seconds ...
                    rise = time2text(t0, round2seconds)
                    sett = time2text(t1, round2seconds)
                    ris2 = time2text(t2, round2seconds)
                    finalstate = True
                else:
                    if not(y[0]) and y[1] and not(y[2]):
                        # get the UT1 time rounded to minutes OR seconds ...
                        sett = time2text(t0, round2seconds)
                        rise = time2text(t1, round2seconds)
                        set2 = time2text(t2, round2seconds)
                        finalstate = False
                    else:
                        # this should never get here!
                        rise_set_error(y,lats,ts.utc(t[0].utc_datetime()))
            else:
                if len(t) > 3:
                    # this should never get here!
                    rise_set_error(y,lats,ts.utc(t[0].utc_datetime()))

    return rise, sett, ris2, set2, finalstate

def rise_set_error(y, lats, t0):
    # unexpected rise/set values - format message line
    msg = "rise_set {} values for {}: {}".format(len(y),lats, y[0])
    if len(y) > 1:
        msg = msg + " {}".format(y[1])
    if len(y) > 2:
        msg = msg + " {}".format(y[2])
    if len(y) > 3:
        msg = msg + " {}".format(y[3])
    dt = t0.utc_datetime() + timedelta(seconds = t0.dut1)

    if config.logfileopen:
        # write to log file
        config.writeLOG("\n{}".format(dt.isoformat()))
        config.writeLOG("   " + msg)
    else:
        # print to console
        print("{}   {}".format(dt.isoformat(), msg))
    return

#-------------------------------
#   Miscellaneous
#-------------------------------

def getDUT1(d):
    # obtain calculation parameters
    t = ts.ut1(d.year, d.month, d.day, 0, 0, 0)
    return t.dut1, t.delta_t

#-------------------------------
#   Sun and Moon calculations
#-------------------------------

def sunGHA(d):              # used in sunmoontab(m)
    # compute sun's GHA and DEC per hour of day

    t = ts.ut1(d.year, d.month, d.day, hour_of_day, 0, 0)
    position = earth.at(t).observe(sun)
    #ra = position.apparent().radec(epoch='date')[0]
    #dec = position.apparent().radec(epoch='date')[1]
    ra, dec, _ = position.apparent().radec(epoch='date')

    ghas = ['' for x in range(24)]
    decs = ['' for x in range(24)]
    degs = ['' for x in range(24)]
    for i in range(len(dec.degrees)):
        ghas[i] = fmtgha(t[i].gast, ra.hours[i])
        decs[i] = fmtdeg(dec.degrees[i],2)
        degs[i] = dec.degrees[i]
    #for i in range(len(dec.degrees)):
    #    print(i, ghas[i])

    # degs has been added for the suntab function
    return ghas,decs,degs

def sunSD(d):               # used in sunmoontab(m)
    # compute semi-diameter of sun and sun's declination change per hour (in minutes)
    t00 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)
    #t12 = ts.ut1(d.year, d.month, d.day, 12, 0, 0)
    position = earth.at(t00).observe(sun)
    distance = position.apparent().radec(epoch='date')[2]
    dist_km = distance.km
# OLD:  sds = degrees(atan(695500.0 / dist_km))   # radius of sun = 695500 km
    svmr  = degrees(atan(695700.0 / dist_km))   # volumetric mean radius of sun = 695700 km
    sunVMRm = "{:0.1f}".format(svmr * 60)   # convert to minutes of arc

    t0 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)
    position0 = earth.at(t0).observe(sun)
    dec0 = position0.apparent().radec(epoch='date')[1]
    D0 = dec0.degrees * 60.0    # convert to minutes of arc
    t1= ts.ut1(d.year, d.month, d.day, 1, 0, 0)
    position1 = earth.at(t1).observe(sun)
    dec1 = position1.apparent().radec(epoch='date')[1]
    D1 = dec1.degrees * 60.0    # convert to minutes of arc
    if config.d_valNA:
        Dvalue = abs(D1 - D0)
    elif copysign(1.0,D1) == copysign(1.0,D0):
        Dvalue = abs(D1) - abs(D0)
    else:
        Dvalue = -abs(D1 - D0)
    sunDm = "{:0.1f}".format(Dvalue)
    return sunVMRm, sunDm

def moonSD(d):              # used in sunmoontab(m)
    # compute semi-diameter of moon (in minutes)
    t00 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)
    #t12 = ts.ut1(d.year, d.month, d.day, 12, 0, 0)
    position = earth.at(t00).observe(moon)
    distance = position.apparent().radec(epoch='date')[2]
    dist_km = distance.km
# OLD: sdm = degrees(atan(1738.1/dist_km))   # equatorial radius of moon = 1738.1 km
    sdm = degrees(atan(1737.4/dist_km))   # volumetric mean radius of moon = 1737.4 km
    sdmm = "{:0.1f}".format(sdm * 60)  # convert to minutes of arc
    return sdmm

def moonGHA(d, round2seconds = False):  # used in sunmoontab(m) & equationtab (in eventtables.py)
    # compute moon's GHA, DEC and HP per hour of day
    t = ts.ut1(d.year, d.month, d.day, hour_of_day, 0, 0)
    position = earth.at(t).observe(moon)
    #ra = position.apparent().radec(epoch='date')[0]
    #dec = position.apparent().radec(epoch='date')[1]
    #distance = position.apparent().radec(epoch='date')[2]
    ra, dec, distance = position.apparent().radec(epoch='date')

    if round2seconds:
        # also compute moon's GHA at End of Day (23:59:59.5) and Start of Day (24 hours earlier)
        tSoD = ts.ut1(d.year, d.month, d.day-1, 23, 59, 59.5)
        tEoD = ts.ut1(d.year, d.month, d.day, 23, 59, 59.5)
    else:   # round to minutes of time
        # also compute moon's GHA at End of Day (23:59:30) and Start of Day (24 hours earlier)
        tSoD = ts.ut1(d.year, d.month, d.day-1, 23, 59, 30)
        tEoD = ts.ut1(d.year, d.month, d.day, 23, 59, 30)

    posSoD = earth.at(tSoD).observe(moon)
    raSoD = posSoD.apparent().radec(epoch='date')[0]
    ghaSoD = gha2deg(tSoD.gast, raSoD.hours)   # GHA as float
    posEoD = earth.at(tEoD).observe(moon)
    raEoD = posEoD.apparent().radec(epoch='date')[0]
    ghaEoD = gha2deg(tEoD.gast, raEoD.hours)   # GHA as float

    GHAupper = [-1.0 for x in range(24)]
    GHAlower = [-1.0 for x in range(24)]
    gham = ['' for x in range(24)]
    decm = ['' for x in range(24)]
    degm = ['' for x in range(24)]
    HPm  = ['' for x in range(24)]

    for i in range(len(dec.degrees)):
##        raIDL = ra.hours[i] + 12	# at International Date Line
##        if raIDL > 24: raIDL = raIDL - 24
        GHAupper[i] = gha2deg(t[i].gast, ra.hours[i])   # GHA as float
        GHAlower[i] = GHAcolong(GHAupper[i])
        gham[i] = fmtgha(t[i].gast, ra.hours[i])
        decm[i] = fmtdeg(dec.degrees[i],2)
        degm[i] = dec.degrees[i]
        dist_km = distance.km[i]
# OLD:  HP = degrees(atan(6378.0/dist_km))	# radius of earth = 6378.0 km
        HP = degrees(atan(6371.0/dist_km))	# volumetric mean radius of earth = 6371.0 km
        HPm[i] = "{:0.1f}'".format(HP * 60)     # convert to minutes of arc

    # degm has been added for the sunmoontab function
    # GHAupper is an array of GHA per hour as float
    # ghaSoD, ghaEoD = GHA at Start/End of Day as time is rounded to hh:mm (or hh:mm:ss)

    return gham, decm, degm, HPm, GHAupper, GHAlower, ghaSoD, ghaEoD

def moonVD(d00, d):           # used in sunmoontab(m)
# OLD:  # first value required is from 23:30 on the previous day...
# OLD:  t0 = ts.ut1(d00.year, d00.month, d00.day, 23, 30, 0)
    # first value required is at 00:00 on the current day...
    t0 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)
    pos0 = earth.at(t0).observe(moon)
    #ra0 = pos0.apparent().radec(epoch='date')[0]
    #dec0 = pos0.apparent().radec(epoch='date')[1]
    ra0, dec0, _ = pos0.apparent().radec(epoch='date')
    V0 = gha2deg(t0.gast, ra0.hours)
    D0 = dec0.degrees * 60.0    # convert to minutes of arc
    if config.d_valNA:
        D0 = round(D0, 1)

# OLD:  # ...then 24 values at hourly intervals from 23:30 onwards
# OLD:  t = ts.ut1(d.year, d.month, d.day, hour_of_day, 30, 0)
    # ...then 24 values at hourly intervals from 00:00 onwards
    t = ts.ut1(d.year, d.month, d.day, next_hour_of_day, 0, 0)
    position = earth.at(t).observe(moon)
    #ra = position.apparent().radec(epoch='date')[0]
    #dec = position.apparent().radec(epoch='date')[1]
    ra, dec, _ = position.apparent().radec(epoch='date')

    moonVm = ['' for x in range(24)]
    moonDm = ['' for x in range(24)]
    for i in range(len(dec.degrees)):
        V1 = gha2deg(t[i].gast, ra.hours[i])
        Vdelta = V1 - V0
        if Vdelta < 0: Vdelta += 360
        Vdm = (Vdelta-(14.0+(19.0/60.0))) * 60	# subtract 14:19:00
        moonVm[i] = "{:0.1f}'".format(Vdm)
        D1 = dec.degrees[i] * 60.0  # convert to minutes of arc
        if config.d_valNA:
            D1 = round(D1, 1)
            Dvalue = abs(D1 - D0)
        elif copysign(1.0,D1) == copysign(1.0,D0):
            Dvalue = abs(D1) - abs(D0)
        else:
            Dvalue = -abs(D1 - D0)
        moonDm[i] = "{:0.1f}'".format(Dvalue)
        V0 = V1		# store current value as next previous value
        D0 = D1		# store current value as next previous value
    return moonVm, moonDm

#------------------------------------------------
#   Venus, Mars, Jupiter & Saturn calculations
#------------------------------------------------

def venusGHA(d):            # used in planetstab(m)
    t = ts.ut1(d.year, d.month, d.day, hour_of_day, 0, 0)
    position = earth.at(t).observe(venus)
    #ra = position.apparent().radec(epoch='date')[0]
    #dec = position.apparent().radec(epoch='date')[1]
    ra, dec, _ = position.apparent().radec(epoch='date')

    ghas = ['' for x in range(24)]
    decs = ['' for x in range(24)]
    degs = ['' for x in range(24)]
    for i in range(len(dec.degrees)):
        ghas[i] = fmtgha(t[i].gast, ra.hours[i])
        decs[i] = fmtdeg(dec.degrees[i],2)
        degs[i] = dec.degrees[i]
    #for i in range(len(dec.degrees)):
    #    print(i, ghas[i])
    return ghas, decs, degs

def marsGHA(d):             # used in planetstab(m)
    t = ts.ut1(d.year, d.month, d.day, hour_of_day, 0, 0)
    position = earth.at(t).observe(mars)
    #ra = position.apparent().radec(epoch='date')[0]
    #dec = position.apparent().radec(epoch='date')[1]
    ra, dec, _ = position.apparent().radec(epoch='date')

    ghas = ['' for x in range(24)]
    decs = ['' for x in range(24)]
    degs = ['' for x in range(24)]
    for i in range(len(dec.degrees)):
        ghas[i] = fmtgha(t[i].gast, ra.hours[i])
        decs[i] = fmtdeg(dec.degrees[i],2)
        degs[i] = dec.degrees[i]
    #for i in range(len(dec.degrees)):
    #    print(i, ghas[i])
    return ghas, decs, degs

def jupiterGHA(d):          # used in planetstab(m)
    t = ts.ut1(d.year, d.month, d.day, hour_of_day, 0, 0)
    position = earth.at(t).observe(jupiter)
    #ra = position.apparent().radec(epoch='date')[0]
    #dec = position.apparent().radec(epoch='date')[1]
    ra, dec, _ = position.apparent().radec(epoch='date')

    ghas = ['' for x in range(24)]
    decs = ['' for x in range(24)]
    degs = ['' for x in range(24)]
    for i in range(len(dec.degrees)):
        ghas[i] = fmtgha(t[i].gast, ra.hours[i])
        decs[i] = fmtdeg(dec.degrees[i],2)
        degs[i] = dec.degrees[i]
    #for i in range(len(dec.degrees)):
    #    print(i, ghas[i])
    return ghas, decs, degs

def saturnGHA(d):           # used in planetstab(m)
    t = ts.ut1(d.year, d.month, d.day, hour_of_day, 0, 0)
    position = earth.at(t).observe(saturn)
    #ra = position.apparent().radec(epoch='date')[0]
    #dec = position.apparent().radec(epoch='date')[1]
    ra, dec, _ = position.apparent().radec(epoch='date')

    ghas = ['' for x in range(24)]
    decs = ['' for x in range(24)]
    degs = ['' for x in range(24)]
    for i in range(len(dec.degrees)):
        ghas[i] = fmtgha(t[i].gast, ra.hours[i])
        decs[i] = fmtdeg(dec.degrees[i],2)
        degs[i] = dec.degrees[i]
    #for i in range(len(dec.degrees)):
    #    print(i, ghas[i])
    return ghas, decs, degs

def vdm_Venus(d):           # used in planetstab(m)
    # compute v (GHA correction), d (Declination correction), m (magnitude of planet)
    t0 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)
    position0 = earth.at(t0).observe(venus)
    #ra0 = position0.apparent().radec(epoch='date')[0]	# RA
    #dec0 = position0.apparent().radec(epoch='date')[1]	# declination
    ra0, dec0, _ = position0.apparent().radec(epoch='date')
    D0 = dec0.degrees * 60.0    # convert to minutes of arc
    mag = "{:0.2f}".format(planetary_magnitude(position0))  # planetary magnitude

    t1 = ts.ut1(d.year, d.month, d.day, 1, 0, 0)
    position1 = earth.at(t1).observe(venus)
    #ra1 = position1.apparent().radec(epoch='date')[0]	# RA
    #dec1 = position1.apparent().radec(epoch='date')[1]	# declination
    ra1, dec1, _ = position1.apparent().radec(epoch='date')
    D1 = dec1.degrees * 60.0    # convert to minutes of arc

    sha0 = (t0.gast - ra0.hours) * 15
    sha1 = (t1.gast - ra1.hours) * 15
    sha  = norm(sha1 - sha0) - 15
    RAcorrm = "{:0.1f}".format(sha * 60)	# convert to minutes of arc
    if config.d_valNA:
        Dvalue = abs(D1 - D0)
    elif copysign(1.0,D1) == copysign(1.0,D0):
        Dvalue = abs(D1) - abs(D0)
    else:
        Dvalue = -abs(D1 - D0)
    venusDm = "{:0.1f}".format(Dvalue)
    return RAcorrm, venusDm, mag

def vdm_Mars(d):            # used in planetstab(m)
    # compute v (GHA correction), d (Declination correction)
    # NOTE: m (magnitude of planet) comes from alma_ephem.py
    t0 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)
    position0 = earth.at(t0).observe(mars)
    #ra0 = position0.apparent().radec(epoch='date')[0]	# RA
    #dec0 = position0.apparent().radec(epoch='date')[1]	# declination
    ra0, dec0, _ = position0.apparent().radec(epoch='date')
    D0 = dec0.degrees * 60.0    # convert to minutes of arc
    mag = "{:0.2f}".format(planetary_magnitude(position0))  # planetary magnitude

    t1 = ts.ut1(d.year, d.month, d.day, 1, 0, 0)
    position1 = earth.at(t1).observe(mars)
    #ra1 = position1.apparent().radec(epoch='date')[0]	# RA
    #dec1 = position1.apparent().radec(epoch='date')[1]	# declination
    ra1, dec1, _ = position1.apparent().radec(epoch='date')
    D1 = dec1.degrees * 60.0    # convert to minutes of arc

    sha0 = (t0.gast - ra0.hours) * 15
    sha1 = (t1.gast - ra1.hours) * 15
    sha  = norm(sha1 - sha0) - 15
    RAcorrm = "{:0.1f}".format(sha * 60)	# convert to minutes of arc
    if config.d_valNA:
        Dvalue = abs(D1 - D0)
    elif copysign(1.0,D1) == copysign(1.0,D0):
        Dvalue = abs(D1) - abs(D0)
    else:
        Dvalue = -abs(D1 - D0)
    marsDm = "{:0.1f}".format(Dvalue)
    return RAcorrm, marsDm, mag

def vdm_Jupiter(d):         # used in planetstab(m)
    # compute v (GHA correction), d (Declination correction), m (magnitude of planet)
    t0 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)
    position0 = earth.at(t0).observe(jupiter)
    #ra0 = position0.apparent().radec(epoch='date')[0]	# RA
    #dec0 = position0.apparent().radec(epoch='date')[1]	# declination
    ra0, dec0, _ = position0.apparent().radec(epoch='date')
    D0 = dec0.degrees * 60.0    # convert to minutes of arc
    mag = "{:0.2f}".format(planetary_magnitude(position0))  # planetary magnitude

    t1 = ts.ut1(d.year, d.month, d.day, 1, 0, 0)
    position1 = earth.at(t1).observe(jupiter)
    #ra1 = position1.apparent().radec(epoch='date')[0]	# RA
    #dec1 = position1.apparent().radec(epoch='date')[1]	# declination
    ra1, dec1, _ = position1.apparent().radec(epoch='date')
    D1 = dec1.degrees * 60.0    # convert to minutes of arc

    sha0 = (t0.gast - ra0.hours) * 15
    sha1 = (t1.gast - ra1.hours) * 15
    sha  = norm(sha1 - sha0) - 15
    RAcorrm = "{:0.1f}".format(sha * 60)	# convert to minutes of arc
    if config.d_valNA:
        Dvalue = abs(D1 - D0)
    elif copysign(1.0,D1) == copysign(1.0,D0):
        Dvalue = abs(D1) - abs(D0)
    else:
        Dvalue = -abs(D1 - D0)
    jupDm = "{:0.1f}".format(Dvalue)
    return RAcorrm, jupDm, mag

def vdm_Saturn(d):          # used in planetstab(m)
    # compute v (GHA correction), d (Declination correction)
    # NOTE: m (magnitude of planet) comes from alma_ephem.py
    t0 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)
    position0 = earth.at(t0).observe(saturn)
    #ra0 = position0.apparent().radec(epoch='date')[0]	# RA
    #dec0 = position0.apparent().radec(epoch='date')[1]	# declination
    ra0, dec0, _ = position0.apparent().radec(epoch='date')
    D0 = dec0.degrees * 60.0    # convert to minutes of arc
    mag = "{:0.2f}".format(planetary_magnitude(position0))  # planetary magnitude

    t1 = ts.ut1(d.year, d.month, d.day, 1, 0, 0)
    position1 = earth.at(t1).observe(saturn)
    #ra1 = position1.apparent().radec(epoch='date')[0]	# RA
    #dec1 = position1.apparent().radec(epoch='date')[1]	# declination
    ra1, dec1, _ = position1.apparent().radec(epoch='date')
    D1 = dec1.degrees * 60.0    # convert to minutes of arc

    sha0 = (t0.gast - ra0.hours) * 15
    sha1 = (t1.gast - ra1.hours) * 15
    sha  = norm(sha1 - sha0) - 15
    RAcorrm = "{:0.1f}".format(sha * 60)	# convert to minutes of arc
    if config.d_valNA:
        Dvalue = abs(D1 - D0)
    elif copysign(1.0,D1) == copysign(1.0,D0):
        Dvalue = abs(D1) - abs(D0)
    else:
        Dvalue = -abs(D1 - D0)
    satDm = "{:0.1f}".format(Dvalue)
    return RAcorrm, satDm, mag

#-----------------------------------------
#   Aries & planet transit calculations
#-----------------------------------------

def ariesGHA(d):            # used in planetstab(m)
    t = ts.ut1(d.year, d.month, d.day, hour_of_day, 0, 0)

    ghas = ['' for x in range(24)]
    for i in range(24):
        ghas[i] = fmtgha(t[i].gast, 0)
    return ghas

def ariestransit(d):        # used in planetstab(m)
    # returns transit time of aries for the *PREVIOUS* date

    t = ts.ut1(d.year, d.month, d.day, 0, 0, 0)
    trans = 24 - (t.gast / 1.00273790935)
    hr = int(trans)
    # round >=30 seconds to next minute
    #min = tup[-2] + int(round(tup[-1]/60+0.00001))
    min = int(round((trans - hr) * 60))
    if min == 60:
        min = 0
        hr += 1
        if hr == 24:
            hr = 0
    ttime = '{:02d}:{:02d}'.format(hr,min)
    return ttime
    
def planetstransit(d, round2seconds = False):      # used in starstab & meridiantab (in eventtables.py)
    # returns SHA and Meridian Passage for the navigational planets
    d1 = d + timedelta(days=1)
    
# Venus
    t0 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)
    position0 = earth.at(t0).observe(venus)
    #ra0 = position0.apparent().radec(epoch='date')[0]	# RA
    #vau = position0.apparent().radec(epoch='date')[2]	# distance
    ra0, _, vau = position0.apparent().radec(epoch='date')
    vsha = fmtgha(0, ra0.hours)
    hpvenus = "{:0.1f}".format((tan(6371/(vau.au*149597870.7)))*60*180/pi)

    # calculate planet transit
    tfr = t0
    tto = ts.ut1(d1.year, d1.month, d1.day, 0, 0, 0)
    position = earth.at(tfr).observe(venus)
    ra = position.apparent().radec(epoch='date')[0]
    #print('Venus transit: ', tfr.gast, ra.hours)
    start00 = Time.time()                   # 00000
    transit_time, y = almanac.find_discrete(tfr, tto, planet_transit(venus))
    config.stopwatch += Time.time()-start00 # 00000
    #if len(transit_time) != 1:
    #    print('returned %s values' %len(transit_time))
    vtrans = rise_set(transit_time,y,u'Venus   0{} E transit'.format(degree_sign),round2seconds)[0]

# Mars
    position0 = earth.at(t0).observe(mars)
    #ra0 = position0.apparent().radec(epoch='date')[0]	# RA
    #mau = position0.apparent().radec(epoch='date')[2]	# distance
    ra0, _, mau = position0.apparent().radec(epoch='date')
    marssha = fmtgha(0, ra0.hours)
    hpmars = "{:0.1f}".format((tan(6371/(mau.au*149597870.7)))*60*180/pi)

    # calculate planet transit
    tfr = t0
    tto = ts.ut1(d1.year, d1.month, d1.day, 0, 0, 0)
    position = earth.at(tfr).observe(mars)
    ra = position.apparent().radec(epoch='date')[0]
    start00 = Time.time()                   # 00000
    transit_time, y = almanac.find_discrete(tfr, tto, planet_transit(mars))
    config.stopwatch += Time.time()-start00 # 00000
    marstrans = rise_set(transit_time,y,u'Mars    0{} E transit'.format(degree_sign),round2seconds)[0]

# Jupiter
    position0 = earth.at(t0).observe(jupiter)
    ra0 = position0.apparent().radec(epoch='date')[0]	# RA
    jsha = fmtgha(0, ra0.hours)

    # calculate planet transit
    tfr = t0
    tto = ts.ut1(d1.year, d1.month, d1.day, 0, 0, 0)
    position = earth.at(tfr).observe(jupiter)
    ra = position.apparent().radec(epoch='date')[0]
    start00 = Time.time()                   # 00000
    transit_time, y = almanac.find_discrete(tfr, tto, planet_transit(jupiter))
    config.stopwatch += Time.time()-start00 # 00000
    jtrans = rise_set(transit_time,y,u'Jupiter 0{} E transit'.format(degree_sign),round2seconds)[0]
    
# Saturn
    position0 = earth.at(t0).observe(saturn)
    ra0 = position0.apparent().radec(epoch='date')[0]	# RA
    satsha = fmtgha(0, ra0.hours)

    # calculate planet transit
    tfr = t0
    tto = ts.ut1(d1.year, d1.month, d1.day, 0, 0, 0)
    position = earth.at(tfr).observe(saturn)
    ra = position.apparent().radec(epoch='date')[0]
    start00 = Time.time()                   # 00000
    transit_time, y = almanac.find_discrete(tfr, tto, planet_transit(saturn))
    config.stopwatch += Time.time()-start00 # 00000
    sattrans = rise_set(transit_time,y,u'Saturn  0{} E transit'.format(degree_sign),round2seconds)[0]
    
    return [vsha,vtrans,marssha,marstrans,jsha,jtrans,satsha,sattrans,hpmars,hpvenus]

def planet_transit(planet_name):
    # Build a function of time that returns a planet's upper transit time.

    def is_planet_transit_at(t):
        """The function that this returns will expect a single argument that is a 
		:class:`~skyfield.timelib.Time` and will return ``True`` if the moon is up
		or twilight has started, else ``False``."""
        t._nutation_angles = iau2000b(t.tt)
        # Return `True` if the meridian is crossed by time `t`.
        position = earth.at(t).observe(planet_name)
        ra = position.apparent().radec(epoch='date')[0]
        #return t.gast > ra.hours	# incorrect
        return (t.gast - ra.hours + 12) % 24 - 12 > 0

    is_planet_transit_at.rough_period = 0.1  # search increment hint
    return is_planet_transit_at

#-----------------------
#   star calculations
#-----------------------

def stellar_info(d):        # used in starstab
    # returns a list of lists with name, SHA and Dec all navigational stars for epoch of date.

    t00 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)   #calculate at midnight
    #t12 = ts.ut1(d.year, d.month, d.day, 12, 0, 0)  #calculate at noon
    out = []

    for line in db.strip().split('\n'):
        x1 = line.index(',')
        name = line[0:x1]
        HIPnum = line[x1+1:]

        star = Star.from_dataframe(df.loc[int(HIPnum)])
        astrometric = earth.at(t00).observe(star).apparent()
        ra, dec, distance = astrometric.radec(epoch='date')

        sha  = fmtgha(0, ra.hours)
        decl = fmtdeg(dec.degrees)

        out.append([name,sha,decl])
    return out

#-----------------------
#   stellar data
#-----------------------

# List of navigational stars with Hipparcos Catalog Number
db = """
Alpheratz,677
Ankaa,2081
Schedar,3179
Diphda,3419
Achernar,7588
Hamal,9884
Polaris,11767
Acamar,13847
Menkar,14135
Mirfak,15863
Aldebaran,21421
Rigel,24436
Capella,24608
Bellatrix,25336
Elnath,25428
Alnilam,26311
Betelgeuse,27989
Canopus,30438
Sirius,32349
Adhara,33579
Procyon,37279
Pollux,37826
Avior,41037
Suhail,44816
Miaplacidus,45238
Alphard,46390
Regulus,49669
Dubhe,54061
Denebola,57632
Gienah,59803
Acrux,60718
Gacrux,61084
Alioth,62956
Spica,65474
Alkaid,67301
Hadar,68702
Menkent,68933
Arcturus,69673
Rigil Kent.,71683
Kochab,72607
Zuben'ubi,72622
Alphecca,76267
Antares,80763
Atria,82273
Sabik,84012
Shaula,85927
Rasalhague,86032
Eltanin,87833
Kaus Aust.,90185
Vega,91262
Nunki,92855
Altair,97649
Peacock,100751
Deneb,102098
Enif,107315
Al Na'ir,109268
Fomalhaut,113368
Scheat,113881
Markab,113963
"""

#--------------------
#   TWILIGHT table
#--------------------

def twilight(d, lat, hemisph, round2seconds = False):  # used in twilighttab (section 1)
    # Returns for given date and latitude(in full degrees):
    # naut. and civil twilight (before sunrise), sunrise, meridian passage, sunset, civil and nautical twilight (after sunset).
    # NOTE: 'twilight' is only called for every third day in the Full Almanac...
    #       ...therefore daily tracking of the sun state is not possible.

    out = [0,0,0,0,0,0]
    lats = "{:3.1f} {}".format(abs(lat), hemisph)
    locn = Topos(lats, "0.0 E")
    dt = datetime(d.year, d.month, d.day, 0, 0, 0)

    if round2seconds:
        dt -= timedelta(seconds=0.5)      # search from 0.5 seconds before midnight
    else:
        dt -= timedelta(seconds=30)       # search from 30 seconds before midnight

    t0 = ts.ut1(dt.year, dt.month, dt.day,   dt.hour, dt.minute, dt.second)
    t1 = ts.ut1(dt.year, dt.month, dt.day+1, dt.hour, dt.minute, dt.second)
    abhd = False                                # above/below horizon display NOT enabled

    # Sunrise/Sunset...
    start00 = Time.time()                   # 00000
    actual, y = almanac.find_discrete(t0, t1, daylength(locn, 0.8333))
    config.stopwatch += Time.time()-start00 # 00000
    out[2], out[3], r2, s2, fs = rise_set(actual,y,lats,round2seconds)
    if out[2] == '--:--' and out[3] == '--:--':	# if neither sunrise nor sunset...
        abhd = True                             # enable above/below horizon display
        yn = midnightsun(d, hemisph)
        out[2] = yn
        out[3] = yn

    # Civil Twilight...
    start00 = Time.time()                   # 00000
    civil, y = almanac.find_discrete(t0, t1, daylength(locn, 6.0))
    config.stopwatch += Time.time()-start00 # 00000
    out[1], out[4], r2, s2, fs = rise_set(civil,y,lats,round2seconds)
    if abhd and out[1] == '--:--' and out[4] == '--:--':	# if neither begin nor end...
        yn = midnightsun(d, hemisph)
        out[1] = yn
        out[4] = yn

    # Nautical Twilight...
    start00 = Time.time()                   # 00000
    naut, y = almanac.find_discrete(t0, t1, daylength(locn, 12.0))
    config.stopwatch += Time.time()-start00 # 00000
    out[0], out[5], r2, s2, fs = rise_set(naut,y,lats,round2seconds)
    if abhd and out[0] == '--:--' and out[5] == '--:--':	# if neither begin nor end...
        yn = midnightsun(d, hemisph)
        out[0] = yn
        out[5] = yn
    
    return out

def midnightsun(d, hemisph):
    # simple way to fudge whether the sun is up or down when there's no
    # sunrise or sunset on date 'dt' depending on the hemisphere only.

    sunup = False
    n = d.month
    if n > 3 and n < 10:    # if April to September inclusive
        sunup = True
    if hemisph == 'S':
        sunup = not(sunup)
    if sunup == True:
        out = r'''\begin{tikzpicture}\draw (0,0) rectangle (12pt,4pt);\end{tikzpicture}'''
    else:
        out = r'''\rule{12Pt}{4Pt}'''
    return out

def daylength(topos, degBelowHorizon):
    # Build a function of time that returns the daylength.
    topos_at = (earth + topos).at

    def is_sun_up_at(t):
        """The function that this returns will expect a single argument that is a 
		:class:`~skyfield.timelib.Time` and will return ``True`` if the sun is up
		or twilight has started, else ``False``."""
        t._nutation_angles = iau2000b(t.tt)
        # Return `True` if the sun has risen by time `t`.
        return topos_at(t).observe(sun).apparent().altaz()[0].degrees > -degBelowHorizon

    is_sun_up_at.rough_period = 0.5  # twice a day
    return is_sun_up_at

#-------------------------
#   MOONRISE/-SET table
#-------------------------

# create a list of 'moon above/below horizon' states per Latitude...
#    None = unknown; True = above horizon (visible); False = below horizon (not visible)
#    moonvisible[0] is not linked to a latitude but a manual override
moonvisible = [None] * 32       # moonvisible[0] up to moonvisible[31]

# create a list of dates with pre-calculated moonrise/moonset data in 'np_array'
#    MoonDate[0 to MDlen-1] = a date, the index of which corresponds to the first index in 'np_array'
# note: this is only used for hh:mm rise/set times (rounded to the minute)
# note: MDlen > 5 has no advantage - it only wastes array memory space
MDlen = 5                   # number of days in transient MoonData store (np_array)
MoonDate = [None] * MDlen   # MoonDate[0] up to MoonDate[MDlen-1]
MDndx = MDlen - 1           # index to latest added date (initially 0 will be chosen)

# create a homogeneous NumPy array of 2 Moon Rise/Set data values per 31 latitudes, up to 'MDlen' adjacent days
#    This increases performance when creating a Nautical Almanac by about 12% 
#       by avoiding data re-calculation in special cases.
#    MoonData[date][lat][item]
#       date[0 to 9] = a date index 'i' corresponding to MoonDate[i]
#       lat[0 to 31] = index 'i' to config.lat[i]
#       item[0] = rise time (hh:mm) or '--:--'
#       item[1] = set  time (hh:mm) or '--:--'
#       item[1][2:3] ... the middle character is 'finalstate' ... 'n' = above horizon; 'v' = below horizon
np_array = np.ndarray(shape=(MDlen,31,2), dtype=np.dtype('U5'))

def getHorizon(t):
    # calculate the angle of the moon below the horizon at moonrise/set

    position = earth.at(t).observe(moon)   # at noontime (for daily average distance)
    distance = position.apparent().radec(epoch='date')[2]
    dist_km = distance.km
# OLD: sdm = degrees(atan(1738.1/dist_km))   # equatorial radius of moon = 1738.1 km
    sdm = degrees(atan(1737.4/dist_km))   # volumetric mean radius of moon = 1737.4 km
    horizon = sdm + 0.5666667	# moon's equatorial radius + 34' (atmospheric refraction)

    return horizon

def fetchMoonData(d, tFrom, tNoon, tTo, i, lats, hFlag = False, round2seconds=False):
    # calculate & store moon data (rise/set times) or fetch data if pre-calculated.
    # --- THIS IMPROVES PERFORMANCE BY AVOIDING DUPLICATE COSTLY CALCULATIONS AS ---
    # --- 76% OF THE ALMANAC EXECUTION TIME IS SPENT IN almanac.find_discrete()  ---
    # The temporary data store 'np_array' continually overwrites itself with fresh data.
    # note: the transient data store is disabled if rounding to seconds

    # obtain the index to the current date 'd' ... or assign a new index
    global MDndx, MDlen
    iFnd = False
    idx = -1            # an invalid value
    min_d = d
    for k in range(MDlen):
        if MoonDate[k] == d:
            ndx = k
            iFnd = True
        if config.moonDaysCount >= 31 * MDlen and MoonDate[k] < min_d:
            min_d = MoonDate[k]     # find oldest date in 'MoonDate'
            idx = k
    if not iFnd:
        # assigining a new index in a rotary fashion works, however a more intelligent algorithm
        #   is to re-use the index to the oldest date once all 'MDlen' dates are in use.
        if config.moonDaysCount >= 31 * MDlen:
            # assign a new index by re-using the oldest date
            ndx = idx
            MoonDate[ndx] = d
        else:
            # assign a new index in a rotary fashion
            MDndx = (MDndx + 1) % MDlen
            ndx = MDndx
            MoonDate[ndx] = d
        for k in range(31):     # IMPORTANT ... and clear all old values!!!
            np_array[ndx][k][0] = b''
            np_array[ndx][k][1] = b''

    # check the transient data store...
    if round2seconds or len(np_array[ndx][i-1][0]) == 0:     # no data stored - calculate new values

        locn = Topos(lats, "0.0 E")
        horizon = getHorizon(tNoon)
        start00 = Time.time()                   # 00000
        moonrise, y = almanac.find_discrete(tFrom, tTo, moonday(locn, horizon))
        time00 = Time.time()-start00 # 00000
        rise, sett, ris2, set2, fs = rise_set(moonrise,y,lats,round2seconds)

        # only store single events (not double events, which are very rare)
        if ris2 == '--:--' and set2 == '--:--':
            # save 'sett' with moon's finalstate (above/below horizon or currently unknown)
            if fs == True:
                set9 = sett[0:2] + 'n' + sett[3:5]
            elif fs == False:
                set9 = sett[0:2] + 'v' + sett[3:5]
            else:
                set9 = sett

            np_array[ndx][i-1][0] = rise.encode('utf-8')
            np_array[ndx][i-1][1] = set9.encode('utf-8')
        
        #print("np_array[{}][{}][{}] = {}".format(ndx,i-1,0,np_array[ndx][i-1][0]))
        #print("np_array[{}][{}][{}] = {}".format(ndx,i-1,1,np_array[ndx][i-1][1]))
        if hFlag:
            config.stopwatch2 += time00
        else:
            config.stopwatch += time00
    else:                               # fetch stored data
        rise = np_array[ndx][i-1][0]
        sett = np_array[ndx][i-1][1]
        ris2 = '--:--'
        set2 = '--:--'
        fstate = sett[2:3]      # moon final state  (above/below horizon, if known)
        sett = sett[0:2] + ':' + sett[3:5]  # replace middle character
        fs = None

        if fstate == "n":
            fs = True
        elif fstate == "v":
            fs = False

        if hFlag:
            config.moonHorizonFound += 1    # "data found in transient store" count
        else:
            config.moonDataFound += 1       # "data found in transient store" count

    return rise, sett, ris2, set2, fs


def moonrise_set(d, lat, hemisph):  # used by tables.py in twilighttab (section 2)
    # - - - TIMES ARE ROUNDED TO MINUTES - - -
    # returns moonrise and moonset for the given dates and latitude:
    # rise day 1, rise day 2, rise day 3, set day 1, set day 2, set day 3
    # Additionally it also tracks the current state of the moon (above or below horizon)

    i = 1 + config.lat.index(lat)   # index 0 is reserved to enable an explicit setting
    out  = ['--:--','--:--','--:--','--:--','--:--','--:--']	# first event
    out2 = ['--:--','--:--','--:--','--:--','--:--','--:--']	# second event on same day (rare)
    lats = "{:3.1f} {}".format(abs(lat), hemisph)
    locn = Topos(lats, "0.0 E")
    dt = datetime(d.year, d.month, d.day, 0, 0, 0)
    dt -= timedelta(seconds=30)       # search from 30 seconds before midnight

    d9 = d + timedelta(days=-1)
    t9 = ts.ut1(dt.year, dt.month, dt.day-1, dt.hour, dt.minute, dt.second)

    t0 = ts.ut1(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    d1 = d + timedelta(days=1)
    t1 = ts.ut1(dt.year, dt.month, dt.day+1, dt.hour, dt.minute, dt.second)

    d2 = d + timedelta(days=2)
    t2 = ts.ut1(dt.year, dt.month, dt.day+2, dt.hour, dt.minute, dt.second)

    d3 = d + timedelta(days=3)
    t3 = ts.ut1(dt.year, dt.month, dt.day+3, dt.hour, dt.minute, dt.second)

    t4 = ts.ut1(dt.year, dt.month, dt.day+4, dt.hour, dt.minute, dt.second)

    # get the angle of the moon below the horizon at noontime (for daily average distance)
    t9noon = ts.ut1(dt.year, dt.month, dt.day, dt.hour-12, dt.minute, dt.second)
    t0noon = ts.ut1(dt.year, dt.month, dt.day, dt.hour+12, dt.minute, dt.second)
    t1noon = ts.ut1(dt.year, dt.month, dt.day+1, dt.hour+12, dt.minute, dt.second)
    t2noon = ts.ut1(dt.year, dt.month, dt.day+2, dt.hour+12, dt.minute, dt.second)
    t3noon = ts.ut1(dt.year, dt.month, dt.day+3, dt.hour+12, dt.minute, dt.second)

    #horizon = 0.8333333        # 16' (semi-diameter) + 34' (atmospheric refraction)
#-----------------------------------------------------------
    # Moonrise/Moonset on 1st. day ...

    # first compute semi-diameter of moon (in degrees)
    horizon = getHorizon(t0noon)

    config.moonDaysCount += 1
    config.moonDataSeeks += 1
    out[0], out[3], out2[0], out2[3], fs = fetchMoonData(d, t0, t0noon, t1, i, lats)

    if fs != None:
        moonvisible[i] = fs

    if out[0] == '--:--' and out[3] == '--:--':	# if neither moonrise nor moonset...
        config.moonDataSeeks -= 1
        if moonvisible[i] == None:
            getmoonstate(dt, lat, hemisph)			# ...get moon state if unknown
        out[0] = moonstate(i)
        out[3] = moonstate(i)

    if out[0] == '--:--' and out[3] != '--:--':	# if moonset but no moonrise...
        out[0] = moonset_no_rise(d, lat, d9, t9, t9noon, t0, d1, t1, t1noon, t2, i, lats)

    if out[0] != '--:--' and out[3] == '--:--':	# if moonrise but no moonset...
        out[3] = moonrise_no_set(d, lat, d9, t9, t9noon, t0, d1, t1, t1noon, t2, i, lats)

#-----------------------------------------------------------
    # Moonrise/Moonset on 2nd. day ...

    # first compute semi-diameter of moon (in degrees)
    horizon = getHorizon(t1noon)

    config.moonDaysCount += 1
    config.moonDataSeeks += 1
    out[1], out[4], out2[1], out2[4], fs = fetchMoonData(d1, t1, t1noon, t2, i, lats)

    if fs != None:
        moonvisible[i] = fs

    if out[1] == '--:--' and out[4] == '--:--':	# if neither moonrise nor moonset...
        config.moonDataSeeks -= 1
        if moonvisible[i] == None:
            getmoonstate(dt+timedelta(days=1), lat, hemisph)    # ...get moon state if unknown
        out[1] = moonstate(i)
        out[4] = moonstate(i)

    if out[1] == '--:--' and out[4] != '--:--':	# if moonset but no moonrise...
        out[1] = moonset_no_rise(d1, lat, d, t0, t0noon, t1, d2, t2, t2noon, t3, i, lats)

    if out[1] != '--:--' and out[4] == '--:--':	# if moonrise but no moonset...
        out[4] = moonrise_no_set(d1, lat, d, t0, t0noon, t1, d2, t2, t2noon, t3, i, lats)

#-----------------------------------------------------------
    # Moonrise/Moonset on 3rd. day ...

    # first compute semi-diameter of moon (in degrees)
    horizon = getHorizon(t2noon)

    config.moonDaysCount += 1
    config.moonDataSeeks += 1
    out[2], out[5], out2[2], out2[5], fs = fetchMoonData(d2, t2, t2noon, t3, i, lats)

    if fs != None:
        moonvisible[i] = fs

    if out[2] == '--:--' and out[5] == '--:--':	# if neither moonrise nor moonset...
        config.moonDataSeeks -= 1
        if moonvisible[i] == None:
            getmoonstate(dt+timedelta(days=2), lat, hemisph)    # ...get moon state if unknown
        out[2] = moonstate(i)
        out[5] = moonstate(i)

    if out[2] == '--:--' and out[5] != '--:--':	# if moonset but no moonrise...
        out[2] = moonset_no_rise(d2, lat, d1, t1, t1noon, t2, d3, t3, t3noon, t4, i, lats)

    if out[2] != '--:--' and out[5] == '--:--':	# if moonrise but no moonset...
        out[5] = moonrise_no_set(d2, lat, d1, t1, t1noon, t2, d3, t3, t3noon, t4, i, lats)

    return out, out2

def moonday(topos, degBelowHorizon):
    # Build a function of time that returns the "moonlight daylength".
    topos_at = (earth + topos).at

    def is_moon_up_at(t):
        """The function that this returns will expect a single argument that is a 
		:class:`~skyfield.timelib.Time` and will return ``True`` if the moon is up
		or twilight has started, else ``False``."""
        t._nutation_angles = iau2000b(t.tt)
        # Return `True` if the moon has risen by time `t`.
        return topos_at(t).observe(moon).apparent().altaz()[0].degrees > -degBelowHorizon

    is_moon_up_at.rough_period = 0.5  # twice a day
    return is_moon_up_at


def moonstate(ndx):
    # return the current moonstate (if known)
    out = '--:--'
    if moonvisible[ndx] == True:
        #out = 'UP'
        #out = r'''\framebox(12,4){}'''
        #out = r'''{\setlength{\fboxrule}{0.8pt}\setlength{\fboxsep}{0pt}\fbox{\makebox(12,4){}}}'''
        #out = r'''{\setlength{\fboxrule}{0.8pt}\fbox{\parbox[c][0pt]{0pt}{ }}}'''
        #out = r'''\includegraphics[scale=1.0]{./moonup.jpg}'''
        out = r'''\begin{tikzpicture}\draw (0,0) rectangle (12pt,4pt);\end{tikzpicture}'''
    if moonvisible[ndx] == False:
        #out = 'DOWN'
        out = r'''\rule{12Pt}{4Pt}'''
    return out


def getmoonstate(dt, lat, hemisph):
    # populate the moon state (visible or not) for the specified date & latitude
    # note: the first parameter 'dt' is already a datetime 30 seconds before midnight
    #       (for Nautical Almanac) or 0.5 sec before midnight (for Event Time tables)
    # note: getmoonstate is called when there is neither a moonrise nor a moonset on 'dt'

    i = 1 + config.lat.index(lat)   # index 0 is reserved to enable an explicit setting
    lats = '{:3.1f} {}'.format(abs(lat), hemisph)
    locn = Topos(lats, '0.0 E')
    t0 = ts.ut1(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    horizon = 0.8333

    # search for the next moonrise or moonset (returned in moonrise[0] and y[0])
    while moonvisible[i] == None:
        t0 = ts.ut1(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        dt += timedelta(days=1)
        t9 = ts.ut1(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        start00 = Time.time()                   # 00000
        moonrise, y = almanac.find_discrete(t0, t9, moonday(locn, horizon))
        config.stopwatch2 += Time.time()-start00 # 00000
#        for n in range(len(moonrise)):
#            print(y[n], moonrise[n].utc_datetime())
        if len(moonrise) > 0:
#            print()
            if y[0]:
                moonvisible[i] = False
            else:
                moonvisible[i] = True

    return

def moonset_no_rise(Date, lat, prday, t9, t9noon, t0, nxday, t1, t1noon, t2, i, lats, round2seconds=False):
    # if moonset but no moonrise...
    msg = ""
    n = seek_moonrise(prday, t9, t9noon, t0, nxday, t1, t1noon, t2, i, lats, round2seconds)
    if n == 1:
        out = moonstate(i)       # moonrise "below horizon"
        msg = "below horizon (start)"
    if n == -1:
        #print("UP")
        moonvisible[0] = True
        out = moonstate(0)       # moonrise "above horizon"
        msg = "above horizon (end)"
        #print(out[0])
    #if msg != "": print("no moonrise on {} at lat {} => {}".format(Date.strftime("%Y-%m-%d"), lat, msg))
    if n == 0:
        out = r'''\raisebox{0.24ex}{\boldmath$\cdot\cdot$~\boldmath$\cdot\cdot$}'''
    return out

def moonrise_no_set(Date, lat, prday, t9, t9noon, t0, nxday, t1, t1noon, t2, i, lats, round2seconds=False):
    # if moonrise but no moonset...
    msg = ""
    n = seek_moonset(prday, t9, t9noon, t0, nxday, t1, t1noon, t2, i, lats, round2seconds)
    if n == 1:
        out = moonstate(i)       # moonset "above horizon"
        msg = "above horizon (start)"
    if n == -1:
        moonvisible[0] = False
        out = moonstate(0)       # moonset "below horizon"
        msg = "below horizon (end)"
    #if msg != "": print("no moonset on  {} at lat {} => {}".format(Date.strftime("%Y-%m-%d"), lat, msg))
    if n == 0:
        out = r'''\raisebox{0.24ex}{\boldmath$\cdot\cdot$~\boldmath$\cdot\cdot$}'''
    return out

def seek_moonset(prday, t9, t9noon, t0, nxday, t1, t1noon, t2, i, lats, round2seconds=False):
    # for the specified date & latitude ...
    # return -1 if there is NO MOONSET yesterday
    # return +1 if there is NO MOONSET tomorrow
    # return  0 if there was a moonset yesterday and will be a moonset tomorrow
    # note: this is called when there is only a moonrise on the specified date+latitude

    config.moonHorizonSeeks += 1
    m_set_t = 0     # normal case: assume moonsets yesterday & tomorrow

    rise, sett, ris2, set2, fs = fetchMoonData(nxday, t1, t1noon, t2, i, lats, True, round2seconds)

    if sett == '--:--':
        m_set_t = +1    # if no moonset detected - it is after tomorrow
    else:
        config.moonHorizonSeeks += 1
        rise, sett, ris2, set2, fs = fetchMoonData(prday, t9, t9noon, t0, i, lats, True, round2seconds)

        if sett == '--:--':
            m_set_t = -1    # if no moonset detected - it is before yesterday

    return m_set_t

def seek_moonrise(prday, t9, t9noon, t0, nxday, t1, t1noon, t2, i, lats, round2seconds=False):
    # return -1 if there is NO MOONRISE yesterday
    # return +1 if there is NO MOONRISE tomorrow
    # return  0 if there was a moonrise yesterday and will be a moonrise tomorrow
    # note: this is called when there is only a moonset on the specified date+latitude

    config.moonHorizonSeeks += 1
    m_rise_t = 0    # normal case: assume moonrise yesterday & tomorrow

    rise, sett, ris2, set2, fs = fetchMoonData(nxday, t1, t1noon, t2, i, lats, True)

    if rise == '--:--':
        m_rise_t = +1    # if no moonrise detected - it is after tomorrow
    else:
        config.moonHorizonSeeks += 1
        rise, sett, ris2, set2, fs = fetchMoonData(prday, t9, t9noon, t0, i, lats, True)

        if rise == '--:--':
            m_rise_t = -1    # if no moonrise detected - it is before yesterday

    return m_rise_t

#-------------------------
#   EVENT TIME tables
#-------------------------

def moonrise_set2(d, lat, hemisph):  # used in twilighttab of eventtables.py
    # - - - TIMES ARE ROUNDED TO SECONDS - - -
    # returns moonrise and moonset for the given date and latitude:
    #    rise time, set time
    # Additionally it also tracks the current state of the moon (above or below horizon)

    i = 1 + config.lat.index(lat)   # index 0 is reserved to enable an explicit setting
    out  = ['--:--','--:--']	# first event
    out2 = ['--:--','--:--']	# second event on same day (rare)

    lats = "{:3.1f} {}".format(abs(lat), hemisph)
    locn = Topos(lats, "0.0 E")
    dt = datetime(d.year, d.month, d.day, 0, 0, 0)
    dt -= timedelta(seconds=0.5)   # search from 0.5 seconds before midnight

    d9 = d + timedelta(days=-1)
    t9 = ts.ut1(dt.year, dt.month, dt.day-1, dt.hour, dt.minute, dt.second)

    t0 = ts.ut1(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    d1 = d + timedelta(days=1)
    t1 = ts.ut1(dt.year, dt.month, dt.day+1, dt.hour, dt.minute, dt.second)

    t2 = ts.ut1(dt.year, dt.month, dt.day+2, dt.hour, dt.minute, dt.second)

    t9noon = ts.ut1(dt.year, dt.month, dt.day, dt.hour-12, dt.minute, dt.second)
    t0noon = ts.ut1(dt.year, dt.month, dt.day, dt.hour+12, dt.minute, dt.second)
    t1noon = ts.ut1(dt.year, dt.month, dt.day+1, dt.hour+12, dt.minute, dt.second)

    #horizon = 0.8333           # 16' (semi-diameter) + 34' (atmospheric refraction)
#-----------------------------------------------------------
    # Moonrise/Moonset on the selected day ...

    # first compute semi-diameter of moon (in degrees)
    horizon = getHorizon(t0noon)

    out[0], out[1], out2[0], out2[1], fs = fetchMoonData(d, t0, t0noon, t1, i, lats, False, True)

    if fs != None:
        moonvisible[i] = fs

    if out[0] == '--:--' and out[1] == '--:--':	# if neither moonrise nor moonset...
        if moonvisible[i] == None:
            getmoonstate(dt, lat, hemisph)			# ...get moon state if unknown
        out[0] = moonstate(i)
        out[1] = moonstate(i)

    if out[0] == '--:--' and out[1] != '--:--':	# if moonset but no moonrise...
        out[0] = moonset_no_rise(d, lat, d9, t9, t9noon, t0, d1, t1, t1noon, t2, i, lats, True)

    if out[0] != '--:--' and out[1] == '--:--':	# if moonrise but no moonset...
        out[1] = moonrise_no_set(d, lat, d9, t9, t9noon, t0, d1, t1, t1noon, t2, i, lats, True)

    return out, out2

#------------------------------
#   Equation of Time section
#------------------------------

def getGHA(d, hh, mm, ss):
    # calculate the Moon's GHA on date d at hh:mm:ss (ss can be a float)
    t1 = ts.ut1(d.year, d.month, d.day, hh, mm, ss)
    pos = earth.at(t1).observe(moon)
    ra = pos.apparent().radec(epoch='date')[0]
    gha = gha2deg(t1.gast, ra.hours)
    return gha      # GHA as float (degrees)

def roundup(hr, mi):
    # round time up to next minute. Both arguments are integers and all times are within one day.
    # Times (for calculation) between 23:59:30 and 00:00:00 are rounded up to 00:00 ... no 
    # date adjustment is necessary as the calculated time came on purpose from the day before.

    mi += 1         # round minutes up
    if(mi == 60):
        mi = 0
        hr += 1     # round hours up
    if(hr == 24):
        hr = 0
    return hr, mi

def find_transit(d, ghaList, modeLT):
    # Determine the Transit Event Time rounded to the nearest minute.

    # ghaList contains the 'hourly' GHA values on day 'd' for the times:
    #  23:59:30 on d-1; 01:00; 02:00; 03:00 ... 21:00; 22:00; 23:00; 23:59:30
    # Events between 23:59:30 on d-1 and 23:59:30 will show as 00:00 to 23:59

    # This effectively filters out events after 30 seconds before midnight
    #  as these belong to the next day once rounded up to 00:00.
    # Furthermore those from the last 30 seconds of the previous day
    #  will be automatically included (as 00:00).

    # This method may also be used to determine the Lower transit by replacing
    #  GHA with the colongitude GHA (and an adapted ghaList). Thus...
    # modeLT = False means find Upper Transit; = True means find Lower Transit
    
    # This OPTIMIZED version does not calculate every minute from 0 to 59 until
    # it detects a transit event. The minutes search begins from 'min_start'
    # and is so chosen that 2 or 3 values before the event are searched (with the
    # exception when the search begins from zero minutes, where the event might
    # follow immediately).

    # If the transit event is very close to the mid-point between minutes, one cannot
    # reliably estimate to round up or down without inspecting the mid-point GHA value.

    if modeLT:
        txt = "Lower Transit"
    else:
        txt = "Upper Transit"
    hr = -1                 # an invalid hour value
    transit_time = '--:--'  # assume 'no event'
    prev_gha = 0
    prev_time = '--:--'
    mid_gha = 0
    mid_time = '--:--:--'
    gha = 0
    gha_time = '--:--'
    gha = ghaList[0]    # GHA at 23:59:30 on d-1
    gha_top = 360       # min_start defaults to 0

    # find the hour after which the transit event occurs
    for i in range(24): # 0 to 23
        if(ghaList[i+1] < gha):
            hr = i      # event is between hr:00 and {hr+1}:00
            gha_top = ghaList[i]
            break
        gha = ghaList[i+1]  # test GHA at {hr+1}:00

    # estimate where to begin searching by the minute
    min_start = max(0, int((360-gha_top)/0.25)-1)
    if hr == 0:
        # compensation for gha at Start-of-Day being 30 seconds earlier at 23:59:30
        min_start = max(0, min_start-1)

    if hr< 0:
        return transit_time     # no event detected this day

    # if event found... locate it more precisely (to the minute)
    iLoops = 0
    prev_gha = ghaList[i]    # GHA before the event (typically on the hour)
    prev_time = "{:02d}:{:02d}".format(hr,0)
    for mi in range(min_start,60):       # 0 to 59 max
        gha = getGHA(d, hr, mi+1, 0)   # GHA on the minute after the event
        gha_time = "{:02d}:{:02d}".format(hr,mi+1)
        if(modeLT):
            gha = GHAcolong(gha)
        if(gha < prev_gha):
            if(iLoops == 0 and mi > 0): raise ValueError('ERROR: min_start ({}) too large on {} at {} ({})'.format(mi, d, gha_time, txt))
            break       # break when event detected ('hr:mi' is before the event)
        prev_gha = gha  # GHA on the minute before the event
        prev_time = "{:02d}:{:02d}".format(hr,mi+1)
        iLoops += 1

    mid_time = '-'      # no value yet for mid-way between minutes
    diff = prev_gha - 360 + gha      # if negative, round time up

    if(hr == 23 and mi == 59):
        pass            # events between 23:59 and 23:59:30 never round up to 00:00 next day

    elif(hr == 0 and mi == 0):
        mid_gha = getGHA(d, hr, mi, 30)
        mid_time = "{:02d}:{:02d}:{:02d}".format(hr,mi,30)
        if(modeLT):
            mid_gha = GHAcolong(mid_gha)
        if(mid_gha > 180):
            hr, mi = roundup(hr, mi)   # midway is before the event (round minutes up)

    elif(abs(diff) < 0.002):
        # midpoint too close to the transit event to estimate round up or down.
        #    Check the GHA 30 sec later (midway between minutes).
        # (The GHA changes by 0.002 in about 0.5 seconds time)
        mid_gha = getGHA(d, hr, mi, 30)
        mid_time = "{:02d}:{:02d}:{:02d}".format(hr,mi,30)
        if(modeLT):
            mid_gha = GHAcolong(mid_gha)
        if(mid_gha > 180):
            hr, mi = roundup(hr, mi)   # midway is before the event (round minutes up)

    elif(diff < 0):
        # just compare which GHA is closer to zero GHA and round accordingly
        hr, mi = roundup(hr, mi)   # midway is before the event (round minutes up)

    transit_time = "{:02d}:{:02d}".format(hr,mi)
    return transit_time


def roundup2(hr, mi, se):
    # round time up to next second. All arguments are integers and all times are within one day.
    # Times (for calculation) between 23:59:59.5 and 00:00:00 are rounded up to 00:00:00 ... no 
    # date adjustment is necessary as the calculated time came on purpose from the day before.

    se += 1         # round seconds up
    if(se == 60):
        se = 0
        mi += 1     # round minutes up
    if(mi == 60):
        mi = 0
        hr += 1     # round hours up
    if(hr == 24):
        hr = 0
    return hr, mi, se

def find_transit2(d, ghaList, modeLT):
    # Determine the Transit Event Time rounded to the nearest second.

    # ghaList contains the 'hourly' GHA values on day 'd' for the times:
    #  23:59:59.5 on d-1; 01:00; 02:00; 03:00 ... 21:00; 22:00; 23:00; 23:59:59.5
    # Events between 23:59:59.5 on d-1 and 23:59:59.5 will show as 00:00:00 to 23:59:59

    # This effectively filters out events after 0.5 seconds before midnight
    #  as these belong to the next day once rounded up to 00:00:00.
    # Furthermore those from the last 0.5 seconds of the previous day
    #  will be automatically included (as 00:00:00).

    # This method may also be used to determine the Lower transit by replacing
    #  GHA with the colongitude GHA (and an adapted ghaList). Thus...
    # modeLT = False means find Upper Transit; = True means find Lower Transit
    
    # This OPTIMIZED version does not calculate every minute from 0 to 59 
    # and then every second from 0 to 59 until it detects a transit event. 
    # The minutes search begins from 'min_start'; the seconds search from 'sec_start'
    # and are so chosen that 2 or 3 values before the event are searched (with the
    # exception when either minutes or seconds search begins from zero where the event
    #  might follow immediately).

    # If the transit event is very close to the mid-point between minutes/seconds, one
    # cannot reliably estimate to round up or down without inspecting the mid-point GHA value.

    if modeLT:
        txt = "Lower Transit"
    else:
        txt = "Upper Transit"
    hr = -1             # an invalid hour value
    transit_time = '--:--'  # assume 'no event'
    prev_gha = 0
    prev_time = '--:--'
    mid_gha = 0
    mid_time = '--:--:--'
    gha = 0
    gha_time = '--:--'
    gha = ghaList[0]    # GHA at 23:59:59.5 on d-1
    gha_top = 360       # min_start defaults to 0

    # find the hour after which the transit event occurs
    for i in range(24): # 0 to 23
        if(ghaList[i+1] < gha):
            hr = i      # event is between hr:00:00 and {hr+1}:00:00
            gha_top = ghaList[i]
            break
        gha = ghaList[i+1]  # test GHA at {hr+1}:00:00
    # estimate where to begin searching by the minute
    min_start = max(0, int((360-gha_top)/0.25)-1)

    if hr< 0:
        return transit_time     # no event detected this day

    # if event found... locate it more precisely (to the minute)
    iLoops = 0
    prev_gha = ghaList[i]       # GHA before the event (typically on the hour)
    prev_time = "{:02d}:{:02d}".format(hr,0)
    gha = getGHA(d, hr, 0, 0)   # GHA on the minute after the event
    for mi in range(min_start,60):      # 0 to 59 max
        gha = getGHA(d, hr, mi+1, 0)    # GHA on the minute after the event
        gha_time = "{:02d}:{:02d}".format(hr,mi+1)
        if(modeLT):
            gha = GHAcolong(gha)
        if(gha < prev_gha):
            if(iLoops == 0 and mi > 0): raise ValueError('ERROR: min_start ({}) too large on {} at {} ({})'.format(mi, d, gha_time, txt))
            break       # break when event detected ('hr:mi' is before the event)
        prev_gha = gha  # GHA on the minute before the event
        prev_time = "{:02d}:{:02d}".format(hr,mi+1)
        iLoops += 1

    # again locate it more precisely (to the second)
    iLoops = 0
    # NOTE: 0.25 in the sec_start equation below works for every day except 24.08.2063 (Lower Transit)
    #       0.26 is a better choice
    #val = (360-prev_gha)/0.25*60.0
    sec_start = max(0, int((360-prev_gha)/0.26*60.0)-1)
    for se in range(sec_start,60):      # 0 to 59 max
        gha = getGHA(d, hr, mi, se+1)   # GHA on the second after the event
        gha_time = "{:02d}:{:02d}:{:02d}".format(hr,mi,se+1)
        if(modeLT):
            gha = GHAcolong(gha)
        if(gha < prev_gha):
            if(iLoops == 0 and se > 0): raise ValueError('ERROR: sec_start ({}) too large on {} at {} ({})'.format(se, d, gha_time, txt))
            #if(iLoops == 0 and se > 0): raise ValueError('ERROR: sec_start ({}) too large on {} at {} ({}) val = {:f}'.format(se, d, gha_time, txt, val))
            break       # break when event detected ('hr:mi:se' is before event)
        prev_gha = gha  # GHA each second before the event
        prev_time = "{:02d}:{:02d}:{:02d}".format(hr,mi,se+1)
        iLoops += 1

    mid_time = '-'      # no value yet for mid-way between seconds
    diff = prev_gha - 360.0 + gha      # if negative, round time up

    if(hr == 23 and mi == 59 and se == 59):
        pass            # events between 23:59:59 and 23:59:59.5 never round up to 00:00:00 next day

    elif(hr == 0 and mi == 0 and se == 0):
        mid_gha = getGHA(d, hr, mi, se+0.5)
        mid_time = "{:02d}:{:02d}:{:04.1f}".format(hr,mi,se+0.5)
        if(modeLT):
            mid_gha = GHAcolong(mid_gha)
        if(mid_gha > 180):
            hr, mi, se = roundup2(hr, mi, se)    # midway is before the event (round seconds up)

    elif(abs(diff) < 0.001):
        # midpoint too close to the transit event to estimate round up or down...
        #    Check the GHA 0.5 sec later (midway between seconds).
        # (The GHA changes by 0.002 in about 0.5 seconds time)
        mid_gha = getGHA(d, hr, mi, se+0.5)
        mid_time = "{:02d}:{:02d}:{:04.1f}".format(hr,mi,se+0.5)
        if(modeLT):
            mid_gha = GHAcolong(mid_gha)
        if(mid_gha > 180):
            hr, mi, se = roundup2(hr, mi, se)    # midway is before the event (round seconds up)

    elif(diff < 0):
        # just compare which GHA is closer to zero GHA and round accordingly
        hr, mi, se = roundup2(hr, mi, se)     # closer to following GHA (round seconds up)

    transit_time = "{:02d}:{:02d}:{:02d}".format(hr,mi,se)
    return transit_time


def moonphase(d):           # used in twilighttab (section 3)
    # returns the moon's elongation (angle to the sun)

    # convert python 'date' to 'date with time' ...
    dt = datetime(d.year, d.month, d.day, 0, 0, 0)
    # phase is calculated at noon
    dt += timedelta(hours=12)

    t00 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)
    #t12 = ts.ut1(d.year, d.month, d.day, 12, 0, 0)
    phase_angle = almanac.phase_angle(eph, 'moon', t00)     # OLD: t12
    elong = phase_angle.radians

    # phase_angle.degrees is ...
    # 180 at New Moon, drops to 0 at Full Moon, then rises to 180 at New Moon
    
    #pnm = PreviousNewMoon.replace(tzinfo=None)
    #nfm = NextFullMoon.replace(tzinfo=None)
    #pfm = PreviousFullMoon.replace(tzinfo=None)
    #nnm = NextNewMoon.replace(tzinfo=None)

    if WaxingMoon:
        phase = pi - phase_angle.radians
    else:
        phase = pi + phase_angle.radians

    return phase

def moonage(d, d1):         # used in twilighttab (section 3)
    # return the moon's 'age' and percent illuminated

    # percent illumination is calculated at midnight
    t00 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)
    #t12 = ts.ut1(d.year, d.month, d.day, 12, 0, 0)
    phase_angle = almanac.phase_angle(eph, 'moon', t00)     # OLD: t12
    pctrad = 50 * (1.0 + cos(phase_angle.radians))
    pct = "{:.0f}".format(pctrad)

    # calculate age of moon

    pnm = PreviousNewMoon
    nnm = NextNewMoon
    #dt0 = date(pnm.year, pnm.month, pnm.day)
    #dt1 = date(nnm.year, nnm.month, nnm.day)
    dt = datetime.combine(d1, time(0, 0))
    age1td = dt-pnm.replace(tzinfo=None)
    age2td = dt-nnm.replace(tzinfo=None)
    age1 = age1td.days
    age2 = age2td.days
    age = age1
    if age2 >= 0:
        age = age2

    return age,pct

def equation_of_time(d, d1, UpperList, LowerList, extras, round2seconds = False):  # used in twilighttab (section 3)
    # returns equation of time, the sun's transit time, 
    # the moon's transit-, antitransit-time, age and percent illumination.
    # (Equation of Time = Mean solar time - Apparent solar time)

    t00 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)       # EoT at 00h
    position = earth.at(t00).observe(sun)
    ra = position.apparent().radec(epoch='date')[0]
    gha00 = gha2deg(t00.gast, ra.hours)
    eqt00 = gha2eqt(gha00)
    if gha00 <= 180:
        eqt00 = r"\colorbox{{lightgray!60}}{{{}}}".format(eqt00)

    t12 = ts.ut1(d.year, d.month, d.day, 12, 0, 0)      # EoT at 12h
    position = earth.at(t12).observe(sun)
    ra = position.apparent().radec(epoch='date')[0]
    gha12 = gha2deg(t12.gast, ra.hours)
    eqt12 = gha2eqt(gha12)
    if gha12 > 270:
        eqt12 = r"\colorbox{{lightgray!60}}{{{}}}".format(eqt12)

    if round2seconds:
        mpa12 = gha2mpa2(gha12)

        # !! transit times are rounded to the nearest second,
        # !! so the search needs to start and end 0.5 sec earlier
        # !! e.g. after 23h 59m 59.5s rounds up to 00:00:00 next day

        # calculate moon upper transit
        mp_upper = find_transit2(d, UpperList, False)
        # calculate moon lower transit
        mp_lower = find_transit2(d, LowerList, True)
    else:
        mpa12 = gha2mpa(gha12)

        # !! transit times are rounded to the nearest minute,
        # !! so the search needs to start and end 30 sec earlier
        # !! e.g. after 23h 59m 30s rounds up to 00:00 next day

        # calculate moon upper transit
        mp_upper = find_transit(d, UpperList, False)
        # calculate moon lower transit
        mp_lower = find_transit(d, LowerList, True)

    if not(extras):     # omit 'age' and 'pct'
        return eqt00,eqt12,mpa12,mp_upper,mp_lower

    # percent illumination is calculated at midnight
    phase_angle = almanac.phase_angle(eph, 'moon', t00)     # OLD: t12
    pctrad = 50 * (1.0 + cos(phase_angle.radians))
    pct = "{:.0f}".format(pctrad)

    # calculate age of moon

    pnm = PreviousNewMoon
    nnm = NextNewMoon
    #dt0 = date(pnm.year, pnm.month, pnm.day)
    #dt1 = date(nnm.year, nnm.month, nnm.day)
    dt = datetime.combine(d1, time(0, 0))
    age1td = dt-pnm.replace(tzinfo=None)
    age2td = dt-nnm.replace(tzinfo=None)
    age1 = age1td.days
    age2 = age2td.days
    age = age1
    if age2 >= 0:
        age = age2

    return eqt00,eqt12,mpa12,mp_upper,mp_lower,age,pct

def gha2mpa(gha):
    # format an hour angle as 'Sun Mer. Pass' (hh:mm)
    hhmm = '--:--'
    if gha > 270:
        gha = 360 - gha
        mpa = 12 + (gha * 4.0)/60.0
    else:
        mpa = 12 - (gha * 4.0)/60.0

    hr  = int(mpa)
    mi = int(round((mpa - hr) * 60.0)) # minutes round to nearest minute
    if mi == 60:
        mi = 0		# this cannot happen
        hr += 1
    hhmm = '{:02d}:{:02d}'.format(hr,mi)
    return hhmm

def gha2mpa2(gha):
    # format an hour angle as 'Sun Mer. Pass' (hh:mm:ss)
    hhmm = '--:--'
    if gha > 270:
        gha = 360 - gha
        mpa = 12 + (gha * 4.0)/60.0
    else:
        mpa = 12 - (gha * 4.0)/60.0

    hr  = int(mpa)
    mi  = (mpa - hr) * 60.0
    mr  = int(mi)
    se  = (mi - mr) * 60.0
    sr  = int(round(se))    # seconds rounded to nearest second
    if sr == 60:
        sr = 0
        mr += 1
    if mr == 60:
        mr = 0
        hr += 1
    hhmmss = '{:02d}:{:02d}:{:02d}'.format(hr,mr,sr)
    return hhmmss

def gha2eqt(gha):
    # format an hour angle as 'Eqn. of Time' (mm:ss)
    if 100 < gha < 260:
        if gha > 180:
            gha = gha - 180
        else:
            gha = 180 - gha
    else:
        if gha > 270:
            gha = 360 - gha

    eqt = abs(gha * 4.0)	# Eqn. of Time is always positive
    mi = int(eqt)
    sr = int(round((eqt - mi) * 60.0))  # seconds rounded to nearest second
    if sr == 60:
        sr = 0
        mi += 1
    if mi <= 59:
        mmss = '{:02d}:{:02d}'.format(mi,sr)
    else:
        mmss = '??:??'		# indicate error
    return mmss

def find_new_moon(d):       # used in doublepage
    # find previous & next new moon and full moon
    global PreviousNewMoon
    global PreviousFullMoon
    global NextNewMoon
    global NextFullMoon
    global WaxingMoon
    PreviousNewMoon  = None
    NextNewMoon      = None
    PreviousFullMoon = None
    NextFullMoon     = None
    WaxingMoon = None
    # note: the python datetimes above are timezone 'aware' (not 'naive')

    # search from 30 days earlier than noon... till noon on this day
    d0 = d - timedelta(days=30)
    t0 = ts.utc(d0.year, d0.month, d0.day, 12, 0, 0)
    t1 = ts.utc(d.year, d.month, d.day, 12, 0, 0)
    start00 = Time.time()                   # 00000
    t, y = almanac.find_discrete(t0, t1, almanac.moon_phases(eph))
    config.stopwatch += Time.time()-start00 # 00000
    for i in range(len(t)):
        if y[i] == 0:       # 0=New Moon, 1=First Quarter, 2=Full Moon, 3=Last Quarter
            PreviousNewMoon = t[i].utc_datetime()
        if y[i] == 2:       # 2 = Full Moon
            PreviousFullMoon = t[i].utc_datetime()
    # note: if two PreviousNewMoons are found within the range, the last is stored
    # note: if two PreviousFullMoons are found within the range, the last is stored

    if PreviousNewMoon != None and PreviousFullMoon != None:
        # synodic month = about 29.53 days
        t2 = ts.utc(PreviousNewMoon + timedelta(days=28))
        t3 = ts.utc(PreviousNewMoon + timedelta(days=30))
        start00 = Time.time()                   # 00000
        t, y = almanac.find_discrete(t2, t3, almanac.moon_phases(eph))
        config.stopwatch += Time.time()-start00 # 00000
        for i in range(len(t)):
            if y[i] == 0:       # 0 = New Moon
                NextNewMoon = t[i].utc_datetime()

        WaxingMoon = True
        if PreviousFullMoon > PreviousNewMoon:
            WaxingMoon = False
    return