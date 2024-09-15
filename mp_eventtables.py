#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   Copyright (C) 2024  Andrew Bauer

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
# Except for 4 functions this replaces alma_skyfield.py
#     Note: 6 worker processes are sufficient
#     Note: read/write to a global variable will occur randomly and give false
#           results, e.g. if 'moonvisible[]' is declared here.
#     Note: incrementing elapsed time in config.stopwatch fails: result is 0.0
# Shared memory: It is NOT possible to share arbitrary Python objects.
#                Multiprocessing can create shared memory blocks containing C
#                variables and C arrays. A NumPy extension adds shared NumPy arrays.
# ----------------------------------------------------------------------------------

###### Standard library imports ######
from datetime import datetime, timedelta, timezone
import time as Time     # 00000 - stopwatch elements
from math import degrees, atan
#import sys			# sys.exit() does not work here

###### Third party imports ######
from skyfield import VERSION
from skyfield.api import load
from skyfield.api import Topos, Star, wgs84, N, S, E, W     # Topos is deprecated in Skyfield v1.35!
from skyfield import almanac
from skyfield.nutationlib import iau2000b
#from skyfield.data import hipparcos

###### Local application imports ######
import config

#----------------------
#   initialization
#----------------------

hour_of_day = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
degree_sign= u'\N{DEGREE SIGN}'

#----------------------
#   internal methods
#----------------------

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

def time2text(t, with_seconds, debug=False, fs = None):
    # note: times printed are ROUNDED appropriately to the minute or second - for proof, enable 'debug'
    if debug:
        dt = t.utc_datetime()                   # convert to python datetime in UTC
        ut1 = dt + timedelta(seconds=t.dut1)    # convert to datetime in UT1
        print("   ",ut1.isoformat(' '),"   ",t.ut1_strftime('%H:%M:%S'),"   ",t.ut1_strftime('%H:%M'),"   ",bool(fs))

    # Note:     ..._strftime functionality:
    #   If the smallest time unit in your format is minutes or seconds, then the time is rounded
    #    to the nearest minute or second. Otherwise the value is truncated rather than rounded.

    if with_seconds:
        return t.ut1_strftime('%H:%M:%S')
    else:
        return t.ut1_strftime('%H:%M')

def next_rise_set(rise, sett, yR, yS):
    ndxR = 0 if len(rise) > 0 else 10
    ndxS = 0 if len(sett) > 0 else 10
    pickRISE = None         # no idea if RISE or SET comes first and is valid
    prev_dt = datetime.min.replace(tzinfo=timezone.utc)     # closest to datetime zero
    currentstate = None

    while ndxR < len(rise) or ndxS < len(sett):
        if pickRISE is None:        # establish if RISE or SET to be chosen (initialize pickRISE)
            RISEok = SETTok = False
            if ndxR < len(rise): RISEok = True
            if ndxS < len(sett): SETTok = True
            if RISEok and not SETTok: pickRISE = True
            if SETTok and not RISEok: pickRISE = False
            if RISEok and SETTok:
                pickRISE = True if rise[ndxR] < sett[ndxS] else False           # Skyfield >= 1.48 rqrd
            if not RISEok and not SETTok: ndxR += 1; ndxS += 1
            continue      # avoid 't.utc_datetime()' below as 't' unknown
        elif pickRISE:
            t = rise[ndxR]
            if yR[ndxR]: currentstate = False; break
            ndxR += 1
            pickRISE = not pickRISE     # flip RISE to SET & vice-versa
        else:
            t = sett[ndxS]
            if yS[ndxS]: currentstate = True; break
            ndxS += 1
            pickRISE = not pickRISE     # flip RISE to SET & vice-versa

        dt = t.utc_datetime()
        if prev_dt > dt: print("Event time sequence ERROR on {} in mp_eventtables.next_rise_set".format(dt.strftime("%d-%m-%Y")))
        prev_dt = dt

    return currentstate

def fmt_rise_set(rise, sett, yR, yS, txt, with_seconds=False):
    # note: yR and yS must be passed here as it is not possible to .pop() a False time from the Time object.
    # note: if yR or yS returns [], it is interpreted as False. However the time would also be [].
    ndxR = 0 if len(rise) > 0 else 10
    ndxS = 0 if len(sett) > 0 else 10
    pickRISE = None         # no idea if RISE or SET comes first and is valid
    
    prev_dt = datetime.min.replace(tzinfo=timezone.utc)     # closest to datetime zero
    r = s = 0
    Rtxt = ['--:--', '--:--'] #if not with_seconds else ['--:--:--', '--:--:--']
    Stxt = ['--:--', '--:--'] #if not with_seconds else ['--:--:--', '--:--:--']
    finalstate = None   # True if above horizon; False if below horizon; None if unknown

    while ndxR < len(rise) or ndxS < len(sett):
        if pickRISE is None:        # establish if RISE or SET to be chosen (initialize pickRISE)
            RISEok = SETTok = False
            if ndxR < len(rise) and yR[ndxR]: RISEok = True
            if ndxS < len(sett) and yS[ndxS]: SETTok = True
            if RISEok and not SETTok: pickRISE = True
            if SETTok and not RISEok: pickRISE = False
            if RISEok and SETTok:
                pickRISE = True if rise[ndxR] < sett[ndxS] else False           # Skyfield >= 1.48 rqrd
            if not RISEok and not SETTok: ndxR += 1; ndxS += 1
            continue      # avoid 't.utc_datetime()' below as 't' unknown
        elif pickRISE:
            if ndxR < len(rise):
                t = rise[ndxR]
                if yR[ndxR]:
                    Rtxt[r] = time2text(t, with_seconds)
                    r += 1; finalstate = True
                ndxR += 1
            pickRISE = not pickRISE     # flip RISE to SET & vice-versa
        else:
            if ndxS < len(sett):
                t = sett[ndxS]
                if yS[ndxS]:
                    Stxt[s] = time2text(t, with_seconds)
                    s += 1; finalstate = False
                ndxS += 1
            pickRISE = not pickRISE     # flip RISE to SET & vice-versa

        dt = t.utc_datetime()
        if prev_dt > dt: print("Event time sequence ERROR on {} in mp_eventtables.fmt_rise_set".format(dt.strftime("%d-%m-%Y")))
        prev_dt = dt

    return Rtxt[0], Stxt[0], Rtxt[1], Stxt[1], finalstate

def fmt_transits(t, lats, with_seconds = False):
    # analyse the return values from the 'find_transits' method...
    # get planet transit times (if any) rounded to nearest minute
    transit1 = '--:--'
    transit2 = '--:--'
    if len(t) == 1:         # this happens most often
        t0 = t[0]
        # get the UT1 time rounded to minutes OR seconds ...
        transit1 = time2text(t0, with_seconds)
    else:
        if len(t) == 2:		# this happens very rarely
            t0 = t[0]; t1 = t[1]
            # get the UT1 time rounded to minutes OR seconds ...
            transit1 = time2text(t0, with_seconds)
            transit2 = time2text(t1, with_seconds)
        elif len(t) > 2:
            # this should never get here!
            rise_set_error(0,lats,t[0])

    return transit1, transit2

def rise_set(t, y, lats, with_seconds = False):    # 'ts' removed (Aug 2024 simplification)
    # analyse the return values from the 'find_discrete' method...
    # get sun/moon rise/set values (if any) rounded to nearest minute
    rise = '--:--'
    sett = '--:--'
    ris2 = '--:--'
    set2 = '--:--'
    finalstate = None   # True if above horizon; False if below horizon; None if unknown
    if len(t) == 2:		# this happens most often
        t0 = t[0]; t1 = t[1]        # Aug 2024 simplification
        # dt0 = t[0].utc_datetime()
        # sec0 = dt0.second + int(dt0.microsecond)/1000000.
        # t0 = ts.ut1(dt0.year, dt0.month, dt0.day, dt0.hour, dt0.minute, sec0)
        # dt1 = t[1].utc_datetime()
        # sec1 = dt1.second + int(dt1.microsecond)/1000000.
        # t1 = ts.ut1(dt1.year, dt1.month, dt1.day, dt1.hour, dt1.minute, sec1)
        if y[0] and not(y[1]):
            # get the UT1 time rounded to minutes OR seconds ...
            rise = time2text(t0, with_seconds)
            sett = time2text(t1, with_seconds)
            finalstate = False
        else:
            if not(y[0]) and y[1]:
                # get the UT1 time rounded to minutes OR seconds ...
                sett = time2text(t0, with_seconds)
                rise = time2text(t1, with_seconds)
                finalstate = True
            else:
                # this should never get here!
                rise_set_error(y,lats,t[0])     # Aug 2024 simplification
    else:
        if len(t) == 1:		# this happens ocassionally
            t0 = t[0]               # Aug 2024 simplification
            # dt0 = t[0].utc_datetime()
            # sec0 = dt0.second + int(dt0.microsecond)/1000000.
            # t0 = ts.ut1(dt0.year, dt0.month, dt0.day, dt0.hour, dt0.minute, sec0)
            if y[0]:
                # get the UT1 time rounded to minutes OR seconds ...
                rise = time2text(t0, with_seconds)
                finalstate = True
            else:
                # get the UT1 time rounded to minutes OR seconds ...
                sett = time2text(t0, with_seconds)
                finalstate = False
        else:
            if len(t) == 3:		# this happens rarely (in high latitudes mid-year)
                t0 = t[0]; t1 = t[1]; t2 = t[2]     # Aug 2024 simplification
                # dt0 = t[0].utc_datetime()
                # sec0 = dt0.second + int(dt0.microsecond)/1000000.
                # t0 = ts.ut1(dt0.year, dt0.month, dt0.day, dt0.hour, dt0.minute, sec0)
                # dt1 = t[1].utc_datetime()
                # sec1 = dt1.second + int(dt1.microsecond)/1000000.
                # t1 = ts.ut1(dt1.year, dt1.month, dt1.day, dt1.hour, dt1.minute, sec1)
                # dt2 = t[2].utc_datetime()
                # sec2 = dt2.second + int(dt2.microsecond)/1000000.
                # t2 = ts.ut1(dt2.year, dt2.month, dt2.day, dt2.hour, dt2.minute, sec2)
                if y[0] and not(y[1]) and y[2]:
                    # get the UT1 time rounded to minutes OR seconds ...
                    rise = time2text(t0, with_seconds)
                    sett = time2text(t1, with_seconds)
                    ris2 = time2text(t2, with_seconds)
                    finalstate = True
                else:
                    if not(y[0]) and y[1] and not(y[2]):
                        # get the UT1 time rounded to minutes OR seconds ...
                        sett = time2text(t0, with_seconds)
                        rise = time2text(t1, with_seconds)
                        set2 = time2text(t2, with_seconds)
                        finalstate = False
                    else:
                        # this should never get here!
                        rise_set_error(y,lats,t[0])     # Aug 2024 simplification
            else:
                if len(t) > 3:
                    # this should never get here!
                    rise_set_error(y,lats,t[0])     # Aug 2024 simplification

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

#---------------------------------------
#   Planet SHA & transit calculations
#---------------------------------------

# > > > > > > > > > > MULTIPROCESSING ENTRY POINT < < < < < < < < < <
def mp_planetstransit(d, ts, obj, with_seconds = False):  # used in eventtables.meridiantab
    # returns SHA and Meridian Passage for the navigational planets

    out = [None, None, None]    # return [planet_sha, planet_transit] + processing time
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
    lattxt = u'{} 0{} E transit'.format(obj, degree_sign)
    if compareVersion(VERSION, "1.35") >= 0:
        lats = 0.0     # default latitude (any will do)
        topos = wgs84.latlon(lats, 0.0 * E, elevation_m=0.0)
        observer = earth + topos
    else:
        topos = Topos(latNS, "0.0 E")   # Topos is deprecated in Skyfield v1.35!

    # calculate planet SHA
    tfr = ts.ut1(d.year, d.month, d.day, 0, 0, 0)       # search from
    position = earth.at(tfr).observe(planet)
    ra = position.apparent().radec(epoch='date')[0]     # RA
    out[0] = fmtgha(0, ra.hours)    # planet_sha
    
    # calculate planet transit
    d1 = d + timedelta(days=1)
    tto = ts.ut1(d1.year, d1.month, d1.day, 0, 0, 0)    # search to
    start00 = Time.time()                   # 00000
    if compareVersion(VERSION, "1.48") < 0:
        transit_time, y = almanac.find_discrete(tfr, tto, planet_transit(earth, planet))
        time00 = Time.time()-start00        # 00000
        out[1] = rise_set(transit_time,y,lattxt,with_seconds)[0]  # planet_transit
    else:
        transit_time = almanac.find_transits(observer, planet, tfr, tto)
        time00 = Time.time()-start00        # 00000
        out[1] = fmt_transits(transit_time,lattxt,with_seconds)[0]  # planet_transit

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

#------------------------
#   SUN TWILIGHT table
#------------------------

# > > > > > > > > > > MULTIPROCESSING ENTRY POINT < < < < < < < < < <
def mp_twilight(d, lat, ts, with_seconds = False):  # used in eventtables.twilighttab
    # Returns for given date and latitude(in full degrees):
    # naut. and civil twilight (before sunrise), sunrise, meridian passage, sunset, civil and nautical twilight (after sunset).
    # NOTE: 'twilight' is only called for every third day in the Nautical Almanac...
    #       ...therefore daily tracking of the sun state is not possible.

    time00 = 0                              # 00000
    eph = load(config.ephemeris[config.ephndx][0])	# load chosen ephemeris
    earth   = eph['earth']
    sun     = eph['sun']

    out = [None,None,None,None,None,None,None]  # 6 data items + processing time
    hemisph = 'N' if lat >= 0 else 'S'
    latNS = "{:3.1f} {}".format(abs(lat), hemisph)
    if compareVersion(VERSION, "1.35") >= 0:
        topos = wgs84.latlon(lat, 0.0 * E, elevation_m=0.0)
        observer = earth + topos
    else:
        topos = Topos(latNS, "0.0 E")   # Topos is deprecated in Skyfield v1.35!

    dt = datetime(d.year, d.month, d.day, 0, 0, 0)

    if with_seconds:
        dt -= timedelta(seconds=0.5)    # search from 0.5 seconds before midnight
    else:
        dt -= timedelta(seconds=30)     # search from 30 seconds before midnight

    t0 = ts.ut1(dt.year, dt.month, dt.day,   dt.hour, dt.minute, dt.second)
    t1 = ts.ut1(dt.year, dt.month, dt.day+1, dt.hour, dt.minute, dt.second)
    abhd = False                                # above/below horizon display NOT enabled

    # Sunrise/Sunset...
    horizon = 0.8333        # degrees below horizon
    start00 = Time.time()                   # 00000
    if compareVersion(VERSION, "1.48") < 0:
        actual, y = almanac.find_discrete(t0, t1, f_sun(earth, sun, topos, horizon))
        time00 += Time.time()-start00       # 00000
        out[2], out[3], r2, s2, fs = rise_set(actual,y,latNS,with_seconds)
    else:
        sunrise, yR = almanac.find_risings(observer, sun, t0, t1, -horizon)
        sunset,  yS = almanac.find_settings(observer, sun, t0, t1, -horizon)
        time00 += Time.time()-start00       # 00000
        out[2], out[3], r2, s2, fs = fmt_rise_set(sunrise,sunset,yR,yS,latNS,with_seconds)

    if out[2] == '--:--' and out[3] == '--:--':	# if neither sunrise nor sunset...
        abhd = True                             # enable above/below horizon display
        yn = midnightsun(d, hemisph)
        out[2] = yn
        out[3] = yn

    # Civil Twilight...
    horizon = 6.0           # degrees below horizon
    start00 = Time.time()                   # 00000
    if compareVersion(VERSION, "1.48") < 0:
        civil, y = almanac.find_discrete(t0, t1, f_sun(earth, sun, topos, horizon))
        time00 += Time.time()-start00       # 00000
        out[1], out[4], r2, s2, fs = rise_set(civil,y,latNS,with_seconds)
    else:
        sunrise, yR = almanac.find_risings(observer, sun, t0, t1, -horizon)
        sunset,  yS = almanac.find_settings(observer, sun, t0, t1, -horizon)
        time00 += Time.time()-start00       # 00000
        out[1], out[4], r2, s2, fs = fmt_rise_set(sunrise,sunset,yR,yS,latNS,with_seconds)

    if abhd and out[1] == '--:--' and out[4] == '--:--':	# if neither begin nor end...
        yn = midnightsun(d, hemisph)
        out[1] = yn
        out[4] = yn

    # Nautical Twilight...
    horizon = 12.0          # degrees below horizon
    start00 = Time.time()                   # 00000
    if compareVersion(VERSION, "1.48") < 0:
        naut, y = almanac.find_discrete(t0, t1, f_sun(earth, sun, topos, horizon))
        time00 += Time.time()-start00       # 00000
        out[0], out[5], r2, s2, fs = rise_set(naut,y,latNS,with_seconds)
    else:
        sunrise, yR = almanac.find_risings(observer, sun, t0, t1, -horizon)
        sunset,  yS = almanac.find_settings(observer, sun, t0, t1, -horizon)
        time00 += Time.time()-start00       # 00000
        out[0], out[5], r2, s2, fs = fmt_rise_set(sunrise,sunset,yR,yS,latNS,with_seconds)

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

def f_sun(earth, sun, topos, degBelowHorizon):
    # Build a function of time that returns the sun above/below horizon state.
    topos_at = (earth + topos).at

    def is_sun_up_at(t):
        """The function that this returns will expect a single argument that is a 
		:class:`~skyfield.timelib.Time` and will return ``True`` if the sun is up
		or twilight has started, else ``False``."""
        t._nutation_angles = iau2000b(t.tt)
        # Return `True` if the sun has risen by time `t`.
        return topos_at(t).observe(sun).apparent().altaz()[0].degrees > -degBelowHorizon

    #is_sun_up_at.rough_period = 0.5         # 24 samples per day (deprecated)
    is_sun_up_at.step_days = 0.041666667    # = 1.0 / 24.0 (24 samples per day)
    return is_sun_up_at

#-------------------------
#   MOONRISE/-SET table
#-------------------------

def getmoonstate(dt, lat, horizon, ts, earth, moon):
    # populate the moon state (visible or not) for the specified date & latitude
    # note: the first parameter 'dt' is already a datetime 0.5 seconds before midnight
    # note: getmoonstate is called when there is neither a moonrise nor a moonset on 'dt'

    time00 = 0                              # 00000
    i = 1 + config.lat.index(lat)   # index 0 is reserved to enable an explicit setting
    hemisph = 'N' if lat >= 0 else 'S'
    latNS = '{:3.1f} {}'.format(abs(lat), hemisph)
    if compareVersion(VERSION, "1.35") >= 0:
        topos = wgs84.latlon(lat, 0.0 * E, elevation_m=0.0)
        observer = earth + topos
    else:
        topos = Topos(latNS, "0.0 E")   # Topos is deprecated in Skyfield v1.35!

    t0 = ts.ut1(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    #horizon = 0.8333        # degrees below horizon

    # search for the next moonrise or moonset (returned in moonrise[0] and y[0])
    mstate = None
    while mstate == None:
        t0 = ts.ut1(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        dt += timedelta(days=1)
        t9 = ts.ut1(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        start00 = Time.time()               # 00000
        if True or compareVersion(VERSION, "1.48") < 0:
            moonrise, y = almanac.find_discrete(t0, t9, f_moon(earth, moon, topos, horizon))
            time00 += Time.time()-start00   # 00000
            if len(moonrise) > 0:
                mstate = False if y[0] else True
        else:   # !!! DO NOT USE WITH Skyfield 1.48 !!! (see Skyfield Issue #998)
            moonrise, yR = almanac.find_risings(observer, moon, t0, t9, -horizon)
            moonset,  yS = almanac.find_settings(observer, moon, t0, t9, -horizon)
            time00 = Time.time()-start00    # 00000
            mstate = next_rise_set(moonrise,moonset,yR,yS)

    return mstate, time00

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

def seek_moonset(prday, t9, t9noon, t0, nxday, t1, t1noon, t2, i, lat, ts, earth, moon, with_seconds=False):
    # for the specified date & latitude ...
    # return -1 if there is NO MOONSET yesterday
    # return +1 if there is NO MOONSET tomorrow
    # return  0 if there was a moonset yesterday and will be a moonset tomorrow
    # note: this is called when there is only a moonrise on the specified date+latitude

    time00 = 0                              # 00000
    config.moonHorizonSeeks += 1
    m_set_t = 0     # normal case: assume moonsets yesterday & tomorrow
    hemisph = 'N' if lat >= 0 else 'S'
    latNS = "{:3.1f} {}".format(abs(lat), hemisph)
    if compareVersion(VERSION, "1.35") >= 0:
        topos = wgs84.latlon(lat, 0.0 * E, elevation_m=0.0)
        observer = earth + topos
    else:
        topos = Topos(latNS, "0.0 E")   # Topos is deprecated in Skyfield v1.35!

#    rise, sett, ris2, set2, fs = fetchMoonData(nxday, t1, t1noon, t2, i, latNS, True, with_seconds)
    horizon = getHorizon(t1noon, earth, moon)
    start00 = Time.time()                   # 00000
    if True or compareVersion(VERSION, "1.48") < 0:
        moonrise, y = almanac.find_discrete(t1, t2, f_moon(earth, moon, topos, horizon))
        time00 += Time.time()-start00       # 00000
        rise, sett, ris2, set2, fs = rise_set(moonrise,y,latNS,True)
    else:   # !!! DO NOT USE WITH Skyfield 1.48 !!! (see Skyfield Issue #998)
        moonset, yS = almanac.find_settings(observer, moon, t1, t2, -horizon)
        time00 = Time.time()-start00        # 00000
        rise, sett, ris2, set2, fs = fmt_rise_set([],moonset[:1],[],yS,latNS,with_seconds)

    if sett == '--:--':
        m_set_t = +1    # if no moonset detected - it is after tomorrow
    else:
        config.moonHorizonSeeks += 1
#        rise, sett, ris2, set2, fs = fetchMoonData(prday, t9, t9noon, t0, i, latNS, True, with_seconds)
        horizon = getHorizon(t9noon, earth, moon)
        start00 = Time.time()               # 00000
        if True or compareVersion(VERSION, "1.48") < 0:
            moonrise, y = almanac.find_discrete(t9, t0, f_moon(earth, moon, topos, horizon))
            time00 += Time.time()-start00   # 00000
            rise, sett, ris2, set2, fs = rise_set(moonrise,y,latNS,True)
        else:   # !!! DO NOT USE WITH Skyfield 1.48 !!! (see Skyfield Issue #998)
            moonset, yS = almanac.find_settings(observer, moon, t9, t0, -horizon)
            time00 = Time.time()-start00    # 00000
            rise, sett, ris2, set2, fs = fmt_rise_set([],moonset[:1],[],yS,latNS,with_seconds)

        if sett == '--:--':
            m_set_t = -1    # if no moonset detected - it is before yesterday

    return m_set_t, time00

def seek_moonrise(prday, t9, t9noon, t0, nxday, t1, t1noon, t2, i, lat, ts, earth, moon, with_seconds=False):
    # return -1 if there is NO MOONRISE yesterday
    # return +1 if there is NO MOONRISE tomorrow
    # return  0 if there was a moonrise yesterday and will be a moonrise tomorrow
    # note: this is called when there is only a moonset on the specified date+latitude

    time00 = 0                              # 00000
    config.moonHorizonSeeks += 1
    m_rise_t = 0    # normal case: assume moonrise yesterday & tomorrow
    hemisph = 'N' if lat >= 0 else 'S'
    latNS = "{:3.1f} {}".format(abs(lat), hemisph)
    if compareVersion(VERSION, "1.35") >= 0:
        topos = wgs84.latlon(lat, 0.0 * E, elevation_m=0.0)
        observer = earth + topos
    else:
        topos = Topos(latNS, "0.0 E")   # Topos is deprecated in Skyfield v1.35!

#    rise, sett, ris2, set2, fs = fetchMoonData(nxday, t1, t1noon, t2, i, latNS, True)
    horizon = getHorizon(t1noon, earth, moon)
    start00 = Time.time()                   # 00000
    if True or compareVersion(VERSION, "1.48") < 0:
        moonrise, y = almanac.find_discrete(t1, t2, f_moon(earth, moon, topos, horizon))
        time00 += Time.time()-start00       # 00000
        rise, sett, ris2, set2, fs = rise_set(moonrise,y,latNS,True)
    else:   # !!! DO NOT USE WITH Skyfield 1.48 !!! (see Skyfield Issue #998)
        moonrise, yR = almanac.find_risings(observer, moon, t1, t2, -horizon)
        time00 = Time.time()-start00        # 00000
        rise, sett, ris2, set2, fs = fmt_rise_set(moonrise[:1],[],yR,[],latNS,with_seconds)

    if rise == '--:--':
        m_rise_t = +1    # if no moonrise detected - it is after tomorrow
    else:
        config.moonHorizonSeeks += 1
#        rise, sett, ris2, set2, fs = fetchMoonData(prday, t9, t9noon, t0, i, latNS, True)
        horizon = getHorizon(t9noon, earth, moon)
        start00 = Time.time()               # 00000
        if True or compareVersion(VERSION, "1.48") < 0:
            moonrise, y = almanac.find_discrete(t9, t0, f_moon(earth, moon, topos, horizon))
            time00 += Time.time()-start00   # 00000
            rise, sett, ris2, set2, fs = rise_set(moonrise,y,latNS,True)
        else:   # !!! DO NOT USE WITH Skyfield 1.48 !!! (see Skyfield Issue #998)
            moonrise, yR = almanac.find_risings(observer, moon, t9, t0, -horizon)
            time00 = Time.time()-start00    # 00000
            rise, sett, ris2, set2, fs = fmt_rise_set(moonrise[:1],[],yR,[],latNS,with_seconds)

        if rise == '--:--':
            m_rise_t = -1    # if no moonrise detected - it is before yesterday

    return m_rise_t, time00

def moonset_no_rise(date, lat, prday, t9, t9noon, t0, nxday, t1, t1noon, t2, i, ts, earth, moon, with_seconds=False):
    # if moonset but no moonrise...
    msg = ""
    n, t00 = seek_moonrise(prday, t9, t9noon, t0, nxday, t1, t1noon, t2, i, lat, ts, earth, moon, with_seconds)
    if n == 1:
        out = moonstate(False)       # moonrise "below horizon"
        ##msg = "below horizon (start)"
    if n == -1:
        out = moonstate(True)       # moonrise "above horizon"
        ##msg = "above horizon (end)"
    ##if msg != "": print("no moonrise on {} at lat {} => {}".format(date.strftime("%Y-%m-%d"), lat, msg))
    if n == 0:
        out = r'''\raisebox{0.24ex}{\boldmath$\cdot\cdot$~\boldmath$\cdot\cdot$}'''
    return out, t00

def moonrise_no_set(date, lat, prday, t9, t9noon, t0, nxday, t1, t1noon, t2, i, ts, earth, moon, with_seconds=False):
    # if moonrise but no moonset...
    msg = ""
    n, t00 = seek_moonset(prday, t9, t9noon, t0, nxday, t1, t1noon, t2, i, lat, ts, earth, moon, with_seconds)
    if n == 1:
        out = moonstate(True)       # moonset "above horizon"
        ##msg = "above horizon (start)"
    if n == -1:
        out = moonstate(False)       # moonset "below horizon"
        ##msg = "below horizon (end)"
    ##if msg != "": print("no moonset on  {} at lat {} => {}".format(date.strftime("%Y-%m-%d"), lat, msg))
    if n == 0:
        out = r'''\raisebox{0.24ex}{\boldmath$\cdot\cdot$~\boldmath$\cdot\cdot$}'''
    return out, t00

# > > > > > > > > > > MULTIPROCESSING ENTRY POINT < < < < < < < < < <
# > > > > > > > DO NOT WRITE TO config.py  (It's a copy!) < < < < < <

def mp_moonrise_set(d, lat, ts):    # used in eventtables.twilighttab
    # - - - TIMES ARE ROUNDED TO SECONDS - - -
    with_seconds = True
    # returns moonrise and moonset for the given date and latitude:
    #    rise time, set time

    time00 = 0.0    # 00000 - time spent in find_discrete() when at least one time was returned
    timeAB = 0.0    # time spent seeking if moon is above/below horizon
    eph = load(config.ephemeris[config.ephndx][0])	# load chosen ephemeris
    earth   = eph['earth']
    moon    = eph['moon']

    out = [None, None, None]  # return [first_event, second_event, processing time]
    ev1 = ['--:--','--:--']	# first event
    ev2 = ['--:--','--:--']	# second event on same day (rare)
    i = 1 + config.lat.index(lat)   # index 0 is reserved to enable an explicit setting

    hemisph = 'N' if lat >= 0 else 'S'
    latNS = "{:3.1f} {}".format(abs(lat), hemisph)
    if compareVersion(VERSION, "1.35") >= 0:
        topos = wgs84.latlon(lat, 0.0 * E, elevation_m=0.0)
        observer = earth + topos
    else:
        topos = Topos(latNS, "0.0 E")   # Topos is deprecated in Skyfield v1.35!

    dt = datetime(d.year, d.month, d.day, 0, 0, 0)
    
    # search from 0.5 second before midnight (because we are rounding to seconds)
    dt -= timedelta(seconds=0.5)    # equivalent to 'dt -= timedelta(microseconds=500000)'
    #print("       ",dt.isoformat(' '))

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

    horizon = getHorizon(t0noon, earth, moon)   # 0.8307988 on 16-08-2024
    #print("horizon =",horizon)
    start00 = Time.time()                   # 00000
    if True or compareVersion(VERSION, "1.48") < 0:
        moonrise, y = almanac.find_discrete(t0, t1, f_moon(earth, moon, topos, horizon))
        time00 += Time.time()-start00       # 00000
        ev1[0], ev1[1], ev2[0], ev2[1], mstate = rise_set(moonrise,y,latNS,True)
    else:   # !!! DO NOT USE WITH Skyfield 1.48 !!! (see Skyfield Issue #998)
        moonrise, yR = almanac.find_risings(observer, moon, t0, t1, -horizon)
        moonset,  yS = almanac.find_settings(observer, moon, t0, t1, -horizon)

        time00 = Time.time()-start00        # 00000
        ev1[0], ev1[1], ev2[0], ev2[1], mstate = fmt_rise_set(moonrise,moonset,yR,yS,latNS,with_seconds)

    if ev1[0] == '--:--' and ev1[1] == '--:--':	# if neither moonrise nor moonset...
        if mstate == None:
            mstate, t00 = getmoonstate(dt, lat, horizon, ts, earth, moon)	# ...get moon state if unknown
        timeAB += t00                       # 00000
        ev1[0] = moonstate(mstate)
        ev1[1] = moonstate(mstate)

    if ev1[0] == '--:--' and ev1[1] != '--:--':	# if moonset but no moonrise...
        ev1[0], t00 = moonset_no_rise(d, lat, d9, t9, t9noon, t0, d1, t1, t1noon, t2, i, ts, earth, moon, True)
        timeAB += t00                       # 00000

    if ev1[0] != '--:--' and ev1[1] == '--:--':	# if moonrise but no moonset...
        ev1[1], t00 = moonrise_no_set(d, lat, d9, t9, t9noon, t0, d1, t1, t1noon, t2, i, ts, earth, moon, True)
        timeAB += t00                       # 00000

    out[0] = ev1        # [rise, set] for event 1
    out[1] = ev2        # [rise, set] for event 2 (rare)
    # append to list ...
    out[2] = (time00, timeAB)     # time spent (returning >= 1 event time) + (seeking if moon above/below horizon)
    return out

def f_moon (earth, moon, topos, degBelowHorizon):
    # Build a function of time that returns the moon above/below horizon state.
    topos_at = (earth + topos).at

    def is_moon_up_at(t):
        """The function that this returns will expect a single argument that is a 
		:class:`~skyfield.timelib.Time` and will return ``True`` if the moon is up
		or twilight has started, else ``False``."""
        t._nutation_angles = iau2000b(t.tt)
        # Return `True` if the moon has risen by time `t`.
        return topos_at(t).observe(moon).apparent().altaz()[0].degrees > -degBelowHorizon

    #is_moon_up_at.rough_period = 0.5        # 24 samples per day (deprecated)
    is_moon_up_at.step_days = 0.000694444   # = 1.0 / 24.0 / 60.0 (once per minute)
    return is_moon_up_at