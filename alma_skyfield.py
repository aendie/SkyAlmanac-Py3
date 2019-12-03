#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   Copyright (C) 2019  Andrew Bauer

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

# This contains most functions that calculate values for the nautical almanac

import config
import math
import datetime
from skyfield.api import Topos, Star, load
from skyfield import almanac
from skyfield.nutationlib import iau2000b
from skyfield.data import hipparcos
#from skyfield.units import Distance
#from skyfield.units import Angle

#load    = Loader('~/Documents/fishing/SkyData')  # avoids multiple copies of large files

ts = load.timescale()	# timescale object
hipparcos_epoch = ts.tt(1991.25)
eph = load('de421.bsp')	# ephemeris, valid between 1900 and 2050
earth   = eph['earth']
moon    = eph['moon']
sun     = eph['sun']
venus   = eph['venus']
mars    = eph['mars']
jupiter = eph['jupiter barycenter']
saturn  = eph['saturn barycenter']
degree_sign= u'\N{DEGREE SIGN}'

# load the Hipparcos catalog as a 118,218 row Pandas dataframe.
with load.open(hipparcos.URL) as f:
    df = hipparcos.load_dataframe(f)

def init():
    return ts

def sunGHA(d):
    # compute sun's GHA and DEC per hour of day

    hour_of_day = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    t = ts.utc(d.year, d.month, d.day, hour_of_day, 0, 0)
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
    #for i in range(len(dec.degrees)):
    #    print i, ghas[i]

    # degs has been added for the suntab function
    return ghas,decs,degs

def sunSD(d):
    # compute semi-diameter of sun and sun's declination change per hour (in minutes)
    t12 = ts.utc(d.year, d.month, d.day, 12, 0, 0)
    position = earth.at(t12).observe(sun)
    distance = position.apparent().radec(epoch='date')[2]
    dist_km = distance.km
    sds = math.degrees(math.atan(695500.0 / dist_km))	# radius of sun = 695500 km
    sdsm = u"%0.1f" %(sds * 60)	# convert to minutes of arc

    t0 = ts.utc(d.year, d.month, d.day, 0, 0, 0)
    position0 = earth.at(t0).observe(sun)
    dec0 = position0.apparent().radec(epoch='date')[1]
    t1= ts.utc(d.year, d.month, d.day, 1, 0, 0)
    position1 = earth.at(t1).observe(sun)
    dec1 = position1.apparent().radec(epoch='date')[1]
    ds = dec1.degrees - dec0.degrees
    dsm = u"%0.1f" %(ds * 60)	# convert to minutes of arc
    return sdsm, dsm

def moonSD(d):
    # compute semi-diameter of moon (in minutes)
    t12 = ts.utc(d.year, d.month, d.day, 12, 0, 0)
    position = earth.at(t12).observe(moon)
    distance = position.apparent().radec(epoch='date')[2]
    dist_km = distance.km
    sdm = math.degrees(math.atan(1738.1/dist_km))	# equatorial radius of moon = 1738.1 km
    sdmm = u"%0.1f" %(sdm * 60)	# convert to minutes of arc
    return sdmm

def moonGHA(d):
    # compute moon's GHA, DEC and HP per hour of day
    hour_of_day = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    t = ts.utc(d.year, d.month, d.day, hour_of_day, 0, 0)
    position = earth.at(t).observe(moon)
    ra = position.apparent().radec(epoch='date')[0]
    dec = position.apparent().radec(epoch='date')[1]
    distance = position.apparent().radec(epoch='date')[2]

    # also compute moon's GHA at End of Day (23:59:30) and Start of Day (24 hours earlier)
    tSoD = ts.utc(d.year, d.month, d.day-1, 23, 59, 30)
    posSoD = earth.at(tSoD).observe(moon)
    raSoD = posSoD.apparent().radec(epoch='date')[0]
    ghaSoD = gha2deg(tSoD.gast, raSoD.hours)   # GHA as float
    tEoD = ts.utc(d.year, d.month, d.day, 23, 59, 30)
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
        HP = math.degrees(math.atan(6378.0/dist_km))	# radius of earth = 6378.0 km
        HPm[i] = u"%0.1f'" %(HP * 60)	# convert to minutes of arc
    # degm has been added for the sunmoontab function
    # GHAupper is an array of GHA per hour as float
    # ghaSoD, ghaEoD = GHA at Start/End of Day assuming time is rounded to hh:mm
    return gham, decm, degm, HPm, GHAupper, GHAlower, ghaSoD, ghaEoD

def GHAcolong(gha):
    # return the colongitude, e.g. 270° returns 90°
    coGHA = gha + 180
    while coGHA > 360:
        coGHA = coGHA - 360
    return coGHA

def moonVD(d0,d):
    hour_of_day = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    # first value required is from 23:30 on the previous day...
    t0 = ts.utc(d0.year, d0.month, d0.day, 23, 30, 0)
    pos0 = earth.at(t0).observe(moon)
    ra0 = pos0.apparent().radec(epoch='date')[0]
    dec0 = pos0.apparent().radec(epoch='date')[1]
    V0 = gha2deg(t0.gast, ra0.hours)
    D0 = dec0.degrees

    # ...then 24 values at hourly intervals from 23:30 onwards
    t = ts.utc(d.year, d.month, d.day, hour_of_day, 30, 0)
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
        moonVm[i] = u"%0.1f'" %(Vdm)
        D1 = dec.degrees[i]
        moonDm[i] = u"%0.1f'" %((D1-D0) * 60)	# convert to minutes of arc
        V0 = V1		# store current value as next previous value
        D0 = D1		# store current value as next previous value
    return moonVm, moonDm

def norm(delta):
    # normalize the angle between 0° and 360°
    # (usually delta is roughly 15 degrees)
    while delta < 0:
        delta += 360.0
    while delta >= 360.0:
        delta -= 360.0
    return delta

def vdm_Venus(d):
    # compute v (GHA correction), d (Declination correction), m (magnitude of planet)
    t0 = ts.utc(d.year, d.month, d.day, 0, 0, 0)
    position0 = earth.at(t0).observe(venus)
    ra0 = position0.apparent().radec(epoch='date')[0]	# RA
    dec0 = position0.apparent().radec(epoch='date')[1]	# declination

    t1 = ts.utc(d.year, d.month, d.day, 1, 0, 0)
    position1 = earth.at(t1).observe(venus)
    ra1 = position1.apparent().radec(epoch='date')[0]	# RA
    dec1 = position1.apparent().radec(epoch='date')[1]	# declination

    sha0 = (t0.gast - ra0.hours) * 15
    sha1 = (t1.gast - ra1.hours) * 15
    sha  = norm(sha1 - sha0) - 15
    RAcorrm = u"%0.1f" %(sha * 60)	# convert to minutes of arc
    Dcorr = dec1.degrees - dec0.degrees
    Dcorrm = u"%0.1f" %(Dcorr * 60)	# convert to minutes of arc
    return RAcorrm, Dcorrm

def vdm_Mars(d):
    # compute v (GHA correction), d (Declination correction), m (magnitude of planet)
    t0 = ts.utc(d.year, d.month, d.day, 0, 0, 0)
    position0 = earth.at(t0).observe(mars)
    ra0 = position0.apparent().radec(epoch='date')[0]	# RA
    dec0 = position0.apparent().radec(epoch='date')[1]	# declination

    t1 = ts.utc(d.year, d.month, d.day, 1, 0, 0)
    position1 = earth.at(t1).observe(mars)
    ra1 = position1.apparent().radec(epoch='date')[0]	# RA
    dec1 = position1.apparent().radec(epoch='date')[1]	# declination

    sha0 = (t0.gast - ra0.hours) * 15
    sha1 = (t1.gast - ra1.hours) * 15
    sha  = norm(sha1 - sha0) - 15
    RAcorrm = u"%0.1f" %(sha * 60)	# convert to minutes of arc
    Dcorr = dec1.degrees - dec0.degrees
    Dcorrm = u"%0.1f" %(Dcorr * 60)	# convert to minutes of arc
    return RAcorrm, Dcorrm

def vdm_Jupiter(d):
    # compute v (GHA correction), d (Declination correction), m (magnitude of planet)
    t0 = ts.utc(d.year, d.month, d.day, 0, 0, 0)
    position0 = earth.at(t0).observe(jupiter)
    ra0 = position0.apparent().radec(epoch='date')[0]	# RA
    dec0 = position0.apparent().radec(epoch='date')[1]	# declination

    t1 = ts.utc(d.year, d.month, d.day, 1, 0, 0)
    position1 = earth.at(t1).observe(jupiter)
    ra1 = position1.apparent().radec(epoch='date')[0]	# RA
    dec1 = position1.apparent().radec(epoch='date')[1]	# declination

    sha0 = (t0.gast - ra0.hours) * 15
    sha1 = (t1.gast - ra1.hours) * 15
    sha  = norm(sha1 - sha0) - 15
    RAcorrm = u"%0.1f" %(sha * 60)	# convert to minutes of arc
    Dcorr = dec1.degrees - dec0.degrees
    Dcorrm = u"%0.1f" %(Dcorr * 60)	# convert to minutes of arc
    return RAcorrm, Dcorrm

def vdm_Saturn(d):
    # compute v (GHA correction), d (Declination correction), m (magnitude of planet)
    t0 = ts.utc(d.year, d.month, d.day, 0, 0, 0)
    position0 = earth.at(t0).observe(saturn)
    ra0 = position0.apparent().radec(epoch='date')[0]	# RA
    dec0 = position0.apparent().radec(epoch='date')[1]	# declination

    t1 = ts.utc(d.year, d.month, d.day, 1, 0, 0)
    position1 = earth.at(t1).observe(saturn)
    ra1 = position1.apparent().radec(epoch='date')[0]	# RA
    dec1 = position1.apparent().radec(epoch='date')[1]	# declination

    sha0 = (t0.gast - ra0.hours) * 15
    sha1 = (t1.gast - ra1.hours) * 15
    sha  = norm(sha1 - sha0) - 15
    RAcorrm = u"%0.1f" %(sha * 60)	# convert to minutes of arc
    Dcorr = dec1.degrees - dec0.degrees
    Dcorrm = u"%0.1f" %(Dcorr * 60)	# convert to minutes of arc
    return RAcorrm, Dcorrm

def ariesGHA(d):
    hour_of_day = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    t = ts.utc(d.year, d.month, d.day, hour_of_day, 0, 0)

    ghas = ['' for x in range(24)]
    for i in range(24):
        ghas[i] = fmtgha(t[i].gast, 0)
    return ghas

def ariestransit(d):
    # returns transit time of aries for the *PREVIOUS* date

    t = ts.utc(d.year, d.month, d.day, 0, 0, 0)
    trans = 24 - (t.gast / 1.00273790935)
    hr = int(trans)
    # round >=30 seconds to next minute
    #min = tup[-2] + int(round(tup[-1]/60+0.00001))
    min = round((trans - hr) * 60)
    if min == 60:
        min = 0
        hr += 1
        if hr == 24:
            hr = 0
    time = u'%02d:%02d' %(hr,min)
    return time
    
def planetstransit(d):
    # returns SHA and Meridian Passage for the navigational planets
    d1 = d + datetime.timedelta(days=1)
    
# Venus
    t0 = ts.utc(d.year, d.month, d.day, 0, 0, 0)
    position0 = earth.at(t0).observe(venus)
    ra0 = position0.apparent().radec(epoch='date')[0]	# RA
    vau = position0.apparent().radec(epoch='date')[2]	# distance
    vsha = fmtgha(0, ra0.hours)
    hpvenus = u"%0.1f" %((math.tan(6371/(vau.au*149597870.7)))*60*180/math.pi)

    # calculate planet transit
    tfr = t0
    tto = ts.utc(d1.year, d1.month, d1.day, 0, 0, 0)
    position = earth.at(tfr).observe(venus)
    ra = position.apparent().radec(epoch='date')[0]
    #print 'Venus transit: ', tfr.gast, ra.hours
    transit_time, y = almanac.find_discrete(tfr, tto, planet_transit(venus))
    #if len(y) != 1:
    #    print 'returned %s values' %len(y)
    vtrans = rise_set(transit_time,y,u'0%s E transit' %degree_sign)[0]

# Mars
    position0 = earth.at(t0).observe(mars)
    ra0 = position0.apparent().radec(epoch='date')[0]	# RA
    mau = position0.apparent().radec(epoch='date')[2]	# distance
    marssha = fmtgha(0, ra0.hours)
    hpmars = u"%0.1f" %((math.tan(6371/(mau.au*149597870.7)))*60*180/math.pi)

    # calculate planet transit
    tfr = t0
    tto = ts.utc(d1.year, d1.month, d1.day, 0, 0, 0)
    position = earth.at(tfr).observe(mars)
    ra = position.apparent().radec(epoch='date')[0]
    transit_time, y = almanac.find_discrete(tfr, tto, planet_transit(mars))
    marstrans = rise_set(transit_time,y,u'0%s E transit' %degree_sign)[0]

# Jupiter
    position0 = earth.at(t0).observe(jupiter)
    ra0 = position0.apparent().radec(epoch='date')[0]	# RA
    jsha = fmtgha(0, ra0.hours)

    # calculate planet transit
    tfr = t0
    tto = ts.utc(d1.year, d1.month, d1.day, 0, 0, 0)
    position = earth.at(tfr).observe(jupiter)
    ra = position.apparent().radec(epoch='date')[0]
    transit_time, y = almanac.find_discrete(tfr, tto, planet_transit(jupiter))
    jtrans = rise_set(transit_time,y,u'0%s E transit' %degree_sign)[0]
    
# Saturn
    position0 = earth.at(t0).observe(saturn)
    ra0 = position0.apparent().radec(epoch='date')[0]	# RA
    satsha = fmtgha(0, ra0.hours)

    # calculate planet transit
    tfr = t0
    tto = ts.utc(d1.year, d1.month, d1.day, 0, 0, 0)
    position = earth.at(tfr).observe(saturn)
    ra = position.apparent().radec(epoch='date')[0]
    transit_time, y = almanac.find_discrete(tfr, tto, planet_transit(saturn))
    sattrans = rise_set(transit_time,y,u'0%s E transit' %degree_sign)[0]
    
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

def venusGHA(d):
    hour_of_day = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    t = ts.utc(d.year, d.month, d.day, hour_of_day, 0, 0)
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
    #    print i, ghas[i]
    return ghas, decs, degs

def marsGHA(d):
    hour_of_day = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    t = ts.utc(d.year, d.month, d.day, hour_of_day, 0, 0)
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
    #    print i, ghas[i]
    return ghas, decs, degs

def jupiterGHA(d):
    hour_of_day = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    t = ts.utc(d.year, d.month, d.day, hour_of_day, 0, 0)
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
    #    print i, ghas[i]
    return ghas, decs, degs

def saturnGHA(d):
    hour_of_day = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    t = ts.utc(d.year, d.month, d.day, hour_of_day, 0, 0)
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

def stellar_info(d):
    # returns a list of lists with name, SHA and Dec all navigational stars for epoch of date.

    t12 = ts.utc(d.year, d.month, d.day, 12, 0, 0)  #calculate at noon
    out = []

    for line in db.strip().split('\n'):
        x1 = line.index(',')
        name = line[0:x1]
        HIPnum = line[x1+1:]

        star = Star.from_dataframe(df.loc[int(HIPnum)])
        astrometric = earth.at(t12).observe(star).apparent()
        ra, dec, distance = astrometric.radec(epoch='date')

        sha  = fmtgha(0, ra.hours)
        decl = fmtdeg(dec.degrees)

        out.append([name,sha,decl])
    return out
 
def fmtgha(gst, ra):
    # formats angle (hours) to that used in the nautical almanac. (ddd°mm.m)
    theminus = ""
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
    	theminus = u'-'
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
        gm = u"%s%02i°%04.1f" %(theminus,di,mf)
    else:
        if fixedwidth == 3:
            gm = u"%s%03i°%04.1f" %(theminus,di,mf)
        else:
            gm = u"%s%s°%04.1f" %(theminus,di,mf)
    return gm


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


def rise_set(t, y, lats):
    # get sun/moon rise/set values (if any) rounded to nearest minute
    rise = '--:--'
    sett = '--:--'
    ris2 = '--:--'
    set2 = '--:--'
    if len(y) == 2:		# this happens most often
        t0 = ts.utc((t[0].utc_datetime() + datetime.timedelta(seconds=30)).replace(second=0, microsecond=0))
        t1 = ts.utc((t[1].utc_datetime() + datetime.timedelta(seconds=30)).replace(second=0, microsecond=0))
        if y[0] and not(y[1]):
            rise = t0.utc_iso()[11:16]
            sett = t1.utc_iso()[11:16]
        else:
            if not(y[0]) and y[1]:
                sett = t0.utc_iso()[11:16]
                rise = t1.utc_iso()[11:16]
            else:
                # this should never get here!
                rise_set_error(y,lats,ts.utc(t[0].utc_datetime()))
    else:
        if len(y) == 1:		# this happens ocassionally
            t0 = ts.utc((t[0].utc_datetime() + datetime.timedelta(seconds=30)).replace(second=0, microsecond=0))
            if y[0]:
                rise = t0.utc_iso()[11:16]
            else:
                sett = t0.utc_iso()[11:16]
        else:
            if len(y) == 3:		# this happens rarely (in high latitudes in summer)
                t0 = ts.utc((t[0].utc_datetime() + datetime.timedelta(seconds=30)).replace(second=0, microsecond=0))
                t1 = ts.utc((t[1].utc_datetime() + datetime.timedelta(seconds=30)).replace(second=0, microsecond=0))
                t2 = ts.utc((t[2].utc_datetime() + datetime.timedelta(seconds=30)).replace(second=0, microsecond=0))
                if y[0] and not(y[1]) and y[2]:
                    rise = t0.utc_iso()[11:16]
                    sett = t1.utc_iso()[11:16]
                    ris2 = t2.utc_iso()[11:16]
                else:
                    if not(y[0]) and y[1] and not(y[2]):
                        sett = t0.utc_iso()[11:16]
                        rise = t1.utc_iso()[11:16]
                        set2 = t2.utc_iso()[11:16]
                    else:
                        # this should never get here!
                        rise_set_error(y,lats,ts.utc(t[0].utc_datetime()))
            else:
                if len(y) > 3:
                    # this should never get here!
                    rise_set_error(y,lats,ts.utc(t[0].utc_datetime()))

    return rise, sett, ris2, set2

def rise_set_error(y, lats, t0):
    if config.logfileopen:
        # unexpected rise/set values - write to log file
        config.writeLOG(u"\n\nrise_set %s values at %s: %s %s " %(len(y),lats,y[0],y[1]))
        if len(y) > 2:
            config.writeLOG(u"%s" %y[2])
        if len(y) > 3:
            config.writeLOG(u"%s" %y[3])
        config.writeLOG(u"\n%s" %t0.utc_iso())
    else:
        # unexpected rise/set values - print to console
        print("\nrise_set %s values at %s: %s %s " %(len(y),lats, y[0], y[1],))
        if len(y) > 2:
            print("%s" %y[2])
        if len(y) > 3:
            print("%s" %y[3])
        print("%s" %t0.utc_iso())
    return

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


def find_new_moon(d):
    # find previous & next new moon
    global PreviousNewMoon
    global NextNewMoon
    PreviousNewMoon  = None
    NextNewMoon      = None
    # note: the python datetimes above are timezone 'aware' (not 'naive')

    # search from 30 days earlier than noon... till noon on this day
    d0 = d - datetime.timedelta(days=30)
    t0 = ts.utc(d0.year, d0.month, d0.day, 12, 0, 0)
    t1 = ts.utc(d.year, d.month, d.day, 12, 0, 0)
    t, y = almanac.find_discrete(t0, t1, almanac.moon_phases(eph))
    for i in range(len(y)):
        if y[i] == 0:       # 0=New Moon, 1=First Quarter, 2=Full Moon, 3=Last Quarter
            PreviousNewMoon = t[i].utc_datetime()

    if PreviousNewMoon != None:
        # synodic month = about 29.53 days
        t2 = ts.utc(PreviousNewMoon + datetime.timedelta(days=28))
        t3 = ts.utc(PreviousNewMoon + datetime.timedelta(days=30))
        t, y = almanac.find_discrete(t2, t3, almanac.moon_phases(eph))
        for i in range(len(y)):
            if y[i] == 0:       # 0 = New Moon
                NextNewMoon = t[i].utc_datetime()
    return

def getGHA(d, hh, mm, ss):
    # calculate the Moon's GHA on date d at hh:mm:ss
    t1 = ts.utc(d.year, d.month, d.day, hh, mm, ss)
    pos = earth.at(t1).observe(moon)
    ra = pos.apparent().radec(epoch='date')[0]
    gha = gha2deg(t1.gast, ra.hours)
    return gha      # GHA as float (degrees)

def find_transit(d, ghaList, modeLT):
    # ghaList contains the 'hourly' GHA values on day 'd' for the times:
    #  23:59:30 on d-1; 01:00; 02:00; 03:00 ... 21:00; 22:00; 23:00; 23:59:30
    # Events between 23:59:30 on d-1 and 23:59:30 will show as 00:00 to 23:59

    # This effectively filters out events after 30 seconds before midnight
    #  as these belong to the next day once rounded up to 00:00.
    # Furthermore those from the last 30 seconds of the previous day
    #  will be automatically included.
    # In the latter case one cannot compare which GHA is closer to zero
    #  ... the GHA at 00:00:30 must be inspected.

    # this method may also be used to determine the Lower transit by replacing
    #  GHA with the colongitude GHA (and an adapted ghaList). Thus...
    # modeLT = False means find Upper Transit; = True means find Lower Transit
    
    # This OPTIMIZED version does not calculate every minute from 0 to 59 until
    # it detects a transit event. The search begins from 'min_start'.

    hr = -1             # an invalid hour value
    transit_time = '--:--'  # assume 'no event'
    prev_gha = 0
    prev_time = '--:--'
    mid_gha = 0
    mid_time = '--:--:--'
    gha = 0
    gha_time = '--:--'
    gha = ghaList[0]    # GHA at 23:59:30 on d-1
    gha_top = 360       # min_start defaults to 0

    for i in range(24): # 0 to 23
        if(ghaList[i+1] < gha):
            hr = i      # event is between hr:00 and {hr+1}:00
            gha_top = ghaList[i]
            break
        gha = ghaList[i+1]  # GHA at {hr+1}:00
    min_start = int((360-gha_top)/0.245)-1
    if(min_start < 0):
        min_start = 0

    if hr >= 0:         # if event found... locate it more precisely
        prev_gha = ghaList[i]    # GHA before the event (typically on the hour)
        prev_time = u"%02d:%02d" %(hr,0)
        for min in range(min_start,60):       # 0 to 59 max
            gha = getGHA(d, hr, min+1, 0)   # GHA on the minute after the event
            gha_time = u"%02d:%02d" %(hr,min+1)
            if(modeLT):
                gha = GHAcolong(gha)
            if(gha < prev_gha):
                break       # break when event detected ('min' is after event)
            prev_gha = gha   # GHA on the minute before the event
            prev_time = u"%02d:%02d" %(hr,min+1)

        mid_time = u"-"      # no value
        diff = prev_gha - 360 + gha      # if negative, round time up

        if(hr == 23 and min == 59):
            pass            # events between 23:59 and 23:59:30 never round up to 00:00
        elif(hr == 0 and min == 0):
            mid_gha = getGHA(d, hr, min, 30)
            mid_time = u"%02d:%02d:%02d" %(hr,min,30)
            if(modeLT):
                mid_gha = GHAcolong(mid_gha)
            if(mid_gha > 180):
                min += 1        # midway is before the event (round up)
                if(min == 60):
                    min = 0
                    hr += 1
        elif(abs(diff) < 0.002):
            # midpoint too close to zero: to round up or down it's better
            #    to check the gha 30 sec earlier (midway between minutes)
            # (The GHA changes by 0.002 in about 0.5 seconds time)
            mid_gha = getGHA(d, hr, min, 30)
            mid_time = u"%02d:%02d:%02d" %(hr,min,30)
            if(modeLT):
                mid_gha = GHAcolong(mid_gha)
            if(mid_gha > 180):
                min += 1        # midway is before the event (round up)
                if(min == 60):
                    min = 0
                    hr += 1
        elif(diff < 0):
            # just compare which gha is closer to zero GHA and round accordingly
            min += 1            # closer to following GHA (round up)
            if(min == 60):
                min = 0
                hr += 1

        transit_time = u"%02d:%02d" %(hr,min)
    #    if(modeLT):
    #        prev_gha = GHAcolong(prev_gha)
    #        gha = GHAcolong(gha)
    #        mid_gha = GHAcolong(mid_gha)
    #return transit_time, prev_gha, prev_time, gha, gha_time, mid_gha, mid_time

    return transit_time

def equation_of_time(d, d1, UpperList, LowerList):
    # returns equation of time, the sun's transit time, 
    # the moon's transit-, antitransit-time, age and percent illumination.
    # (Equation of Time = Mean solar time - Apparent solar time)

    t00 = ts.utc(d.year, d.month, d.day, 0, 0, 0)
    position = earth.at(t00).observe(sun)
    ra = position.apparent().radec(epoch='date')[0]
    gha00 = gha2deg(t00.gast, ra.hours)
    eqt00 = gha2eqt(gha00)

    # percent illumination is calculated at noon
    t12 = ts.utc(d.year, d.month, d.day, 12, 0, 0)
    position = earth.at(t12).observe(sun)
    ra = position.apparent().radec(epoch='date')[0]
    gha12 = gha2deg(t12.gast, ra.hours)
    eqt12 = gha2eqt(gha12)
    mpa12 = gha2mpa(gha12)

    phase_angle = almanac.phase_angle(eph, 'moon', t12)
    pctrad = 50 * (1.0 + math.cos(phase_angle.radians))
    pct = u"%.0f" %(pctrad)

    # !! transit times are rounded to the nearest minute,
    # !! so the search needs to start and end 30 sec earlier
    # !! e.g. after 23h 59m 30s rounds up to 00:00 next day

    # calculate moon upper transit

    mp_upper = find_transit(d, UpperList, False)

    # calculate moon lower transit

    mp_lower = find_transit(d, LowerList, True)

    # calculate age of moon

    pnm = PreviousNewMoon
    nnm = NextNewMoon
    #dt0 = datetime.date(pnm.year, pnm.month, pnm.day)
    #dt1 = datetime.date(nnm.year, nnm.month, nnm.day)
    dt  = datetime.datetime.combine(d1, datetime.time(0, 0))
    age1td = dt-pnm.replace(tzinfo=None)
    age2td = dt-nnm.replace(tzinfo=None)
    age1 = age1td.days
    age2 = age2td.days
    age = age1
    if age2 >= 0:
        age = age2

    return eqt00,eqt12,mpa12,mp_upper,mp_lower,age,pct

def gha2mpa(gha):
    # format an hour angle as 'Mer. Pass' (hh:mm)
    hhmm = "--:--"
    if gha > 270:
        gha = 360 - gha
    
    mpa = 12 + (gha * 4.0)/60.0
    hr  = int(mpa)
    min = int(round((mpa - hr) * 60.0))
    if min == 60:
        min = 0		# this cannot happen
        hr += 1
    hhmm = u'%02d:%02d' %(hr,min)
    return hhmm

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
    min = int(eqt)
    sec = int(round((eqt - min) * 60.0))
    if sec == 60:
        sec = 0
        min += 1
    if min < 59:
        mmss = u'%02d:%02d' %(min,sec)
    else:
        mmss = u'??:??'		# indicate error
    return mmss
