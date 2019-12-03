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

import config
import datetime		# required for .timedelta()
import sys			# required for .stdout.write()
from alma_ephem import *
from alma_skyfield import *

UpperLists = [[], [], []]    # moon GHA per hour for 3 days
LowerLists = [[], [], []]    # moon colong GHA per hour for 3 days

def planetstab(date):
    # generates a LaTeX table for the navigational plantets (traditional style)
    tab = r'''\noindent
    \begin{tabular*}{0.75\textwidth}[t]{@{\extracolsep{\fill}}|c|r|rr|rr|rr|rr|}
    \multicolumn{1}{c}{\normalsize{}} & \multicolumn{1}{c}{\normalsize{Aries}} &  \multicolumn{2}{c}{\normalsize{Venus}}& \multicolumn{2}{c}{\normalsize{Mars}} & \multicolumn{2}{c}{\normalsize{Jupiter}} & \multicolumn{2}{c}{\normalsize{Saturn}}\\ 
'''
    n = 0
    while n < 3:
        tab = tab + r'''\hline
    \rule{0pt}{2.4ex}\textbf{%s} & \multicolumn{1}{c|}{\textbf{GHA}} & \multicolumn{1}{c}{\textbf{GHA}} & \multicolumn{1}{c|}{\textbf{Dec}} & \multicolumn{1}{c}{\textbf{GHA}} & \multicolumn{1}{c|}{\textbf{Dec}}& \multicolumn{1}{c}{\textbf{GHA}} & \multicolumn{1}{c|}{\textbf{Dec}}& \multicolumn{1}{c}{\textbf{GHA}} & \multicolumn{1}{c|}{\textbf{Dec}} \\ 
    \hline\rule{0pt}{2.6ex}\noindent
''' %(date.strftime("%a"))
        aGHA             = ariesGHA(date)
        vGHA, vDEC, vDEG = venusGHA(date)
        mGHA, mDEC, mDEG = marsGHA(date)
        jGHA, jDEC, jDEG = jupiterGHA(date)
        sGHA, sDEC, sDEG = saturnGHA(date)
        h = 0

        if config.decf != '+':	# USNO format for Declination
            while h < 24:
                if h > 0:
                    prevDECv = vDEG[h-1]
                    prevDECm = mDEG[h-1]
                    prevDECj = jDEG[h-1]
                    prevDECs = sDEG[h-1]
                else:
                    prevDECv = vDEG[0]		# hour -1 = hour 0
                    prevDECm = mDEG[0]		# hour -1 = hour 0
                    prevDECj = jDEG[0]		# hour -1 = hour 0
                    prevDECs = sDEG[0]		# hour -1 = hour 0
                if h < 23:
                    nextDECv = vDEG[h+1]
                    nextDECm = mDEG[h+1]
                    nextDECj = jDEG[h+1]
                    nextDECs = sDEG[h+1]
                else:
                    nextDECv = vDEG[23]	    # hour 24 = hour 23
                    nextDECm = mDEG[23]	    # hour 24 = hour 23
                    nextDECj = jDEG[23]	    # hour 24 = hour 23
                    nextDECs = sDEG[23]	    # hour 24 = hour 23

                # format declination checking for hemisphere change
                printNS, printDEG = declCompare(prevDECv,vDEG[h],nextDECv,h)
                vdec = NSdecl(vDEC[h],h,printNS,printDEG,False)

                printNS, printDEG = declCompare(prevDECm,mDEG[h],nextDECm,h)
                mdec = NSdecl(mDEC[h],h,printNS,printDEG,False)

                printNS, printDEG = declCompare(prevDECj,jDEG[h],nextDECj,h)
                jdec = NSdecl(jDEC[h],h,printNS,printDEG,False)

                printNS, printDEG = declCompare(prevDECs,sDEG[h],nextDECs,h)
                sdec = NSdecl(sDEC[h],h,printNS,printDEG,False)

                line = u"%s & %s & %s & %s & %s & %s & %s & %s & %s & %s" %(h,aGHA[h],vGHA[h],vdec,mGHA[h],mdec,jGHA[h],jdec,sGHA[h],sdec)
                lineterminator = u"\\\ \n"
                if h < 23 and (h+1)%6 == 0:
                    lineterminator = u"\\\[2Pt] \n"
                tab = tab + line + lineterminator
                h += 1

        else:			# Positive/Negative Declinations
            while h < 24:
                line = u"%s & %s & %s & %s & %s & %s & %s & %s & %s & %s" %(h,aGHA[h],vGHA[h],vDEC[h],mGHA[h],mDEC[h],jGHA[h],jDEC[h],sGHA[h],sDEC[h])
                lineterminator = u"\\\ \n"
                if h < 23 and (h+1)%6 == 0:
                    lineterminator = u"\\\[2Pt] \n"
                tab = tab + line + lineterminator
                h += 1

        RAc_v, Dc_v = vdm_Venus(date)
        RAc_m, Dc_m = vdm_Mars(date)
        RAc_j, Dc_j = vdm_Jupiter(date)
        RAc_s, Dc_s = vdm_Saturn(date)
        mag_v, mag_m, mag_j, mag_s = magnitudes(date)
        tab = tab + r"""\hline 
        \multicolumn{2}{|c|}{\rule{0pt}{2.4ex}Mer.pass.:%s} &  \multicolumn{2}{c|}{v%s d%s m%s}& \multicolumn{2}{c|}{v%s d%s m%s} & \multicolumn{2}{c|}{v%s d%s m%s} & \multicolumn{2}{c|}{v%s d%s m%s}\\ 
        \hline
        \multicolumn{10}{c}{}\\
""" %(ariestransit(date+datetime.timedelta(days=1)),RAc_v,Dc_v,mag_v,RAc_m,Dc_m,mag_m,RAc_j,Dc_j,mag_j,RAc_s,Dc_s,mag_s)
        n += 1
        date += datetime.timedelta(days=1)
    tab = tab + r"""\end{tabular*}
"""
    return tab

def planetstabm(date):
    # generates a LaTeX table for the navigational plantets (modern style)
    tab = r'''\vspace{6Pt}\noindent
    \renewcommand{\arraystretch}{1.1}
    \setlength{\tabcolsep}{4pt}
    \begin{tabular}[t]{@{}crcrrcrrcrrcrr@{}}
    \multicolumn{1}{c}{\normalsize{h}} & 
    \multicolumn{1}{c}{\normalsize{Aries}} & & 
    \multicolumn{2}{c}{\normalsize{Venus}}& & 
    \multicolumn{2}{c}{\normalsize{Mars}} & & 
    \multicolumn{2}{c}{\normalsize{Jupiter}} & & 
    \multicolumn{2}{c}{\normalsize{Saturn}}\\ 
    \cmidrule{2-2} \cmidrule{4-5} \cmidrule{7-8} \cmidrule{10-11} \cmidrule{13-14}
'''
    n = 0
    while n < 3:
        tab = tab + r'''
    \multicolumn{1}{c}{\textbf{%s}} & \multicolumn{1}{c}{\textbf{GHA}} && 
    \multicolumn{1}{c}{\textbf{GHA}} & \multicolumn{1}{c}{\textbf{Dec}} &&  \multicolumn{1}{c}{\textbf{GHA}} & \multicolumn{1}{c}{\textbf{Dec}} &&  \multicolumn{1}{c}{\textbf{GHA}} & \multicolumn{1}{c}{\textbf{Dec}} &&  \multicolumn{1}{c}{\textbf{GHA}} & \multicolumn{1}{c}{\textbf{Dec}} \\
''' %(date.strftime("%a"))
        aGHA             = ariesGHA(date)
        vGHA, vDEC, vDEG = venusGHA(date)
        mGHA, mDEC, mDEG = marsGHA(date)
        jGHA, jDEC, jDEG = jupiterGHA(date)
        sGHA, sDEC, sDEG = saturnGHA(date)

        h = 0

        if config.decf != '+':	# USNO format for Declination
            while h < 24:
                band = int(h/6)
                group = band % 2
                if h > 0:
                    prevDECv = vDEG[h-1]
                    prevDECm = mDEG[h-1]
                    prevDECj = jDEG[h-1]
                    prevDECs = sDEG[h-1]
                else:
                    prevDECv = vDEG[0]		# hour -1 = hour 0
                    prevDECm = mDEG[0]		# hour -1 = hour 0
                    prevDECj = jDEG[0]		# hour -1 = hour 0
                    prevDECs = sDEG[0]		# hour -1 = hour 0
                if h < 23:
                    nextDECv = vDEG[h+1]
                    nextDECm = mDEG[h+1]
                    nextDECj = jDEG[h+1]
                    nextDECs = sDEG[h+1]
                else:
                    nextDECv = vDEG[23]	    # hour 24 = hour 23
                    nextDECm = mDEG[23]	    # hour 24 = hour 23
                    nextDECj = jDEG[23]	    # hour 24 = hour 23
                    nextDECs = sDEG[23]	    # hour 24 = hour 23

                # format declination checking for hemisphere change
                printNS, printDEG = declCompare(prevDECv,vDEG[h],nextDECv,h)
                vdec = NSdecl(vDEC[h],h,printNS,printDEG,True)

                printNS, printDEG = declCompare(prevDECm,mDEG[h],nextDECm,h)
                mdec = NSdecl(mDEC[h],h,printNS,printDEG,True)

                printNS, printDEG = declCompare(prevDECj,jDEG[h],nextDECj,h)
                jdec = NSdecl(jDEC[h],h,printNS,printDEG,True)

                printNS, printDEG = declCompare(prevDECs,sDEG[h],nextDECs,h)
                sdec = NSdecl(sDEC[h],h,printNS,printDEG,True)

                line = r'''\color{blue} {%s} & 
''' %(h)
                line = line + u"%s && %s & %s && %s & %s && %s & %s && %s & %s\\\ \n" %(aGHA[h],vGHA[h],vdec,mGHA[h],mdec,jGHA[h],jdec,sGHA[h],sdec)
                if group == 1:
                    tab = tab + r'''\rowcolor{LightCyan}
'''
                tab = tab + line
                h += 1

        else:			# Positive/Negative Declinations
            while h < 24:
                band = int(h/6)
                group = band % 2
                line = r'''\color{blue} {%s} & 
''' %(h)
                line = line + u"%s && %s & %s && %s & %s && %s & %s && %s & %s\\\ \n" %(aGHA[h],vGHA[h],vDEC[h],mGHA[h],mDEC[h],jGHA[h],jDEC[h],sGHA[h],sDEC[h])
                if group == 1:
                    tab = tab + r'''\rowcolor{LightCyan}
'''
                tab = tab + line
                h += 1

        RAc_v, Dc_v = vdm_Venus(date)
        RAc_m, Dc_m = vdm_Mars(date)
        RAc_j, Dc_j = vdm_Jupiter(date)
        RAc_s, Dc_s = vdm_Saturn(date)
        mag_v, mag_m, mag_j, mag_s = magnitudes(date)
        tab = tab + r"""\cmidrule{1-2} \cmidrule{4-5} \cmidrule{7-8} \cmidrule{10-11} \cmidrule{13-14} 
        \multicolumn{2}{c}{\footnotesize{Mer.pass.:%s}} && 
        \multicolumn{2}{c}{\footnotesize{v%s d%s m%s}} && 
        \multicolumn{2}{c}{\footnotesize{v%s d%s m%s}} && 
        \multicolumn{2}{c}{\footnotesize{v%s d%s m%s}} && 
        \multicolumn{2}{c}{\footnotesize{v%s d%s m%s}}\\ 
        \cmidrule{1-2} \cmidrule{4-5} \cmidrule{7-8} \cmidrule{10-11} \cmidrule{13-14}
""" %(ariestransit(date+datetime.timedelta(days=1)),RAc_v,Dc_v,mag_v,RAc_m,Dc_m,mag_m,RAc_j,Dc_j,mag_j,RAc_s,Dc_s,mag_s)
        if n < 2:
            tab = tab + r"""\multicolumn{10}{c}{}\\
"""
        n += 1
        date += datetime.timedelta(days=1)

    tab = tab+r"""
    \end{tabular}
    \quad"""
    return tab


def starstab(date):
    # returns a table with ephemerieds for the navigational stars
    out = r"""\begin{tabular*}{0.25\textwidth}[t]{@{\extracolsep{\fill}}|rrr|}
    \multicolumn{3}{c}{\normalsize{Stars}}  \\ 
"""
    if config.tbls == "m":
        out = out + r"""\hline
        & \multicolumn{1}{c}{\multirow{2}{*}{\textbf{SHA}}} 
        & \multicolumn{1}{c|}{\multirow{2}{*}{\textbf{Dec}}} \\
        & & \multicolumn{1}{c|}{} \\
"""
    else:
        out = out + r"""\hline
        \rule{0pt}{2.4ex} & \multicolumn{1}{c}{\textbf{SHA}} & \multicolumn{1}{c|}{\textbf{Dec}} \\ 
        \hline\rule{0pt}{2.6ex}\noindent
"""
    stars = stellar_info(date+datetime.timedelta(days=1))
    for i in range(len(stars)):
        out = out + r"""%s & %s & %s \\""" %(stars[i][0],stars[i][1],stars[i][2])
        out = out + u'\n'
    m = u'\\hline\n'

    # returns 3 tables with SHA & Mer.pass for Venus, Mars, Jupiter and Saturn
    for i in range(3):
        datestr = r"""\rule{0pt}{2.6ex}%s %s %s""" %(date.strftime("%b"), (date+datetime.timedelta(days=i)).strftime("%d"), (date+datetime.timedelta(days=i)).strftime("%a"))
        m = m + u'\\hline \n'
        if config.tbls == "m":
            m = m + """\multicolumn{1}{|r}{\multirow{2}{*}{\\textbf{%s}}} 
            & \multicolumn{1}{c}{\multirow{2}{*}{\\textbf{SHA}}} 
            & \multicolumn{1}{r|}{\multirow{2}{*}{\\textbf{Mer.pass}}} \\\\
            & & \multicolumn{1}{r|}{} \\\ \n""" %datestr
        else:
            m = m + (u" \\textbf{%s} & \\textbf{SHA} & \\textbf{Mer.pass} \\\ \n" %datestr)
        datex = date + datetime.timedelta(days=i)
        p = planetstransit(datex)
        m = m + u'Venus & %s & %s \\\ \n' %(p[0],p[1])
        m = m + u'Mars & %s & %s \\\ \n' %(p[2],p[3])
        m = m + u'Jupiter & %s & %s \\\ \n' %(p[4],p[5])
        m = m + u'Saturn & %s & %s \\\ \n' %(p[6],p[7])
        m = m + u'\\hline \n'
    out = out + m

    # returns a table with Horizontal parallax for Venus and Mars
    hp = u'\\hline \n'
    hp = hp + u'\multicolumn{2}{|r}{\\rule{0pt}{2.6ex}\\textbf{Horizontal parallax}} & \multicolumn{1}{c|}{}\\\ \n'
    hp = hp + u'\multicolumn{2}{|r}{Venus:} & \multicolumn{1}{c|}{%s} \\\ \n' %(p[9])
    hp = hp + u'\multicolumn{2}{|r}{Mars:} & \multicolumn{1}{c|}{%s} \\\ \n' %(p[8])
    hp = hp + u'\\hline \n'
    out = out + hp
    
    out = out + r'\end{tabular*}'
    return out


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

def buildLOWlists(n, ghaSoD, ghaPerHour, ghaEoD):
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

def sunmoontab(date):
    # generates LaTeX table for sun and moon (traditional style)
    tab = r'''\noindent
    \begin{tabular*}{0.55\textwidth}[t]{@{\extracolsep{\fill}}|c|rr|rrrrr|}
    \multicolumn{1}{c}{\normalsize{h}}& \multicolumn{2}{c}{\normalsize{Sun}} & \multicolumn{5}{c}{\normalsize{Moon}} \\ 
'''
    n = 0
    while n < 3:
        tab = tab + r'''\hline
    \multicolumn{1}{|c|}{\rule{0pt}{2.6ex}\textbf{%s}} &\multicolumn{1}{c}{\textbf{GHA}} & \multicolumn{1}{c|}{\textbf{Dec}}  & \multicolumn{1}{c}{\textbf{GHA}} & \multicolumn{1}{c}{\textbf{\(\nu\)}} & \multicolumn{1}{c}{\textbf{Dec}} & \multicolumn{1}{c}{\textbf{d}} & \multicolumn{1}{c|}{\textbf{HP}} \\ 
    \hline\rule{0pt}{2.6ex}\noindent
''' %(date.strftime("%a"))

        date0 = date - datetime.timedelta(days=1)
        ghas, decs, degs = sunGHA(date)
        gham, decm, degm, HPm, GHAupper, GHAlower, ghaSoD, ghaEoD = moonGHA(date)
        vmin, dmin = moonVD(date0,date)

        buildUPlists(n, ghaSoD, GHAupper, ghaEoD)
        buildLOWlists(n, ghaSoD, GHAupper, ghaEoD)

        h = 0
        if config.decf != '+':	# USNO format for Declination
            mlastNS = ''
            while h < 24:
                if h > 0:
                    prevDEC = degs[h-1]
                else:
                    prevDEC = degs[0]		# hour -1 = hour 0
                if h < 23:
                    nextDEC = degs[h+1]
                else:
                    nextDEC = degs[23]	# hour 24 = hour 23
                
                # format declination checking for hemisphere change
                printNS, printDEG = declCompare(prevDEC,degs[h],nextDEC,h)
                sdec = NSdecl(decs[h],h,printNS,printDEG,False)

                mdec, mNS = NSdeg(decm[h],False,h)
                if h < 23:
                    if mNS != mlastNS or math.copysign(1.0,degm[h]) != math.copysign(1.0,degm[h+1]):
                        mdec, mNS = NSdeg(decm[h],False,h,True)	# force N/S
                mlastNS = mNS

                line = u"%s & %s & %s & %s & %s & %s & %s & %s" %(h,ghas[h],sdec,gham[h],vmin[h],mdec,dmin[h],HPm[h])
                lineterminator = u"\\\ \n"
                if h < 23 and (h+1)%6 == 0:
                    lineterminator = u"\\\[2Pt] \n"
                tab = tab + line + lineterminator
                h += 1

        else:			# Positive/Negative Declinations
            while h < 24:
                line = u"%s & %s & %s & %s & %s & %s & %s & %s" %(h,ghas[h],decs[h],gham[h],vmin[h],decm[h],dmin[h],HPm[h])
                lineterminator = u"\\\ \n"
                if h < 23 and (h+1)%6 == 0:
                    lineterminator = u"\\\[2Pt] \n"
                tab = tab + line + lineterminator
                h += 1
                
        sds, dsm = sunSD(date)
        sdmm = moonSD(date)
        tab = tab + r"""\hline
    \rule{0pt}{2.4ex} & \multicolumn{1}{c}{SD.=%s} & \multicolumn{1}{c|}{d=%s} & \multicolumn{5}{c|}{S.D.=%s} \\
    \hline
""" %(sds,dsm,sdmm)
        if n < 2:
            # add space between tables...
            tab = tab + r"""\multicolumn{7}{c}{}\\[-1.5ex]"""
        n += 1
        date += datetime.timedelta(days=1)
    tab = tab + r"""\end{tabular*}"""
    return tab


def sunmoontabm(date):
    # generates LaTeX table for sun and moon (modern style)
    tab = r'''\noindent
    \renewcommand{\arraystretch}{1.1}
    \setlength{\tabcolsep}{4pt}
    \quad\quad
    \begin{tabular}[t]{@{}crrcrrrrr@{}}
    \multicolumn{1}{c}{\normalsize{h}} & 
    \multicolumn{2}{c}{\normalsize{Sun}} & &
    \multicolumn{5}{c}{\normalsize{Moon}} \\ 
    \cmidrule{2-3} \cmidrule{5-9}
'''
    # note: \quad\quad above shifts all tables to the right (still within margins)
    n = 0
    while n < 3:
        tab = tab + r'''
    \multicolumn{1}{c}{\textbf{%s}} & \multicolumn{1}{c}{\textbf{GHA}} & \multicolumn{1}{c}{\textbf{Dec}} & & \multicolumn{1}{c}{\textbf{GHA}} & \multicolumn{1}{c}{\textbf{\(\nu\)}} & \multicolumn{1}{c}{\textbf{Dec}} & \multicolumn{1}{c}{\textbf{d}} & \multicolumn{1}{c}{\textbf{HP}} \\ 
''' %(date.strftime("%a"))

        date0 = date - datetime.timedelta(days=1)
        ghas, decs, degs = sunGHA(date)
        gham, decm, degm, HPm, GHAupper, GHAlower, ghaSoD, ghaEoD = moonGHA(date)
        vmin, dmin = moonVD(date0,date)

        buildUPlists(n, ghaSoD, GHAupper, ghaEoD)
        buildLOWlists(n, ghaSoD, GHAupper, ghaEoD)

        h = 0
        if config.decf != '+':	# USNO format for Declination
            mlastNS = ''
            while h < 24:
                band = int(h/6)
                group = band % 2
                if h > 0:
                    prevDEC = degs[h-1]
                else:
                    prevDEC = degs[0]		# hour -1 = hour 0
                if h < 23:
                    nextDEC = degs[h+1]
                else:
                    nextDEC = degs[23]	# hour 24 = hour 23
                
                # format declination checking for hemisphere change
                printNS, printDEG = declCompare(prevDEC,degs[h],nextDEC,h)
                sdec = NSdecl(decs[h],h,printNS,printDEG,True)

                mdec, mNS = NSdeg(decm[h],True,h)
                if h < 23:
                    if mNS != mlastNS or math.copysign(1.0,degm[h]) != math.copysign(1.0,degm[h+1]):
                        mdec, mNS = NSdeg(decm[h],True,h,True)	# force NS
                mlastNS = mNS

                line = r'''\color{blue} {%s} & 
''' %(h)
                line = line + u"%s & %s && %s & %s & %s & %s & %s \\\ \n" %(ghas[h],sdec,gham[h],vmin[h],mdec,dmin[h],HPm[h])

                if group == 1:
                    tab = tab + r'''\rowcolor{LightCyan}
'''
                tab = tab + line
                h += 1

        else:			# Positive/Negative Declinations
            while h < 24:
                band = int(h/6)
                group = band % 2
                line = r'''\color{blue} {%s} & 
''' %(h)
                line = line + u"%s & %s && %s & %s & %s & %s & %s \\\ \n" %(ghas[h],decs[h],gham[h],vmin[h],decm[h],dmin[h],HPm[h])
                if group == 1:
                    tab = tab + r'''\rowcolor{LightCyan}
'''
                tab = tab + line
                h += 1

        sds, dsm = sunSD(date)
        sdmm = moonSD(date)
        tab = tab + r"""\cmidrule{2-3} \cmidrule{5-9}
        \multicolumn{1}{c}{} & \multicolumn{1}{c}{\footnotesize{SD.=%s}} & 
        \multicolumn{1}{c}{\footnotesize{d=%s}} && \multicolumn{5}{c}{\footnotesize{S.D.=%s}} \\
        \cmidrule{2-3} \cmidrule{5-9}
""" %(sds,dsm,sdmm)
        if n < 2:
            # add space between tables...
            tab = tab + r"""\multicolumn{7}{c}{}\\[-1.5ex]
"""
        n += 1
        date += datetime.timedelta(days=1)
    tab = tab + r"""
    \end{tabular}
    \quad\quad"""
    return tab

##NEW##
def declCompare(prev_deg, curr_deg, next_deg, hr):
    # for Declinations only...
    # decide if to print N/S; decide if to print degrees
    # note: the first three arguments are declinations in degrees (float)
    prNS = False
    prDEG = False
    psign = math.copysign(1.0,prev_deg)
    csign = math.copysign(1.0,curr_deg)
    nsign = math.copysign(1.0,next_deg)
    pdeg = abs(prev_deg)
    cdeg = abs(curr_deg)
    ndeg = abs(next_deg)
    pdegi = int(pdeg)
    cdegi = int(cdeg)
    ndegi = int(ndeg)
    pmin = round((pdeg-pdegi)*60, 1)	# minutes (float), rounded to 1 decimal place
    cmin = round((cdeg-cdegi)*60, 1)	# minutes (float), rounded to 1 decimal place
    nmin = round((ndeg-ndegi)*60, 1)	# minutes (float), rounded to 1 decimal place
    pmini = int(pmin)
    cmini = int(cmin)
    nmini = int(nmin)
    if pmini == 60:
        pmin -= 60
        pdegi += 1
    if cmini == 60:
        cmin -= 60
        cdegi += 1
    if nmini == 60:
        nmin -= 60
        ndegi += 1
    # now we have the values in degrees+minutes as printed

    if hr%6 == 0:
        prNS = True			# print N/S for hour = 0, 6, 12, 18
    else:
        if psign != csign:
            prNS = True		# print N/S if previous sign different
    if hr < 23:
        if csign != nsign:
            prNS = True		# print N/S if next sign different
    if prNS == False:
        if pdegi != cdegi:
            prDEG = True	# print degrees if changed since previous value
        if cdegi != ndegi:
            prDEG = True	# print degrees if next value is changed
    else:
        prDEG= True			# print degrees is N/S to be printed
    return prNS, prDEG

##NEW##
def NSdecl(deg, hr, printNS, printDEG, modernFMT):
    # reformat degrees latitude to Ndd°mm.m or Sdd°mm.m
    if deg[0:1] == '-':
        hemisph = u'S'
        deg = deg[1:]
    else:
        hemisph = u'N'
    if not(printDEG):
        deg = deg[3:]	# skip the degrees (always dd°mm.m)
        if (hr+3)%6 == 0:
            deg = r'''\raisebox{0.24ex}{\boldmath$\cdot$~\boldmath$\cdot$~~}''' + deg
    if modernFMT:
        if printNS or hr%6 == 0:
            sdeg = u"\\textcolor{blue}{%s}" %hemisph + deg
        else:
            sdeg = deg
    else:
        if printNS or hr%6 == 0:
            sdeg = u"\\textbf{%s}" %hemisph + deg
        else:
            sdeg = deg
    #print("sdeg: ", sdeg)
    return sdeg


def NSdeg(deg, modern=False, hr=0, forceNS=False):
    # reformat degrees latitude to Ndd°mm.m or Sdd°mm.m
    if deg[0:1] == '-':
        hemisph = u'S'
        deg = deg[1:]
    else:
        hemisph = u'N'
    if modern:
        if forceNS or hr%6 == 0:
            sdeg = u"\\textcolor{blue}{%s}" %hemisph + deg
        else:
            sdeg = deg
    else:
        if forceNS or hr%6 == 0:
            sdeg = u"\\textbf{%s}" %hemisph + deg
        else:
            sdeg = deg
    return sdeg, hemisph


def twilighttab(date):
    # returns the twilight and moonrise tables, finally EoT data

# Twilight tables ...........................................
    #lat = [72,70,68,66,64,62,60,58,56,54,52,50,45,40,35,30,20,10,0, -10,-20,-30,-35,-40,-45,-50,-52,-54,-56,-58,-60]
    latNS = [72, 70, 58, 40, 10, -10, -50, -60]
    tab = r'''\begin{tabular*}{0.45\textwidth}[t]{@{\extracolsep{\fill}}|r|ccc|ccc|}
    \multicolumn{7}{c}{\normalsize{}} \\'''

    if config.tbls == "m":
    # The header begins with a thin empty row as top padding; and the top row with
    # bold text has some padding below it. This result gives a balanced impression.
        tab = tab + r"""\hline
    \multicolumn{1}{|c|}{} & & & \multicolumn{1}{|c|}{} & \multicolumn{1}{c|}{} & & \multicolumn{1}{c|}{}\\[-2.0ex]

    \multicolumn{1}{|c|}{\multirow{2}{*}{\textbf{Lat.}}} & 
    \multicolumn{2}{c}{\multirow{1}{*}{\footnotesize{\textbf{Twilight}}}} & 
    \multicolumn{1}{|c|}{\multirow{2}{*}{\textbf{Sunrise}}} & 
    \multicolumn{1}{c|}{\multirow{2}{*}{\textbf{Sunset}}} & 
    \multicolumn{2}{c|}{\multirow{1}{*}{\footnotesize{\textbf{Twilight}}}} \\[0.6ex] 

    \multicolumn{1}{|c|}{} & 
    \multicolumn{1}{c}{Naut.} & 
    \multicolumn{1}{c}{Civil} & 
    \multicolumn{1}{|c|}{} & 
    \multicolumn{1}{c|}{} & 
    \multicolumn{1}{c}{Civil} & 
    \multicolumn{1}{c|}{Naut.}\\ 
    \hline\rule{0pt}{2.6ex}\noindent
"""
    else:
        tab = tab + r"""\hline
    \multicolumn{1}{|c|}{\rule{0pt}{2.4ex}\multirow{2}{*}{\textbf{Lat.}}} & 
    \multicolumn{2}{c}{\textbf{Twilight}} & 
    \multicolumn{1}{|c|}{\multirow{2}{*}{\textbf{Sunrise}}} & 
    \multicolumn{1}{c|}{\multirow{2}{*}{\textbf{Sunset}}} & 
    \multicolumn{2}{c|}{\textbf{Twilight}} \\ 

    \multicolumn{1}{|c|}{} & 
    \multicolumn{1}{c}{Naut.} & 
    \multicolumn{1}{c}{Civil} & 
	\multicolumn{1}{|c|}{} & 
	\multicolumn{1}{c|}{} &
    \multicolumn{1}{c}{Civil} & 
    \multicolumn{1}{c|}{Naut.}\\ 
    \hline\rule{0pt}{2.6ex}\noindent
"""
    lasthemisph = ""
    j = 5
    for i in config.lat:
        if i >= 0:
            hemisph = u'N'
        else:
            hemisph = u'S'
        if not(i in latNS):
            hs = ""
        else:
            hs = hemisph
            if j%6 == 0:
                tab = tab + r"""\rule{0pt}{2.6ex}
"""
        lasthemisph = hemisph
        # day+1 to calculate for the second day (three days are printed on one page)
        twi = twilight(date+datetime.timedelta(days=1), i)
        line = u"\\textbf{%s}" % hs + " " + "%s°" %(abs(i))
        line = line + u" & %s & %s & %s & %s & %s & %s \\\ \n" %(twi[0],twi[1],twi[2],twi[3],twi[4],twi[5])
        tab = tab + line
        j += 1
    # add space between tables...
    tab = tab + r"""\hline\multicolumn{7}{c}{}\\[-1.5ex]"""

# Moonrise & Moonset ...........................................
    if config.tbls == "m":
        tab = tab + r"""\hline
    \multicolumn{1}{|c|}{} & & & \multicolumn{1}{c|}{} & & & \multicolumn{1}{c|}{}\\[-2.0ex] 

    \multicolumn{1}{|c|}{\multirow{2}{*}{\textbf{Lat.}}} & 
    \multicolumn{3}{c|}{\multirow{1}{*}{\footnotesize{\textbf{Moonrise}}}} & 
    \multicolumn{3}{c|}{\multirow{1}{*}{\footnotesize{\textbf{Moonset}}}} \\[0.6ex] 
"""
    else:
        tab = tab + r"""\hline
    \multicolumn{1}{|c|}{\rule{0pt}{2.4ex}\multirow{2}{*}{\textbf{Lat.}}} & 
    \multicolumn{3}{c|}{\textbf{Moonrise}} & 
    \multicolumn{3}{c|}{\textbf{Moonset}} \\ 
"""

    weekday = [date.strftime("%a"),(date+datetime.timedelta(days=1)).strftime("%a"),(date+datetime.timedelta(days=2)).strftime("%a")]
    tab = tab + r"""\multicolumn{1}{|c|}{} & 
    \multicolumn{1}{c}{%s} & 
    \multicolumn{1}{c}{%s} & 
    \multicolumn{1}{c|}{%s} & 
    \multicolumn{1}{c}{%s} & 
    \multicolumn{1}{c}{%s} & 
    \multicolumn{1}{c|}{%s} \\ 
    \hline\rule{0pt}{2.6ex}\noindent
""" %(weekday[0],weekday[1],weekday[2],weekday[0],weekday[1],weekday[2])

    moon = [0,0,0,0,0,0]
    moon2 = [0,0,0,0,0,0]
    lasthemisph = ""
    j = 5
    for i in config.lat:
        if i >= 0:
            hemisph = u'N'
        else:
            hemisph = u'S'
        if not(i in latNS):
            hs = ""
        else:
            hs = hemisph
            if j%6 == 0:
                tab = tab + r"""\rule{0pt}{2.6ex}
"""
        lasthemisph = hemisph
        moon, moon2 = moonrise_set(date, i)
        if not(double_events_found(moon,moon2)):
            tab = tab + u"\\textbf{%s}" % hs + " " + "%s°" %(abs(i))
            tab = tab + u" & %s & %s & %s & %s & %s & %s \\\ \n" %(moon[0],moon[1],moon[2],moon[3],moon[4],moon[5])
        else:
# print a row with two moonrise/moonset events on the same day & latitude
            tab = tab + r"""\multirow{2}{*}{\textbf{%s} %s°}""" %(hs,abs(i))
# top row...
            for k in range(len(moon)):
                if moon2[k] != '--:--':
                    tab = tab + r""" & %s""" %(moon[k])
                else:
                    tab = tab + r""" & \multirow{2}{*}{%s}""" %(moon[k])
            tab = tab + r"""\\"""	# terminate top row
# bottom row...
            for k in range(len(moon)):
                if moon2[k] != '--:--':
                    tab = tab + r""" & %s""" %(moon2[k])
                else:
                    tab = tab + r"""&"""
            tab = tab + r"""\\"""	# terminate bottom row
        j += 1
    # add space between tables...
    tab = tab + r"""\hline\multicolumn{7}{c}{}\\[-1.5ex]"""

# Equation of Time section ...........................................
    if config.tbls == "m":
        tab = tab + r"""\hline
    \multicolumn{1}{|c|}{} & & & \multicolumn{1}{c|}{} & & & \multicolumn{1}{c|}{}\\[-2.0ex]

    \multicolumn{1}{|c|}{\multirow{4}{*}{\footnotesize{\textbf{Day}}}} & 
    \multicolumn{3}{c|}{\multirow{1}{*}{\footnotesize{\textbf{Sun}}}} & 
    \multicolumn{3}{c|}{\multirow{1}{*}{\footnotesize{\textbf{Moon}}}} \\[0.6ex] 

    \multicolumn{1}{|c|}{} & 
    \multicolumn{2}{c}{Eqn.of Time} & 
    \multicolumn{1}{|c|}{Mer.} & 
    \multicolumn{2}{c}{Mer.Pass.} & 
    \multicolumn{1}{|c|}{} \\ 

    \multicolumn{1}{|c|}{} &\multicolumn{1}{c}{00\textsuperscript{h}} & \multicolumn{1}{c}{12\textsuperscript{h}} & \multicolumn{1}{|c|}{Pass} & \multicolumn{1}{c}{Upper} & \multicolumn{1}{c}{Lower} &\multicolumn{1}{|c|}{Age} \\ 

    \multicolumn{1}{|c|}{} &\multicolumn{1}{c}{mm:ss} & \multicolumn{1}{c}{mm:ss} & \multicolumn{1}{|c|}{hh:mm} & \multicolumn{1}{c}{hh:mm} & \multicolumn{1}{c}{hh:mm} &\multicolumn{1}{|c|}{} \\ 
    \hline\rule{0pt}{3.0ex}\noindent
"""
    else:
        tab = tab + r"""\hline
    \multicolumn{1}{|c|}{\rule{0pt}{2.4ex}\multirow{4}{*}{\textbf{Day}}} & 
	\multicolumn{3}{c|}{\textbf{Sun}} & \multicolumn{3}{c|}{\textbf{Moon}} \\ 

    \multicolumn{1}{|c|}{} & \multicolumn{2}{c}{Eqn.of Time} & \multicolumn{1}{|c|}{Mer.} & \multicolumn{2}{c}{Mer.Pass.} & \multicolumn{1}{|c|}{} \\ 

    \multicolumn{1}{|c|}{} & \multicolumn{1}{c}{00\textsuperscript{h}} & \multicolumn{1}{c}{12\textsuperscript{h}} & \multicolumn{1}{|c|}{Pass} & \multicolumn{1}{c}{Upper} & \multicolumn{1}{c}{Lower} &\multicolumn{1}{|c|}{Age} \\

    \multicolumn{1}{|c|}{} & \multicolumn{1}{c}{mm:ss} & \multicolumn{1}{c}{mm:ss} & \multicolumn{1}{|c|}{hh:mm} & \multicolumn{1}{c}{hh:mm} & \multicolumn{1}{c}{hh:mm} &\multicolumn{1}{|c|}{} \\
    \hline\rule{0pt}{3.0ex}\noindent
"""

    d = date
    for k in range(3):
        eq = equation_of_time(d,d + datetime.timedelta(days=1),UpperLists[k],LowerLists[k])
        if k == 2:
            tab = tab + u"%s & %s & %s & %s & %s & %s & %s(%s\\%%) \\\[0.3ex] \n" %(d.strftime("%d"),eq[0],eq[1],eq[2],eq[3],eq[4],eq[5],eq[6])
        else:
            tab = tab + u"%s & %s & %s & %s & %s & %s & %s(%s\\%%) \\\ \n" %(d.strftime("%d"),eq[0],eq[1],eq[2],eq[3],eq[4],eq[5],eq[6])
        d += datetime.timedelta(days=1)
    tab = tab + r"""\hline
    \end{tabular*}
"""
    return tab


def double_events_found(m1, m2):
    # check for two moonrise/moonset events on the same day & latitude
    dbl = False
    for i in range(len(m1)):
        if m2[i] != '--:--':
            dbl = True
    return dbl


def doublepage(date):
    # creates a doublepage (3 days) of the nautical almanac

    find_new_moon(date)
    #import alma_skyfield
    #print("previous  new moon: %s" %alma_skyfield.PreviousNewMoon)
    #print("next      new moon: %s" %alma_skyfield.NextNewMoon)

    page = r"""
    \sffamily
    \noindent
    \textbf{%s, %s, %s   (%s.,  %s.,  %s.)}
    
    \begin{scriptsize}
""" %(date.strftime("%B %d"),(date+datetime.timedelta(days=1)).strftime("%d"),(date+datetime.timedelta(days=2)).strftime("%d"),date.strftime("%a"),(date+datetime.timedelta(days=1)).strftime("%a"),(date+datetime.timedelta(days=2)).strftime("%a"))
    if config.tbls == "m":
        page = page + planetstabm(date)
    else:
        page = page + planetstab(date)
    page = page + starstab(date)
    str1 = r"""\end{scriptsize}

    \newpage
    \begin{flushright}
    \textbf{%s to %s}
    \end{flushright}
    
    \begin{scriptsize}
""" %(date.strftime("%Y %B %d"),(date+datetime.timedelta(days=2)).strftime("%b. %d"))
    page = page + str1
    if config.tbls == "m":
        page = page + sunmoontabm(date)
    else:
        page = page + sunmoontab(date)
    page = page + twilighttab(date)
    page = page + r"""\end{scriptsize}
    \newpage
"""
    return page


def pages(first_day, p):
    # make 'p' doublepages beginning with first_day
    out = ''
    pmth = ''
    for i in range(p):
        if p == 122:	# if Full Almanac for a year...
            cmth = first_day.strftime("%b ")
            if cmth != pmth:
                print		# progress indicator - next month
                print(cmth,)
            else:
                sys.stdout.write('.')	# progress indicator
                sys.stdout.flush()
            pmth = cmth
        out = out + doublepage(first_day)
        first_day += datetime.timedelta(days=3)
    if p == 122:	# if Full Almanac for a year...
        print		# newline to terminate progress indicator
    return out


def almanac(first_day, pagenum):
    # make almanac from date till date
    year = first_day.year
    mth = first_day.month
    day = first_day.day

    alm = r"""\documentclass[10pt, twoside, a4paper]{report}
    \usepackage[utf8x]{inputenc}
    \usepackage[english]{babel}
    \usepackage{fontenc}
"""
    if config.tbls == "m":
        alm = alm + r"""
    \usepackage[ top=10mm, bottom=18mm, left=12mm, right=10mm ]{geometry}
    \usepackage[table]{xcolor}
    \definecolor{darknight}{rgb}{0.18, 0.27, 0.33}
    \definecolor{LightCyan}{rgb}{0.88,1,1}
    \usepackage{booktabs}
    \usepackage{multirow}
"""
    else:
        alm = alm + r"""
    \usepackage[ top=21mm, bottom=21mm, left=12mm, right=8mm]{geometry}
    \usepackage{multirow}
"""

    alm = alm + r"""
    \newcommand{\HRule}{\rule{\linewidth}{0.5mm}}
    \usepackage[pdftex]{graphicx}	% for \includegraphics

    \begin{document}

    % for the title page only...
    \newgeometry{ top=21mm, bottom=15mm, left=12mm, right=8mm}
    \begin{titlepage}
"""

    alm = alm + r"""
    \begin{center}

    \textsc{\Large Generated using PyEphem and Skyfield}\\
    \large http://rhodesmill.org/skyfield/\\[0.7cm]

    % TRIM values: left bottom right top
    \includegraphics[clip, trim=12mm 20cm 12mm 21mm, width=0.92\textwidth]{./A4chart0-180_P.pdf}\\[0.3cm]
    \includegraphics[clip, trim=12mm 20cm 12mm 21mm, width=0.92\textwidth]{./A4chart180-360_P.pdf}\\[0.8cm]

    \textsc{\huge The Nautical Almanac}\\[0.7cm]
"""
    if pagenum == 122:
        alm = alm + r"""
        \HRule \\[0.5cm]
        { \Huge \bfseries %s}\\[0.2cm]
        \HRule \\
""" %(year)
    else:
        alm = alm + r"""
        \HRule \\[0.5cm]
        { \Huge \bfseries from %s.%s.%s}\\[0.2cm]
        \HRule \\
""" %(day,mth,year)

    if config.tbls == "m":
        alm = alm + r"""
        \begin{center} \large
        \emph{Author:}\\
        Enno \textsc{Rodegerdts}\\[6Pt]
        \emph{Skyfield interface:}\\
        Andrew \textsc{Bauer}
"""
    else:
        alm = alm + r"""
        \begin{center} \large
        \emph{Author:}\\
        Enno \textsc{Rodegerdts}\\
        \emph{Skyfield interface:}\\
        Andrew \textsc{Bauer}
"""

    alm = alm + r"""\end{center}

    {\large \today}
    \HRule \\[0.2cm]
    \end{center}
    
    \begin{description}\footnotesize
    
    \item[Disclaimer:] These are computer generated tables. Use on your own risk. 
    The accuracy has been checked as good as possible but can not be guaranteed. 
    This means, if you get lost on the oceans because of errors in this publication I can not be held liable. 
    For security relevant applications you should buy an official version of the nautical almanac. You need one anyway since this publication only contains the daily pages of the Nautical Almanac.
    
    \end{description}
    
    \end{titlepage}
    \restoregeometry    % so it does not affect the rest of the pages
"""
    alm = alm + pages(first_day,pagenum)
    alm = alm + u'\end{document}'
    return alm

