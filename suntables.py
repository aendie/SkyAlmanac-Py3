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
from alma_skyfield import *

def suntab(date):
    # generates LaTeX table for sun only (traditional)
    tab = r'''\noindent
    \begin{tabular*}{0.2\textwidth}[t]{@{\extracolsep{\fill}}|c|rr|}
'''
    n = 0
    while n < 3:
        tab = tab + r'''\hline 
        \multicolumn{1}{|c|}{\rule{0pt}{2.6ex}\textbf{%s}} &\multicolumn{1}{c}{\textbf{GHA}} &\multicolumn{1}{c|}{\textbf{Dec}}\\ 
        \hline\rule{0pt}{2.6ex}\noindent
''' %(date.strftime("%d"))

        ghas, decs, degs = sunGHA(date)
        h = 0

        if config.decf != '+':	# USNO format for Declination
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

                line = u"%s & %s & %s" %(h,ghas[h],sdec)
                lineterminator = u"\\\ \n"
                if h < 23 and (h+1)%6 == 0:
                    lineterminator = u"\\\[2Pt] \n"
                tab = tab + line + lineterminator
                h += 1

        else:			# Positive/Negative Declinations
            while h < 24:
                line = u"%s & %s & %s" %(h,ghas[h],decs[h])
                lineterminator = u"\\\ \n"
                if h < 23 and (h+1)%6 == 0:
                    lineterminator = u"\\\[2Pt] \n"
                tab = tab + line + lineterminator
                h += 1

        sds, dsm = sunSD(date)
        tab = tab + r"""\hline
        \rule{0pt}{2.4ex} & \multicolumn{1}{c}{SD.=%s} & \multicolumn{1}{c|}{d=%s} \\
        \hline
""" %(sds,dsm)
        if n < 2:
            # add space between tables...
            tab = tab + r"""\multicolumn{1}{c}{}\\[-0.5ex]"""
        n += 1
        date += datetime.timedelta(days=1)
    tab = tab + r"""\end{tabular*}"""
    return tab

def suntabm(date):
    # generates LaTeX table for sun only (modern)
    tab = r'''\noindent
    \renewcommand{\arraystretch}{1.1}
    \setlength{\tabcolsep}{4pt}
    \begin{tabular}[t]{@{}crr}
'''
    n = 0
    while n < 3:
        tab = tab + r'''
    \multicolumn{1}{c}{\footnotesize{\textbf{%s}}} & 
    \multicolumn{1}{c}{\footnotesize{\textbf{GHA}}} &  
    \multicolumn{1}{c}{\footnotesize{\textbf{Dec}}}\\ 
    \cmidrule{1-3}
''' %(date.strftime("%d"))

        ghas, decs, degs = sunGHA(date)
        h = 0

        if config.decf != '+':	# USNO format for Declination
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

                line = r'''\color{blue} {%s} & 
''' %(h)
                line = line + u"%s & %s" %(ghas[h],sdec)
                if group == 1:
                    tab = tab + r'''\rowcolor{LightCyan}
'''
                lineterminator = u"\\\ \n"
                if h < 23 and (h+1)%6 == 0:
                    lineterminator = u"\\\[2Pt] \n"
                tab = tab + line + lineterminator
                h += 1

        else:			# Positive/Negative Declinations
            while h < 24:
                band = int(h/6)
                group = band % 2
                line = r'''\color{blue} {%s} & 
''' %(h)
                line = line + u"%s & %s" %(ghas[h],decs[h])
                if group == 1:
                    tab = tab + r'''\rowcolor{LightCyan}
'''
                lineterminator = u"\\\ \n"
                if h < 23 and (h+1)%6 == 0:
                    lineterminator = u"\\\[2Pt] \n"
                tab = tab + line + lineterminator
                h += 1

        sds, dsm = sunSD(date)
        tab = tab + r"""\cmidrule{2-3}
        & \multicolumn{1}{c}{\footnotesize{SD.=%s}} & \multicolumn{1}{c}{\footnotesize{d=%s}} \\
        \cmidrule{2-3}
""" %(sds,dsm)
        if n < 2:
            # add space between tables...
            tab = tab + r"""\multicolumn{3}{c}{}\\[-1.5ex]
"""
        n += 1
        date += datetime.timedelta(days=1)
    tab = tab + r"""
    \end{tabular}"""
    return tab


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

def page(date):
    # creates a page(15 days) of the Sun almanac
    page = r"""
    \sffamily
    \noindent
    \begin{flushright}
    \textbf{%s to %s}
    \end{flushright}
    
    \begin{scriptsize}
    """ %(date.strftime("%Y %B %d"), (date + datetime.timedelta(days=14)).strftime("%b. %d"))
    if config.tbls == "m":
        page = page + suntabm(date)
        page = page + r'''\quad
'''
        page = page + suntabm(date + datetime.timedelta(days=3))
        page = page + r'''\quad
'''
        page = page + suntabm(date + datetime.timedelta(days=6))
        page = page + r'''\quad
'''
        page = page + suntabm(date + datetime.timedelta(days=9))
        page = page + r'''\quad
'''
        page = page + suntabm(date + datetime.timedelta(days=12))
    else:
        page = page + suntab(date)
        page = page + suntab(date + datetime.timedelta(days=3))
        page = page + suntab(date + datetime.timedelta(days=6))
        page = page + suntab(date + datetime.timedelta(days=9))
        page = page + suntab(date + datetime.timedelta(days=12))
    page = page + r"""\end{scriptsize}
    \newpage
"""
    return page


def pages(first_day, p):
    # make 'p' pages beginning with first_day
    out = ''
    for i in range(p):
        out = out + page(first_day)
        first_day += datetime.timedelta(days=15)
    return out


def almanac(first_day, pagenum):
    # make almanac from date till date
    year = first_day.year
    mth = first_day.month
    day = first_day.day

    alm = r"""\documentclass[10pt, twoside, a4paper]{report}
    \usepackage[utf8x]{inputenc}
    \usepackage[english]{babel}
    \usepackage{fontenc}"""

    if config.tbls == "m" and config.decf != '+':	# USNO format for Declination
        alm = alm + r"""
    \usepackage[ top=8mm, bottom=18mm, left=13mm, right=8mm ]{geometry}"""

    if config.tbls == "m" and config.decf == '+':	# Positive/Negative Declinations
        alm = alm + r"""
    \usepackage[ top=8mm, bottom=18mm, left=17mm, right=11mm ]{geometry}"""

    if config.tbls == "m":
        alm = alm + r"""
    \usepackage[table]{xcolor}
    \definecolor{LightCyan}{rgb}{0.88,1,1}
    \usepackage{booktabs}"""
    else:
        alm = alm + r"""
    \usepackage[ top=21mm, bottom=21mm, left=16mm, right=10mm]{geometry}"""
    
    alm = alm + r"""
    \newcommand{\HRule}{\rule{\linewidth}{0.5mm}}
    \usepackage[pdftex]{graphicx}

    \begin{document}

    \begin{titlepage}"""
    if config.tbls == "m":
        alm = alm + r'''\vspace*{2cm}'''

    alm = alm + r"""
    \begin{center}
     
    \textsc{\Large Generated using Skyfield}\\
    \large http://rhodesmill.org/skyfield/\\[1.5cm]

    \includegraphics[width=0.4\textwidth]{./Ra}\\[1cm]

    \textsc{\huge The Nautical Almanac for the Sun}\\[0.7cm]
"""

    if pagenum == 25:
        alm = alm + r"""
        \HRule \\[0.6cm]
        { \Huge \bfseries %s}\\[0.4cm]
        \HRule \\[1.5cm]
""" %(year)
    else:
        alm = alm + r"""
        \HRule \\[0.6cm]
        { \Huge \bfseries from %s.%s.%s}\\[0.4cm]
        \HRule \\[1.5cm]
""" %(day,mth,year)

    if config.tbls == "m":
        alm = alm + r"""
        \begin{center} \large
        \emph{Author:}\\
        Enno \textsc{Rodegerdts}\\[6Pt]
        \emph{Skyfield interface \& Table Design:}\\
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

    \vfill

    {\large \today}
    \HRule \\[0.6cm]
    \end{center}
    
    \begin{description}\footnotesize
    
    \item[Disclaimer:] These are computer generated tables. Use on your own risk. 
    The accuracy has been checked as good as possible but can not be guaranteed. 
    This means, if you get lost on the oceans because of errors in this publication I can not be held liable. 
    For security relevant applications you should buy an official version of the nautical almanac.
    
    \end{description}
     
    \end{titlepage}
"""
    if config.tbls == "m":
        alm = alm + r"""\vspace*{3cm}
"""
    else:
        alm = alm + r"""\vspace*{1.5cm}
"""
    alm = alm + r"""
    DIP corrects for height of eye over the surface. This value has to be subtracted from the sextant altitude ($H_s$). The  correction in degrees for height of eye in meters is given by the following formula: 
    \[d=0.0293\sqrt{m}\]
    This is the first correction (apart from index error) that has to be applied to the measured altitude.
    
    The next correction is for refraction in the Earth's atmosphere. As usual this table is correct for 10°C and a pressure of 1010hPa. This correction has to be applied to apparent altitude ($H_a$). The exact values can be calculated by the following formula.
    \[R_0=\cot \left( H_a + \frac{7.31}{H_a+4.4}\right)\]
    For other than standard conditions, calculate a correction factor for $R_0$ by: \[f=\frac{0.28P}{T+273}\] where $P$ is the pressure in hectopascal and $T$ is the temperature in °C.
    
     Semidiameter has to be added for lower limb sights and subtracted for upper limb sights. The value for semidiameter is tabulated in the daily pages.
    
    To correct your sextant altitude $H_s$ do the following:
    Calculate $H_a$ by
     \[H_a= H_s+I-dip\] 
    Where $I$ is the sextants index error. Than calculate the observed altitude $H_o$ by
    \[H_o= H_a-R+P\pm SD\]
    where $R$ is refraction, $P$ is parallax and $SD$ is the semidiameter.
    
    Sight reduction tables can be downloaded for the US governments internet pages. Search for HO-229 or HO-249.  These values can also be calculated with to, relatively simple, formulas
    \[ \sin H_c= \sin L \sin d + \cos L \cos d \cos LHA\]
    and
    \[\cos A = \frac{\sin d - \sin L \sin H_c}{\cos L \cos H_c}\]
    where $A$ is the azimuth angle, $L$ is the latitude, $d$ is the declination and $LHA$ is the local hour angle. The azimuth ($Z_n$) is given by the following rule:
    \begin{itemize}
          \item if the $LHA$ is greater than 180°, $Z_n=A$
          \item if the $LHA$ is less than 180°, $Z_n = 360^\circ - A$
    \end{itemize}

    \newpage
"""
    alm = alm + pages(first_day,pagenum)
    alm = alm + u"\end{document}"
    return alm
