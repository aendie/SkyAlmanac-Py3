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

# Skyfield functions for Lunar Distance tables and charts

###### Standard library imports ######
from datetime import date
from math import atan, degrees, copysign
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

###### Local application imports ######
import config
import ld_stardata

#---------------------------
#   Module initialization
#---------------------------

urlIERS = "ftp://ftp.iers.org/products/eop/rapid/standard/"
urlUSNO = "https://maia.usno.navy.mil/ser7/"        # alternate location
urlDCIERS = "https://datacenter.iers.org/data/9/"   # alternate location

hour_of_day3 = [0, 12, 24]
hour_of_day5 = [0, 6, 12, 18, 24]
hour_of_day = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
next_hour_of_day = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
hour_of_day26 = [-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
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

def ld_init_sf(spad):
    global ts, pandasDF, eph, earth, moon, sun, venus, mars, jupiter, saturn
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
        pandasDF = hipparcos.load_dataframe(f)

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

#-------------------------------------------------
#   Miscellaneous  (Lunar Distance tables only)
#-------------------------------------------------

def getDUT1(d):       # used in 'page' (Lunar DIstance tables only)
    # obtain calculation parameters
    t = ts.ut1(d.year, d.month, d.day, 0, 0, 0)
    return t.dut1, t.delta_t

#-----------------------------------------------------
#   Moon calculations  (Lunar Distance tables only)
#-----------------------------------------------------

def moon_SD(d):         # used in moontab
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

def moon_GHA(d):        # used in moontab
    # compute moon's GHA, DEC and HP per hour of day
    t = ts.ut1(d.year, d.month, d.day, hour_of_day, 0, 0)
    position = earth.at(t).observe(moon)
    #ra = position.apparent().radec(epoch='date')[0]
    #dec = position.apparent().radec(epoch='date')[1]
    #distance = position.apparent().radec(epoch='date')[2]
    ra, dec, distance = position.apparent().radec(epoch='date')

    # also compute moon's GHA at End of Day (23:59:30) and Start of Day (24 hours earlier)
    tSoD = ts.ut1(d.year, d.month, d.day-1, 23, 59, 30)
    posSoD = earth.at(tSoD).observe(moon)
    raSoD = posSoD.apparent().radec(epoch='date')[0]
    ghaSoD = gha2deg(tSoD.gast, raSoD.hours)   # GHA as float
    tEoD = ts.ut1(d.year, d.month, d.day, 23, 59, 30)
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
    # ghaSoD, ghaEoD = GHA at Start/End of Day assuming time is rounded to hh:mm

    return gham, decm, degm, HPm, GHAupper, GHAlower, ghaSoD, ghaEoD

def moon_VD(d0,d):           # used in moontab
    # first value required is at 00:00 on the current day...
    t0 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)
    pos0 = earth.at(t0).observe(moon)
    #ra0 = pos0.apparent().radec(epoch='date')[0]
    #dec0 = pos0.apparent().radec(epoch='date')[1]
    ra0, dec0, _ = pos0.apparent().radec(epoch='date')
    V0 = gha2deg(t0.gast, ra0.hours)
    D0 = dec0.degrees

    # ...then 24 values at hourly intervals from 00:00 onwards
    t = ts.ut1(d.year, d.month, d.day, next_hour_of_day, 0, 0)
    position = earth.at(t).observe(moon)
    #ra  = position.apparent().radec(epoch='date')[0]
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
        D1 = dec.degrees[i]
        moonDm[i] = "{:0.1f}'".format((D1-D0) * 60)	# convert to minutes of arc
        V0 = V1		# store current value as next previous value
        D0 = D1		# store current value as next previous value
    return moonVm, moonDm

#-----------------------------------------------------------------
#   Moon transit time calculation  (Lunar Distance tables only)
#-----------------------------------------------------------------

def getGHA(d, hh, mm, ss):
    # calculate the Moon's GHA on date d at hh:mm:ss (ss can be a float)
    t1 = ts.ut1(d.year, d.month, d.day, hh, mm, ss)
    pos = earth.at(t1).observe(moon)
    ra = pos.apparent().radec(epoch='date')[0]
    gha = gha2deg(t1.gast, ra.hours)
###    print("getGHA: {}  {:02d}:{:02d}:{:04.1f}   {}".format(d, hh, mm, ss, gha))
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

def find_transit(d, ghaList, modeLT):   # used in moontab
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

####    if(modeLT):
####        prev_gha = GHAcolong(prev_gha)
####        gha = GHAcolong(gha)
####        mid_gha = GHAcolong(mid_gha)
####    return transit_time, prev_gha, prev_time, gha, gha_time, mid_gha, mid_time


#-------------------------------------------------------------
#   Sun and Moon calculations  (Lunar Distance tables only)
#-------------------------------------------------------------

def sunSD(d):
    # compute semi-diameter of sun at 0h and 23h
    sdsm = [0.0, 0.0]
    i = 0
    for hh in [0, 23]:
        t00 = ts.ut1(d.year, d.month, d.day, hh, 0, 0)
        position = earth.at(t00).observe(sun)
        distance = position.apparent().radec(epoch='date')[2]
        dist_km = distance.km
        # volumetric mean radius of sun = 695700 km
        sds = degrees(atan(695700.0 / dist_km))
        sdsm[i] = "{:0.1f}".format(sds * 60)   # convert to minutes of arc
        i += 1

    return sdsm

#-------------------------------------------------------------
#   Sun and Moon calculations  (Lunar Distance charts only)
#-------------------------------------------------------------

def sunGHA(d):              # used in addPLANET and showLD
    # compute sun's GHA and DEC at 0h, 6h, 12h, 18h, 24h
    t = ts.ut1(d.year, d.month, d.day, hour_of_day5, 0, 0)
    position = earth.at(t).observe(sun)
    #ra   = position.apparent().radec(epoch='date')[0]
    #decR = position.apparent().radec(epoch='date')[1]
    ra, decR, _ = position.apparent().radec(epoch='date')

    sha = [None] * 5
    dec = [None] * 5

    for i in range(len(decR.degrees)):
        sha[i] = (- ra.hours[i]) * 15
        if sha[i] < 0: sha[i] += 360
        dec[i] = decR.degrees[i]

    return sha, dec

def moonGHA(d):             # used in getMOON, addMOON and Main
    # compute moon's GHA, DEC and HP at 0h, 12h, 24h
    t = ts.ut1(d.year, d.month, d.day, hour_of_day3, 0, 0)
    position = earth.at(t).observe(moon)
    #ra   = position.apparent().radec(epoch='date')[0]
    #decR = position.apparent().radec(epoch='date')[1]
    ra, decR, _ = position.apparent().radec(epoch='date')

    sha = [None] * 3
    dec = [None] * 3

    for i in range(len(decR.degrees)):
        sha[i] = (- ra.hours[i]) * 15
        if sha[i] < 0: sha[i] += 360
        dec[i] = decR.degrees[i]

    return sha, dec

#------------------------------------------------------------------------------
#   Venus, Mars, Jupiter & Saturn calculations  (Lunar Distance charts only)
#------------------------------------------------------------------------------

def venusGHA(d):            # used in addPLANET and showLD
    # compute planet's GHA and DEC at 0h, 6h, 12h, 18h, 24h
    t = ts.ut1(d.year, d.month, d.day, hour_of_day5, 0, 0)
    position = earth.at(t).observe(venus)
    #ra   = position.apparent().radec(epoch='date')[0]
    #decR = position.apparent().radec(epoch='date')[1]
    ra, decR, _ = position.apparent().radec(epoch='date')

    sha = [None] * 5
    dec = [None] * 5

    for i in range(len(decR.degrees)):
        sha[i] = (- ra.hours[i]) * 15
        if sha[i] < 0: sha[i] += 360
        dec[i] = decR.degrees[i]

    return sha, dec

def marsGHA(d):             # used in addPLANET and showLD
    # compute planet's GHA and DEC at 0h, 6h, 12h, 18h, 24h
    t = ts.ut1(d.year, d.month, d.day, hour_of_day5, 0, 0)
    position = earth.at(t).observe(mars)
    #ra   = position.apparent().radec(epoch='date')[0]
    #decR = position.apparent().radec(epoch='date')[1]
    ra, decR, _ = position.apparent().radec(epoch='date')

    sha = [None] * 5
    dec = [None] * 5

    for i in range(len(decR.degrees)):
        sha[i] = (- ra.hours[i]) * 15
        if sha[i] < 0: sha[i] += 360
        dec[i] = decR.degrees[i]

    return sha, dec

def jupiterGHA(d):          # used in addPLANET and showLD
    # compute planet's GHA and DEC at 0h, 6h, 12h, 18h, 24h
    t = ts.ut1(d.year, d.month, d.day, hour_of_day5, 0, 0)
    position = earth.at(t).observe(jupiter)
    #ra   = position.apparent().radec(epoch='date')[0]
    #decR = position.apparent().radec(epoch='date')[1]
    ra, decR, _ = position.apparent().radec(epoch='date')

    sha = [None] * 5
    dec = [None] * 5

    for i in range(len(decR.degrees)):
        sha[i] = (- ra.hours[i]) * 15
        if sha[i] < 0: sha[i] += 360
        dec[i] = decR.degrees[i]

    return sha, dec

def saturnGHA(d):           # used in addPLANET and showLD
    # compute planet's GHA and DEC at 0h, 6h, 12h, 18h, 24h
    t = ts.ut1(d.year, d.month, d.day, hour_of_day5, 0, 0)
    position = earth.at(t).observe(saturn)
    #ra   = position.apparent().radec(epoch='date')[0]
    #decR = position.apparent().radec(epoch='date')[1]
    ra, decR, _ = position.apparent().radec(epoch='date')

    sha = [None] * 5
    dec = [None] * 5

    for i in range(len(decR.degrees)):
        sha[i] = (- ra.hours[i]) * 15
        if sha[i] < 0: sha[i] += 360
        dec[i] = decR.degrees[i]

    return sha, dec

#-----------------------
#   star calculations
#-----------------------

def getHipparcos(HIPnum, t00):          # used in ld_charts.getc and .getstar

    # get star data from Hipparcos (HIgh Precision PARallax COllecting Satellite)
    star = Star.from_dataframe(pandasDF.loc[int(HIPnum)])
    astrometric = earth.at(t00).observe(star)
    ra, dec, distance = astrometric.radec(epoch='date')
    mag = pandasDF.loc[int(HIPnum)]['magnitude']

    return ra, dec, mag

def getCustomStar(starname, t00):
    if starname == "HIP78727": # getHipparcos returns 'nan' for ra & dec
        star = Star(ra_hours=(16, 4, 22.60), dec_degrees=(-11, 22, 23.0), ra_mas_per_year=-60.0, dec_mas_per_year=-29.0)
        mag = 4.16
    elif starname == "HIP55203": # getHipparcos returns 'nan' for ra & dec
        star = Star(ra_hours=(11, 18, 11.24), dec_degrees=(31, 31, 50.8))
        mag = 3.79
    else:
        print("Error: {} not implemented in getCustomStar".format(starname))
        sys.exit(0)

    astrometric = earth.at(t00).observe(star)
    ra, dec, distance = astrometric.radec(epoch='date')

    return ra, dec, mag

#---------------------------------
#   Lunar Distance calculations
#---------------------------------

def ld_planets(d):          # used in ld_tables.moontab, ld_charts.LDstrategy
    # 'out' returns a list with: name, SHA, Dec, max LD angle, max RA, list of LD per hour of day
    #       for sun and 4 navigational planets on epoch of date.
    # 'tup' returns a list of tuples with: NEGATIVE index (0 to -5) to list within 'out', max LD angle with sign
    #       indicating if East (-ve) or West (+ve) of the moon 
    #       (120° max; invalid planets have 1000° - these have no data)
    # 'ra_m" returns the moon's RA per hour of day

    out = []
    ra_sun = [None] * 26
    NewMoonHours = []   # List includes the 'hour of day' when sun-moon LD is < 10°
                        #   (the moon is hardly visible during New Moon)
                        # ... thus no Lunar Distance measurements can be made.
    l_idx = [i for i in range(0, -5, -1)]   # 5 index values (including zero)
    firstLD_per_planet    = [None] * 5      # sun + 4 navigational planet LD angles
    lastLD_per_planet     = [None] * 5      # sun + 4 navigational planet LD angles
    maxLD_per_planet      = [None] * 5      # sun + 4 navigational planet LD angles
    minLD_per_planet      = [None] * 5      # sun + 4 navigational planet LD angles
    maxLDdelta_per_planet = [None] * 5      # sun + 4 navigational planet LD angles
    LDhours_per_planet    = [None] * 5      # sun + 4 navigational planet LD angles
    mag_per_planet        = [None] * 5      # sun + 4 navigational planet LD angles

    # 26 hours/day need to be calculated: 23h on 'day-1' is needed for hourly LD delta at 0h on 'day'
    #     23h on 'day-1' is needed for hourly LD delta at 0h on 'day'
    #     22h on 'day-1' is needed for rate of change of hourly LD delta at 0h on 'day'
    t = ts.ut1(d.year, d.month, d.day, hour_of_day26, 0, 0)
    e = earth.at(t)
    pos_m = e.observe(moon).apparent()
    ra_m = pos_m.radec(epoch='date')[0]

    for idx in range(5):
        ld_pm = ['' for x in range(24)]     # Lunar Distance planet-moon per hour
        ra_pm = ['' for x in range(24)]     # Right Ascension difference 'moon - planet' per hour
        if   idx == 0:
            name = "Sun"
            Vmag = -26.74
            pos_p = e.observe(sun).apparent()
            pos_H = pos_p   # Helios
        elif idx == 1:
            name = "Venus"
            Vmag = -4.14    # mean brightness (-2.98 to -4.6)
            pos_p = e.observe(venus).apparent()
        elif idx == 2:
            name = "Mars"
            Vmag = 0.71     # mean brightness
            pos_p = e.observe(mars).apparent()
        elif idx == 3:
            name = "Jupiter"
            Vmag = -2.20     # mean brightness
            pos_p = e.observe(jupiter).apparent()
        elif idx == 4:
            name = "Saturn"
            Vmag = 0.46     # mean brightness
            pos_p = e.observe(saturn).apparent()

        sep_pm = pos_m.separation_from(pos_p)
        ra_p, dec, distance = pos_p.radec(epoch='date')
        #ra_p = pos_p.radec(epoch='date')[0]
        if idx > 0:     # if a planet
            sep_pH = pos_H.separation_from(pos_p)

        #sha  = fmtgha(0, ra_p.hours)
        #decl = fmtdeg(dec.degrees)

        n = 0                   # count valid moon-planet LD angles (e.g. under 120°)
        sd = 100.0              # any fake value above 10°
        ld_first = 0.0          # first valid LD
        ld_last = 0.0           # last valid LD
        ld_max = 0.0            # maximum LD
        ld_min = 400.0          # minimum LD (invalid value initially)
        ld_max_ra = 0.0         # direction from moon (right or left)
        ld_min_ra = 0.0         # direction from moon (right or left)
        ld_delta_max = 0.0      # max hourly change in LD

        # negative hours are chosen so as to calculate rate of change of hourly LD delta for hour "0":
        #   = ld_delta[hour0-hour-1]    versus    prev_ld_delta[hour-1-hour-2]

        for i in range(-2, 24):
            ld = sep_pm.degrees[i+2]                # Lunar Distance
            if idx > 0: sd = sep_pH.degrees[i+2]    # Solar Distance (if a planet)
            if idx == 0:
                ra_sun[i+2] = ra_p.hours[i+2]
            if i == -2:     # if i = -2
                prev_ld = ld    # initialize 'previous lunar distance'...
                prev_ld_delta = 10.0    # fake initial value
                continue        # ... only!!
            if i < 0:       # if i = -1
                ld_delta = abs(ld - prev_ld)    # in degrees
                prev_ld = ld
                prev_ld_delta = ld_delta
                continue        # ... only!!

            # if i >= 0
            if idx == 0 and ld < 10.0: NewMoonHours.append(i)    # 'New Moon' (hours when sun-moon LD < 10°)
            if idx == 0 and ld < 40.0:
                ld_pm[i] = r"ld \textless 40.0"
                continue  # moon is not visible if sun-moon LD < 40°

            skip = False
            ld_delta = abs(ld - prev_ld)    # in degrees
            if ld_delta < 0.25: 
                skip = True     # ensure LD delta > 15' of arc
                ld_pm[i] = r"ld/h \textless 15'"
            else:
                # skip if rate of change of ld_delta too high (non-linear)
                chg = ld_delta - prev_ld_delta
                if abs(chg) < 8:    # first value is fake (hour2-hour1) vs (hour1-hour0)
                    if abs(chg) > 0.016:    # cutoff chosen empirically
                        #print("{}: {}h ld_delta change = {}".format(name,i,chg))
                        ld_pm[i] = r"ld/h rate \textgreater 0.016"
                        skip = True
            prev_ld_delta = ld_delta
            prev_ld = ld
            if skip: continue       # ignore as ld hourly rate < 15' of arc

            if sd < 10.0:   # ignore if Solar Distance < 10°
                ld_pm[i] = r"sd \textless 10.0"
                continue

#            if idx > 0 and i in set(NewMoonHours):
            if i in set(NewMoonHours):
                ld_pm[i] = "newMoon"   # enter in List but don't count as Data
                continue     # unmeasurable due to New Moon

##          Following idea dropped in favor of checking hourly rate of change of hourly LD delta
##            if idx > 0 and ld < 7.0: continue    # moon - planet is at least 7°

            if idx > 0:     # if a planet (i.e. if not the sun)
                ##if ra_p.hours[i+1] > ra_m.hours[i+1]:     # if RA(planet) > RA(moon)
                if cmp_ra(ra_p.hours[i+2], ra_m.hours[i+2]):    # if RA(planet) > RA(moon)
                    #if ra_p.hours[i+1] > ra_sun[i+1] > ra_m.hours[i+1]:   # if sun in-between...
                    if cmp_ra(ra_p.hours[i+2], ra_sun[i+2]) and cmp_ra(ra_sun[i+2], ra_m.hours[i+2]):
                        ld_pm[i] = "planet-sun-moon"
                        continue
                else:
                    #if ra_p.hours[i+1] < ra_sun[i+1] < ra_m.hours[i+1]:   # if sun in-between...
                    if cmp_ra(ra_m.hours[i+2], ra_sun[i+2]) and cmp_ra(ra_sun[i+2], ra_p.hours[i+2]):
                        ld_pm[i] = "moon-sun-planet"
                        continue

            if ld >= 120.0:
                ld_pm[i] = "ld $\geq$ 120"
                continue

            ra_diff = diff_ra(ra_m.hours[i+2], ra_p.hours[i+2])   # RA difference sun/planet-moon
            if not (-24 < ra_diff < 24): raise Exception("ra_diff outside limits")
            ra_pm[i] = fmtdeg(ra_diff*15)
            if ld_delta > ld_delta_max: ld_delta_max = ld_delta
            ld_last = ld
            ld_last_ra_diff = ra_diff
            if ld_first == 0.0:
                ld_first = ld
                ld_first_ra_diff = ra_diff
            if ld > ld_max:
                ld_max = ld
                ld_max_ra = ra_diff
                ra_moon_max = ra_m.hours[i+2]
                ra_planet_max = ra_p.hours[i+2]
                ld_max_i = i
            if ld < ld_min:
                ld_min = ld
                ld_min_ra = ra_diff
                ld_min_i = i
            if ld < 120:
                # add the LD angle to the list
                n += 1
                ld_pm[i] = fmtdeg(ld)

        # Unless we have a New Moon, choose to include 3 hour-values minimum per sun/planet per day
        # (because a day could have 22 hours of New Moon, thus 2 valid LD values would be excluded)
        if len(NewMoonHours) == 0 and n < 3: n = 0
        maxLDdelta_per_planet[idx] = ld_delta_max
        LDhours_per_planet[idx] = n
        mag_per_planet[idx] = Vmag
        if n > 0:
            firstLD_per_planet[idx] = copysign(ld_first, ld_first_ra_diff)
            lastLD_per_planet[idx] = copysign(ld_last, ld_last_ra_diff)
            maxLD_per_planet[idx] = copysign(ld_max, ld_max_ra)
            minLD_per_planet[idx] = copysign(ld_min, ld_min_ra)
            #print("Moon {:2d}h RA: {}   {} RA: {}".format(ld_max_i, ra_moon_max, name, ra_planet_max))
        else:       # if no valid LD data
            firstLD_per_planet[idx] = 1000.0    # invalid value
            maxLD_per_planet[idx] = 1000.0      # invalid value
            minLD_per_planet[idx] = 1000.0      # invalid value

        # List with these values per planet ...
        # [0] - sun/planet name
        # [1] - OBJECT: sun/planet RA (26 values: -2h to 23h)
        # [2] - OBJECT: moon RA       (26 values: -2h to 23h)
        # [3] - max LD in degrees
        # [4] - RA difference sun/planet-moon at hour of max LD
        # [5] - LIST of LD per hour (24 values: 0h to 23h)
        out.append([name,ra_p,ra_m,ld_max,ld_max_ra,ld_pm])       # list of values per planet and per hour

        if config.debug_planet_data:
            sha00 = (- ra_p.hours[2]) * 15
            if sha00 < 0: sha00 += 360
            print("\n{} SHA at 0h = {:.1f} LDmax = {:.3f} with RAdiff = {:.3f}".format(name,sha00,ld_max,ld_max_ra))
            ld_pm2 = []
            for ii in ld_pm:
                ld_pm2.append(ii.replace(r"\textless","<").replace(r"$\geq$",">=").replace(r"$^\circ$","°").replace(r"\textgreater",">"))    # make it readable
            print(name,ld_pm2)

    # List of tuples with these values per planet ...
    # [0] - sun/planet index: 0 = sun and -1 to -4 for Venus, Mars, Jupiter, Saturn
    # [1] - first valid LD per sun/planet (-ve if lower RA than Moon; +ve if higher)
    # [2] - last  valid LD per sun/planet (-ve if lower RA than Moon; +ve if higher)
    # [3] - max hourly LD delta per sun/planet
    # [4] - number of hours (0 to 24) with a valid LD value
    # [5] - sun/planet magnitude (very approximate)
    tup = list(zip(l_idx, firstLD_per_planet, lastLD_per_planet, maxLDdelta_per_planet, LDhours_per_planet, mag_per_planet))

    return out, tup, NewMoonHours, ra_m

def cmp_ra(ra_obj, ra_moon):
    # compare RA of two objects and return True if ra_obj > ra_moon
    #    i.e. if (ra_obj - ra_moon) < (ra_moon - ra.obj)
    # taking into consideration that values are circular from 0 to 24 hours
    #    e.g. RA 1 hour > RA 23 hours (max difference will be 8 hours or 120°)

    ang = abs(ra_obj - ra_moon)
    flip = True if ang > 12 else False
    
    if not flip:
        return (ra_obj > ra_moon)
    else:
        return (ra_moon > ra_obj)

def diff_ra(ra_moon, ra_obj):
    # return the signed difference in RA of the smaller angle
    #         (ra_obj - ra_moon) or (ra_moon - ra_obj)
    # taking into consideration that values are circular from 0 to 24 hours
    #    e.g. RA 1 hour - RA 23 hours = +2 hours (max difference will be ±8 hours or ±120°)

    ang = abs(ra_obj - ra_moon)
    flip = True if ang > 12 else False
    
    if not flip:
        return ra_moon - ra_obj
    else:
        if ra_moon > ra_obj:
            return ra_moon - 24 - ra_obj
        else:
            return ra_moon + 24 - ra_obj

def ld_stars(d, NewMoonHours, ra_sun):      # used in moontab, LDstrategy
    # 'out' returns a list with: name, SHA, Dec, max LD angle, max RA, list of LD per hour of day
    #       for 21 navigational stars (plus Polaris) on epoch of date.
    # 'tup' returns a list of tuples with: index to list within 'out', max LD angle with sign
    #       indicating if East (-ve) or West (+ve) of the moon 
    #       (120° max; invalid stars have 1000° - these have no data)

    out = []
    ra_s = [None] * 22          # RA per star
    l_idx = [i for i in range(1, 23)]   # 22 index values (1 to 22)
    firstLD_per_star = [None] * 22      # 21 navigational stars + Polaris
    lastLD_per_star = [None] * 22       # 21 navigational stars + Polaris
    maxLD_per_star = [None] * 22        # 21 navigational stars + Polaris
    minLD_per_star = [None] * 22        # 21 navigational stars + Polaris
    maxLDdelta_per_star = [None] * 22   # 21 navigational stars + Polaris
    LDhours_per_star = [None] * 22      # 21 navigational stars + Polaris
    mag_per_star = [None] * 22          # 21 navigational stars + Polaris

    # 26 hours/day need to be calculated:
    #     23h on 'day-1' is needed for hourly LD delta at 0h on 'day'
    #     22h on 'day-1' is needed for rate of change of hourly LD delta at 0h on 'day'
    t = ts.ut1(d.year, d.month, d.day, hour_of_day26, 0, 0)
    t00 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)           # observe at midnight
    #t12 = ts.ut1(d.year, d.month, d.day, 12, 0, 0)          # observe at noon
    e = earth.at(t)
    pos_m = e.observe(moon).apparent()
    ra_m  = pos_m.radec(epoch='date')[0]
    pos_H = e.observe(sun).apparent()

    ns_idx = 0      # index to navstars (0 to 21)
    for line in ld_stardata.navstars.strip().split('\n'):
        ld_sm = ['' for x in range(24)] # Lunar Distance star-moon per hour
        #ra_sm = ['' for x in range(24)]
        x1 = line.index(',')
        name = line[:x1]
        line = line[x1+1:]
        x2 = line.index(',')
        objnum = line[:x2]
        line = line[x2+1:]
        x3 = line.index(',')
        HIPnum = line[:x3]
        Hpmag = float(line[x3+1:])          # Hipparcos magnitude

        star = Star.from_dataframe(pandasDF.loc[int(HIPnum)])
        pos_s = earth.at(t00).observe(star).apparent()
        sep_sm = pos_m.separation_from(pos_s)
        ra, dec, distance = pos_s.radec(epoch='date')
        ra_h = ra.hours
        sep_sH = pos_H.separation_from(pos_s)

        #sha  = fmtgha(0, ra.hours)
        #decl = fmtdeg(dec.degrees)

        n = 0                   # count valid moon-star LD angles (e.g. under 120°)
        ld_first = 0.0          # first valid LD
        ld_last = 0.0           # last valid LD
        ld_max = 0.0            # maximum LD
        ld_min = 400.0          # minimum LD (invalid value initially)
        ld_max_ra = 0.0         # direction from moon (right or left)
        ld_min_ra = 0.0         # direction from moon (right or left)
        ld_delta_max = 0.0      # max hourly change in LD

        # negative hours are chosen so as to calculate rate of change of hourly LD delta for hour "0":
        #   = ld_delta[hour0-hour-1]    versus    prev_ld_delta[hour-1-hour-2]

        for i in range(-2, 24):
            ld = sep_sm.degrees[i+2]    # Lunar Distance
            sd = sep_sH.degrees[i+2]    # Solar Distance
            if i == -2:     # if i = -2
                prev_ld = ld    # initialize 'previous lunar distance'...
                prev_ld_delta = 10.0    # fake initial value
                continue        # ... only!!
            if i < 0:       # if i = -1
                ld_delta = abs(ld - prev_ld)    # in degrees
                prev_ld = ld
                prev_ld_delta = ld_delta
                continue        # ... only!!

            # if i >= 0
            skip = False
            #if ns_idx == 21: print(name, ld, abs(ld - prev_ld))
            ld_delta = abs(ld - prev_ld)    # in degrees
            if ld_delta < 0.25: 
                skip = True     # ensure LD delta > 15' of arc
                ld_sm[i] = r"ld/h \textless 15'"
            else:
                # skip if rate of change of ld_delta too high (non-linear)
                chg = ld_delta - prev_ld_delta
                if abs(chg) < 8:    # first value is fake (hour2-hour1) vs (hour1-hour0)
                    if abs(chg) > 0.016:    # cutoff chosen empirically
                        #print("{}: {}h ld_delta change = {}".format(name,i,chg))
                        ld_sm[i] = r"ld/h rate \textgreater 0.016"
                        skip = True
            prev_ld_delta = ld_delta
            prev_ld = ld
            if skip: continue     # ignore as ld hourly rate < 15' of arc

            if sd < 10.0:   # ignore if Solar Distance < 10°
                ld_sm[i] = r"sd \textless 10.0"
                continue

            if i in set(NewMoonHours):
                ld_sm[i] = "newMoon"   # enter in List but don't count as Data
                continue     # unmeasurable due to New Moon

##          Following idea dropped in favor of checking hourly rate of change of hourly LD delta
##            if ld < 8.0: continue    # moon - star is at least 8°

            ##if ra.hours > ra_m.hours[i+1]:     # if RA(star) > RA(moon)
            if cmp_ra(ra.hours, ra_m.hours[i+2]):   # if RA(star) > RA(moon)
            #    if ra.hours > ra_sun[i+1] > ra_m.hours[i+1]:   # if sun in-between...
                if cmp_ra(ra.hours, ra_sun[i+2]) and cmp_ra(ra_sun[i+2], ra_m.hours[i+2]):
                    ld_sm[i] = "star-sun-moon"
                    continue
            else:
            #    if ra.hours < ra_sun[i+1] < ra_m.hours[i+1]:   # if sun in-between...
                if cmp_ra(ra_m.hours[i+2], ra_sun[i+2]) and cmp_ra(ra_sun[i+2], ra.hours):
                    ld_sm[i] = "moon-sun-star"
                    continue

            if ld >= 120.0: 
                ld_sm[i] = "ld $\geq$ 120"
                continue

            ra_diff = diff_ra(ra_m.hours[i+2], ra.hours)    # RA difference sun/planet-moon
            #if ns_idx == 5: print("ra_diff of {} = {}".format(ns_idx, ra_diff))
            if not (-24 < ra_diff < 24): raise Exception("ra_diff outside limits")
            if ld_delta > ld_delta_max: ld_delta_max = ld_delta
            ld_last = ld
            ld_last_ra_diff = ra_diff
            if ld_first == 0.0:
                ld_first = ld
                ld_first_ra_diff = ra_diff
            if ld > ld_max:
                ld_max = ld
                ld_max_ra = ra_diff
                ra_moon_max = ra_m.hours[i+2]
                ra_star_max = ra.hours
                ld_max_i = i
                #if ns_idx == 21: print("i = {} ld_max = {}".format(i,ld_max))
            if ld < ld_min:
                ld_min = ld
                ld_min_ra = ra_diff
                ld_min_i = i
            if ld < 120:
                # add the LD angle to the list
                n += 1
                ld_sm[i] = fmtdeg(ld)

        # Unless we have a New Moon, choose to include 3 hour-values minimum per sun/planet per day
        # (because a day could have 22 hours of New Moon, thus 2 valid LD values would be excluded)
        if len(NewMoonHours) == 0 and n < 3: n = 0
        maxLDdelta_per_star[ns_idx] = ld_delta_max
        LDhours_per_star[ns_idx] = n
        mag_per_star[ns_idx] = Hpmag
        if n > 0:
            firstLD_per_star[ns_idx] = copysign(ld_first, ld_first_ra_diff)
            lastLD_per_star[ns_idx] = copysign(ld_last, ld_last_ra_diff)
            maxLD_per_star[ns_idx] = copysign(ld_max, ld_max_ra)
            minLD_per_star[ns_idx] = copysign(ld_min, ld_min_ra)
            #print("Moon {:2d}h RA: {}   {} RA: {}".format(ld_max_i, ra_moon_max, name, ra_star_max))
        else:       # if no valid LD data
            firstLD_per_star[ns_idx] = 1000.0   # invalid value
            maxLD_per_star[ns_idx] = 1000.0     # invalid value
            minLD_per_star[ns_idx] = 1000.0     # invalid value

        # List with these values per star ...
        # [0] - star name
        # [1] - OBJECT: star RA (1 value at 0h)
        # [2] - OBJECT: moon RA (26 values: -2h to 23h)
        # [3] - max LD in degrees
        # [4] - RA difference star-moon at hour of max LD
        # [5] - LIST of LD per hour (24 values: 0h to 23h)
        out.append([name,ra_h,ra_m,ld_max,ld_max_ra,ld_sm])   # list of values per star and per hour
        ns_idx += 1

        if config.debug_star_data:
            sha00 = (- ra_h) * 15
            if sha00 < 0: sha00 += 360
            print("\n{} SHA at 0h = {:.1f} LDmax = {:.3f} with RAdiff = {:.3f}".format(name,sha00,ld_max,ld_max_ra))
            ld_sm2 = []
            for ii in ld_sm:
                ld_sm2.append(ii.replace(r"\textless","<").replace(r"$\geq$",">=").replace(r"$^\circ$","°").replace(r"\textgreater",">"))    # make it readable
            print(name,ld_sm2)

    # list of tuples with these values per star ...
    # [0] - star index: 1 to 22
    # [1] - first valid LD per star (-ve if lower RA than Moon; +ve if higher)
    # [2] - last  valid LD per star (-ve if lower RA than Moon; +ve if higher)
    # [3] - max hourly LD delta per star
    # [4] - number of hours (0 to 24) with a valid LD value
    # [5] - star magnitude ('Hipparcos magnitude')
    tup = list(zip(l_idx, firstLD_per_star, lastLD_per_star, maxLDdelta_per_star, LDhours_per_star, mag_per_star))

    return out, tup