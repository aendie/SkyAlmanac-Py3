#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   Copyright (C) 2019  Andrew Bauer
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

# This contains a few functions that calculate values for the nautical almanac

import ephem        # for sunrise/sunset, moonrise/moonset, planet magnitudes
import datetime
import config
import sys

ephem_venus   = ephem.Venus()
ephem_mars    = ephem.Mars()
ephem_jupiter = ephem.Jupiter()
ephem_saturn  = ephem.Saturn()
degree_sign= u'\N{DEGREE SIGN}'

#----------------------
#   internal methods
#----------------------

def hhmm(date): 
    # turn an ephem.date (float) into a time string formatted hh:mm
    tup = date.tuple()
    hr = tup[-3]
    # round >=30 seconds to next minute
    min = tup[-2] + int(round((tup[-1]/60)+0.00001))
#    nextday = False
    if min == 60:
        min = 0
        hr += 1
        if hr == 24:
            hr = 0
#            nextday = True	# time rounded up into next day
    time = u"%02d:%02d" %(hr,min)
#    return time, nextday
    # NOTE: this function could easily return the information that rounding
    #       flipped into the next day, however this is not required here.
    return time

def flag_msg(msg):
    if config.logfileopen:
        # if open - write to log file
        config.writeLOG(msg + '\n')
    else:
        # otherwise - print to console
        print(msg)
    return

#------------------------------------------------
#   Venus, Mars, Jupiter & Saturn calculations
#------------------------------------------------

def magnitudes(date):       # used in planetstab(m)
    # returns  magitude for the navigational planets.
    # (Skyfield 1.16 does not provide this)
    
    obs = ephem.Observer()
    
    #Venus
    obs.date = date
    ephem_venus.compute(date)
    mag_venus = u"%0.1f" %(ephem_venus.mag)
    
    #Mars
    obs.date = date
    ephem_mars.compute(date)
    mag_mars = u"%0.1f" %(ephem_mars.mag)
    
    #Jupiter
    obs.date = date
    ephem_jupiter.compute(date)
    mag_jupiter = u"%0.1f" %(ephem_jupiter.mag)
    
    #Saturn
    obs.date = date
    ephem_saturn.compute(date)
    mag_saturn = u"%0.1f" %(ephem_saturn.mag)
    
    return mag_venus,mag_mars,mag_jupiter,mag_saturn

#--------------------
#   TWILIGHT table
#--------------------

def twilight(date, lat, hemisph):   # used in twilighttab (section 1)
    # Returns for given date and latitude(in full degrees):
    # naut. and civil twilight (before sunrise), sunrise, sunset, civil and nautical twilight (after sunset).
    # NOTE: 'twilight' is only called for every third day in the Full Almanac...
    #       ...therefore daily tracking of the sun state is not possible.

    out = [0,0,0,0,0,0]
    obs = ephem.Observer()
    latitude = ephem.degrees('%s:00:00.0' %lat)
    obs.lat = latitude
    # first convert 'date' (a Python datetime.date) to a PyEphem date...
    d = ephem.date(date) - 30 * ephem.second    # search from 30 seconds before midnight
    obs.date = d
    obs.pressure = 0
    s = ephem.Sun(obs)
    s.compute(d)
    r = s.radius

    obs.horizon = ephem.degrees('-12')+r	# Nautical twilight ...
    try:
        out[0] = hhmm(obs.next_rising(s))	# begin
    except:
        out[0] = '--:--'
    obs.date = d
    try:
        out[5] = hhmm(obs.next_setting(s))	# end
    except:
        out[5] = '--:--'
    if out[0] == '--:--' and out[5] == '--:--':	# if neither begin nor end...
        yn = midnightsun(date, hemisph)
        out[0] = yn
        out[5] = yn
#-----------------------------------------------------------
    obs.horizon = ephem.degrees('-6')+r		# Civil twilight...
    obs.date = d
    try:
        out[1] = hhmm(obs.next_rising(s))	# begin
    except:
        out[1] = '--:--'
    obs.date = d
    try:
        out[4] = hhmm(obs.next_setting(s))	# end
    except:
        out[4] = '--:--'
    if out[1] == '--:--' and out[4] == '--:--':	# if neither begin nor end...
        yn = midnightsun(date, hemisph)
        out[1] = yn
        out[4] = yn
#-----------------------------------------------------------
    obs.horizon = '-0:34'
    obs.date = d
    try:
        out[2] = hhmm(obs.next_rising(s))	# sunrise
    except:
        out[2] = '--:--'
    obs.date = d
    try:
        out[3] = hhmm(obs.next_setting(s))	# sunset
    except:
        out[3] = '--:--'
    if out[2] == '--:--' and out[3] == '--:--':	# if neither sunrise nor sunset...
        yn = midnightsun(date, hemisph)
        out[2] = yn
        out[3] = yn

    return out

##NEW##
def midnightsun(dt, hemisph):
    # simple way to fudge whether the sun is up or down when there's no
    # sunrise or sunset on date 'dt' depending on the hemisphere only.

    sunup = False
    n = dt.month
    if n > 3 and n < 10:    # if April to September inclusive
        sunup = True
    if hemisph == 'S':
        sunup = not(sunup)
    if sunup == True:
        out = r'''\begin{tikzpicture}\draw (0,0) rectangle (12pt,4pt);\end{tikzpicture}'''
    else:
        out = r'''\rule{12Pt}{4Pt}'''
    return out

#-------------------------
#   MOONRISE/-SET table
#-------------------------

##NEW##
# create a list of 'moon above/below horizon' states per Latitude...
#    None = unknown; True = above horizon (visible); False = below horizon (not visible)
moonvisible = [None] * 31       # moonvisible[0] up to moonvisible[30]

def moonrise_set(date, lat):    # used in twilighttab (section 2)
    # returns moonrise and moonset for the given date and latitude plus next 2 days:
    #    rise day 1, rise day 2, rise day 3, set day 1, set day 2, set day 3
    # Additionally it also tracks the current state of the moon (above or below horizon)

    i = config.lat.index(lat)
    out  = ['--:--','--:--','--:--','--:--','--:--','--:--']	# first event
    out2 = ['--:--','--:--','--:--','--:--','--:--','--:--']	# second event on same day (rare)

    obs = ephem.Observer()
    latitude = ephem.degrees('%s:00:00.0' %lat)
    obs.lat = latitude
    obs.pressure = 0
    obs.horizon = '-0:34'
    # first convert 'date' (a Python datetime.date) to a PyEphem date...
    d = ephem.date(date) - 30 * ephem.second    # search from 30 seconds before midnight
    obs.date = d
    m = ephem.Moon(obs)
    m.compute(d)
#-----------------------------------------------------------
    # Moonrise/Moonset on 1st. day ...
    try:
        firstrising = obs.next_rising(m)
        if firstrising-obs.date >= 1:
            raise ValueError('event next day')
        out[0] = hhmm(firstrising)		# note: overflow to 00:00 next day is correct here
        lastevent = firstrising
        moonvisible[i] = True
    except Exception:                   # includes NeverUpError and AlwaysUpError
        out[0] = '--:--'
        lastevent = 0

    if out[0] != '--:--':
        try:
            nextr = obs.next_rising(m, start=firstrising)
            if nextr-obs.date < 1:
                out2[0] = hhmm(nextr)	# note: overflow to 00:00 next day is correct here
                lastevent = nextr
        except UnboundLocalError:
            pass
        except ephem.NeverUpError:
            pass
        except ephem.AlwaysUpError:
            pass
        except Exception:
            flag_msg("Oops! %s occured, line: %s" %(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
            #sys.exc_clear()		# only in Python 2

    obs.date = d
    try:
        firstsetting = obs.next_setting(m)
        if firstsetting-obs.date >= 1:
            raise ValueError('event next day')
        out[3] = hhmm(firstsetting)		# note: overflow to 00:00 next day is correct here
        if firstsetting > lastevent:
            lastevent = firstsetting
            moonvisible[i] = False
    except Exception:                   # includes NeverUpError and AlwaysUpError
        out[3] = '--:--'

    if out[3] != '--:--':
        try:
            nexts = obs.next_setting(m, start=firstsetting)
            if nexts-obs.date < 1:
                out2[3] = hhmm(nexts)	# note: overflow to 00:00 next day is correct here
            if nexts > lastevent:
                moonvisible[i] = False
        except UnboundLocalError:
            pass
        except ephem.NeverUpError:
            pass
        except ephem.AlwaysUpError:
            pass
        except Exception:
            flag_msg("Oops! %s occured, line: %s" %(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
            #sys.exc_clear()		# only in Python 2

    if out[0] == '--:--' and out[3] == '--:--':	# if neither moonrise nor moonset...
        if moonvisible[i] == None:
            getmoonstate(d, lat)			# ...get moon state if unknown
        out[0] = moonstate(i)
        out[3] = moonstate(i)
#-----------------------------------------------------------
    # Moonrise/Moonset on 2nd. day ...
    d = ephem.date(date + datetime.timedelta(days=1)) - 30 * ephem.second
    obs.date = d
    m.compute(d)
    try:
        firstrising = obs.next_rising(m)
        if firstrising-obs.date >= 1:
            raise ValueError('event next day')
        out[1] = hhmm(firstrising)		# note: overflow to 00:00 next day is correct here
        lastevent = firstrising
        moonvisible[i] = True
    except Exception:                   # includes NeverUpError and AlwaysUpError
        out[1] = '--:--'
        lastevent = 0

    if out[1] != '--:--':
        try:
            nextr = obs.next_rising(m, start=firstrising)
            if nextr-obs.date < 1:
                out2[1] = hhmm(nextr)	# note: overflow to 00:00 next day is correct here
                lastevent = nextr
        except UnboundLocalError:
            pass
        except ephem.NeverUpError:
            pass
        except ephem.AlwaysUpError:
            pass
        except Exception:
            flag_msg("Oops! %s occured, line: %s" %(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
            #sys.exc_clear()		# only in Python 2

    obs.date = d
    try:
        firstsetting = obs.next_setting(m)
        if firstsetting-obs.date >= 1:
            raise ValueError('event next day')
        out[4] = hhmm(firstsetting)		# note: overflow to 00:00 next day is correct here
        if firstsetting > lastevent:
            lastevent = firstsetting
            moonvisible[i] = False
    except Exception:                   # includes NeverUpError and AlwaysUpError
        out[4] = '--:--'

    if out[4] != '--:--':
        try:
            nexts = obs.next_setting(m, start=firstsetting)
            if nexts-obs.date < 1:
                out2[4] = hhmm(nexts)	# note: overflow to 00:00 next day is correct here
            if nexts > lastevent:
                moonvisible[i] = False
        except UnboundLocalError:
            pass
        except ephem.NeverUpError:
            pass
        except ephem.AlwaysUpError:
            pass
        except Exception:
            flag_msg("Oops! %s occured, line: %s" %(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
            #sys.exc_clear()		# only in Python 2

    if out[1] == '--:--' and out[4] == '--:--':	# if neither moonrise nor moonset...
        if moonvisible[i] == None:
            getmoonstate(d, lat)			# ...get moon state if unknown
        out[1] = moonstate(i)
        out[4] = moonstate(i)
#-----------------------------------------------------------
    # Moonrise/Moonset on 3rd. day ...
    d = ephem.date(date + datetime.timedelta(days=2)) - 30 * ephem.second
    obs.date = d
    m.compute(d)
    try:
        firstrising = obs.next_rising(m)
        if firstrising-obs.date >= 1:
            raise ValueError('event next day')
        out[2] = hhmm(firstrising)		# note: overflow to 00:00 next day is correct here
        lastevent = firstrising
        moonvisible[i] = True
    except Exception:                   # includes NeverUpError and AlwaysUpError
        out[2] = '--:--'
        lastevent = 0

    if out[2] != '--:--':
        try:
            nextr = obs.next_rising(m, start=firstrising)
            if nextr-obs.date < 1:
                out2[2] = hhmm(nextr)	# note: overflow to 00:00 next day is correct here
                lastevent = nextr
        except UnboundLocalError:
            pass
        except ephem.NeverUpError:
            pass
        except ephem.AlwaysUpError:
            pass
        except Exception:
            flag_msg("Oops! %s occured, line: %s" %(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
            #sys.exc_clear()		# only in Python 2

    obs.date = d
    try:
        firstsetting = obs.next_setting(m)
        if firstsetting-obs.date >= 1:
            raise ValueError('event next day')
        out[5] = hhmm(firstsetting)		# note: overflow to 00:00 next day is correct here
        if firstsetting > lastevent:
            lastevent = firstsetting
            moonvisible[i] = False
    except Exception:                   # includes NeverUpError and AlwaysUpError
        out[5] = '--:--'

    if out[5] != '--:--':
        try:
            nexts = obs.next_setting(m, start=firstsetting)
            if nexts-obs.date < 1:
                out2[5] = hhmm(nexts)	# note: overflow to 00:00 next day is correct here
            if nexts > lastevent:
                moonvisible[i] = False
        except UnboundLocalError:
            pass
        except ephem.NeverUpError:
            pass
        except ephem.AlwaysUpError:
            pass
        except Exception:
            flag_msg("Oops! %s occured, line: %s" %(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
            #sys.exc_clear()		# only in Python 2

    if out[2] == '--:--' and out[5] == '--:--':	# if neither moonrise nor moonset...
        if moonvisible[i] == None:
            getmoonstate(d, lat)			# ...get moon state if unknown
        out[2] = moonstate(i)
        out[5] = moonstate(i)

    return out, out2

##NEW##
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

##NEW##
def getmoonstate(d, lat):
    # populate the moon state (visible or not) for the specified date & latitude
    # note: the first parameter 'd' is already an ephem date 30 seconds before midnight
    # note: getmoonstate is called when there is neither a moonrise nor a moonset on 'd'

    i = config.lat.index(lat)
    latitude = ephem.degrees('%s:00:00.0' %lat)
    obs = ephem.Observer()
    #d = ephem.date(date - 30 * ephem.second)
    obs.pressure = 0
    obs.horizon = '-0:34'
    m = ephem.Moon(obs)
    err = False
    obs.date = d
    obs.lat = latitude
    m.compute(d)
    nextrising = d + 100.0	# in case moonset but no next moonrise
    nextsetting = d + 100.0	# in case moonrise but no next moonset

    try:
        nextrising  = obs.next_rising(m)
    except ephem.NeverUpError:
        err = True
        #print "nr NeverUp"
        moonvisible[i] = False
    except ephem.AlwaysUpError:
        err = True
        #print "nr AlwaysUp"
        moonvisible[i] = True
    except Exception:
        flag_msg("Oops! moon nextR %s: %s occured, line: %s" %(i,sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
        #sys.exc_clear()		# only in Python 2

    obs.date = d
    if not(err):	# note - 'nextrising' above *should* fail
        try:
            nextsetting = obs.next_setting(m)
        except ephem.NeverUpError:
            err = True
            #print "ns NeverUp"
            moonvisible[i] = False
        except ephem.AlwaysUpError:
            err = True
            #print "ns AlwaysUp"
            moonvisible[i] = True
        except Exception:
            flag_msg("Oops! moon nextS %s: %s occured, line: %s" %(i,sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
            #sys.exc_clear()		# only in Python 2

    if not(err):	# note - "err == True" *is* expected...
        # however if we found both, which occured first?
        moonvisible[i] = False
        if nextrising > nextsetting:
            moonvisible[i] = True
        #print("%s" %i, nextrising, nextsetting, moonvisible[i])
    return
