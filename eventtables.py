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

# NOTE: the new format statement requires a literal '{' to be entered as '{{',
#       and a literal '}' to be entered as '}}'. The old '%' format specifier
#       will be removed from Python at some later time. See:
# https://docs.python.org/3/whatsnew/3.0.html#pep-3101-a-new-approach-to-string-formatting

###### Standard library imports ######
# don't confuse the 'date' method with the 'Date' variable!
from datetime import date, datetime, timedelta
import sys			# required for .stdout.write()
import signal       # for init_worker

###### Local application imports ######
import config
if config.MULTIpr:      # in multi-processing mode ...
    # ------------------------------------------------------
    # EITHER comment next 2 lines out to invoke executor.map
    MPmode = 0
    import multiprocessing as mp
    #  *OR*  comment next 2 lines out to invoke pool.map
##    MPmode = 1
##    import concurrent.futures
    # ------------------------------------------------------
    # ! DO NOT PLACE imports IN CONDITIONAL 'if'-STATEMENTS WHEN MULTI-PROCESSING !
    from functools import partial
    # ... following is still required for SINGLE-PROCESSING (in multi-processing mode):
    from alma_skyfield import planetstransit, moonGHA, equation_of_time, getDUT1, find_new_moon
    # ... following is required for MULTI-PROCESSING:
    from mp_eventtables import mp_twilight, mp_moonrise_set, mp_planetstransit
else:
    # ... following is required for SINGLE-PROCESSING:
    from alma_skyfield import twilight, moonrise_set2, planetstransit, moonGHA, equation_of_time, getDUT1, find_new_moon


UpperLists = [[], []]    # moon GHA per hour for 2 days
LowerLists = [[], []]    # moon colong GHA per hour for 2 days
msg0 = "\nKeyboardInterrupt detected - multiprocessing aborted."

#------------------------
#   internal functions
#------------------------

def fmtdate(d):
    if config.pgsz == 'Letter': return d.strftime("%m/%d/%Y")
    return d.strftime("%d.%m.%Y")

def fmtdates(d1,d2):
    if config.pgsz == 'Letter': return d1.strftime("%m/%d/%Y") + " - " + d2.strftime("%m/%d/%Y")
    return d1.strftime("%d.%m.%Y") + " - " + d2.strftime("%d.%m.%Y")

def buildUPlists2(n, ghaSoD, ghaPerHour, ghaEoD):
    # build list of hourly GHA values with modified start and end time to
    #  account for rounding times to the second where 23:59:>59.5 rounds up
    #  00:00:00 the next day.
    UpperLists[n] = [-1.0 for x in range(25)]
    UpperLists[n][0] = ghaSoD
    for i in range(23):
        UpperLists[n][i+1] = ghaPerHour[i+1]
    UpperLists[n][24] = ghaEoD
    return

def buildLOWlists2(n, ghaSoD, ghaPerHour, ghaEoD):
    # build list of hourly GHA colong values with modified start and end
    #   time to account for rounding times to the minute where 23:59:>30
    #   rounds up 00:00 the next day.
    LowerLists[n] = [-1.0 for x in range(25)]
    LowerLists[n][0] = GHAcolong(ghaSoD)
    for i in range(23):
        LowerLists[n][i+1] = GHAcolong(ghaPerHour[i+1])
    LowerLists[n][24] = GHAcolong(ghaEoD)
    return

def GHAcolong(gha):
    # return the colongitude, e.g. 270° returns 90° and 90° returns 270°
    coGHA = gha + 180
    while coGHA > 360:
        coGHA = coGHA - 360
    return coGHA

def double_events_found(m1, m2):
    # check for two moonrise/moonset events on the same day & latitude
    dbl = False
    for i in range(len(m1)):
        if m2[i] != '--:--':
            dbl = True
    return dbl

def twilight_symbol(oldtwi):
    twi = []
    for event in oldtwi:
        if event == '--:--':
            twi.append('\mytwilightsymbol{1.0ex}')
        else: twi.append(event)
    return twi

# >>>>>>>>>>>>>>>>>>>>>>>>
def mp_twilight_worker(Date, ts, lat):
    #print(" mp_twilight_worker Start {}".format(lat))
    hemisph = 'N' if lat >= 0 else 'S'
    twi = mp_twilight(Date, lat, ts, True) # ===>>> mp_eventtables.py
    #print(" mp_twilight_worker Finish {}".format(lat))
    return twi      # return list for all latitudes

def mp_moonlight_worker(Date, ts, lat):
    #print(" mp_moonlight_worker Start  {}".format(lat))
    ml = mp_moonrise_set(Date, lat, ts)    # ===>>> mp_eventtables.py
    #print(" mp_moonlight_worker Finish {}".format(lat))
    return ml       # return list for all latitudes

def twilighttab(Date, ts):
    # returns the sun twilight and moonrise/moonset tables

    if config.MULTIpr:
        # multiprocess twilight values per latitude simultaneously
        if MPmode == 0:      # with pool.map
            partial_func = partial(mp_twilight_worker, Date, ts)

            try:
                # RECOMMENDED: chunksize = 1
                listoftwi = pool.map(partial_func, config.lat, 1)
            except KeyboardInterrupt:
                print(msg0)
                sys.exit(0)

        if MPmode == 1:      # with executor.map
            partial_func = partial(mp_twilight_worker, Date, ts)
            future_value = executor.map(partial_func, config.lat)
            listoftwi = list(future_value)

        for k in range(len(listoftwi)):
            config.stopwatch += listoftwi[k][6]     # accumulate multiprocess processing time
            del listoftwi[k][-1]
        #print("listoftwi = {}".format(listoftwi))

        # multiprocess moonrise/moonset values per latitude simultaneously
        if MPmode == 0:      # with pool.map
            partial_func2 = partial(mp_moonlight_worker, Date, ts)

            try:
                # RECOMMENDED: chunksize = 1
                listmoon = pool.map(partial_func2, config.lat, 1)
            except KeyboardInterrupt:
                print(msg0)
                sys.exit(0)

        if MPmode == 1:      # with executor.map
            partial_func2 = partial(mp_moonlight_worker, Date, ts)
            future_val = executor.map(partial_func2, config.lat)
            listmoon = list(future_val)

        for k in range(len(listmoon)):
            tuple_times = listmoon[k][-1]
            config.stopwatch  += tuple_times[0]         # accumulate multiprocess processing time
            config.stopwatch2 += tuple_times[1]         # accumulate multiprocess processing time
            del listmoon[k][-1]
        #print("listmoon = {}".format(listmoon))

# Sun Twilight tables ...........................................
    #lat = [72,70,68,66,64,62,60,58,56,54,52,50,45,40,35,30,20,10,0, -10,-20,-30,-35,-40,-45,-50,-52,-54,-56,-58,-60]
    latNS = [72, 70, 58, 40, 10, -10, -50, -60]
#    tab = r'''\begin{tabular*}{0.72\textwidth}[t]{@{\extracolsep{\fill}}|r|ccc|ccc|cc|}
    tab = r'''\begin{tabular}[t]{|r|ccc|ccc|cc|}
%%%\multicolumn{9}{c}{\normalsize{}}\\
'''

    ondate = Date.strftime("%d %B %Y")
    tab = tab + r'''\hline
\multicolumn{{9}}{{|c|}}{{\rule{{0pt}}{{2.4ex}}{{\textbf{{{}}}}}}}\\
'''.format(ondate)

    tab = tab + r'''\hline
\multicolumn{1}{|c|}{\rule{0pt}{2.4ex}\multirow{2}{*}{\textbf{Lat.}}} & 
\multicolumn{2}{c}{\textbf{Twilight}} & 
\multicolumn{1}{|c|}{\multirow{2}{*}{\textbf{Sunrise}}} & 
\multicolumn{1}{c|}{\multirow{2}{*}{\textbf{Sunset}}} & 
\multicolumn{2}{c|}{\textbf{Twilight}} & 
\multicolumn{1}{c|}{\multirow{2}{*}{\textbf{Moonrise}}} & 
\multicolumn{1}{c|}{\multirow{2}{*}{\textbf{Moonset}}}\\
\multicolumn{1}{|c|}{} & 
\multicolumn{1}{c}{Naut.} & 
\multicolumn{1}{c}{Civil} & 
\multicolumn{1}{|c|}{} & 
\multicolumn{1}{c|}{} & 
\multicolumn{1}{c}{Civil} & 
\multicolumn{1}{c|}{Naut.} & 
\multicolumn{1}{c|}{} & 
\multicolumn{1}{c|}{}\\
\hline\rule{0pt}{2.6ex}\noindent
'''
    lasthemisph = ""
    j = 5
    for lat in config.lat:
        hemisph = 'N' if lat >= 0 else 'S'
        hs = ""
        if (lat in latNS):
            hs = hemisph
            if j%6 == 0:
                tab = tab + r'''\rule{0pt}{2.6ex}
'''
        lasthemisph = hemisph

        if config.MULTIpr:
            twi = listoftwi[j-5]
            moon = listmoon[j-5][0]
            moon2 = listmoon[j-5][1]
        else:
            twi = twilight(Date, lat, hemisph, True)
            moon, moon2 = moonrise_set2(Date, lat)
        twi = twilight_symbol(twi)

        if not(double_events_found(moon,moon2)):
            line = r'''\textbf{{{}}}'''.format(hs) + r''' {}$^\circ$'''.format(abs(lat))
            line = line + r''' & {} & {} & {} & {} & {} & {} & {} & {} \\
'''.format(twi[0],twi[1],twi[2],twi[3],twi[4],twi[5],moon[0],moon[1])
        else:
            # print a row with two moonrise/moonset events on the same day & latitude
            line = r'''\multirow{{2}}{{*}}{{\textbf{{{}}} {}$^\circ$}}'''.format(hs,abs(lat))
            line = line + r''' & \multirow{{2}}{{*}}{{{}}}'''.format(twi[0])
            line = line + r''' & \multirow{{2}}{{*}}{{{}}}'''.format(twi[1])
            line = line + r''' & \multirow{{2}}{{*}}{{{}}}'''.format(twi[2])
            line = line + r''' & \multirow{{2}}{{*}}{{{}}}'''.format(twi[3])
            line = line + r''' & \multirow{{2}}{{*}}{{{}}}'''.format(twi[4])
            line = line + r''' & \multirow{{2}}{{*}}{{{}}}'''.format(twi[5])

# top row...
            for k in range(len(moon)):
                if moon2[k] != '--:--':
                    line = line + r''' & \colorbox{{khaki!45}}{{{}}}'''.format(moon[k])
                else:
                    line = line + r''' & \multirow{{2}}{{*}}{{{}}}'''.format(moon[k])
            line = line + r'''\\
'''	# terminate top row
# bottom row...
            line = line + r'''& & & & & & '''
            for k in range(len(moon)):
                if moon2[k] != '--:--':
                    line = line + r''' & \colorbox{{khaki!45}}{{{}}}'''.format(moon2[k])
                else:
                    line = line + r'''&'''
            line = line + r''' \\
'''	# terminate bottom row

        tab = tab + line
        j += 1
    # add space between tables...
    tab = tab + r'''\hline\multicolumn{9}{c}{}\\
'''
    tab = tab + r'''\end{tabular}
'''
    return tab

# >>>>>>>>>>>>>>>>>>>>>>>>
def mp_planets_worker(Date, ts, obj):
    #print(" mp_planets_worker Start  {}".format(obj))
    sha = mp_planetstransit(Date, ts, obj, True)    # ===>>> mp_eventtables.py
    #print(" mp_planets_worker Finish {}".format(obj))
    return sha      # return list for four planets

def meridiantab(Date, ts):
    # returns a table with ephemerides for the navigational stars
    # LaTeX SPACING: \enskip \quad \qquad

    if config.MULTIpr and config.WINpf and MPmode == 0:
        # multiprocess 'SHA + transit times' simultaneously
        objlist = ['venus', 'mars', 'jupiter', 'saturn']
        # set constant values to all arguments which are not changed during parallel processing
        partial_func2 = partial(mp_planets_worker, Date, ts)

        try:
            listofsha = pool.map(partial_func2, objlist, 1)     # RECOMMENDED: chunksize = 1
        except KeyboardInterrupt:
            print(msg0)
            sys.exit(0)

        for k in range(len(listofsha)):
            config.stopwatch += listofsha[k][2]     # accumulate multiprocess processing time
            del listofsha[k][-1]
        #print("listofsha = {}".format(listofsha))

    out = r'''\quad
\begin{tabular*}{0.25\textwidth}[t]{@{\extracolsep{\fill}}|rrr|}
%%%\multicolumn{3}{c}{\normalsize{}}\\
'''
    m = ""
    # returns a table with SHA & Mer.pass for Venus, Mars, Jupiter and Saturn
    datestr = r'''{} {}'''.format(Date.strftime("%b"), Date.strftime("%d"))
    m = m + r'''\hline
& & \multicolumn{{1}}{{r|}}{{}}\\[-2.0ex]
\textbf{{{}}} & \textbf{{SHA}} & \textbf{{Mer.pass}}\\
\hline\multicolumn{{3}}{{|r|}}{{}}\\[-2.0ex]
'''.format(datestr)

    if config.MULTIpr and config.WINpf and MPmode == 0:
        p = [item for sublist in listofsha for item in sublist]
    else:
        p = planetstransit(Date, True)

    m = m + r'''Venus & {} & {} \\
'''.format(p[0],p[1])
    m = m + r'''Mars & {} & {} \\
'''.format(p[2],p[3])
    m = m + r'''Jupiter & {} & {} \\
'''.format(p[4],p[5])
    m = m + r'''Saturn & {} & {} \\
'''.format(p[6],p[7])
    m = m + r'''\hline\multicolumn{3}{c}{}\\
'''
    out = out + m

    out = out + r'''\end{tabular*}
\par    % put next table below here
'''
    return out

# >>>>>>>>>>>>>>>>>>>>>>>>
def equationtab(Date, dpp):
    # returns the Equation of Time section for 'Date' and 'Date+1'

    d = Date
    # first create the UpperLists & LowerLists arrays ...
    nn = 0
    while nn < dpp:
        gham, decm, degm, HPm, GHAupper, GHAlower, ghaSoD, ghaEoD = moonGHA(d, True)

        buildUPlists2(nn, ghaSoD, GHAupper, ghaEoD)
        buildLOWlists2(nn, ghaSoD, GHAupper, ghaEoD)
        nn += 1
        d += timedelta(days=1)

    tab = r'''\begin{tabular}[t]{|r|ccc|ccc|}
%\multicolumn{7}{c}{\normalsize{}}\\
\cline{1-7}
\multicolumn{1}{|c|}{\rule{0pt}{2.4ex}\multirow{4}{*}{\textbf{Day}}} & 
\multicolumn{3}{c|}{\textbf{Sun}} & \multicolumn{3}{c|}{\textbf{Moon}}\\
\multicolumn{1}{|c|}{} & \multicolumn{2}{c}{Eqn.of Time} & \multicolumn{1}{|c|}{Mer.} & \multicolumn{2}{c}{Mer.Pass.} & \multicolumn{1}{|c|}{}\\
\multicolumn{1}{|c|}{} & \multicolumn{1}{c}{00\textsuperscript{h}} & \multicolumn{1}{c}{12\textsuperscript{h}} & \multicolumn{1}{|c|}{Pass} & \multicolumn{1}{c}{Upper} & \multicolumn{1}{c}{Lower} &\multicolumn{1}{|c|}{Age}\\
\multicolumn{1}{|c|}{} & \multicolumn{1}{c}{mm:ss} & \multicolumn{1}{c}{mm:ss} & \multicolumn{1}{|c|}{hh:mm:ss} & \multicolumn{1}{c}{hh:mm:ss} & \multicolumn{1}{c}{hh:mm:ss} &\multicolumn{1}{|c|}{}\\
\cline{1-7}\rule{0pt}{3.0ex}\noindent
'''

    d = Date
    for k in range(dpp):
        eq = equation_of_time(d,d + timedelta(days=1),UpperLists[k],LowerLists[k],True,True)
        tab = tab + r'''{} & {} & {} & {} & {} & {} & {}({}\%) \\
'''.format(d.strftime("%d"),eq[0],eq[1],eq[2],eq[3],eq[4],eq[5],eq[6])
        d += timedelta(days=1)

    tab = tab + r'''\cline{1-7}
\end{tabular}'''
    return tab

#----------------------
#   page preparation
#----------------------

def page(Date, ts, dpp):

    # time delta values for the initial date&time...
    dut1, deltat = getDUT1(Date)
    timeDUT1 = r"DUT1 = UT1-UTC = {:+.4f} sec\quad$\Delta$T = TT-UT1 = {:+.4f} sec".format(dut1, deltat)

    Lfoot_IERSEOP = ""
    if config.dt_IERSEOP != None:
        # the IERS EOP data start date is 2nd January 1973
        if Date + timedelta(days=1) >= date(1973, 1, 2):
            Lfoot_IERSEOP = config.txtIERSEOP
        if Date + timedelta(days=1) >= config.dt_IERSEOP:
            Lfoot_IERSEOP = config.endIERSEOP
        if Date > config.dt_IERSEOP:
            Lfoot_IERSEOP = r'''\textbf{No IERS EOP prediction data available}'''

    find_new_moon(Date)     # required for 'moonage' and 'equation_of_time"
    #leftindent = ""
    #rightindent = ""

    if dpp > 1:
        str2 = r'''\textbf{{{} to {} UT}}'''.format(Date.strftime("%Y %B %d"),(Date+timedelta(days=dpp-1)).strftime("%b. %d"))
    else:
        str2 = r'''\textbf{{{} UT}}'''.format(Date.strftime("%Y %B %d"))

    if config.FANCYhd:
        page = r'''
% ------------------ N E W   P A G E ------------------
\newpage
\sffamily
\lhead{{\textsf{{\footnotesize{{{}}}}}}}
\rhead{{\textsf{{\textbf{{{}}}}}}}
\lfoot{{\textsf{{\footnotesize{{{}}}}}}}
\begin{{scriptsize}}
'''.format(timeDUT1, str2, Lfoot_IERSEOP)
    else:   # old formatting
        page = r'''
% ------------------ N E W   P A G E ------------------
\newpage
\sffamily
\noindent
\begin{{flushleft}}     % required so that \par works
{{\footnotesize {}}}\hfill{}
\end{{flushleft}}\par
\begin{{scriptsize}}
'''.format(timeDUT1, str2)

    Date2 = Date+timedelta(days=1)
    page += twilighttab(Date,ts)
    page += meridiantab(Date,ts)
    if dpp == 2:
        page += twilighttab(Date2,ts)
        page += meridiantab(Date2,ts)
    page += equationtab(Date,dpp)

    # to avoid "Overfull \hbox" messages, leave a paragraph end before the end of a size change. (This may only apply to tabular* table style) See lines below...
    page = page + r'''

\end{scriptsize}'''
    return page

#   This simple but effective function eliminates endless keyboard interrupts
#   each time Ctrl-C is issued, while none actually kill the parent process
#   ... and this causes the Command Prompt window (in Windows, MPmode=0) to hang.
def init_worker():
    # Prevent child process from ever receiving a KeyboardInterrupt.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def pages(first_day, dtp, ts):
    # dtp = 0 if for entire year; = -1 if for entire month; else days to print

    if config.MULTIpr:
        # Windows & macOS defaults to "spawn"; Unix to "fork"
        #mp.set_start_method("spawn")
        n = config.CPUcores
        if n > 12: n = 12   # use 12 cores maximum
        if (config.WINpf or config.MACOSpf) and n > 8: n = 8   # 8 maximum if Windows or Mac OS
        if MPmode == 0:
            global pool
            pool = mp.Pool(n, init_worker)   # start 8 max. worker processes
        if MPmode == 1:
            global executor
            executor = concurrent.futures.ProcessPoolExecutor(max_workers=config.CPUcores,initializer=init_worker)

    out = ''
    pmth = ''
    dpp = 2         # 2 days per page maximum
    day1 = first_day

    if dtp == 0:        # if entire year
        year = first_day.year
        yr = year
        while year == yr:
            cmth = day1.strftime("%b ")
            day2 = day1 + timedelta(days=1)
            if day2.year != yr:
                dpp -= day2.day
                if dpp <= 0: return out
            if cmth != pmth:
                print() # progress indicator - next month
                #print(cmth, end='')
                sys.stdout.write(cmth)	# next month
                sys.stdout.flush()
                pmth = cmth
            else:
                sys.stdout.write('.')	# progress indicator
                sys.stdout.flush()
            out += page(day1,ts,dpp)
            day1 += timedelta(days=2)
            year = day1.year

    elif dtp == -1:     # if entire month
        mth = first_day.month
        m = mth
        while mth == m:
            cmth = day1.strftime("%b ")
            day2 = day1 + timedelta(days=1)
            if day2.month != m:
                dpp -= day2.day
                if dpp <= 0: return out
            if cmth != pmth:
                print() # progress indicator - next month
                #print(cmth, end='')
                sys.stdout.write(cmth)	# next month
                sys.stdout.flush()
                pmth = cmth
            else:
                sys.stdout.write('.')	# progress indicator
                sys.stdout.flush()
            out += page(day1,ts,dpp)
            day1 += timedelta(days=2)
            mth = day1.month

    else:           # print 'dtp' days beginning with first_day
        i = dtp   # don't decrement dtp
        while i > 0:
            if i < 2: dpp = i
            out += page(day1,ts,dpp)
            i -= 2
            day1 += timedelta(days=2)

    if dtp <= 0:       # if Event Time Tables for a whole month/year...
        print("\n")	    # 2 x newline to terminate progress indicator

    if config.MULTIpr:
        if MPmode == 0:
            pool.close()    # close all worker processes
            pool.join()
        if MPmode == 1:
            executor.shutdown()

    return out

#--------------------------
#   external entry point
#--------------------------

def makeEVtables(first_day, dtp, ts):
    # make tables starting from first_day
    # dtp = 0 if for entire year; = -1 if for entire month; else days to print

    if config.FANCYhd:
        return makeEVnew(first_day, dtp, ts) # use the 'fancyhdr' package
    else:
        return makeEVold(first_day, dtp, ts) # use old formatting

#   The following functions are intentionally separate functions.
#   'makeEVold' is required for TeX Live 2019, which is the standard
#   version in Ubuntu 20.04 LTS which expires in April 2030.

def hdrEVnew(first_day, dtp, vsep1, vsep2):
    # build the front page

    tex = r'''
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
    \textsc{{\huge Event Time Tables}}\\[{}]'''.format(vsep1,vsep2)

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
    \item[Disclaimer:] These are computer generated tables. They focus on times of rising and setting events and are rounded to the second (not primarily intended for navigation). Meridian Passage times of the sun, moon and four planets are included. All times are in UT (=UT1).
    The author claims no liability for any consequences arising from use of these tables.
    \end{description}
\end{titlepage}'''

    return tex

def makeEVnew(first_day, dtp, ts):
    # make tables starting from first_day
    # dtp = 0 if for entire year; = -1 if for entire month; else days to print

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
        # data pages...
        tm = "26.6mm"       # was "21mm" [v2q]
        bm = "18mm"         # was "18mm" [v2q]
        hs = "2.6pt"        # headsep  (page 3 onwards) [v2q]
        fs = "15pt"         # footskip (page 3 onwards) [v2q]
        lm = "16mm"
        rm = "16mm"
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
        # data pages...
        tm = "17.8mm"       # was "12.2mm" [v2q]
        bm = "17mm"         # was "13mm"
        hs = "2.6pt"        # headsep  (page 3 onwards) [v2q]
        fs = "15pt"         # footskip (page 3 onwards) [v2q]
        lm = "15mm"
        rm = "11mm"

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
\fancypagestyle{page2}[frontpage]{
  \fancyfootoffset[R]{0pt}% recalculate \headwidth
  \lfoot{\textsf{\footnotesize{https://thenauticalalmanac.com/}}}
  \cfoot{\centerline{Page \thepage}}
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
\setlength\fboxsep{1.5pt}       % ONLY used by \colorbox in alma_skyfield.py
\newcommand{\mytwilightsymbol}[1]{\tikz[baseline=-0.8ex]{
\draw[] (0.0,-0.9*#1) -- (0.6*#1,0.9*#1);
\draw[] (#1,-0.9*#1) -- (1.6*#1,0.9*#1);
\draw[] (2.0*#1,-0.9*#1) -- (2.6*#1,0.9*#1);
\draw[] (3.0*#1,-0.9*#1) -- (3.6*#1,0.9*#1);}}
\begin{document}
\pagestyle{frontpage}'''

    if not config.DPonly:
        tex += hdrEVnew(first_day,dtp,vsep1,vsep2)

    tex += r'''
\pagestyle{datapage}  % page style for data pages'''

    tex += pages(first_day,dtp,ts)
    tex += r'''
\end{document}'''
    return tex

# ===   ===   ===   ===   ===   ===   ===   ===   ===   ===   ===   ===   ===
# ===   ===   ===   ===   O L D   F O R M A T T I N G   ===   ===   ===   ===
# ===   ===   ===   ===   ===   ===   ===   ===   ===   ===   ===   ===   ===

def hdrEVold(first_day, dtp, tm1, bm1, lm1, rm1, vsep1, vsep2):
    # build the front page

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
    \textsc{{\huge Event Time Tables}}\\[{}]'''.format(vsep1,vsep2)

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
    \item[Disclaimer:] These are computer generated tables. They focus on times of rising and setting events and are rounded to the second (not primarily intended for navigation). Meridian Passage times of the sun, moon and four planets are included. All times are in UT (=UT1).
    The author claims no liability for any consequences arising from use of these tables.
    \end{description}
\end{titlepage}
\restoregeometry    % so it does not affect the rest of the pages'''

    return tex

def makeEVold(first_day, dtp, ts):
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
        rm = "16mm"
    else:
        # pay attention to the limited page height
        paper = "letterpaper"
        vsep1 = "0.8cm"
        vsep2 = "0.7cm"
        tm1 = "12mm"    # title page...
        bm1 = "15mm"
        lm1 = "12mm"
        rm1 = "12mm"
        tm = "12.2mm"   # data pages...
        bm = "13mm"
        lm = "15mm"
        rm = "11mm"

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
\setlength\fboxsep{1.5pt}       % ONLY used by \colorbox in alma_skyfield.py
\newcommand{\mytwilightsymbol}[1]{\tikz[baseline=-0.8ex]{
\draw[] (0.0,-0.9*#1) -- (0.6*#1,0.9*#1);
\draw[] (#1,-0.9*#1) -- (1.6*#1,0.9*#1);
\draw[] (2.0*#1,-0.9*#1) -- (2.6*#1,0.9*#1);
\draw[] (3.0*#1,-0.9*#1) -- (3.6*#1,0.9*#1);}}
\begin{document}'''

    if not config.DPonly:
        tex += hdrEVold(first_day,dtp,tm1,bm1,lm1,rm1,vsep1,vsep2)

    tex += pages(first_day,dtp,ts)
    tex += r'''
\end{document}'''
    return tex