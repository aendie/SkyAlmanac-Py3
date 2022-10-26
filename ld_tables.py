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

# NOTE: the new format statement requires a literal '{' to be entered as '{{',
#       and a literal '}' to be entered as '}}'. The old '%' format specifier
#       will be removed from Python at some later time. See:
# https://docs.python.org/3/whatsnew/3.0.html#pep-3101-a-new-approach-to-string-formatting

###### Standard library imports ######
# don't confuse the 'date' method with the 'Date' variable!
from datetime import date, datetime, timedelta
from math import copysign

###### Local application imports ######
import config
from ld_skyfield import getDUT1, moon_GHA, moon_SD, moon_VD, ld_planets, ld_stars, find_transit, sunSD

UpperLists = [[], [], []]    # moon GHA per hour for 3 days

#------------------------
#   internal functions
#------------------------

def fmtdate(d):
    if config.pgsz == 'Letter': return d.strftime("%m/%d/%Y")
    return d.strftime("%d.%m.%Y")

def fmtdates(d1,d2):
    if config.pgsz == 'Letter': return d1.strftime("%m/%d/%Y") + " - " + d2.strftime("%m/%d/%Y")
    return d1.strftime("%d.%m.%Y") + " - " + d2.strftime("%d.%m.%Y")

def buildUPlists(n, ghaSoD, ghaPerHour, ghaEoD):
    # build list of hourly GHA values with modified start and end time to
    #  account for rounding times to the minute where 23:59:>30 rounds up
    #  00:00 the next day.
    UpperLists[n] = [-1.0 for x in range(25)]
    UpperLists[n][0] = ghaSoD
    for i in range(23):
        UpperLists[n][i+1] = ghaPerHour[i+1]
    UpperLists[n][24] = ghaEoD
    return

def NSdeg(deg, modern=False, hr=0, forceNS=False):
    # reformat degrees latitude to Ndd°mm.m or Sdd°mm.m
    if deg[0:1] == '-':
        hemisph = 'S'
        deg = deg[1:]
    else:
        hemisph = 'N'
    if modern:
        if forceNS or hr%6 == 0:
            sdeg = r'''\textcolor{{blue}}{{{}}}'''.format(hemisph) + deg
        else:
            sdeg = deg
    else:
        if forceNS or hr%6 == 0:
            sdeg = r'''\textbf{{{}}}'''.format(hemisph) + deg
        else:
            sdeg = deg
    return sdeg, hemisph


#---------------------------------
#   create Lunar Distance table
#---------------------------------

def moontab(Date, dpp, strat):
    # generates LaTeX table for moon and Lunar Distance (traditional style)

    tex = r'''\setlength{\tabcolsep}{5pt}  % default 6pt
\noindent'''
    n = 0
    while n < dpp:      # maximum 3 days on a page

# >>>>>>>>>>>> Calculate all required data <<<<<<<<<<<<

        if config.debug_strategy:
            print("=" * 70)
        Date0 = Date - timedelta(days=1)
        gham, decm, degm, HPm, GHAupper, GHAlower, ghaSoD, ghaEoD = moon_GHA(Date)
        vmin, dmin = moon_VD(Date0,Date)

        buildUPlists(n, ghaSoD, GHAupper, ghaEoD)

        out2, tup2, NMhours, ra_m = ld_planets(Date)   # planets & sun
        out, tup = ld_stars(Date, NMhours, out2[0][1].hours)
        tup = tup + tup2
        tup.sort(key = lambda x: x[1])  # sort by signed first valid LD
        if config.debug_strategy:
            print("New Moon hours:\n{}".format(NMhours))
            for i in range(len(out2)):
                print("{}:\n{}".format(out2[i][0], out2[i][5]))
            for i in range(len(out)):
                print("{}:\n{}".format(out[i][0], out[i][5]))

# =================================================================
#                        Strategy "C"
# =================================================================

# >>>>>>>>>>>> Decide which LD lists to print (8 maximum) <<<<<<<<<<<<

        if strat == "C":
            LDtxt = " (objects with highest brightness)"
            # build list of objects sorted by largest hourly LD delta first
            tuple_list = [None] * 27
            for i in range(len(tup)):
##                tuple_list[i] = (tup[i][0], tup[i][4], copysign(1, tup[i][1]), tup[i][3])
                tuple_list[i] = (tup[i][0], tup[i][5], copysign(1, tup[i][1]), tup[i][4])
            tuple_list.sort(key = lambda x: x[1])   # sort by object magnitude
            if config.debug_strategy:
                print("--- tuples with highest brightness first ---")
                print(tuple_list)
##                print([y[0] for y in tuple_list].index(3))  # find index of star in tuple_list

# =================================================================
#                        Strategy "B"
# =================================================================

# >>>>>>>>>>>> Decide which LD lists to print (8 maximum) <<<<<<<<<<<<

        if strat == "B":
            LDtxt = " (objects with largest hourly LD delta)"
            # build list of objects sorted by largest hourly LD delta first
            tuple_list = [None] * 27
            for i in range(len(tup)):
##                tuple_list[i] = (tup[i][0], tup[i][2], copysign(1, tup[i][1]), tup[i][3])
                tuple_list[i] = (tup[i][0], tup[i][3], copysign(1, tup[i][1]), tup[i][4])
            tuple_list.sort(key = lambda x: -x[1])  # sort by max hourly LD delta
            if config.debug_strategy:
                print("--- tuples with largest ld_delta_max first ---")
                print(tuple_list)
##                print([y[0] for y in tuple_list].index(3))  # find index of star in tuple_list

# =================================================================
#                Code common to Strategy "C" and "B"
# =================================================================

        if strat == "B" or strat == "C":
            # split the list into Positive and Negative LD (RA in relation to the Moon)
            NEGlist = []
            POSlist = []
            for i in range(len(tuple_list)):
                if tuple_list[i][3] > 0:        # ignore objects with no data
                    if tuple_list[i][2] > 0:
                        POSlist.append(tuple_list[i][0])    # object index
                    else:
                        NEGlist.append(tuple_list[i][0])    # object index

            # attempt to pick objects evenly from Positive and Negative lists:
            OUTlist = []
            i_neg = 0
            i_pos = 0
            i_out = 0
            while i_out < 8:
                if i_neg < len(NEGlist):
                    OUTlist.append(NEGlist[i_neg])
                    i_neg += 1
                    i_out += 1
                if i_pos < len(POSlist):
                    OUTlist.append(POSlist[i_pos])
                    i_pos += 1
                    i_out += 1
                if i_neg == len(NEGlist) and i_pos == len(POSlist): break
            iLists = len(OUTlist)
            #print("   {} lists".format(iLists))

# >>>>>>>>>>>> Gather data from LD lists <<<<<<<<<<<<

            iCols = iLists
            if iCols < 5: LDtxt = ""    # not wide enough to print full text
            extracols = ""
            obj = [None] * iCols
            ld  = [None] * 24
            iC = 0
            # output the objects in OUTlist in the sequence within 'tup'
            for i in range(len(tup)):
                ndx = tup[i][0]
                if ndx in set(OUTlist):
                    ld_first = tup[i][1]    # first valid lunar distance angle in the day
                    sgn = "-" if ld_first < 0 else "+"
                    ld_last = tup[i][2]     # last valid lunar distance angle in the day
                    sgn2 = "-" if ld_last < 0 else "+"
                    if sgn != sgn2: sgn = u"\u00B1"     # plus-minus symbol
                    if ndx > 0:
                        #print("out({})".format(ndx-1))
                        obj[iC] = sgn + out[ndx-1][0]       # star name
                        ld[iC] = out[ndx-1][5]        # lunar distance angles per hour
                    else:
                        #print("out2({})".format(-ndx))
                        obj[iC] = sgn + out2[-ndx][0]       # planet name
                        ld[iC] = out2[-ndx][5]        # lunar distance angles per hour
                    #print(obj[iC])
                    extracols = extracols + r'''r|'''
                    i_out -= 1
                    iC += 1
                if i_out == 0: break

# =================================================================
#                        Strategy "A"
# =================================================================

# >>>>>>>>>>>> Decide which LD lists to print (8 maximum) <<<<<<<<<<<<

        if strat == "A":
            LDtxt = " (objects closest to the Moon)"
            iClosest = -1       # index of object closest to Moon (invalid value initially)
            for i in range(len(tup)):
                ld_first = tup[i][1]    # first valid lunar distance angle in the day
                if ld_first >= 0.0:
                    iClosest = i
                    break

            iLists = 0         # number of valid lists
            for i in range(len(tup)):
                ld_first = tup[i][1]    # first valid lunar distance angle in the day
                if ld_first < 1000.0: iLists += 1

            iFrom = 0
            if iLists <= 8:
                iCols = iLists
            else:
                iRem = iLists - 8       # count of lists that won't be printed
                                        #    (and highest 'iFrom' value)
                iCols = 8
                #iFrom = int(iRem / 2.0) # pick middle section of Lists
                if iClosest > iCols/2:
                    iFrom = iClosest - int(iCols/2)
                #iFrom = iClosest - 4    # four -ve LD lists before +ve LD lists
                if iFrom > iRem: iFrom = iRem
                #print("iCols = {}   iFrom = {}   iClosest = {}".format(iCols, iFrom, iClosest))

# >>>>>>>>>>>> Gather data from LD lists <<<<<<<<<<<<

            if iCols < 5: LDtxt = ""    # not wide enough to print full text
            i = iFrom
            extracols = ""
            obj = [None] * iCols
            ld  = [None] * 24
            for iC in range(iCols):
                #print(tup[iC])
                ndx = tup[i][0]
                ld_first = tup[i][1]    # first valid lunar distance angle in the day
                sgn = "-" if ld_first < 0 else "+"
                ld_last = tup[i][2]     # last valid lunar distance angle in the day
                sgn2 = "-" if ld_last < 0 else "+"
                if sgn != sgn2: sgn = u"\u00B1"     # plus-minus symbol
                if ndx > 0:
                    #print("out({})".format(ndx-1))
                    obj[iC] = sgn + out[ndx-1][0]       # star name
                    ld[iC] = out[ndx-1][5]        # lunar distance angles per hour
                else:
                    #print("out2({})".format(-ndx))
                    obj[iC] = sgn + out2[-ndx][0]       # planet name
                    ld[iC] = out2[-ndx][5]        # lunar distance angles per hour
                i += 1
                #print(obj[iC])
                #print(ld[iC])
                extracols = extracols + r'''r|'''
            if len(NMhours) == 24:      # if NewMoon all day, i.e. iCols == 0
                extracols = extracols + r'''r|'''   # add a fake column
        
# =================================================================

        # is the Sun a selected celestial object?
        sunSDrqrd = False
        iC = 0
        for objX in obj:
            if objX[1:] == "Sun":
                sunSDrqrd = True
                break
            iC += 1

        if sunSDrqrd:
            sdsm = sunSD(Date)  # get sun's SD at 0h and 23h
            ldx00 = ld[iC][0]
            ldx23 = ld[iC][23]
            if ldx00.find("circ") == -1: ldx00 = ''
            if ldx23.find("circ") == -1: ldx23 = ''
            sdsval = sdsm[0]
            if ldx00 == '': sdsval = sdsm[1]
            if ldx00 != '' and ldx23 != '': # if we have LD at 0h and 23h
                if sdsm[0] == sdsm[1]:
                    sdstxt = "Sun SD = " + sdsval + r'''$'$'''
                else:
                    sdstxt = r'''Sun SD = {}$'$ at 0h; {}$'$ at 23h'''.format(sdsm[0],sdsm[1])
            else:
                sdstxt = "Sun SD = " + sdsval + r'''$'$'''

        if config.debug_strategy:
            print("{} columns of data".format(iCols))

# >>>>>>>>>>>> Format LaTeX table <<<<<<<<<<<<

        # format day as an ordinal number
        day = Date.day
        mth = Date.month
        if 4 <= day <= 20 or 24 <= day <= 30:
            suffix = "th"
        else:
            suffix = ["st", "nd", "rd"][day % 10 - 1]
        day_ord = r'''{}\textsuperscript{{{}}}'''.format(str(day), suffix)

        # format date like "26th Oct"
        day_mth = r'''Moon ({})'''.format(day_ord + Date.strftime(" %b"))

        if len(NMhours) == 24:      # if NewMoon all day, i.e. iCols == 0
            extracols = extracols + r'''r|'''   # add a fake column

        tex += r'''
\begin{{tabular}}[t]{{|c|rrrrr|{}}}'''.format(extracols)

        tex += r'''
\multicolumn{{1}}{{c}}{{\normalsize{{h}}}} & \multicolumn{{5}}{{c}}{{\normalsize{{{}}}}}'''.format(day_mth)

        if iCols > 0:
            tex += r''' & \multicolumn{{{}}}{{c}}{{\normalsize{{Lunar Distance{}}}}}'''.format(iCols,LDtxt)

        tex += r'''\\
\hline
\multicolumn{{1}}{{|c|}}{{\rule{{0pt}}{{2.6ex}}\textbf{{{}}}}} & \multicolumn{{1}}{{c}}{{\textbf{{GHA}}}} & \multicolumn{{1}}{{c}}{{\(\nu\)}} & \multicolumn{{1}}{{c}}{{\textbf{{Dec}}}} & \multicolumn{{1}}{{c}}{{\textit{{d}}}} & \multicolumn{{1}}{{c|}}{{\textbf{{HP}}}}'''.format(Date.strftime("%a"))

        for iC in range(iCols):
            tex += r''' & \multicolumn{{1}}{{c|}}{{\textbf{{{}}}}}'''.format(obj[iC])
        if len(NMhours) == 24:      # add fake column (iCols == 0)
            tex += r''' & \multicolumn{1}{c|}{}'''
        tex += r'''\\
\hline\rule{0pt}{2.6ex}\noindent
'''

        h = 0
        mlastNS = ''
        while h < 24:
            if h > 0:
                prevDECm = degm[h-1]
            else:
                prevDECm = degm[0]		# hour -1 = hour 0
            if h < 23:
                nextDECm = degm[h+1]
            else:
                nextDECm = degm[23]	    # hour 24 = hour 23

            mdec, mNS = NSdeg(decm[h],False,h)
            if mNS != mlastNS or copysign(1.0,prevDECm) != copysign(1.0,nextDECm):
                mdec, mNS = NSdeg(decm[h],False,h,True)	# force N/S
            mlastNS = mNS

            line = r'''{} & {} & {} & {} & {} & {}'''.format(h,gham[h],vmin[h],mdec,dmin[h],HPm[h])

            if h in set(NMhours):       # better than "if ld[0][h] == "newMoon":"
                txt = "New Moon"
                if iCols > 2:
                    ttt = "----" * iCols
                    txt = ttt + " New Moon " + ttt
                if iCols > 0 or len(NMhours) == 24:
                    line = line + r''' & \multicolumn{{{}}}{{c|}}{{{}}}'''.format(iCols, txt)
            else:
                for i in range(iCols):
                    ldx = ld[i][h]
                    if not config.debug_strategy:           # if not in DEBUG mode ...
                        if ldx.find("circ") == -1: ldx = '' # suppress all invalid entries
                    line = line + r''' & {}'''.format(ldx)

            lineterminator = r'''\\
'''
            if h < 23 and (h+1)%6 == 0:
                lineterminator = r'''\\[2Pt]
'''
            tex += line + lineterminator
            h += 1

        sdmm = moon_SD(Date)
        mp_upper = find_transit(Date, UpperLists[n], False)    # calculate moon upper transit
        tex += r'''\hline
\rule{{0pt}}{{2.4ex}}\textbf{{{}}} & \multicolumn{{5}}{{c|}}{{SD = {}$'$ \quad Mer. pass. {}}}'''.format(day_ord,sdmm,mp_upper)
        if iCols > 0:
            if sunSDrqrd:
                tex += r''' & \multicolumn{{{}}}{{c|}}{{{}}}'''.format(iCols,sdstxt)
            else:
                tex += r''' & \multicolumn{{{}}}{{c|}}{{}}'''.format(iCols)
        if len(NMhours) == 24:      # add fake column (iCols == 0)
            tex += r''' & \multicolumn{1}{c|}{}'''
        tex += r'''\\
\hline
'''
        if n < 2:
            # add space between tables...
            tex += r'''\multicolumn{5}{c}{}\\[-1.5ex]
'''
        n += 1
        Date += timedelta(days=1)
        tex += r'''\end{tabular}
\par\noindent    % put next table below here'''
    return tex

#----------------------
#   page preparation
#----------------------

def page(Date, dpp, strat):
    # creates a page (max. 3 days) of tables

    # time delta values for the initial date&time...
    dut1, deltat = getDUT1(Date)
    timeDUT1 = r"DUT1 = UT1-UTC = {:+.4f} sec\quad$\Delta$T = TT-UT1 = {:+.4f} sec".format(dut1, deltat)

    Lfoot_IERSEOP = ""
    if config.dt_IERSEOP != None:
        # the IERS EOP data start date is 2nd January 1973
        if Date + timedelta(days=2) >= date(1973, 1, 2):
            Lfoot_IERSEOP = config.txtIERSEOP
        if Date + timedelta(days=2) >= config.dt_IERSEOP:
            Lfoot_IERSEOP = config.endIERSEOP
        if Date > config.dt_IERSEOP:
            Lfoot_IERSEOP = r'''\textbf{No IERS EOP prediction data available}'''

    page = ''

    if dpp > 1:
        str2 = r'''\textbf{{{} to {} UT}}
'''.format(Date.strftime("%Y %B %d"),(Date+timedelta(days=dpp-1)).strftime("%b. %d"))
    else:
        str2 = r'''\textbf{{{} UT}}
'''.format(Date.strftime("%Y %B %d"))

    if config.FANCYhd:
        str1 = r'''
% ------------------ N E W   P A G E ------------------
\newpage
\sffamily
\lhead{{\textsf{{\footnotesize{{{}}}}}}}
\rhead{{\textsf{{\textbf{{{}}}}}}}
\lfoot{{\textsf{{\footnotesize{{{}}}}}}}
\begin{{scriptsize}}
'''.format(timeDUT1, str2, Lfoot_IERSEOP)
    else:   # old formatting
        str1 = r'''
% ------------------ N E W   P A G E ------------------
\newpage
\sffamily
\noindent
\begin{{flushleft}}     % required so that \par works
{{\footnotesize {}}}\hfill{}
\end{{flushleft}}\par
\begin{{scriptsize}}
'''.format(timeDUT1, str2)

    page = page + str1

    page = page + moontab(Date,dpp,strat)
    page = page + r'''
\end{scriptsize}'''
    # to avoid "Overfull \hbox" messages, leave a paragraph end before the end of a size change. (See lines above)
    return page


def pages(first_day, dtp, strat):
    # make pages beginning with first_day
    # dtp = 0 if for entire year; = -1 if for entire month; else days to print

    out = ''
    pmth = ''
    dpp = 3         # 3 days per page maximum
    day1 = first_day

    if dtp == 0:        # if entire year
        year = first_day.year
        yr = year
        while year == yr:
            day3 = day1 + timedelta(days=2)
            if day3.year != yr:
                dpp -= day3.day
                if dpp <= 0: return out
            out += page(day1,dpp,strat)
            day1 += timedelta(days=3)
            year = day1.year

    elif dtp == -1:     # if entire month
        mth = first_day.month
        m = mth
        while mth == m:
            day3 = day1 + timedelta(days=2)
            if day3.month != m:
                dpp -= day3.day
                if dpp <= 0: return out
            out += page(day1,dpp,strat)
            day1 += timedelta(days=3)
            mth = day1.month

    else:           # print 'dtp' days beginning with first_day
        i = dtp   # don't decrement dtp
        while i > 0:
            if i < 3: dpp = i
            out += page(day1,dpp,strat)
            i -= 3
            day1 += timedelta(days=3)

    return out

def page2():
    return r'''
\setcounter{page}{2}    % otherwise it's 1
    %\vspace*{5mm}
    \noindent
    \textbf{Lunar Distance}\\[12pt]
    \noindent
    The Lunar Distance method (or the old method of ``lunars'') is an 18th century technique to find the time, typically to reset ship's clocks or as an emergency procedure.
    The method uses the Moon's apparent motion relative to the Sun, planets or stars like a clock to find a reference time (e.g. GMT).
    ``Until 1906, the Nautical Almanac included lunar distance tables showing predicted geocentric angular distances between the Moon and selected bodies in 3-hour intervals. After the tables were dropped, lunar distances fell more or less into oblivion.''\footnote{Henning Umland, Chapter 7 - Finding Time and Longitude by Lunar Distances}\\[12pt]
    \noindent
    ``The methods are a good deal more laborious than the more commonplace procedures of celestial navigation. 
    It is perhaps the most difficult possible operation within the discipline of celestial navigation.
    However, one argument for maintaining celestial skills is the utility of celestial navigation as an emergency substitute for electronic navigation.''\footnote{Eric Romelczyk, The Journal of Navigation, Volume 72, Issue 6}
    ``Nothing else comes close to the lunar for developing skill with a sextant - and the observation is demanding enough to hold one's interest for a lifetime.''\footnote{Bruce Stark, page vi, Tables For Clearing the Lunar Distance and Finding Universal Time by Sextant Observation}
    Thus it is still a valuable process to learn and indeed worthwhile mastering.
    (A practised user can routinely find the correct time to within ±30 seconds.)\\[12pt]
    \noindent
    ``Because the Moon moves much slower across the sky than the stars, its changing position can be used in sort of a reverse process of sight reduction to find the time.''\footnote{Bruce Stark, https://www.celestaire.com/product/tables-for-clearing-the-lunar-distance/}
    ``The basic idea of the lunar distance method is easy to comprehend. Since the Moon moves across the celestial sphere at a rate of about 0.5$^\circ$ per hour, the angular distance between the Moon and a celestial body in her path varies at a similar rate and rapidly enough to be used to measure the time. The time corresponding with an observed lunar distance can be found by comparison with tabulated values.''\footnote{Henning Umland, Chapter 7 - Finding Time and Longitude by Lunar Distances}
    (The continuous motion of the Moon through the sky day-by-day implies that different celestial bodies will be selected for LD measurements on different days.)\\[12pt]
    \noindent
    The following Lunar Distance tables can contain up to 8 celestial bodies per day (due to the page width limitation).
    Generally, an attempt is made to include an even number of objects to the east and west of the Moon. 
    The maximum LD angle chosen for inclusion in the tables is 120$^\circ$, which is about the maximum angle a sextant can measure.\\[12pt]
    \noindent
    The celestial bodies available for LD measurement include the Sun, four planets (Venus, Mars, Jupiter, Saturn), 21 navigational stars (with magnitude $\leq$ 1.5) and Polaris.\\[12pt]
    \noindent
    Three different strategies are available to select suitable celestial bodies for inclusion in a daily LD table:
    \begin{itemize}
    \item pick celestial bodies closest to the Moon
    \item pick celestial bodies with the highest hourly LD delta (for best accuracy in time determination)
    \item pick the brightest celestial bodies (possibly easier to locate in the sky)
    \end{itemize}
    The celestial body LD angle at a particular hour of day still needs to fulfill several requirements:
    \begin{itemize}
    \item the LD of the Sun is \textgreater 10$^\circ$ as the Moon is hardly visible during New Moon. (This applies to \underline{all} celestial bodies)
    \item the LD of the Sun is \textgreater 40$^\circ$ (otherwise the Moon is not visible)
    \item only LD angles \textless 120$^\circ$ are tabulated
    \item the angle between the celestial body and the Sun (``Solar Distance'') is \textgreater 10$^\circ$ (otherwise the celestial body might not be visible)
    \item the Sun is not between the celestial body and the Moon (based on the Right Ascenscion of all three)
    \item the hourly LD delta is \textgreater 15$'$ of arc (to avoid measurement errors).
    ``The rate of change of LD becomes zero when LD passes through a minimum or maximum, making an observation useless.''\footnote{Henning Umland, Chapter 7 - Finding Time and Longitude by Lunar Distances}
    \item the rate of change of the hourly LD delta does not exceed 0.016$^\circ$ (= 0.96$'$). This empirical figure removes LD values where linear interpolation (between hours) becomes unreliable.
    \end{itemize}
    Suggested further reading: ``Stark Tables: For Clearing the Lunar Distance and Finding Universal Time by Sextant Observation'' by Bruce Stark, ISBN 978-0-914025-21-4'''

#--------------------------
#   external entry point
#--------------------------

def makeLDtables(first_day, dtp, strat):

    if config.FANCYhd:
        return makeLDnew(first_day, dtp, strat) # use the 'fancyhdr' package
    else:
        return makeLDold(first_day, dtp, strat) # use old formatting

#   The following functions are intentionally separate functions.
#   'makeEVold' is required for TeX Live 2019, which is the standard
#   version in Ubuntu 20.04 LTS which expires in April 2030.

def hdrEVnew(first_day,dtp,vsep1,vsep2):
    # build the front page
    year = first_day.year
    mth = first_day.month
    day = first_day.day

    tex = r'''
\pagestyle{frontpage}
    \begin{titlepage}
    \begin{center}
    \textsc{\Large Generated using Skyfield}\\
    \large http://rhodesmill.org/skyfield/\\[0.7cm]'''

    if config.dockerized:   # DOCKER ONLY
        fn1 = "../A4chart0-180_P.pdf"
        fn2 = "../A4chart180-360_P.pdf"
    else:
        fn1 = "./A4chart0-180_P.pdf"
        fn2 = "./A4chart180-360_P.pdf"

    tex += r'''
    % TRIM values: left bottom right top
    \includegraphics[clip, trim=12mm 20cm 12mm 21mm, width=0.92\textwidth]{{{}}}\\[0.3cm]
    \includegraphics[clip, trim=12mm 20cm 12mm 21mm, width=0.92\textwidth]{{{}}}\\'''.format(fn1,fn2)
    
    tex += r'''[{}]
    \textsc{{\huge Lunar Distance}}\\[{}]'''.format(vsep1,vsep2)

    if dtp == 0:
        tex += r'''
    \HRule \\[0.5cm]
    {{ \Huge \bfseries {}}}\\[0.2cm]
    \HRule \\'''.format(first_day.year)
    elif dtp == -1:
        tex += r'''
    \HRule \\[0.5cm]
    {{ \Huge \bfseries {}}}\\[0.2cm]
    \HRule \\'''.format(first_day.strftime("%B %Y"))
    elif dtp > 1:
        tex += r'''
    \HRule \\[0.5cm]
    {{ \Huge \bfseries {}}}\\[0.2cm]
    \HRule \\'''.format(fmtdates(first_day,first_day+timedelta(days=dtp-1)))
    else:
        tex += r'''
    \HRule \\[0.5cm]
    {{ \Huge \bfseries {}}}\\[0.2cm]
    \HRule \\'''.format(fmtdate(first_day))

    tex += r'''
    \begin{center}\begin{tabular}[t]{rl}
    \large\emph{Author:} & \large Andrew \textsc{Bauer}\\
    \end{tabular}\end{center}'''

    tex += r'''
    {\large \today}
    \HRule \\[0.2cm]
    \end{center}
    \begin{description}[leftmargin=5.5em,style=nextline]\footnotesize
    \item[Disclaimer:] These are computer generated tables - use them at your own risk. They replicate Lunar Distance algorithms with no guarantee of accuracy. They are intended to encourage the use of sextants, be it as a hobby or as a backup when electronics fail. The author claims no liability for any consequences arising from use of these tables and accompanying charts.
    \end{description}
\end{titlepage}
\pagestyle{page2}  % page style for page 2'''

    tex += page2()

    return tex

def makeLDnew(first_day, dtp, strat):
    # make tables starting from first_day

    # page size specific parameters
    # NOTE: 'bm' (bottom margin) is an unrealistic value used only to determine the vertical size of 'body' (textheight), which must be large enough to include all the tables. 'tm' (top margin) and 'hs' (headsep) determine the top of body. Finally use 'fs' (footskip) to position the footer.
    if config.pgsz == "A4":
        # A4 ... pay attention to the limited page width
        paper = "a4paper"
        # title page...
        vsep1 = "1.5cm"
        vsep2 = "1.0cm"
        tm1 = "21mm"
        bm1 = "15mm"
        lm1 = "10mm"
        rm1 = "10mm"
        # page 2 text...
        tm2 = "21mm"
        bm2 = "18mm"
        fs2 = "20pt"
        # data pages...
        tm = "27.6mm"       # was "21mm"
        bm = "16mm"         # was "18mm"
        hs = "4.9pt"        # headsep  (page 3 onwards)
        fs = "12pt"         # footskip (page 3 onwards)
        lm = "16mm"
        rm = "12mm"
    else:
        # LETTER ... pay attention to the limited page height
        paper = "letterpaper"
        # title page...
        vsep1 = "0.8cm"
        vsep2 = "0.7cm"
        tm1 = "12mm"
        bm1 = "15mm"
        lm1 = "12mm"
        rm1 = "12mm"
        # page 2 text...
        tm2 = "12mm"
        bm2 = "13mm"
        fs2 = "20pt"
        # data pages...
        tm = "17.8mm"       # was "12mm"
        bm = "10.5mm"       # was "12mm"
        hs = "2.6pt"        # headsep  (page 3 onwards)
        fs = "12pt"         # footskip (page 3 onwards)
        lm = "16mm"
        rm = "14mm"

    # default is 'oneside'...
    tex = r'''\documentclass[10pt, {}]{{report}}'''.format(paper)

    tex += r'''
%\usepackage[utf8]{inputenc}
\usepackage[english]{babel}
\usepackage{fontenc}
\usepackage{enumitem} % used to customize the {description} environment'''

    # to troubleshoot add "showframe, verbose," below:
    tex += r'''
\usepackage[nomarginpar, top={}, bottom={}, left={}, right={}]{{geometry}}'''.format(tm1,bm1,lm1,rm1)

    # define page styles
    # CAUTION: putting '\fancyhf{}' in frontpage style also clears the footer in page2!
    tex += r'''
%------------ page styles ------------
\usepackage{fancyhdr}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\fancypagestyle{frontpage}{
}
\fancypagestyle{page2}[frontpage]{'''
    tex += r'''
  \newgeometry{{nomarginpar, top={}, bottom={}, left={}, right={}, headsep={}, footskip={}}}'''.format(tm2,bm2,lm,rm,hs,fs2)
    tex += r'''
  \cfoot{\centerline{Page \thepage}}
  \fancyfootoffset[R]{0pt}% recalculate \headwidth
}
\fancypagestyle{datapage}[page2]{'''
    tex += r'''
  \newgeometry{{nomarginpar, top={}, bottom={}, left={}, right={}, headsep={}, footskip={}}}'''.format(tm,bm,lm,rm,hs,fs)
    tex += r'''
  \rfoot{\textsf{\footnotesize{https://pypi.org/project/skyalmanac/}}}
} %-----------------------------------'''

    # Note: \DeclareUnicodeCharacter is not compatible with some versions of pdflatex
    tex += r'''
\usepackage{xcolor}  % highlight double moon events on same day
\definecolor{khaki}{rgb}{0.76, 0.69, 0.57}
\usepackage{multirow}
\newcommand{\HRule}{\rule{\linewidth}{0.5mm}}
\usepackage[pdftex]{graphicx}	% for \includegraphics
\usepackage{tikz}				% for \draw  (load after 'graphicx')
%\showboxbreadth=50  % use for logging
%\showboxdepth=50    % use for logging
%\DeclareUnicodeCharacter{00B0}{\ensuremath{{}^\circ}}
\setlength\fboxsep{1.5pt}       % ONLY used by \colorbox in ldist_skyfield.py
\begin{document}'''

    if not config.DPonly:
        tex += hdrEVnew(first_day,dtp,vsep1,vsep2)

    tex += r'''
\pagestyle{datapage}  % the default page style for the document'''

    tex += pages(first_day,dtp,strat)
    tex += r'''
\end{document}'''
    return tex

# ===   ===   ===   ===   ===   ===   ===   ===   ===   ===   ===   ===   ===
# ===   ===   ===   ===   O L D   F O R M A T T I N G   ===   ===   ===   ===
# ===   ===   ===   ===   ===   ===   ===   ===   ===   ===   ===   ===   ===

def hdrEVold(first_day,dtp,tm1,bm1,lm1,rm1,vsep1,vsep2):
    # build the front page
    year = first_day.year
    mth = first_day.month
    day = first_day.day

    tex = r'''
% for the title page only...
\newgeometry{{nomarginpar, top={}, bottom={}, left={}, right={}}}'''.format(tm1,bm1,lm1,rm1)

    tex += r'''
    \begin{titlepage}
    \begin{center}
    \textsc{\Large Generated using Skyfield}\\
    \large http://rhodesmill.org/skyfield/\\[0.7cm]'''

    if config.dockerized:   # DOCKER ONLY
        fn1 = "../A4chart0-180_P.pdf"
        fn2 = "../A4chart180-360_P.pdf"
    else:
        fn1 = "./A4chart0-180_P.pdf"
        fn2 = "./A4chart180-360_P.pdf"

    tex += r'''
    % TRIM values: left bottom right top
    \includegraphics[clip, trim=12mm 20cm 12mm 21mm, width=0.92\textwidth]{{{}}}\\[0.3cm]
    \includegraphics[clip, trim=12mm 20cm 12mm 21mm, width=0.92\textwidth]{{{}}}\\'''.format(fn1,fn2)
    
    tex += r'''[{}]
    \textsc{{\huge Lunar Distance}}\\[{}]'''.format(vsep1,vsep2)

    if dtp == 0:
        tex += r'''
    \HRule \\[0.5cm]
    {{ \Huge \bfseries {}}}\\[0.2cm]
    \HRule \\'''.format(first_day.year)
    elif dtp == -1:
        tex += r'''
    \HRule \\[0.5cm]
    {{ \Huge \bfseries {}}}\\[0.2cm]
    \HRule \\'''.format(first_day.strftime("%B %Y"))
    elif dtp > 1:
        tex += r'''
    \HRule \\[0.5cm]
    {{ \Huge \bfseries {}}}\\[0.2cm]
    \HRule \\'''.format(fmtdates(first_day,first_day+timedelta(days=dtp-1)))
    else:
        tex += r'''
    \HRule \\[0.5cm]
    {{ \Huge \bfseries {}}}\\[0.2cm]
    \HRule \\'''.format(fmtdate(first_day))

    tex += r'''
    \begin{center}\begin{tabular}[t]{rl}
    \large\emph{Author:} & \large Andrew \textsc{Bauer}\\
    \end{tabular}\end{center}'''

    tex += r'''
    {\large \today}
    \HRule \\[0.2cm]
    \end{center}
    \begin{description}[leftmargin=5.5em,style=nextline]\footnotesize
    \item[Disclaimer:] These are computer generated tables - use them at your own risk. They replicate Lunar Distance algorithms with no guarantee of accuracy. They are intended to encourage the use of sextants, be it as a hobby or as a backup when electronics fail. The author claims no liability for any consequences arising from use of these tables and accompanying charts.
    \end{description}
\end{titlepage}
\restoregeometry    % so it does not affect the rest of the pages'''

    tex += page2()

    return tex

def makeLDold(first_day, dtp, strat):
    # make tables starting from first_day
    # dtp = 0 if for entire year; = -1 if for entire month; else days to print

    # page size specific parameters
    if config.pgsz == "A4":
        # pay attention to the limited page width
        paper = "a4paper"
        vsep1 = "1.5cm"
        vsep2 = "1.0cm"
        tm1 = "21mm"    # title page...
        bm1 = "15mm"
        lm1 = "10mm"
        rm1 = "10mm"
        tm = "21mm"     # data pages...
        bm = "18mm"
        lm = "16mm"
        rm = "12mm"
    else:
        # pay attention to the limited page height
        paper = "letterpaper"
        vsep1 = "0.8cm"
        vsep2 = "0.7cm"
        tm1 = "12mm"    # title page...
        bm1 = "15mm"
        lm1 = "12mm"
        rm1 = "12mm"
        tm = "12mm"   # data pages...
        bm = "12mm"
        lm = "16mm"
        rm = "14mm"

    # default is 'oneside'...
    tex = r'''\documentclass[10pt, {}]{{report}}'''.format(paper)

    tex += r'''
%\usepackage[utf8]{inputenc}
\usepackage[english]{babel}
\usepackage{fontenc}
\usepackage{enumitem} % used to customize the {description} environment'''

    # to troubleshoot add "showframe, verbose," below:
    tex += r'''
\usepackage[nomarginpar, top={}, bottom={}, left={}, right={}]{{geometry}}'''.format(tm,bm,lm,rm)

    # Note: \DeclareUnicodeCharacter is not compatible with some versions of pdflatex
    tex += r'''
\usepackage{xcolor}  % highlight double moon events on same day
\definecolor{khaki}{rgb}{0.76, 0.69, 0.57}
\usepackage{multirow}
\newcommand{\HRule}{\rule{\linewidth}{0.5mm}}
\setlength{\footskip}{15pt}
\usepackage[pdftex]{graphicx}	% for \includegraphics
\usepackage{tikz}				% for \draw  (load after 'graphicx')
%\showboxbreadth=50  % use for logging
%\showboxdepth=50    % use for logging
%\DeclareUnicodeCharacter{00B0}{\ensuremath{{}^\circ}}
\setlength\fboxsep{1.5pt}       % ONLY used by \colorbox in ldist_skyfield.py
\begin{document}'''

    if not config.DPonly:
        tex += hdrEVold(first_day,dtp,tm1,bm1,lm1,rm1,vsep1,vsep2)

    tex += pages(first_day,dtp,strat)
    tex += r'''
\end{document}'''
    return tex