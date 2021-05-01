#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

# This contains a few functions that calculate values for the nautical almanac

# Standard library imports
import datetime
import sys

# Third party imports
import ephem        # for sunrise/sunset, moonrise/moonset, planet magnitudes

# Local application imports
import config

ephem_venus   = ephem.Venus()
ephem_mars    = ephem.Mars()
ephem_jupiter = ephem.Jupiter()
ephem_saturn  = ephem.Saturn()
#degree_sign= u'\N{DEGREE SIGN}'

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
    time = '{:02d}:{:02d}'.format(hr,min)    # time = "%02d:%02d" %(hr,min)
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
    mag_venus = "{:0.1f}".format(ephem_venus.mag)  # mag_venus = "%0.1f" %(ephem_venus.mag)
    
    #Mars
    obs.date = date
    ephem_mars.compute(date)
    mag_mars = "{:0.1f}".format(ephem_mars.mag)    # mag_mars = "%0.1f" %(ephem_mars.mag)
    
    #Jupiter
    obs.date = date
    ephem_jupiter.compute(date)
    mag_jupiter = "{:0.1f}".format(ephem_jupiter.mag) # mag_jupiter = "%0.1f" %(ephem_jupiter.mag)
    
    #Saturn
    obs.date = date
    ephem_saturn.compute(date)
    mag_saturn = "{:0.1f}".format(ephem_saturn.mag)  # mag_saturn = "%0.1f" %(ephem_saturn.mag)
    
    return mag_venus,mag_mars,mag_jupiter,mag_saturn

#--------------------
#   TWILIGHT table
#--------------------

def twilight(date, lat, hemisph):   # used in twilighttab (section 1)
    # Returns for given date and latitude(in full degrees):
    # naut. and civil twilight (before sunrise), sunrise, sunset, civil and nautical twilight (after sunset).
    # NOTE: 'twilight' is only called for every third day in the Full Almanac...
    #       ...therefore daily tracking of the sun state is impossible.

    out = [0,0,0,0,0,0]
    obs = ephem.Observer()
    latitude = ephem.degrees('{}:00:00.0'.format(lat))
    obs.lat = latitude
    # first convert 'date' (a Python datetime.date) to an Ephem date...
    d = ephem.date(date) - 30 * ephem.second    # search from 30 seconds before midnight
    obs.date = d
    obs.pressure = 0
    s = ephem.Sun(obs)
    s.compute(d)
    r = s.radius
    abhd = False                                # above/below horizon display NOT enabled

    obs.horizon = '-0:34'   # 34' (atmospheric refraction)
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
        abhd = True                             # enable above/below horizon display
        yn = midnightsun(date, hemisph)
        out[2] = yn
        out[3] = yn
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
    if abhd and out[1] == '--:--' and out[4] == '--:--':	# if neither begin nor end...
        yn = midnightsun(date, hemisph)
        out[1] = yn
        out[4] = yn
#-----------------------------------------------------------
    obs.horizon = ephem.degrees('-12')+r	# Nautical twilight ...
    obs.date = d
    try:
        out[0] = hhmm(obs.next_rising(s))	# begin
    except:
        out[0] = '--:--'
    obs.date = d
    try:
        out[5] = hhmm(obs.next_setting(s))	# end
    except:
        out[5] = '--:--'
    if abhd and out[0] == '--:--' and out[5] == '--:--':	# if neither begin nor end...
        yn = midnightsun(date, hemisph)
        out[0] = yn
        out[5] = yn
#-----------------------------------------------------------

    return out

def midnightsun(dt, hemisph):
    # simple way to fudge whether the sun is up or down when there's no
    # sunrise or sunset on date 'dt' depending on the hemisphere only.
    # Note: this works for the chosen latitudes to be calculated.

    sunup = False
    mth = dt.month
    if mth > 3 and mth < 10:    # if April to September inclusive
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

# create a list of 'moon above/below horizon' states per Latitude...
#    None = unknown; True = above horizon (visible); False = below horizon (not visible)
#    moonvisible[0] is not linked to a latitude but a manual override
moonvisible = [None] * 32       # moonvisible[0] up to moonvisible[31]

def moonrise_set(date, lat):    # used by tables.py in twilighttab (section 2)
    # - - - TIMES ARE ROUNDED TO MINUTES - - -
    # returns moonrise and moonset for the given date and latitude plus next 2 days:
    #    rise day 1, rise day 2, rise day 3, set day 1, set day 2, set day 3
    # Additionally it also tracks the current state of the moon (above or below horizon)

    i = 1 + config.lat.index(lat)   # index 0 is reserved to enable an explicit setting
    out  = ['--:--','--:--','--:--','--:--','--:--','--:--']	# first event
    out2 = ['--:--','--:--','--:--','--:--','--:--','--:--']	# second event on same day (rare)

    obs = ephem.Observer()
    latitude = ephem.degrees('{}:00:00.0'.format(lat))
    obs.lat = latitude
    obs.pressure = 0
    obs.horizon = '-0:34'       # 34' (atmospheric refraction)
    # first convert 'date' (a Python datetime.date) to an Ephem date...
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
            flag_msg("Oops! {} occured, line: {}".format(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
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
            flag_msg("Oops! {} occured, line: {}".format(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
            #sys.exc_clear()		# only in Python 2

    if out[0] == '--:--' and out[3] == '--:--':	# if neither moonrise nor moonset...
        if moonvisible[i] == None:
            getmoonstate(d, lat)			# ...get moon state if unknown
        out[0] = moonstate(i)
        out[3] = moonstate(i)

    if out[0] == '--:--' and out[3] != '--:--':	# if moonset but no moonrise...
        out[0] = moonset_no_rise(d, date, i, lat)

    if out[0] != '--:--' and out[3] == '--:--':	# if moonrise but no moonset...
        out[3] = moonrise_no_set(d, date, i, lat)

#-----------------------------------------------------------
    # Moonrise/Moonset on 2nd. day ...
    d2 = date + datetime.timedelta(days=1)
    d = ephem.date(d2) - 30 * ephem.second
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
            flag_msg("Oops! {} occured, line: {}".format(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
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
            flag_msg("Oops! {} occured, line: {}".format(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
            #sys.exc_clear()		# only in Python 2

    if out[1] == '--:--' and out[4] == '--:--':	# if neither moonrise nor moonset...
        if moonvisible[i] == None:
            getmoonstate(d, lat)			# ...get moon state if unknown
        out[1] = moonstate(i)
        out[4] = moonstate(i)

    if out[1] == '--:--' and out[4] != '--:--':	# if moonset but no moonrise...
        out[1] = moonset_no_rise(d, d2, i, lat)

    if out[1] != '--:--' and out[4] == '--:--':	# if moonrise but no moonset...
        out[4] = moonrise_no_set(d, d2, i, lat)

#-----------------------------------------------------------
    # Moonrise/Moonset on 3rd. day ...
    d3 = date + datetime.timedelta(days=2)
    d = ephem.date(d3) - 30 * ephem.second
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
            flag_msg("Oops! {} occured, line: {}".format(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
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
            flag_msg("Oops! {} occured, line: {}".format(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
            #sys.exc_clear()		# only in Python 2

    if out[2] == '--:--' and out[5] == '--:--':	# if neither moonrise nor moonset...
        if moonvisible[i] == None:
            getmoonstate(d, lat)			# ...get moon state if unknown
        out[2] = moonstate(i)
        out[5] = moonstate(i)

    if out[2] == '--:--' and out[5] != '--:--':	# if moonset but no moonrise...
        out[2] = moonset_no_rise(d, d3, i, lat)

    if out[2] != '--:--' and out[5] == '--:--':	# if moonrise but no moonset...
        out[5] = moonrise_no_set(d, d3, i, lat)

    return out, out2

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

def getmoonstate(d, lat):
    # populate the moon state (visible or not) for the specified date & latitude
    # note: the first parameter 'd' is already an ephem date 30 seconds before midnight
    # note: getmoonstate is called when there is neither a moonrise nor a moonset on 'd'

    i = 1 + config.lat.index(lat)   # index 0 is reserved to enable an explicit setting
    latitude = ephem.degrees('{}:00:00.0'.format(lat))
    obs = ephem.Observer()
    #d = ephem.date(date) - 30 * ephem.second
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
        #print("nr NeverUp")
        moonvisible[i] = False
    except ephem.AlwaysUpError:
        err = True
        #print("nr AlwaysUp")
        moonvisible[i] = True
    except Exception:
        flag_msg("Oops! moon nextR {}: {} occured, line: {}".format(i,sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
        #sys.exc_clear()		# only in Python 2

    obs.date = d
    if not(err):	# note - 'nextrising' above *should* fail
        try:
            nextsetting = obs.next_setting(m)
        except ephem.NeverUpError:
            err = True
            #print("ns NeverUp")
            moonvisible[i] = False
        except ephem.AlwaysUpError:
            err = True
            #print("ns AlwaysUp")
            moonvisible[i] = True
        except Exception:
            flag_msg("Oops! moon nextS {}: {} occured, line: {}".format(i,sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
            #sys.exc_clear()		# only in Python 2

    if not(err):	# note - "err == True" *is* expected...
        # however if we found both, which occured first?
        moonvisible[i] = False
        if nextrising > nextsetting:
            moonvisible[i] = True
        #print("{}".format(i), nextrising, nextsetting, moonvisible[i])
    return

##NEW##
def moonset_no_rise(d, date, i, lat):
    # if moonset but no moonrise...
    msg = ""
    n = seek_moonrise(d, lat)
    if n == 1:
        out = moonstate(i)       # moonrise "below horizon"
        msg = "below horizon (start)"
    if n == -1:
        #print("UP")
        moonvisible[0] = True
        out = moonstate(0)       # moonrise "above horizon"
        msg = "above horizon (end)"
        #print(out[0])
    #if msg != "":
        #print("no moonrise on {} at lat {} => {}".format(ephem.date(date).datetime().strftime("%Y-%m-%d"), lat, msg))
    if n == 0:
        out = r'''\raisebox{0.24ex}{\boldmath$\cdot\cdot$~\boldmath$\cdot\cdot$}'''
    return out

##NEW##
def moonrise_no_set(d, date, i, lat):
    # if moonrise but no moonset...
    msg = ""
    n = seek_moonset(d, lat)
    if n == 1:
        out = moonstate(i)       # moonset "above horizon"
        msg = "above horizon (start)"
    if n == -1:
        moonvisible[0] = False
        out = moonstate(0)       # moonset "below horizon"
        msg = "below horizon (end)"
    #if msg != "":
        #print("no moonset on  {} at lat {} => {}".format(ephem.date(date).datetime().strftime("%Y-%m-%d"), lat, msg))
    if n == 0:
        out = r'''\raisebox{0.24ex}{\boldmath$\cdot\cdot$~\boldmath$\cdot\cdot$}'''
    return out

##NEW##
def seek_moonset(d, lat):
    # for the specified date & latitude ...
    # return -1 if there is NO MOONSET yesterday
    # return +1 if there is NO MOONSET tomorrow
    # return  0 if there was a moonset yesterday and will be a moonset tomorrow
    # note: this is called when there is only a moonrise on the specified date+latitude

    m_set_t = 0     # normal case: assume moonsets yesterday & tomorrow

    i = 1 + config.lat.index(lat)   # index 0 is reserved to enable an explicit setting
    latitude = ephem.degrees('{}:00:00.0'.format(lat))
    obs = ephem.Observer()
    #d = ephem.date(date) - 30 * ephem.second
    obs.pressure = 0    # turn off PyEphem’s native mechanism for computing atmospheric refraction near the horizon
    obs.horizon = '-0:34'
    m = ephem.Moon(obs)
    err = False
    obs.date = d
    obs.lat = latitude
    m.compute(d)
    nextsetting = d + 10.0	# in case moonrise but no next moonset

    try:
        nextsetting = obs.next_setting(m)
    except ephem.NeverUpError:
        err = True
        #print("ns NeverUp")
        flag_msg("Oops! moon nextS {}: {} occured, line: {}".format(i,sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
    except ephem.AlwaysUpError:
        err = True
        m_set_t = +1
        #print("ns AlwaysUp")
    except Exception:
        flag_msg("Oops! moon nextS {}: {} occured, line: {}".format(i,sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
        #sys.exc_clear()		# only in Python 2

    if not(err):	# note - "err == True" *is* expected...
        # moonset detected - is it after tomorrow?
        if nextsetting > d + 2.0:
            m_set_t = +1

    obs.date = d
    if m_set_t == 0:
        try:
            prevsetting = obs.previous_setting(m)
        except ephem.NeverUpError:
            err = True
            m_set_t = -1
            #print("ps NeverUp")
        except ephem.AlwaysUpError:
            err = True
            #print("ps AlwaysUp")
            flag_msg("Oops! moon prevS {}: {} occured, line: {}".format(i,sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
        except Exception:
            flag_msg("Oops! moon prevS {}: {} occured, line: {}".format(i,sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
            #sys.exc_clear()		# only in Python 2

        if not(err):	# note - "err == True" *is* expected...
            # moonset detected - is it before yesterday?
            if prevsetting < d - 1.0:
                m_set_t = -1
        #print("m_set_t = {}".format(m_set_t))
    return m_set_t

##NEW##
def seek_moonrise(d, lat):
    # return -1 if there is NO MOONRISE yesterday
    # return +1 if there is NO MOONRISE tomorrow
    # return  0 if there was a moonrise yesterday and will be a moonrise tomorrow
    # note: this is called when there is only a moonset on the specified date+latitude

    m_rise_t = 0    # normal case: assume moonrise yesteray & tomorrow

    i = 1 + config.lat.index(lat)   # index 0 is reserved to enable an explicit setting
    latitude = ephem.degrees('{}:00:00.0'.format(lat))
    obs = ephem.Observer()
    #d = ephem.date(date) - 30 * ephem.second
    obs.pressure = 0
    obs.horizon = '-0:34'
    m = ephem.Moon(obs)
    err = False
    obs.date = d
    obs.lat = latitude
    m.compute(d)
    nextrising = d + 10.0	# in case moonset but no next moonrise

    try:
        nextrising  = obs.next_rising(m)
    except ephem.NeverUpError:
        err = True
        m_rise_t = +1
        #print("nr NeverUp")
    except ephem.AlwaysUpError:
        err = True
        #print("nr AlwaysUp")
        flag_msg("Oops! moon nextR {}: {} occured, line: {}".format(i,sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
    except Exception:
        flag_msg("Oops! moon nextR {}: {} occured, line: {}".format(i,sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
        #sys.exc_clear()		# only in Python 2

    if not(err):	# note - "err == True" *is* expected...
        # moonrise detected - is it after tomorrow?
        if nextrising > d + 2.0:
            m_rise_t = +1

    obs.date = d
    if m_rise_t == 0:
        try:
            prevrising = obs.previous_rising(m)
        except ephem.NeverUpError:
            err = True
            #print("pr NeverUp")
            flag_msg("Oops! moon prevR {}: {} occured, line: {}".format(i,sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
        except ephem.AlwaysUpError:
            err = True
            m_rise_t = -1
            #print("pr AlwaysUp")
        except Exception:
            flag_msg("Oops! moon prevR {}: {} occured, line: {}".format(i,sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
            #sys.exc_clear()		# only in Python 2

        if not(err):	# note - "err == True" *is* expected...
            # moonrise detected - is it before yesterday?
            if prevrising < d - 1.0:
                m_rise_t = -1

        #print("m_rise_t = {}".format(m_rise_t))
    return m_rise_t
