#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   Copyright (C) 2022  Andrew Bauer

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

# ----------------------------------------------------------------------------------
# THIS MODULE IS OPTIMIZED SPECIFICALLY FOR MULTIPROCESSING (DATA BASED PARALELLISM)
#     Note: 6 worker processes are sufficient
#     Note: read/write to a global variable will occur randomly and give false
#           results, e.g. if 'moonvisible[]' is declared here.
#     Note: incrementing elapsed time in config.stopwatch fails: result is 0.0
# Shared memory: It is NOT possible to share arbitrary Python objects.
#                Multiprocessing can create shared memory blocks containing C
#                variables and C arrays. A NumPy extension adds shared NumPy arrays.
# ----------------------------------------------------------------------------------

###### Standard library imports ######
from datetime import datetime, timedelta
from time import time         # 00000 - stopwatch elements
from math import degrees, atan, tan, pi

###### Third party imports ######
from skyfield.api import load
from skyfield.api import Topos, Star
from skyfield import almanac
from skyfield.nutationlib import iau2000b
#from skyfield.data import hipparcos

###### Local application imports ######
import config

#----------------------
#   initialization
#----------------------

hour_of_day = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
next_hour_of_day = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
degree_sign= u'\N{DEGREE SIGN}'

#----------------------
#   internal methods
#----------------------

def GHAcolong(gha):
    # return the colongitude, e.g. 270° returns 90°
    coGHA = gha + 180
    while coGHA > 360:
        coGHA = coGHA - 360
    return coGHA

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

def fmtgha(gst, ra):
    # formats angle (hours) to that used in the nautical almanac. (ddd°mm.m)
    sha = (gst - ra) * 15
    if sha < 0:
        sha = sha + 360
    return fmtdeg(sha)

def time2text(t, round2seconds):
    if round2seconds:
        return t.ut1_strftime('%H:%M:%S')
    else:
        return t.ut1_strftime('%H:%M')

def rise_set(t, y, lats, ts, round2seconds = False):
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

#-------------------------------------------------------
#   Aries, Venus, Mars, Jupiter & Saturn calculations
#-------------------------------------------------------

def mp_ariesGHA(d, ts):            # used in planetstab(m)
    t = ts.ut1(d.year, d.month, d.day, hour_of_day, 0, 0)

    ghas = ['' for x in range(24)]
    for i in range(24):
        ghas[i] = fmtgha(t[i].gast, 0)
    return ghas

def mp_venusGHA(d, ts, earth, venus):            # used in planetstab(m)
    t = ts.ut1(d.year, d.month, d.day, hour_of_day, 0, 0)
    position = earth.at(t).observe(venus)
    ra = position.apparent().radec(epoch='date')[0]
    dec = position.apparent().radec(epoch='date')[1]

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

def mp_marsGHA(d, ts, earth, mars):             # used in planetstab(m)
    t = ts.ut1(d.year, d.month, d.day, hour_of_day, 0, 0)
    position = earth.at(t).observe(mars)
    ra = position.apparent().radec(epoch='date')[0]
    dec = position.apparent().radec(epoch='date')[1]

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

def mp_jupiterGHA(d, ts, earth, jupiter):          # used in planetstab(m)
    t = ts.ut1(d.year, d.month, d.day, hour_of_day, 0, 0)
    position = earth.at(t).observe(jupiter)
    ra = position.apparent().radec(epoch='date')[0]
    dec = position.apparent().radec(epoch='date')[1]

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

def mp_saturnGHA(d, ts, earth, saturn):           # used in planetstab(m)
    t = ts.ut1(d.year, d.month, d.day, hour_of_day, 0, 0)
    position = earth.at(t).observe(saturn)
    ra = position.apparent().radec(epoch='date')[0]
    dec = position.apparent().radec(epoch='date')[1]

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

#---------------------------------------
#   Planet SHA & transit calculations
#---------------------------------------

# > > > > > > > > > > MULTIPROCESSING ENTRY POINT < < < < < < < < < <
def mp_planetGHA(d, ts, obj):  # used in planetstab

    out = [None, None, None]  # return [planet_sha, planet_transit] + processing time
    eph = load(config.ephemeris[config.ephndx][0])	# load chosen ephemeris
    earth   = eph['earth']
    if obj == 'venus':   venus   = eph['venus']
    if obj == 'jupiter': jupiter = eph['jupiter barycenter']
    if obj == 'saturn':  saturn  = eph['saturn barycenter']
    if obj == 'mars':
        if config.ephndx >= 3:
            mars = eph['mars barycenter']
        else:
            mars = eph['mars']

    # calculate planet GHA
    DEC = None
    DEG = None
    if obj == 'aries':      GHA           = mp_ariesGHA(d, ts)
    elif obj == 'venus':    GHA, DEC, DEG = mp_venusGHA(d, ts, earth, venus)
    elif obj == 'mars':     GHA, DEC, DEG = mp_marsGHA(d, ts, earth, mars)
    elif obj == 'jupiter':  GHA, DEC, DEG = mp_jupiterGHA(d, ts, earth, jupiter)
    elif obj == 'saturn':   GHA, DEC, DEG = mp_saturnGHA(d, ts, earth, saturn)

    out[0] = GHA
    out[1] = DEC
    out[2] = DEG
    return out

# > > > > > > > > > > MULTIPROCESSING ENTRY POINT < < < < < < < < < <
def mp_planetstransit(d, ts, obj, round2seconds = False):  # used in starstab & meridiantab (in eventtables.py)
    # returns SHA and Meridian Passage for the navigational planets

    out = [None, None, None]  # return [planet_sha, planet_transit] + processing time
    eph = load(config.ephemeris[config.ephndx][0])	# load chosen ephemeris
    earth   = eph['earth']
    if obj == 'venus':   planet = eph['venus']
    if obj == 'jupiter': planet = eph['jupiter barycenter']
    if obj == 'saturn':  planet = eph['saturn barycenter']
    if obj == 'mars':
        if config.ephndx >= 3:
            planet = eph['mars barycenter']
        else:
            planet = eph['mars']

    # calculate planet SHA
    tfr = ts.ut1(d.year, d.month, d.day, 0, 0, 0)       # search from
    position = earth.at(tfr).observe(planet)
    ra = position.apparent().radec(epoch='date')[0]     # RA
    out[0] = fmtgha(0, ra.hours)    # planet_sha
    
    # calculate planet transit
    d1 = d + timedelta(days=1)
    tto = ts.ut1(d1.year, d1.month, d1.day, 0, 0, 0)    # search to
    start00 = time()                    # 00000
    transit_time, y = almanac.find_discrete(tfr, tto, planet_transit(earth, planet))
    time00 = time()-start00             # 00000
    lats = u'{} 0{} E transit'.format(obj, degree_sign)
    out[1] = rise_set(transit_time,y,lats,ts, round2seconds = False)[0]  # planet_transit

    out[2] = time00     # append processing time to list
    return out

def planet_transit(earth, planet_name):
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

def hor_parallax(d, ts):      # used in starstab (in eventtables.py)

    eph = load(config.ephemeris[config.ephndx][0])	# load chosen ephemeris
    earth = eph['earth']
    venus = eph['venus']
    if config.ephndx >= 3:
        mars = eph['mars barycenter']
    else:
        mars = eph['mars']

# Venus
    t0 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)
    position0 = earth.at(t0).observe(venus)
    vau = position0.apparent().radec(epoch='date')[2]	# distance
    hpvenus = "{:0.1f}".format((tan(6371/(vau.au*149597870.7)))*60*180/pi)

# Mars
    position0 = earth.at(t0).observe(mars)
    mau = position0.apparent().radec(epoch='date')[2]	# distance
    hpmars = "{:0.1f}".format((tan(6371/(mau.au*149597870.7)))*60*180/pi)

    return [hpmars,hpvenus]

#-------------------------------
#   Sun and Moon calculations
#-------------------------------

def mp_sunGHA(d, ts, earth, sun):              # used in sunmoontab(m)
    # compute sun's GHA and DEC per hour of day

    t = ts.ut1(d.year, d.month, d.day, hour_of_day, 0, 0)
    position = earth.at(t).observe(sun)
    ra = position.apparent().radec(epoch='date')[0]
    dec = position.apparent().radec(epoch='date')[1]

    ghas = ['' for x in range(24)]
    decs = ['' for x in range(24)]
    degs = ['' for x in range(24)]
    for i in range(len(dec.degrees)):
        ghas[i] = fmtgha(t[i].gast, ra.hours[i])
        decs[i] = fmtdeg(dec.degrees[i],2)
        degs[i] = dec.degrees[i]

    # degs has been added for the suntab function
    return ghas,decs,degs

def mp_moonGHA(d, ts, earth, moon, round2seconds = False):  # used in sunmoontab(m) & equationtab (in eventtables.py)
    # compute moon's GHA, DEC and HP per hour of day
    t = ts.ut1(d.year, d.month, d.day, hour_of_day, 0, 0)
    position = earth.at(t).observe(moon)
    ra = position.apparent().radec(epoch='date')[0]
    dec = position.apparent().radec(epoch='date')[1]
    distance = position.apparent().radec(epoch='date')[2]

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

def mp_moonVD(d00, d, ts, earth, moon):           # used in sunmoontab(m)
# OLD:  # first value required is from 23:30 on the previous day...
# OLD:  t0 = ts.ut1(d00.year, d00.month, d00.day, 23, 30, 0)
    # first value required is from 00:00 on the current day...
    t0 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)
    pos0 = earth.at(t0).observe(moon)
    ra0 = pos0.apparent().radec(epoch='date')[0]
    dec0 = pos0.apparent().radec(epoch='date')[1]
    V0 = gha2deg(t0.gast, ra0.hours)
    D0 = dec0.degrees

# OLD:  # ...then 24 values at hourly intervals from 23:30 onwards
# OLD:  t = ts.ut1(d.year, d.month, d.day, hour_of_day, 30, 0)
    # ...then 24 values at hourly intervals from 00:00 onwards
    t = ts.ut1(d.year, d.month, d.day, next_hour_of_day, 0, 0)
    position = earth.at(t).observe(moon)
    ra = position.apparent().radec(epoch='date')[0]
    dec = position.apparent().radec(epoch='date')[1]

    moonVm = ['' for x in range(24)]
    moonDm = ['' for x in range(24)]
    for i in range(len(dec.degrees)):
        V1 = gha2deg(t[i].gast, ra.hours[i])
        Vdelta = V1 - V0
        if Vdelta < 0:
            Vdelta += 360
        Vdm = (Vdelta-(14.0+(19.0/60.0))) * 60	# subtract 14:19:00
        moonVm[i] = "{:0.1f}'".format(Vdm)
        D1 = dec.degrees[i]
        moonDm[i] = "{:0.1f}'".format((D1-D0) * 60)	# convert to minutes of arc
        V0 = V1		# store current value as next previous value
        D0 = D1		# store current value as next previous value
    return moonVm, moonDm

# > > > > > > > > > > MULTIPROCESSING ENTRY POINT < < < < < < < < < <
def mp_sunmoon(date, ts, n):

    eph = load(config.ephemeris[config.ephndx][0])	# load chosen ephemeris
    earth   = eph['earth']
    sun     = eph['sun']
    moon    = eph['moon']

    d = date + timedelta(days=n)
    d0 = d - timedelta(days=1)
    ghas, decs, degs = mp_sunGHA(d, ts, earth, sun)
    gham, decm, degm, HPm, GHAupper, GHAlower, ghaSoD, ghaEoD = mp_moonGHA(d, ts, earth, moon)
    vmin, dmin = mp_moonVD(d0,d, ts, earth, moon)

    #buildUPlists(n, ghaSoD, GHAupper, ghaEoD)
    #buildLOWlists(n, ghaSoD, GHAupper, ghaEoD)

    out = (ghas, decs, degs, gham, decm, degm, HPm, GHAupper, GHAlower, ghaSoD, ghaEoD, vmin, dmin)
    return out

#-----------------------
#   star calculations
#-----------------------

# > > > > > > > > > > MULTIPROCESSING ENTRY POINT < < < < < < < < < <
def mp_stellar_info(d, ts, df, n):        # used in starstab
    # returns a list of lists with name, SHA and Dec all navigational stars for epoch of date.

    # load the Hipparcos catalog as a 118,218 row Pandas dataframe.
    #with load.open(hipparcos.URL) as f:
        #hipparcos_epoch = ts.tt(1991.25)
    #    df = hipparcos.load_dataframe(f)

    eph = load(config.ephemeris[config.ephndx][0])	# load chosen ephemeris
    earth   = eph['earth']

    t00 = ts.ut1(d.year, d.month, d.day, 0, 0, 0)   #calculate at midnight
    #t12 = ts.ut1(d.year, d.month, d.day, 12, 0, 0)  #calculate at noon
    out = []

    if n == 0: db = db1
    elif n == 1: db = db2
    elif n == 2: db = db3
    elif n == 3: db = db4
    elif n == 4: db = db5
    else: db = db6

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

# List of navigational stars with Hipparcos Catalog Number
db1 = """
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
"""
db2 = """
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
"""
db3 = """
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
"""
db4 = """
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
"""
db5 = """
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
"""
db6 = """
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

# > > > > > > > > > > MULTIPROCESSING ENTRY POINT < < < < < < < < < <
def mp_twilight(d, lat, hemisph, ts, round2seconds = False):  # used in twilighttab (section 1)
    # Returns for given date and latitude(in full degrees):
    # naut. and civil twilight (before sunrise), sunrise, meridian passage, sunset, civil and nautical twilight (after sunset).
    # NOTE: 'twilight' is only called for every third day in the Nautical Almanac...
    #       ...therefore daily tracking of the sun state is not possible.

    time00 = 0.0                        # 00000
    eph = load(config.ephemeris[config.ephndx][0])	# load chosen ephemeris
    earth   = eph['earth']
    sun     = eph['sun']

    out = [None,None,None,None,None,None,None]  # 6 data items + processing time
    lats = "{:3.1f} {}".format(abs(lat), hemisph)
    locn = Topos(lats, "0.0 E")
    dt = datetime(d.year, d.month, d.day, 0, 0, 0)

    if round2seconds:
        dt -= timedelta(seconds=0.5)    # search from 0.5 seconds before midnight
    else:
        dt -= timedelta(seconds=30)     # search from 30 seconds before midnight

    t0 = ts.ut1(dt.year, dt.month, dt.day,   dt.hour, dt.minute, dt.second)
    t1 = ts.ut1(dt.year, dt.month, dt.day+1, dt.hour, dt.minute, dt.second)
    abhd = False                                # above/below horizon display NOT enabled

    # Sunrise/Sunset...
    start00 = time()                    # 00000
    actual, y = almanac.find_discrete(t0, t1, daylength(earth, sun, locn, 0.8333))
    time00 += time()-start00            # 00000
    out[2], out[3], r2, s2, fs = rise_set(actual,y,lats,ts,round2seconds)
    if out[2] == '--:--' and out[3] == '--:--':	# if neither sunrise nor sunset...
        abhd = True                             # enable above/below horizon display
        yn = midnightsun(d, hemisph)
        out[2] = yn
        out[3] = yn

    # Civil Twilight...
    start00 = time()                    # 00000
    civil, y = almanac.find_discrete(t0, t1, daylength(earth, sun, locn, 6.0))
    time00 += time()-start00            # 00000
    out[1], out[4], r2, s2, fs = rise_set(civil,y,lats,ts,round2seconds)
    if abhd and out[1] == '--:--' and out[4] == '--:--':	# if neither begin nor end...
        yn = midnightsun(d, hemisph)
        out[1] = yn
        out[4] = yn

    # Nautical Twilight...
    start00 = time()                    # 00000
    naut, y = almanac.find_discrete(t0, t1, daylength(earth, sun, locn, 12.0))
    time00 += time()-start00            # 00000
    out[0], out[5], r2, s2, fs = rise_set(naut,y,lats,ts,round2seconds)
    if abhd and out[0] == '--:--' and out[5] == '--:--':	# if neither begin nor end...
        yn = midnightsun(d, hemisph)
        out[0] = yn
        out[5] = yn

    out[6] = time00     # append processing time to list
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

def daylength(earth, sun, topos, degBelowHorizon):
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

def getmoonstate(dt, lat, hemisph, ts, earth, moon):
    # populate the moon state (visible or not) for the specified date & latitude
    # note: the first parameter 'dt' is already a datetime 30 seconds before midnight
    # note: getmoonstate is called when there is neither a moonrise nor a moonset on 'dt'

    time00 = 0.0                        # 00000
    Hseeks = 0
    lats = '{:3.1f} {}'.format(abs(lat), hemisph)
    locn = Topos(lats, '0.0 E')
    t0 = ts.ut1(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    horizon = 0.8333

    # search for the next moonrise or moonset (returned in moonrise[0] and y[0])
    mstate = None
    while mstate == None:
        Hseeks += 1
        t0 = ts.ut1(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        dt += timedelta(days=1)
        t9 = ts.ut1(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        start00 = time()                # 00000
        moonrise, y = almanac.find_discrete(t0, t9, moonday(earth, moon, locn, horizon))
        time00 += time()-start00        # 00000
        if len(moonrise) > 0:
            if y[0]:
                mstate = False
            else:
                mstate = True
    return mstate, time00, Hseeks

def getHorizon(t, earth, moon):
    # calculate the angle of the moon below the horizon at moonrise/set

    position = earth.at(t).observe(moon)   # at noontime (for daily average distance)
    distance = position.apparent().radec(epoch='date')[2]
    dist_km = distance.km
# OLD: sdm = degrees(atan(1738.1/dist_km))   # equatorial radius of moon = 1738.1 km
    sdm = degrees(atan(1737.4/dist_km))   # volumetric mean radius of moon = 1737.4 km
    horizon = sdm + 0.5666667	# moon's equatorial radius + 34' (atmospheric refraction)

    return horizon

def moonstate(mstate):
    # return the current moonstate (if known)
    out = '--:--'
    if mstate == True:      # above horizon
        out = r'''\begin{tikzpicture}\draw (0,0) rectangle (12pt,4pt);\end{tikzpicture}'''
    if mstate == False:     # below horizon
        out = r'''\rule{12Pt}{4Pt}'''
    return out

#def seek_moonset(prday, t9, t9noon, t0, nxday, t1, t1noon, t2, i, lats, ts, earth, moon):
def seek_moonset(t9, t9noon, t0, t1, t1noon, t2, lats, ts, earth, moon):
    # for the specified date & latitude ...
    # return -1 if there is NO MOONSET yesterday
    # return +1 if there is NO MOONSET tomorrow
    # return  0 if there was a moonset yesterday and will be a moonset tomorrow
    # note: this is called when there is only a moonrise on the specified date+latitude

    time00 = 0.0                        # 00000
    Hseeks = 1
    m_set_t = 0     # normal case: assume moonsets yesterday & tomorrow

    locn = Topos(lats, "0.0 E")
    horizon = getHorizon(t1noon, earth, moon)
    start00 = time()                    # 00000
    moonrise, y = almanac.find_discrete(t1, t2, moonday(earth, moon, locn, horizon))
    time00 += time()-start00            # 00000
    rise, sett, ris2, set2, fs = rise_set(moonrise,y,lats,ts)

    if sett == '--:--':
        m_set_t = +1    # if no moonset detected - it is after tomorrow
    else:
        Hseeks += 1
        locn = Topos(lats, "0.0 E")
        horizon = getHorizon(t9noon, earth, moon)
        start00 = time()                # 00000
        moonrise, y = almanac.find_discrete(t9, t0, moonday(earth, moon, locn, horizon))
        time00 += time()-start00        # 00000
        rise, sett, ris2, set2, fs = rise_set(moonrise,y,lats,ts)

        if sett == '--:--':
            m_set_t = -1    # if no moonset detected - it is before yesterday

    return m_set_t, time00, Hseeks

#def seek_moonrise(prday, t9, t9noon, t0, nxday, t1, t1noon, t2, i, lats, ts, earth, moon):
def seek_moonrise(t9, t9noon, t0, t1, t1noon, t2, lats, ts, earth, moon):
    # for the specified date & latitude ...
    # return -1 if there is NO MOONRISE yesterday
    # return +1 if there is NO MOONRISE tomorrow
    # return  0 if there was a moonrise yesterday and will be a moonrise tomorrow
    # note: this is called when there is only a moonset on the specified date+latitude

    time00 = 0.0                        # 00000
    Hseeks = 1
    m_rise_t = 0    # normal case: assume moonrise yesterday & tomorrow

    locn = Topos(lats, "0.0 E")
    horizon = getHorizon(t1noon, earth, moon)
    start00 = time()                    # 00000
    moonrise, y = almanac.find_discrete(t1, t2, moonday(earth, moon, locn, horizon))
    time00 += time()-start00            # 00000
    rise, sett, ris2, set2, fs = rise_set(moonrise,y,lats,ts)

    if rise == '--:--':
        m_rise_t = +1    # if no moonrise detected - it is after tomorrow
    else:
        Hseeks += 1
        locn = Topos(lats, "0.0 E")
        horizon = getHorizon(t9noon, earth, moon)
        start00 = time()                # 00000
        moonrise, y = almanac.find_discrete(t9, t0, moonday(earth, moon, locn, horizon))
        time00 += time()-start00        # 00000
        rise, sett, ris2, set2, fs = rise_set(moonrise,y,lats,ts)

        if rise == '--:--':
            m_rise_t = -1    # if no moonrise detected - it is before yesterday

    return m_rise_t, time00, Hseeks

#def moonset_no_rise(date, lat, prday, t9, t9noon, t0, nxday, t1, t1noon, t2, i, lats, ts, earth, moon):
def moonset_no_rise(date, lat, t9, t9noon, t0, t1, t1noon, t2, lats, ts, earth, moon):
    # if moonset but no moonrise...
    msg = ""
    n, t00, Hseeks = seek_moonrise(t9, t9noon, t0, t1, t1noon, t2, lats, ts, earth, moon)
    if n == 1:
        out = moonstate(False)      # moonrise "below horizon"
        ##msg = "below horizon (start)"
    if n == -1:
        out = moonstate(True)       # moonrise "above horizon"
        ##msg = "above horizon (end)"
    ##if msg != "": print("no moonrise on {} at lat {} => {}".format(date.strftime("%Y-%m-%d"), lat, msg))
    if n == 0:
        out = r'''\raisebox{0.24ex}{\boldmath$\cdot\cdot$~\boldmath$\cdot\cdot$}'''
    return out, t00, Hseeks

#def moonrise_no_set(date, lat, prday, t9, t9noon, t0, nxday, t1, t1noon, t2, i, lats, ts, earth, moon):
def moonrise_no_set(date, lat, t9, t9noon, t0, t1, t1noon, t2, lats, ts, earth, moon):
    # if moonrise but no moonset...
    msg = ""
    n, t00, Hseeks = seek_moonset(t9, t9noon, t0, t1, t1noon, t2, lats, ts, earth, moon)
    if n == 1:
        out = moonstate(True)       # moonset "above horizon"
        ##msg = "above horizon (start)"
    if n == -1:
        out = moonstate(False)      # moonset "below horizon"
        ##msg = "below horizon (end)"
    ##if msg != "": print("no moonset on  {} at lat {} => {}".format(date.strftime("%Y-%m-%d"), lat, msg))
    if n == 0:
        out = r'''\raisebox{0.24ex}{\boldmath$\cdot\cdot$~\boldmath$\cdot\cdot$}'''
    return out, t00, Hseeks

# > > > > > > > > > > MULTIPROCESSING ENTRY POINT < < < < < < < < < <
# > > > > > > > DO NOT WRITE TO config.py  (It's a copy!) < < < < < <

def mp_moonrise_set(d, lat, mstate0, hemisph, ts):  # used by nautical.py in twilighttab (section 2)
    # - - - TIMES ARE ROUNDED TO MINUTES - - -
    # returns moonrise and moonset for the given dates and latitude:
    # rise day 1, rise day 2, rise day 3, set day 1, set day 2, set day 3

    time00 = 0.0    # 00000 - time spent in find_discrete() when at least one time was returned
    timeAB = 0.0    # time spent seeking if moon is above/below horizon
    Hseeks = 0      # count horizon seeks
    Mseeks = 0      # count of moonrise and/or moonset seeks (a time is returned)
    eph = load(config.ephemeris[config.ephndx][0])	# load chosen ephemeris
    earth   = eph['earth']
    moon    = eph['moon']

    # return [first_event, second_event] per day + processing time + Hseeks
    out = [None, None, None, None]
    ev1 = ['--:--','--:--','--:--','--:--','--:--','--:--']	# first event
    ev2 = ['--:--','--:--','--:--','--:--','--:--','--:--']	# second event on same day (rare)

    lats = "{:3.1f} {}".format(abs(lat), hemisph)
    locn = Topos(lats, "0.0 E")
    dt = datetime(d.year, d.month, d.day, 0, 0, 0)
    dt -= timedelta(seconds=30)     # search from 30 seconds before midnight

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

    #horizon = 0.8333           # 16' (semi-diameter) + 34' (atmospheric refraction)
#-----------------------------------------------------------
    # Moonrise/Moonset on 1st. day ...

    iH = 0
    Mseeks += 1
    locn = Topos(lats, "0.0 E")
    horizon = getHorizon(t0noon, earth, moon)
    start00 = time()                    # 00000
    moonrise, y = almanac.find_discrete(t0, t1, moonday(earth, moon, locn, horizon))
    time00 += time()-start00            # 00000
    ev1[0], ev1[3], ev2[0], ev2[3], mstate1 = rise_set(moonrise,y,lats,ts)

    if ev1[0] == '--:--' and ev1[3] == '--:--':	# if neither moonrise nor moonset...
        Mseeks -= 1
        if mstate1 == None:
            if mstate0 != None:
                mstate1 = mstate0        # get the last known moon state
            else:   # must search for the moon state...
                mstate1, t00, iH = getmoonstate(dt, lat, hemisph, ts, earth, moon)	# ...get moon state if unknown
                timeAB += t00                   # 00000
        ev1[0] = moonstate(mstate1)
        ev1[3] = moonstate(mstate1)

    elif ev1[0] == '--:--' and ev1[3] != '--:--':	# if moonset but no moonrise...
        ev1[0], t00, iH = moonset_no_rise(d, lat, t9, t9noon, t0, t1, t1noon, t2, lats, ts, earth, moon)
        timeAB += t00                   # 00000

    elif ev1[0] != '--:--' and ev1[3] == '--:--':	# if moonrise but no moonset...
        ev1[3], t00, iH = moonrise_no_set(d, lat, t9, t9noon, t0, t1, t1noon, t2, lats, ts, earth, moon)
        timeAB += t00                   # 00000
    Hseeks += iH
#-----------------------------------------------------------
    # Moonrise/Moonset on 2nd. day ...

    iH = 0
    Mseeks += 1
    locn = Topos(lats, "0.0 E")
    horizon = getHorizon(t1noon, earth, moon)
    start00 = time()                    # 00000
    moonrise, y = almanac.find_discrete(t1, t2, moonday(earth, moon, locn, horizon))
    time00 += time()-start00            # 00000
    ev1[1], ev1[4], ev2[1], ev2[4], mstate2 = rise_set(moonrise,y,lats,ts)

    if ev1[1] == '--:--' and ev1[4] == '--:--':	# if neither moonrise nor moonset...
        Mseeks -= 1
        if mstate2 == None:
            if mstate1 != None:
                mstate2 = mstate1        # get the last known moon state
            else:   # must search for the moon state...
                mstate2, t00, iH = getmoonstate(dt+timedelta(days=1), lat, hemisph, ts, earth, moon)	# ...get moon state if unknown
                timeAB += t00                   # 00000
        ev1[1] = moonstate(mstate2)
        ev1[4] = moonstate(mstate2)

    elif ev1[1] == '--:--' and ev1[4] != '--:--':	# if moonset but no moonrise...
        ev1[1], t00, iH = moonset_no_rise(d1, lat, t0, t0noon, t1, t2, t2noon, t3, lats, ts, earth, moon)
        timeAB += t00                   # 00000

    elif ev1[1] != '--:--' and ev1[4] == '--:--':	# if moonrise but no moonset...
        ev1[4], t00, iH = moonrise_no_set(d1, lat, t0, t0noon, t1, t2, t2noon, t3, lats, ts, earth, moon)
        timeAB += t00                   # 00000
    Hseeks += iH
#-----------------------------------------------------------
    # Moonrise/Moonset on 3rd. day ...

    iH = 0
    Mseeks += 1
    locn = Topos(lats, "0.0 E")
    horizon = getHorizon(t2noon, earth, moon)
    start00 = time()                    # 00000
    moonrise, y = almanac.find_discrete(t2, t3, moonday(earth, moon, locn, horizon))
    time00 += time()-start00            # 00000
    ev1[2], ev1[5], ev2[2], ev2[5], mstate3 = rise_set(moonrise,y,lats,ts)

    if ev1[2] == '--:--' and ev1[5] == '--:--':	# if neither moonrise nor moonset...
        Mseeks -= 1
        if mstate3 == None:
            if mstate2 != None:
                mstate3 = mstate2        # get the last known moon state
            else:   # must search for the moon state...
                mstate3, t00, iH = getmoonstate(dt+timedelta(days=2), lat, hemisph, ts, earth, moon)	# ...get moon state if unknown
                timeAB += t00                   # 00000
        ev1[2] = moonstate(mstate3)
        ev1[5] = moonstate(mstate3)

    elif ev1[2] == '--:--' and ev1[5] != '--:--':	# if moonset but no moonrise...
        ev1[2], t00, iH = moonset_no_rise(d2, lat, t1, t1noon, t2, t3, t3noon, t4, lats, ts, earth, moon)
        timeAB += t00                   # 00000

    elif ev1[2] != '--:--' and ev1[5] == '--:--':	# if moonrise but no moonset...
        ev1[5], t00, iH = moonrise_no_set(d2, lat, t1, t1noon, t2, t3, t3noon, t4, lats, ts, earth, moon)
        timeAB += t00                   # 00000
    Hseeks += iH
#-----------------------------------------------------------

    out[0] = ev1        # [rise day 1, rise day 2, rise day 3, set day 1, set day 2, set day 3] for event 1
    out[1] = ev2        # [rise day 1, rise day 2, rise day 3, set day 1, set day 2, set day 3] for event 2 (rare)
    # append to list ...
    out[2] = (time00, timeAB)     # time spent (returning >= 1 event time) + (seeking if moon above/below horizon)
    out[3] = (Mseeks, Hseeks, mstate3)     # count of (moonrise/set seeks) + (horizon seeks) + moon state
    return out

def moonday(earth, moon, topos, degBelowHorizon):
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