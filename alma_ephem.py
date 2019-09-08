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

import config
import ephem        # for sunrise/sunset, moonrise/moonset, planet magnitudes
import datetime

ephem_venus   = ephem.Venus()
ephem_mars    = ephem.Mars()
ephem_jupiter = ephem.Jupiter()
ephem_saturn  = ephem.Saturn()
degree_sign= u'\N{DEGREE SIGN}'


def magnitudes(date):
    # returns  magitude for the navigational planets.
    # (Skyfield 1.11 does not provide this)
    
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


def time(date): 
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
    time = u'%02d:%02d' %(hr,min)
#    return time, nextday
    # NOTE: this function could easily return the information that rounding
    #       flipped into the next day, however this is not required here.
    return time


def twilight(date, lat):
    # Returns for given date and latitude(in full degrees):
    # naut. and civil twilight (before sunrise), sunrise, sunset, civil and nautical twilight (after sunset).

    out = [0,0,0,0,0,0]
    obs = ephem.Observer()
    latitude = ephem.degrees('%s:00:00.0' %lat)
    obs.lat = latitude
    d = ephem.date(date) - 30 * ephem.second    # search from 30 seconds before midnight
    obs.date = d
    obs.pressure = 0
    s = ephem.Sun(obs)
    s.compute(d)
    r = s.radius

    # Nautical Twilight...
    obs.horizon = ephem.degrees('-12')+r	# Nautical twilight ...
    try:
        out[0] = time(obs.next_rising(s))	# begin
    except:
        out[0] = u'--:--'
    obs.date = d
    try:
        out[5] = time(obs.next_setting(s))	# end
    except:
        out[5] = u'--:--'

    # Civil Twilight...
    obs.horizon = ephem.degrees('-6')+r		# Civil twilight...
    obs.date = d
    try:
        out[1] = time(obs.next_rising(s))	# begin
    except:
        out[1] = u'--:--'
    obs.date = d
    try:
        out[4] = time(obs.next_setting(s))	# end
    except:
        out[4] = u'--:--'

    # Sunrise/Sunset...
    obs.horizon = '-0:34'
    obs.date = d
    try:
        out[2] = time(obs.next_rising(s))	# sunrise
    except:
        out[2] = u'--:--'
    obs.date = d
    try:
        out[3] = time(obs.next_setting(s))	# sunset
    except:
        out[3] = u'--:--'
    
    return out

def moonrise_set(date,lat):
    # returns moonrise and moonset for the given date and latitude plus next 2 days:
    #    rise day 1, rise day 2, rise day 3, set day 1, set day 2, set day 3

    out  = [u'--:--',u'--:--',u'--:--',u'--:--',u'--:--',u'--:--']	# first event
    out2 = [u'--:--',u'--:--',u'--:--',u'--:--',u'--:--',u'--:--']	# second event on same day (rare)

    obs = ephem.Observer()
    latitude = ephem.degrees('%s:00:00.0' %lat)
    obs.lat = latitude
    obs.pressure = 0
    obs.horizon = '-0:34'
    d = ephem.date(date) - 30 * ephem.second    # search from 30 seconds before midnight
    obs.date = d
    m = ephem.Moon(obs)
    m.compute(d)

    # Moonrise/Moonset on 1st. day ...
    try:
        firstrising = obs.next_rising(m)
        if firstrising-obs.date >= 1:
            raise ValueError('event next day')
        out[0] = time(firstrising)		# note: overflow to 00:00 next day is correct here
    except Exception:
        out[0] = u'--:--'
    try:
        nextr = obs.next_rising(m, start=firstrising)
        if nextr-obs.date < 1:
            out2[0] = time(nextr)		# note: overflow to 00:00 next day is correct here
    except UnboundLocalError:
        pass
    except ephem.NeverUpError:
        pass
    except ephem.AlwaysUpError:
        pass
    except Exception:
        flag_msg("Oops! %s occured, line: %s" %(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
        sys.exc_clear()		# only in Python 2

    obs.date = d
    try:
        firstsetting = obs.next_setting(m)
        if firstsetting-obs.date >= 1:
            raise ValueError('event next day')
        out[3] = time(firstsetting)		# note: overflow to 00:00 next day is correct here
    except Exception:
        out[3] = u'--:--'
    try:
        nexts = obs.next_setting(m, start=firstsetting)
        if nexts-obs.date < 1:
            out2[3] = time(nexts)		# note: overflow to 00:00 next day is correct here
    except UnboundLocalError:
        pass
    except ephem.NeverUpError:
        pass
    except ephem.AlwaysUpError:
        pass
    except Exception:
        flag_msg("Oops! %s occured, line: %s" %(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
        sys.exc_clear()		# only in Python 2
#-----------------------------------------------------------
    # Moonrise/Moonset on 2nd. day ...
    d = ephem.date(date + datetime.timedelta(days=1)) - 30 * ephem.second
    obs.date = d
    m.compute(d)
    try:
        firstrising = obs.next_rising(m)
        if firstrising-obs.date >= 1:
            raise ValueError('event next day')
        out[1] = time(firstrising)		# note: overflow to 00:00 next day is correct here
    except Exception:
        out[1] = u'--:--'
    try:
        nextr = obs.next_rising(m, start=firstrising)
        if nextr-obs.date < 1:
            out2[1] = time(nextr)		# note: overflow to 00:00 next day is correct here
    except UnboundLocalError:
        pass
    except ephem.NeverUpError:
        pass
    except ephem.AlwaysUpError:
        pass
    except Exception:
        flag_msg("Oops! %s occured, line: %s" %(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
        sys.exc_clear()		# only in Python 2

    obs.date = d
    try:
        firstsetting = obs.next_setting(m)
        if firstsetting-obs.date >= 1:
            raise ValueError('event next day')
        out[4] = time(firstsetting)		# note: overflow to 00:00 next day is correct here
    except Exception:
        out[4] = u'--:--'
    try:
        nexts = obs.next_setting(m, start=firstsetting)
        if nexts-obs.date < 1:
            out2[4] = time(nexts)		# note: overflow to 00:00 next day is correct here
    except UnboundLocalError:
        pass
    except ephem.NeverUpError:
        pass
    except ephem.AlwaysUpError:
        pass
    except Exception:
        flag_msg("Oops! %s occured, line: %s" %(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
        sys.exc_clear()		# only in Python 2
#-----------------------------------------------------------
    # Moonrise/Moonset on 3rd. day ...
    d = ephem.date(date + datetime.timedelta(days=2)) - 30 * ephem.second
    obs.date = d
    m.compute(d)
    try:
        firstrising = obs.next_rising(m)
        if firstrising-obs.date >= 1:
            raise ValueError('event next day')
        out[2] = time(firstrising)		# note: overflow to 00:00 next day is correct here
    except Exception:
        out[2] = u'--:--'
    try:
        nextr = obs.next_rising(m, start=firstrising)
        if nextr-obs.date < 1:
            out2[2] = time(nextr)		# note: overflow to 00:00 next day is correct here
    except UnboundLocalError:
        pass
    except ephem.NeverUpError:
        pass
    except ephem.AlwaysUpError:
        pass
    except Exception:
        flag_msg("Oops! %s occured, line: %s" %(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
        sys.exc_clear()		# only in Python 2

    obs.date = d
    try:
        firstsetting = obs.next_setting(m)
        if firstsetting-obs.date >= 1:
            raise ValueError('event next day')
        out[5] = time(firstsetting)		# note: overflow to 00:00 next day is correct here
    except Exception:
        out[5] = u'--:--'
    try:
        nexts = obs.next_setting(m, start=firstsetting)
        if nexts-obs.date < 1:
            out2[5] = time(nexts)		# note: overflow to 00:00 next day is correct here
    except UnboundLocalError:
        pass
    except ephem.NeverUpError:
        pass
    except ephem.AlwaysUpError:
        pass
    except Exception:
        flag_msg("Oops! %s occured, line: %s" %(sys.exc_info()[1],sys.exc_info()[2].tb_lineno))
        sys.exc_clear()		# only in Python 2

    return out, out2
