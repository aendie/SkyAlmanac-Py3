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
import sys
from datetime import datetime, timedelta
import math

###### Local application imports ######
import config
import ld_stardata
from ld_skyfield import sunGHA, moonGHA, venusGHA, marsGHA, jupiterGHA, saturnGHA, ld_planets, ld_stars, getHipparcos, getCustomStar

#   My apologies to those who read this . . .
#   Although use of global variables is frowned upon by the Python community,
#   I have chosen to employ global variables in this module to reduce the
#   number of arguments passed to some functions, so that the function
#   arguments focus on the frequently changing parameters.
#   A comment before a function describes which global variables are used.
#   . . . and Murphy whispered in his sleep "If it works, don't touch it"

LDtargets = ['sun','ven','mar','jup','sat','Ache','Acru','Adha','Alde','Alta','Anta','Arct','Bete','Cano','Cape','Dene','Foma','Hada','Pola','Poll','Proc','Regu','Rige','Rigi','Siri','Spic','Vega']

# reserve memory for 41 stars in a constellation
#global csize
csize = 0
#global cstars
cstars = [[None]*4 for i in range(41)]  # cstars[0][0] up to cstars[40][3]

planet_x = []   # empty list of planets added (to check if they partially overlap)
stars_LD = []   # empty list of LD stars (to print at bottom of page)
degree_sign= u'\N{DEGREE SIGN}'

# globals required in: getc, showLD, buildchart, printcname, addstar, addtext ...
shamin = shamax = sharng = None
decmin = decmax = None
PREVobjects = []        # list of LD objects from previous day
PREVobjColour = []      # list of LD object-colour tuples from previous day

#---------------------------
#   Module initialization
#---------------------------

def init_A4(ts, d0=None):
    # initialize variables for this module

    global sf
    if config.pgsz == "A4":
        sf = 1.39               # scale factor (1.39cm to 10 degrees SHA/DEC)
    else:
        sf = 1.31               # scale factor (1.31cm to 10 degrees SHA/DEC)

    ## A4/Letter LANDSCAPE ##
    global const_fs
    const_fs = "large"          # constellation name fontsize (12pt)
    global navstar_fs
    navstar_fs = "normalsize"   # navigational star fontsize (10pt)
    #navstar_fs = "fontsize{6pt}" # navigational star fontsize (6pt)
    global navnum_fs
    navnum_fs = "Large"         # navigational starnum fontsize (14.4pt)
    global star_fs
    star_fs = "footnotesize"    # star fontsize (8pt)
    global title_fs
    title_fs ="Large"           # title, SHA, DEC fontsize (14.4pt)
    global ns_fs
    ns_fs = "large"             # North, South fontsize (12pt)
    
    if d0 != None:
        global t00              # getc() requires 't00'; makeLDcharts updates 't00'
        t00 = ts.utc(d0.year, d0.month, d0.day, 0, 0, 0)
    
    return

#----------------------------
#   astronomical functions
#----------------------------

# global variables >>>> shamin, sharng
def SHAleftofzero(sha):
    # return True if SHA 0° is within plot borders; and if 'sha' is left of SHA 0° and within plot borders
    # return False otherwise
    if 360 - shamin <= sharng:
        # SHA 0° is within plot and not first SHA, i.e. SHAs < 360° are plotted
        return (sha >= shamin)
    else: return False

# global variables >>>> sharng
def ext_sha(sha0):
    # calculate a fake "extended sha" value that will
    # transform to a correct X-axis coordinate whether
    # within plot left/right borders or not. It can be 
    # < 0 or >= 360 based upon where SHA 0° lies on the
    # X-axis (which depends on 'x_o', the X-axis plot offset).

    # This is to facilitate computation of coordinates that
    # are beyond the LEFT or RIGHT plot borders but are
    # required to draw constellation or Lunar Distance lines.

    sha = sha0 % 360.0      # 0 <= sha < 360 (just in case!)

    v = outsideplot(sha)
    if v == 0: 
        if SHAleftofzero(sha): return sha - 360.0
        return sha      # unchanged
    if v == +1:
        if sha < sharng - x_o: return sha + 360.0
        return sha      # unchanged
    if v == -1:
        if sha > -x_o: return sha - 360.0
        return sha      # unchanged

# global variables >>>> shamin, shamax
def outsideplot(sha0):
    # As constellations have a limited size, if some points
    #   are within the plot area (i.e. ignore constellations
    #   completely outside the plot area!!!), detect points
    #   just beyond the left or right plot borders...
    #   ... in order to complete the constellation lines

    # 'mid_sha' is the center SHA of the unplotted range
    # return -1 if 'sha' left of left plot border (up to 'mid_sha')
    # return +1 if 'sha' right of right plot border (up to 'mid_sha')
    # return  0 otherwise
    # (lines will be correctly clipped if -1 or +1 is returned)
    sha = sha0 % 360.0      # 0 <= sha < 360

    if shamax > shamin:
        edge_sha = (shamax - shamin) / 2
    else:
        edge_sha = (shamin - shamax) / 2
    mid_sha = shamax + edge_sha
    if mid_sha > 360:
        mid_sha -= 360

    # check if within left edge_sha
    if mid_sha < shamin:
        v = -1 if mid_sha < sha < shamin else 0
    else:
        v = 0 if shamin <= sha <= mid_sha else -1
    if v != 0: return v

    # check if within right edge_sha
    if mid_sha > shamax:
        v = 1 if mid_sha > sha > shamax else 0
    else:
        v = 0 if shamax >= sha >= mid_sha else 1
    return v

# global variables >>>> decmin, decmax
def outofbounds_dec(dec):
    # As constellations have a limited size, if some points
    #   are within the plot area (i.e. ignore constellations
    #   completely above or below the plot area!!!), detect points
    #   just beyond the lower or upper plot borders...
    #   ... in order to complete the constellation lines

    # return -1 if 'dec' below lower plot border
    # return +1 if 'dec' above upper plot border
    # return  0 otherwise
    # (lines will be correctly clipped if -1 or +1 is returned)
    
    if dec > decmax: return +1
    if dec < decmin: return -1
    return 0

def shaadd(sha, inc):
    ang = sha + inc
    ang = ang % 360     # DO NOT CHANGE TO FLOAT with "ang = ang % 360.0"
    #if ang >= 360: ang = ang - 360
    return ang

# global variables >>>> shamin, shamax
def outofbounds_sha(sha):
    if sha < 0 or sha >= 360:
        raise Exception("SHA not in range 0 <= SHA < 360")
        sys.exit(0)
# check if object within plot range (x-axis)
    if shamax > shamin:
        v = False if shamin <= sha <= shamax else True
    else:
        v = True if shamax < sha < shamin else False
    return v

def validSHA(FROMsha, sha, TOsha):
# check if the SHA lies between FROMsha and TO sha
    if FROMsha < TOsha:
        return True if FROMsha < sha < TOsha else False
    else:
        x = False
        if sha > FROMsha or sha < TOsha: x = True
        return x

# all local variables below!
def sha_inc(shamin, shamax):
    # increment shamin & shamax by 5 degrees
    shamin += 5
    if shamin >= 360: shamin -= 360
    shamax += 5
    if shamax >= 360: shamax -= 360
    return shamin, shamax

def ra_sha(ra):
    # convert angle (hours) to sha (degrees)
    sha = (- ra) * 15
    if sha < 0:
        sha = sha + 360
    return sha

def group_width(csha):
    # get the constellation width, and min and max SHA
    # find the largest gap in sorted SHA values: this is not in the constellation!
    cwth = c_min = c_max = 0.0
    if len(csha) < 2: return cwth, c_min, c_max
    maxdiff = 0.0
    #csha.sort()         # CAUTION: this modifies the list in-place
    new_csha = sorted(csha)     # this creates a new list

    for i in range(len(new_csha)):
        if i == 0:
            diff = 360 - (new_csha[-1] - new_csha[0])
        else:
            diff = new_csha[i] - new_csha[i-1]
        if diff > maxdiff:
            maxdiff = diff
            c_max = new_csha[i-1] if i > 0 else new_csha[-1]
            k = i

    c_min = new_csha[k]
    cwth = c_max - c_min
    if cwth < 0: cwth += 360

    return cwth, c_min, c_max

def group_range(cdec):
    # get the min and max DEC from a list; also the mid DEC
    d_mid = d_min = d_max = 0.0
    if len(cdec) == 0: return d_mid, d_min, d_max
    cdec.sort()

    d_min = cdec[0]
    d_max = cdec[-1]
    d_mid = (d_max + d_min) / 2.0

    return d_mid, d_min, d_max

#-----------------------------------------------
#   graphical functions for chart constructon
#-----------------------------------------------

# global variables >>>> decmin, decmax, sharng, t00
def getc(cname, skipstars=[], c='consGrey'):
#   get constellation parameters and plot it
# cname     = constellation name
# skipstars = skip 'plotstar' for these (instead they are plotted using 'addstar')
# c         = colour of constellation pattern lines

##    global d
##    print("d = {}; type = {}".format(d,type(d)))
    global csize
    global cstars
    csha = []           # build list of SHA values of stars in constellation
    out = ""
    cpattern = ""
    fnd = False
    ndx = 0
    starstoplot = 0
    cnameSHA = 999.0    #invalid value
    cnameDEC = 100.0    #invalid value
    cname2SHA = 999.0   #invalid value
    cname2DEC = 100.0   #invalid value
    for line in ld_stardata.constellations.strip().split('\n'):
        if not(fnd):
            x1 = line.find(':')
            if x1 != -1:
                if cname == line[0:x1]:
                    fnd = True
                    x2 = cname.find('_')
                    if x2 == -1:
                        x3 = line.find(',')
                        if x3 != -1:
                            cname1 = cname
                            cnameSHA = float(line[x1+1:x3])
                            cnameDEC = float(line[x3+1:])
                    else:
                        cname1 = cname[0:x2]
                        cname2 = cname[x2+1:]
                        x4 = line.find(';')
                        part1 = line[x1+1:x4]
                        part2 = line[x4+1:]
                        x3 = part1.find(',')
                        if x3 != -1:
                            cnameSHA = float(part1[0:x3])
                            cnameDEC = float(part1[x3+1:])
                        x4 = part2.find(',')
                        if x4 != -1:
                            cname2SHA = float(part2[0:x4])
                            cname2DEC = float(part2[x4+1:])
                    continue
        else:
            if line[3:4] == ' ':
                # save all stars in constellation
                bayercode = line[0:3]
                HIPnum = line[4:]

                ##t00 = ts.utc(d.year, d.month, d.day, 0, 0, 0)
                ra, dec, mag = getHipparcos(HIPnum, t00)

                sha = ra_sha(ra.hours)
                csha.append(sha)
                v = outsideplot(sha)
                if v == 0 and outofbounds_dec(dec.degrees) == 0: starstoplot += 1

                if cname == "CraterXXX":    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                    print("{} {}, sha = {:.3f}  v = {} w = {}".format(cname,bayercode,sha,v,SHAleftofzero(sha)))
                if v == 0 and SHAleftofzero(sha): sha -= 360       # NEW
                if v == -1: sha -= 360
                x = (x_o + sha) * sf / 10.0
                y = dec.degrees * sf / 10.0
#####                print("cstars = {} {} {} {}".format(bayercode,x,y,mag))
                #out += plotstar(x,y)  # don't plot here!
                cstars[ndx][0] = bayercode
                cstars[ndx][1] = x
                cstars[ndx][2] = y
                cstars[ndx][3] = mag
                ndx += 1
                csize = ndx
            else:
                if line[0:1] == "#":    # comment line
                    continue
                cpattern = line
                break

    if not fnd: return ""
    cwth, c_min, c_max = group_width(csha)
    #print("       {:5.2f} {} extends from {:.2f} to {:.2f}".format(cwth,cname,c_min,c_max))
    if cwth > 85:
        # maximum permitted constellation width is (360 - plot width)/2 = 85°
        #   Constellations that are wider must be split into smaller units
        #   because the mid-point of the unplotted region (e.g. 275° for a
        #   plot from 0° to 190°) determines if a connecting line should
        #   extend to the right or the left plot border.
        print("ERROR: {} width {:.2f}, extends from {:.2f} to {:.2f}".format(cname,cwth,c_min,c_max))
    if starstoplot == 0: return ""
 
    # clip area is the plot boundary
    x1 = 0.0
    y1 = decmin * sf / 10.0
    x2 = sharng * sf / 10.0
    y2 = decmax * sf / 10.0
    out += r"""
% constellation: {}
\begin{{scope}}
  \clip ({:.3f},{:.3f}) rectangle ({:.3f},{:.3f});""".format(cname, x1, y1, x2, y2)

    # draw constellation shape pattern
    while len(cpattern) > 4:
        starfr = cpattern[0:3]
        join = False
        cp = cpattern[3:4]
        if cp == "-":
            join = True
            dp = ""             # default is 'thin' 0.4pt
        if cp == "=":
            join = True
            dp = "very thick,"  # 0.8pt
        starto = cpattern[4:7]
        cpattern = cpattern[4:]
        if join:
            x1, y1 = findstar(starfr)
            x2, y2 = findstar(starto)
            # draw constellation shape in colour 'c'
            out += r"""
  \draw[%s%s] (%0.3f,%0.3f) -- (%0.3f,%0.3f);""" %(dp,c,x1,y1,x2,y2)

    # plot stars in constellation (*after* drawing the shape pattern)
    for ndx in range(csize):
        bayercode = cstars[ndx][0]
        # don't overlay a black circle with another colour ... it leaves a thin black rim
        if bayercode not in skipstars:
            x = cstars[ndx][1]
            y = cstars[ndx][2]
            mag = cstars[ndx][3]
            out += plotstar(x,y,mag)

    out += r"""
\end{scope}"""
    # print constellation name at locn in degrees
    out1 = ""
    if cnameDEC != 100.0:
        out1 = printcname(cname1,cnameSHA,cnameDEC)
    if cname2DEC != 100.0:
        out2 = printcname(cname2,cname2SHA,cname2DEC)
        # second word exists - was the first word printed?
        if out1 != "" and out2 != "":
            out += out1 + out2     # print both or none
    else:
        out += out1

    return out

# global variables >>>> decmin, decmax, sharng
def printcname(cname, sha, dec, p='right', c='gray'):
    # print constellation name
    v = outsideplot(sha)
    if v != 0: return ""
    if outofbounds_dec(dec) != 0: return ""
    # skip constellation names that are within 1.5° of upper or lower plot border...
    if abs(dec - decmin) < 1.5 or abs(dec - decmax) < 1.5: return ""
    if v == 0 and SHAleftofzero(sha): sha = sha - 360       # NEW

    x = (x_o + sha) * sf / 10.0
    y = dec * sf / 10.0

    if cname == 'Draco2': cname = 'Draco'   # patch (Draco is wide - print twice)
    if cname == 'Hydra2': cname = 'Hydra'   # patch (Hydra is split into two constellations)
    if cname == 'ScorpiusXXX':
        # first declare a new variable and store the length of 'cname' text in it
        # within tikz, it's necessary to surround this in \pgfinterruptpicture ... \endpgfinterruptpicture
        # use tcolorbox to apply a background color (colback), text color (colupper) and opacity (opacityfill) - this requires 'standard jigsaw'
        out = r"""
  \settowidth{\myl}{\pgfinterruptpicture\%s{%s}\endpgfinterruptpicture}
  \draw (%0.2f,%0.2f) node[%s] {\begin{tcolorbox}[standard jigsaw,size=minimal,colupper=%s,colback=white,opacityfill=0.7,width=\myl]{\%s{%s}}\end{tcolorbox}};
""" %(const_fs,cname,x,y,p,c,const_fs,cname)

    else:
        if cname == "GeminiXX":
            print("{}: x/sf= {:.2f} y= {}  {}".format(cname,x/sf,y,p))
        # prevent constellation names crossing the right plot border...
        deltaX = 0.0
        x_max = sharng / 10.0
##        if x/sf > x_max - 0.3 and p == 'right': p = 'left'    # don't switch sides
        if x/sf > x_max - 0.4 and p == 'right':  return ""  # e.g. remove Leo
        elif x/sf > x_max - 0.7 and p == 'right' and len(cname) >= 5:  return ""    # e.g. remove Indus
        elif x/sf > x_max - 1.2 and p == 'right' and len(cname) >= 8: return ""     # e.g. remove Aquarius
        elif x/sf > x_max - 1.6 and p == 'right' and len(cname) >= 10: return ""    # e.g. for Camelopardalis
        #elif x/sf > x_max - 0.7 and p == 'right' and len(cname) <= 5: deltaX = 0.7
        #elif x/sf > x_max - 1.0 and p == 'right' and len(cname) >= 6: deltaX = 1.0
        x -= deltaX

        out = r"""
  \draw[color=%s] (%0.2f,%0.2f) node[%s] {\%s{%s}};""" %(c,x,y,p,const_fs,cname)

    return out

def findstar(bayercode):
    x = 1.0
    y = 1.0
    global csize
    global cstars
    for ndx in range(csize):
        if cstars[ndx][0] == bayercode:
            x = cstars[ndx][1]
            y = cstars[ndx][2]
            break
    return x, y

def getstar(fname):
    # return SHA and Dec for epoch of date.
    if fname[:3] == "HIP":
        ra, dec, mag = getCustomStar(fname, t00)
        sha = ra_sha(ra.hours)
        return fname,sha,dec.degrees,mag

    for line in ld_stardata.popstars.split('\n'):
        if line[7:] == fname:
            HIPnum = line[:6].lstrip(' ')
            ra, dec, mag = getHipparcos(HIPnum, t00)
            #if math.isnan(ra) or math.isnan(dec):    # e.g. HIP78727, HIP55203
            sha = ra_sha(ra.hours)
            return fname,sha,dec.degrees,mag
    print("getstar error: {} not found in Hipparcos catalogue".format(fname))
    sys.exit(0)

def plotstar(x, y, mag=5.0, c='black', op=1.0, c2='black'):
    if mag == 5.0:
        m = 0.5
    else:       # A4 Landscape
        m = ((5.0 - mag) / 2.3) + 0.6

    pct = ",opacity=%s" %(op) if op != 1.0 else ''
    if c == 'white':
        # c2 is the circle colour
        m2 = m - 0.18    # subtract just less than half the line thickness (in pt)
        out = r"""
  \fill[color=%s%s] (%0.3f,%0.3f) circle[radius=%0.2f pt];
  \draw [color=%s] (%0.3f,%0.3f) circle[radius=%0.2f pt];""" %(c, pct, x, y, m, c2, x, y, m2)

    else:
        out = r"""
  \fill[color=%s%s] (%0.3f,%0.3f) circle[radius=%0.2f pt];""" %(c, pct, x, y, m)

    return out

def numpos(p, rn, n):
# improve the x, y coordinates for the navigational star number
# find the opposite side (of the star name) to place the number of the navigational star
    updown = False
    p2 = p

    # switch   left <=> right
    if p.find('right') != -1:
        p2 = p.replace("right", "left")
    if p.find('left') != -1:
        p2 = p.replace("left", "right")

    # switch   above <=> below
    if p.find('above') != -1:
        p2 = p.replace("above", "below")
        updown = True
    if p.find('below') != -1:
        p2 = p.replace("below", "above")
        updown = True

    # swap X   +ve <=> -ve
    if p2.find('xshift=-') != -1:
        p2 = p2.replace("xshift=-", "xshift=")
    else:
        if p2.find('xshift=') != -1:
            p2 = p2.replace("xshift=", "xshift=-")

    # if above or below: swap Y   +ve <=> -ve
    if updown:
        if p2.find('yshift=-') != -1:
            p2 = p2.replace("yshift=-", "yshift=")
        else:
            if p2.find('yshift=') != -1:
                p2 = p2.replace("yshift=", "yshift=-")

    # rn can only contain 1 comma
    i1 = rn.find(',')
    if i1 == -1:
        s1 = rn
        s2 = ''
    else:
        s1 = rn[:i1]
        s2 = rn[i1+1:]
        if s2.find(',') != -1:
            print("ERROR: incorrect parameters for star {}: '{}'".format(n,rn))
            sys.exit()

    if s1.startswith('xshift='):
        i2 = p2.find('xshift=')
        if i2 != -1:
            i3 = p2.find('ex', i2)
            p2 = p2.replace(p2[i2:i3+2], s1, 1)
        else: p2 = p2 + ',' + s1

    if s1.startswith('yshift='):
        i2 = p2.find('yshift=')
        if i2 != -1:
            i3 = p2.find('ex', i2)
            p2 = p2.replace(p2[i2:i3+2], s1, 1)
        else: p2 = p2 + ',' + s1

    if s2 == '':
        #print("{}: '{}'  =>  '{}'".format(n,p,p2))
        return p2

    if s2.startswith('xshift='):
        i2 = p2.find('xshift=')
        if i2 != -1:
            i3 = p2.find('ex', i2)
            p2 = p2.replace(p2[i2:i3+2], s2, 1)
        else: p2 = p2 + ',' + s2

    if s2.startswith('yshift='):
        i2 = p2.find('yshift=')
        if i2 != -1:
            i3 = p2.find('ex', i2)
            p2 = p2.replace(p2[i2:i3+2], s2, 1)
        else: p2 = p2 + ',' + s2

    #print("{}: '{}'  =>  '{}'".format(n,p,p2))
    return p2

# global variables >>> d00, sharng, stars_LD
def addstar(starname, n=0, c='black', p='right', rn=''):
    global stars_LD
    # plot the star as a filled circle ...
    name, sha, dec, mag = getstar(starname)
    if outofbounds_sha(sha): return ""
    if outofbounds_dec(dec) != 0: return ""
    if SHAleftofzero(sha): sha = sha - 360       # NEW

    x = (x_o + sha) * sf / 10.0
    y = dec * sf / 10.0
    c2 = c
    if c == 'blue': c = 'airforceBlue'
    fsize = star_fs
    if c2 == 'blue':
        c2 = 'orange'
        c2 = 'airforceBlue'
        fsize = navstar_fs
    out = plotstar(x,y,mag,c2)

    # print the star name ...
    x_max = sharng / 10.0
    if starname == 'XXX':
        # first declare a new variable and store the length of 'starname' text in it
        # within tikz, it's necessary to surround this in \pgfinterruptpicture ... \endpgfinterruptpicture
        # use tcolorbox to apply a background color (colback), text color (colupper) and opacity (opacityfill) - this requires 'standard jigsaw'
        out += r"""
  \settowidth{\myl}{\pgfinterruptpicture\%s{%s}\endpgfinterruptpicture}
  \draw (%0.2f,%0.2f) node[%s] {\begin{tcolorbox}[standard jigsaw,size=minimal,colupper=%s,colback=white,opacityfill=0.7,width=\myl]{\%s{%s}}\end{tcolorbox}};""" %(fsize,name,x,y,p,c,fsize,name)

    else:
        if n == 0:
            # prevent starname crossing the right or left plot border...
            if not (x/sf > x_max - 1.0 and p.startswith('right') and len(name) >= 5) and not (x/sf < 1.2 and p.startswith('left')):
                p2 = "opacity=0.4," + p
                out += r"""
  \draw[color=%s] (%0.2f,%0.2f) node[%s,font=\%s] {%s};""" %(c, x, y, p2, fsize, name)
        else:
            nsf = ''
            p2 = "opacity=0.5," + numpos(p,rn,n)
            # prevent starname crossing the left or right plot border...
            if not (x/sf > x_max - 1.0 and p.startswith('right')) and not (x/sf < 1.2 and p.startswith('left')):
                # print star name AND navigational star number from the Nautical Almanac
                out += r"""
  \draw[color=%s] (%0.2f,%0.2f) node[%s,font=\%s%s] {%s};
  \draw[color=airforceBlue] (%0.2f,%0.2f) node[%s] {\fontfamily{phv}\%s\textbf{%s}};""" %(c, x, y, p, fsize, nsf, name, x, y, p2, navnum_fs, n)
            else:
                # print only the navigational star number from the Nautical Almanac
                stars_LD.append([starname, n, False])   # append star name, nav number, 'True' if used for LD
                out += r"""
  \draw[color=airforceBlue] (%0.2f,%0.2f) node[%s] {\fontfamily{phv}\%s\textbf{%s}};""" %(x, y, p2, navnum_fs, n)

    return out

# global variables >>> d00, sharng
def addtext(starname, txt, c='black', p='right'):
# add text without plotting a star
    name, sha, dec, mag = getstar(starname)
    if outofbounds_sha(sha): return ""
    if outofbounds_dec(dec) != 0: return ""
    if SHAleftofzero(sha): sha = sha - 360       # NEW
    x = (x_o + sha) * sf / 10.0
    y = dec * 9 * sf / 90.0
    # prevent starname crossing the right or left plot border...
    out = ""
    x_max = sharng / 10.0
    if not (x/sf > x_max - 1.0 and p.startswith('right') and len(name) >= 5) and not (x/sf < 1.2 and p.startswith('left')):
        p2 = "opacity=0.4," + p
        out = r"""
  \draw[color=%s] (%0.2f,%0.2f) node[%s,font=\%s] {%s};""" %(c, x, y, p2, star_fs, txt)

    return out

# global variables >>> d00
def adddot(starname):
    name, sha, dec, mag = getstar(starname)
    if outofbounds_sha(sha): return ""
    if outofbounds_dec(dec) != 0: return ""
    if SHAleftofzero(sha): sha = sha - 360       # NEW
    x = (x_o + sha) * sf / 10.0
    y = dec * 9 * sf / 90.0
    #print("{}  x = {:.3f}  y = {:.3f}  mag = {}  sha = {:.3f}  dec = {:.3f}".format(starname,x,y,mag,sha,dec))
    out = plotstar(x,y,mag)
    return out

def getMOON(date):
    # get the X coordinate of the Moon at 00h
    sha, dec = moonGHA(date)

    if outofbounds_sha(sha[0]): return None
    Xsha = ext_sha(sha[0])
    xObj = (x_o + Xsha) * sf / 10.0
    return xObj

def XaxisLD(xMoon, sha, just):
    if xMoon == None: return 0.0
    
    Xsha = ext_sha(sha)
    xObj = (x_o + Xsha) * sf / 10.0
    if just == 'right':
        if xObj > xMoon: return xObj - xMoon
        else: return 0.0
    elif just == 'left':
        if xObj < xMoon: return xMoon - xObj
        else: return 0.0
    else: return 0.0

def addMOON(newMoon, checkpos = False):
    out = ""
    xyMoon00 = [None, None]
    xyMoon24 = [None, None]
    s = [None] * 3
    d = [None] * 3
    s, d = moonGHA(d00)
    t = ["0h", "12h", "24h"]
    
    # first check all coordinates
    outofrange = False
    for i in range(3):
        sha = s[i]
        dec = d[i]
        if outofbounds_sha(sha): outofrange = True
        if outofbounds_dec(dec) != 0: outofrange = True
        #print(i, sha, dec, outofbounds_sha(sha), outofbounds_dec(dec))
    if not checkpos and outofrange: return out, xyMoon00, xyMoon24

    if not outofrange:
        for i in range(3):
            sha = s[i]
            dec = d[i]
            #if outofbounds_sha(sha): continue
            #if outofbounds_dec(dec) != 0: continue
            if SHAleftofzero(sha):
                sha = sha - 360     # NEW
                s[i] = sha          # IMPORTANT
            # chart coordinates of Moon...
            x = (x_o + sha) * sf / 10.0
            y = dec * sf / 10.0
            out += plotstar(x,y,1.0,'amaranth',0.6)
            if i == 0:
                xyMoon00[0] = x
                xyMoon00[1] = y
            if i == 2:
                xyMoon24[0] = x
                xyMoon24[1] = y
            # chart coordinates of associated time of day (0h 12h 24h)...
            x = (x_o + sha -0.4) * sf / 10.0
            y = (dec + 1.5) * sf / 10.0
            out += r"""
  \draw[color=%s] (%0.2f,%0.2f) node[font=\%s] {%s};""" %('black', x, y, star_fs, t[i])

    txt = "New Moon" if newMoon else "Moon"
    dx = s[0] - s[2]
    dy = d[0] - d[2]
    #print("dx",dx)
    ang = math.atan(dy/dx)
    rot = "%0.3f" %(ang*todegrees)
    txtsep = 4.5
    # chart coordinates of 'Moon' text...
    x = (x_o + s[1] - (txtsep*math.sin(ang))) * sf / 10.0
    y = (d[1] + (txtsep*math.cos(ang))) * sf / 10.0
    out += r"""
  \draw[color=%s] (%0.3f,%0.3f) node[opacity=0.6,rotate=%s] {\fontfamily{phv}\%s\textbf{%s}};""" %('amaranth', x, y, rot, navnum_fs, txt)

    if checkpos: return x, y    # only return the coordinates of "Moon" text
    # also return the coordinates of the moon at 0h
    return out, xyMoon00, xyMoon24

def addSUN():
    return addPLANET("Sun")

# global variables >>> planet_x
def addPLANET(planet):
    out = ""
    s = [None] * 5
    d = [None] * 5
    if planet == "Venus":
        s, d = venusGHA(d00)
    elif planet == "Mars":
        s, d = marsGHA(d00)
    elif planet == "Jupiter":
        s, d = jupiterGHA(d00)
    elif planet == "Saturn":
        s, d = saturnGHA(d00)
    elif planet == "Sun":
        s, d = sunGHA(d00)

    # first check all coordinates (print as long as one is in range)
    outofrange = True
    oneoutofrange = False
    for i in range(5):
        sha = s[i]
        dec = d[i]
        if not outofbounds_sha(sha): outofrange = False
        else: oneoutofrange = True
    if outofrange: return out

    for i in [4,3,2,1,0]:
        sha = s[i]
        dec = d[i]
        if outofbounds_sha(sha):
            if x_o >= 0 and outsideplot(sha) == -1: sha -= 360
            #if x_o < 0 and outsideplot(sha) == +1: sha += 360
            s[i] = sha          # IMPORTANT
        else:
            if SHAleftofzero(sha): 
                sha = sha - 360     # NEW
                s[i] = sha          # IMPORTANT
        x = (x_o + sha) * sf / 10.0
        y = dec * sf / 10.0
        # DO NOT USE OPACITY < 1.0 BECAUSE THEY OVERLAP
        #print(" {:13} x={:7.3f}  y={:7.3f}   {}".format(planet+":",x/sf,y/sf,i))
        if i == 0:
            out += plotstar(x,y,1,'white',1.0,'blue2')
        else:
            out += plotstar(x,y,1,'blue2',1.0)

    if oneoutofrange: return out    # don't print label or arrow

    # direction of movement
    dx = s[0] - s[4]
    dy = d[0] - d[4]
    #print("dx",dx)
    ang = math.atan(dy/dx)
    rot = "%0.3f" %(ang*todegrees)
    txtsep = 3.0 if dx > 0 else -3.0
    midX = (x_o + s[2]) * sf / 10.0

    # check if existing planets already in this vicinity
    global planet_x
    for item in planet_x:
        if abs(item[0] - midX) < 1.0:
            xx = item[1]
            yy = item[2]
            x = (x_o + s[2] + (txtsep*math.sin(ang))) * sf / 10.0
            y = (d[2] - (txtsep*math.cos(ang))) * sf / 10.0
            sep1 = math.sqrt((xx-x)**2 + (yy-y)**2)
            x = (x_o + s[2] + (-txtsep*math.sin(ang))) * sf / 10.0
            y = (d[2] - (-txtsep*math.cos(ang))) * sf / 10.0
            sep2 = math.sqrt((xx-x)**2 + (yy-y)**2)
            if sep2 > sep1: txtsep = - txtsep
            break

    # check if moon is very close
    xx, yy = addMOON(False, True)   # returns coordinates of "Moon" text
    if abs(xx - midX) < 0.7:
        x = (x_o + s[2] + (txtsep*math.sin(ang))) * sf / 10.0
        y = (d[2] - (txtsep*math.cos(ang))) * sf / 10.0
        sep1 = math.sqrt((xx-x)**2 + (yy-y)**2)
        x = (x_o + s[2] + (-txtsep*math.sin(ang))) * sf / 10.0
        y = (d[2] - (-txtsep*math.cos(ang))) * sf / 10.0
        sep2 = math.sqrt((xx-x)**2 + (yy-y)**2)
        if sep2 > sep1: txtsep = - txtsep

    x = (x_o + s[2] + (txtsep*math.sin(ang))) * sf / 10.0
    y = (d[2] - (txtsep*math.cos(ang))) * sf / 10.0

    planet_x.append([midX, x, y]) # append list: planet X-position at 12h and text position

    lnsep = 5.0 if txtsep > 0 else -5.0
    lnlng = 3.6 / 2     # half line length
    arlng = 1.0
    arang = 30/todegrees
    # NOTE: direction-of-movement arrows are separated (above or below object) to
    #       minimize collision of RIGHT-moving objects with LEFT-moving objects.
    if dx > 0:  # print name with LEFT arrow (direction of movement) below object
        c2 = 'blue2'
        x0 = (x_o + s[2] + lnsep*math.sin(ang) - lnlng*math.cos(ang)) * sf / 10.0
        y0 = (d[2] - lnsep*math.cos(ang) - lnlng*math.sin(ang)) * sf / 10.0
        x1 = x0 + (lnlng * sf / 5.0)
        y1 = y0
        x2 = x0 + arlng*math.cos(arang) * sf / 10.0
        y2 = y0 + arlng*math.sin(arang) * sf / 10.0
        x3 = x2
        y3 = y0 - arlng*math.sin(arang) * sf / 10.0
    else:   # print name with RIGHT arrow (direction of movement) above object
        c2 = 'blue2'       # was c2 = 'Bronze'
        x0 = (x_o + s[2] + lnsep*math.sin(ang) + lnlng*math.cos(ang)) * sf / 10.0
        y0 = (d[2] - lnsep*math.cos(ang) + lnlng*math.sin(ang)) * sf / 10.0
        x1 = x0 - (lnlng * sf / 5.0)
        y1 = y0
        x2 = x0 - arlng*math.cos(arang) * sf / 10.0
        y2 = y0 + arlng*math.sin(arang) * sf / 10.0
        x3 = x2
        y3 = y0 - arlng*math.sin(arang) * sf / 10.0

    out += r"""
  \draw[color=%s] (%0.3f,%0.3f) node[rotate=%s,font=\%s] {%s};""" %(c2, x, y, rot, navstar_fs, planet)

    out += r"""
\begin{scope}
  \draw [rotate around={%.1f:(%0.3f,%0.3f)},color=%s] (%0.3f,%0.3f) -- (%0.3f,%0.3f)
  (%0.3f,%0.3f) -- (%0.3f,%0.3f) -- (%0.3f,%0.3f);
\end{scope}""" %(ang*todegrees, x0, y0, c2, x0, y0, x1, y1, x2, y2, x0, y0, x3, y3)

    return out

#---------------------------------
#   pick Lunar Distance targets
#---------------------------------

# global variables >>> d00
def LDstrategy(strat):
    # generate Lunar Distance targets according to chosen strategy

    # arguments for LD graphics ... create a list for the day
    LDlist = []     # List of chosen celestial objects
    H0list = []     # Lunar Distance angle at 0h per chosen celestial object
    SGNlist = []    # left and/or right of Moon 'sign' per chosen celestial object

# >>>>>>>>>>>> Calculate all required data <<<<<<<<<<<<

    out2, tup2, NMhours, ra_m = ld_planets(d00)   # planets & sun
    #print(out2[0][1].hours)
    #print("NMhours",NMhours)
    out, tup = ld_stars(d00, NMhours, out2[0][1].hours)
    #print("\nout =", out)
    #print()
    tup = tup + tup2
    tup.sort(key = lambda x: x[1])  # sort by signed first valid LD
    if config.debug_strategy:
        print("New Moon hours:\n{}".format(NMhours))

# =================================================================
#                        Strategy "C"
# =================================================================

# >>>>>>>>>>>> Decide which Lists to print (8 maximum) <<<<<<<<<<<<

    if strat == "C":
        LDtxt = " (objects with highest brightness)"
        # build list of objects sorted by largest hourly LD delta first
        tuple_list = [None] * 27
        for i in range(len(tup)):
            tuple_list[i] = (tup[i][0], tup[i][5], math.copysign(1, tup[i][1]), tup[i][4])
        tuple_list.sort(key = lambda x: x[1])   # sort by object magnitude
        if config.debug_strategy:
            print("--- tuples with highest brightness first ---")
            print(tuple_list)

# =================================================================
#                        Strategy "B"
# =================================================================

# >>>>>>>>>>>> Decide which Lists to print (8 maximum) <<<<<<<<<<<<

    if strat == "B":
        LDtxt = " (objects with largest hourly LD delta)"
        # build list of objects sorted by largest hourly LD delta first
        tuple_list = [None] * 27
        for i in range(len(tup)):
            tuple_list[i] = (tup[i][0], tup[i][3], math.copysign(1, tup[i][1]), tup[i][4])
        tuple_list.sort(key = lambda x: -x[1])  # sort by max hourly LD delta
        if config.debug_strategy:
            print("--- tuples with largest ld_delta_max first ---")
            print(tuple_list)

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
        #print(OUTlist)

# >>>>>>>>>>>> Gather data from Lists <<<<<<<<<<<<

        iCols = iLists
        if iCols < 5: LDtxt = ""    # not wide enough to print full text
        #extracols = ""
        obj = [None] * iCols
        ld  = [None] * 24
        iC = 0
        # output the objects in OUTlist in the sequence within 'tup'
        for i in range(len(tup)):
            ndx = tup[i][0]
            #print("ndx=",ndx)
            if ndx in set(OUTlist):
                ld_first = tup[i][1]      # first valid lunar distance angle in the day
                sgn = "-" if ld_first < 0 else "+"
                ld_last = tup[i][2]     # last valid lunar distance angle in the day
                sgn2 = "-" if ld_last < 0 else "+"
                if sgn != sgn2: sgn = u"\u00B1"     # plus-minus symbol
                SGNlist.append(sgn)
                if ndx > 0:
                    #print("out({})".format(ndx-1))
                    obj[iC] = out[ndx-1][0]         # star name
                    LDlist.append(obj[iC][:4])      # first 4 chars
                    obj[iC] = sgn + obj[iC]         # prepend sign ('+' or '-')
                    ld[iC] = out[ndx-1][5]          # lunar distance angles per hour
                    H0list.append(out[ndx-1][5][0]) # lunar distance angles at 0h
                else:
                    #print("out2({})".format(-ndx))
                    obj[iC] = out2[-ndx][0]         # planet name
                    LDlist.append(obj[iC].lower()[:3])   # first 3 chars (lowercase)
                    obj[iC] = sgn + obj[iC]         # prepend sign ('+' or '-')
                    ld[iC] = out2[-ndx][5]          # lunar distance angles per hour
                    H0list.append(out2[-ndx][5][0]) # lunar distance angles at 0h
                #print(obj[iC])
                #extracols += r'''r|'''
                i_out -= 1
                iC += 1
            if i_out == 0: break

# =================================================================
#                        Strategy "A"
# =================================================================

# >>>>>>>>>>>> Decide on target objects (8 maximum) <<<<<<<<<<<<

    if strat == "A":
        LDtxt = " (objects closest to the Moon)"
        iClosest = -1       # index of object closest to Moon (invalid value initially)
        for i in range(len(tup)):
            ld_first = tup[i][1]    # first valid lunar distance angle in the day
            if ld_first >= 0.0:
                iClosest = i
                break

        iLists = 0          # number of valid objects
        for i in range(len(tup)):
            ld_first = tup[i][1]    # first valid lunar distance angle in the day
            if ld_first < 1000.0: iLists += 1

        iFrom = 0
        if iLists <= 8:
            iCols = iLists
        else:
            iRem = iLists - 8       # count of objects that won't be printed
                                    #    (and highest 'iFrom' value)
            iCols = 8
            #iFrom = int(iRem / 2.0) # pick middle section of Objects
            if iClosest > iCols/2:
                iFrom = iClosest - int(iCols/2)
            #iFrom = iClosest - 4    # four -ve LD objects before +ve LD objects
            if iFrom > iRem: iFrom = iRem
            #print("iCols = {}   iFrom = {}   iClosest = {}".format(iCols, iFrom, iClosest))

# >>>>>>>>>>>> Gather data from Objects <<<<<<<<<<<<

        if iCols < 5: LDtxt = ""    # not wide enough to print full text
        i = iFrom
        #extracols = ""
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
            SGNlist.append(sgn)
            if ndx > 0:
                #print("out({})".format(ndx-1))
                obj[iC] = out[ndx-1][0]         # star name
                LDlist.append(obj[iC][:4])      # first 4 chars
                obj[iC] = sgn + obj[iC]         # prepend sign ('+' or '-')
                ld[iC] = out[ndx-1][5]          # lunar distance angles per hour
                H0list.append(out[ndx-1][5][0]) # lunar distance angles at 0h
            else:
                #print("out2({})".format(-ndx))
                obj[iC] = out2[-ndx][0]         # planet name
                LDlist.append(obj[iC].lower()[:3])   # first 3 chars (lowercase)
                obj[iC] = sgn + obj[iC]         # prepend sign ('+' or '-')
                ld[iC] = out2[-ndx][5]          # lunar distance angles per hour
                H0list.append(out2[-ndx][5][0]) # lunar distance angles at 0h
            i += 1
            #print(obj[iC])
            #print(ld[iC])
            #extracols += r'''r|'''
        #if len(NMhours) == 24:      # if NewMoon all day, i.e. iCols == 0
            #extracols += r'''r|'''   # add a fake column

# =================================================================

    if config.debug_strategy:
        print("\n{} columns of data".format(iCols))
        print("LDlist = {}".format(LDlist))
        print("H0list = {}\n".format(H0list))

    return LDlist, H0list, SGNlist

def beginPDF(ori, tm, bm, lm, rm):

# ---------- DOCUMENT INITIALIZATION ----------
    tex = r"""\pdfminorversion=4
\documentclass[10pt, %s]{report}
\usepackage[utf8]{inputenc}
\usepackage[english]{babel}
\usepackage{fontenc}    %% tikz fonts are clearer than with \usepackage[T1]{fontenc}
\usepackage{url}""" %(ori)

    if config.pgsz == "Letter":
        tex += r"""
\usepackage{setspace}
\setstretch{0.96}"""

    tex += r"""
\usepackage[ top=%s, bottom=%s, left=%s, right=%s]{geometry}
\usepackage[svgnames]{xcolor}
\usepackage{multicol}
\definecolor{darkTan}{rgb}{0.65, 0.41, 0.10}
\definecolor{consGrey}{rgb}{0.82, 0.82, 0.82}
\definecolor{ColumbiaBlue}{rgb}{0.61, 0.87, 1.0}
\definecolor{airforceBlue}{rgb}{0.36, 0.54, 0.66}
\definecolor{amaranth}{rgb}{0.9, 0.17, 0.31}
\definecolor{azure}{rgb}{0.0, 0.5, 1.0}
\definecolor{blue2}{rgb}{0.01, 0.28, 1.0}
\definecolor{PastelOrange}{rgb}{1.0, 0.7, 0.28}
\definecolor{Bronze}{rgb}{0.8, 0.5, 0.2}
\definecolor{OliveDrab}{rgb}{0.42, 0.56, 0.14}
%%colours for Lunar Distance lines...
\definecolor{Dark chestnut}{rgb}{0.6, 0.41, 0.38}
\definecolor{Green (pigment)}{rgb}{0.0, 0.65, 0.31}
\definecolor{Gold (metallic)}{rgb}{0.83, 0.69, 0.22}
\definecolor{Celestial blue}{rgb}{0.29, 0.59, 0.82}
\definecolor{Dark turquoise}{rgb}{0.0, 0.79, 0.79}
\definecolor{Rose pink}{rgb}{1.0, 0.4, 0.8}
\definecolor{Orange (color wheel)}{rgb}{1.0, 0.5, 0.0}
\definecolor{Lavender indigo}{rgb}{0.58, 0.34, 0.92}
%%\usepackage[pdftex]{graphicx}	%% for \includegraphics
\usepackage{tikz}				%% for \draw  (load after 'graphicx')
\usepackage{tcolorbox}          %% to apply a background color to text (load after 'tikz')
\usetikzlibrary{decorations.text}   %% to print text on a curve
\DeclareUnicodeCharacter{00B0}{\ensuremath{{}^\circ}}""" %(tm,bm,lm,rm)

    tex += r'''
\begin{{document}}
  \thispagestyle{{empty}}         % no page number
  \newlength{{\myl}}              % for \tcolorbox
  %\renewcommand{{\sfdefault}}{{cmss}}
  \newcommand*{{\gangnamstyle}}{{\sffamily\{}\color{{Teal}}}}'''.format(navstar_fs)

    return tex

def Page1(tm1, bm1, lm1, rm1, parsep):

    tex = r'''
  % for the first page only...
  \newgeometry{{nomarginpar, top={}, bottom={}, left={}, right={}}}'''.format(tm1,bm1,lm1,rm1)

    tex += r'''
  \setcounter{page}{2}    % otherwise it's 1
  \noindent
  {\centerline{\large\textbf{A brief introduction to the Lunar Distance Charts}}}\\[-6pt]'''

    if config.pgsz == "Letter":
        tex += r'''
  \setlength{\columnsep}{20pt}'''

    tex += r'''
  \begin{multicols}{2}
  \normalsize\noindent
  The following charts are a graphical way of representing the data in the Lunar Distance Tables, which are created separately and should accompany these charts.
  The intention behind these charts is simply to put the available data into a picture so one can appreciate the relative positions of the Moon, Sun, the four navigational planets, and the 21 stars (magnitude $\leq$ 1.5) plus Polaris used as Lunar Distance targets, in addition to the remaining stars (with magnitude \textless 5.0) and their constellations in the sky.\\%s''' %(parsep)

    tex += r'''
  \noindent
  No attempt is made to depict which objects are visible from the Earth - as this is dependent on the observer's location (daytime?/nighttime? and between moonrise and moonset?).
  The celestial objects are found as positioned on the charts: SHA, or Sidereal Hour Angle, (together with Declination) fixes the position of the objects. SHA units effectively cancel out the Earth's rotation. Thus the stars ``remain fixed'' in the sky, and the Sun hardly moves at all in just one day. The navigationsl stars have standard numbering.\footnote{Wikipedia ``List of stars for navigation'' (\url{https://en.wikipedia.org/wiki/List_of_stars_for_navigation})}\\%s''' %(parsep)

    tex += r'''
  \noindent
  The daily chart is automatically scaled (SHA and Declination) to give the best view of all (or most of) the celestial objects involved in the Lunar Distance Tables. The most appropriate objects change daily - the strategy to pick suitable objects is basically those with the largest change in hourly LD angle and within reach of a sextant (LD \textless 120$^\circ$).\\%s''' %(parsep)

    tex += r'''
  \noindent
  The Moon is the fastest moving object. One chart page represents data for one day in Universal Time (UT) - the same time standard as used in Nautical Almanacs. Lunar Distance is the angle between the center of the Moon and the center of a chosen celestial object.
  This angle, up to around 120$^\circ$, can be measured with a \mbox{sextant}, though normally the angle from the edge of the Moon (and Sun) is measured and a correction is required to add or subtract the semi-diameter of the Moon (and Sun).\\%s''' %(parsep)

    tex += r'''
  \noindent
  The Lunar Distance Tables show the angle between two objects for every hour of the day. It is pointless to draw all of these on a chart, so only the position of the Moon at 0h, 12h and 24h is shown. Furthermore, only the Lunar Distance lines at 0h (start of day) are drawn - with one exception.
  Ocassionally an object has no valid Lunar Distance value at 0h, so 24h (end of day) is used instead. There are various possible reasons for this, such as: the object is too close to the Moon (the LD values change significantly non-linearly); the object comes into range during the day (as the LD angle drops below 120$^\circ$).
  \vfill\null
  \columnbreak
  \noindent
  The Sun and (navigational) planets also change their position slightly during the day. A blue circle indicates the position at 0h (start of day) and a blue ``smudge'' shows where the object (the blue circle) moves to by 24h (end of day). In addition, the planet's name is printed nearby with an arrow indicating the direction of movement. (Note: planets ocassionally ``stop'' and change direction in SHA units, i.e. against the stary sky.)
  A \mbox{special} event is a New Moon... if you can't see the Moon, no Lunar Distance measurements are possiblle. Fortunately this ``blackout'' doesn't last too long.\\%s''' %(parsep)

    tex += r'''
  \noindent
  So, what's the motivation to master the technique of Lunar Distance measurement, \mbox{essentially} an 18th century technique to calibrate the time on a ship's clock? \mbox{Indeed}, this technique is considered to be the supreme discipline of sextant usage. 
  ``The methods are a good deal more laborious than the more commonplace procedures of celestial navigation. 
  It is perhaps the most difficult possible operation within the discipline of celestial navigation.
  However, one argument for maintaining celestial skills is the utility of celestial navigation as an emergency substitute for electronic navigation.''\footnote{Eric Romelczyk, The Journal of Navigation, Volume 72, Issue 6 ``GMT and Longitude by Lunar Distance: Two Methods Compared From a Practitioner's Point of View''}
  ``Nothing else comes close to the lunar for developing skill with a sextant - and the observation is demanding enough to hold one's interest for a lifetime.''\footnote{Bruce Stark, page vi, ``Tables For Clearing the Lunar Distance and Finding Universal Time by Sextant Observation'', ISBN 978-0-914025-21-4}\\%s''' %(parsep)

    tex += r'''
  \noindent
  Well, what happens when the electronics on a yacht fail? ``According to \mbox{BoatUS} Marine Insurance, the odds of a boat being struck by lightning are 1 in 1000, increasing to 3.3 in high risk areas.''\footnote{Mawgan Grace, Ocean Sailor, October 2021 (\url{https://oceansailormagazine.com/ocean-sailor-october-2021/}), Page 11 ``Thunderbolts \& Lightning''}
  There is also one infrequent event that can destroy electronics: a geomagnetic storm, such as the Carrington Event (\url{https://en.wikipedia.org/wiki/Carrington_Event}) when a solar CME hit the Earth's magnetosphere in 1859.
  It's a safe bet that this will occur again. And this time it could take out some GPS satellites. Mastering the Lunar Distance technique is thus a wise insurance policy (assuming the tables are already printed on paper).\\%s''' %(parsep)

    tex += r'''
  \noindent
  \textbf{Acknowledgements:} \newline The charts and LD tables are created with Skyfield (\url{https://rhodesmill.org/skyfield/}), thanks to Brandon Rhodes. The graphics are created with LaTeX using TikZ (\url{https://www.ctan.org/pkg/pgf}) version \pgfversion, thanks to Till Tantau and the team that maintain it. Kudos to the Python Software Foundation! Thanks also to Jorrit Visser for his Lunar Distance tables (\url{http://celnav.nl/}).\\[-6pt]
  \end{multicols}
  \noindent
  \textbf{Disclaimer:} These are computer generated tables - use them at your own risk. They replicate Lunar Distance algorithms with no guarantee of accuracy. They are intended to encourage people to use a sextant, be it as a hobby or as a backup when electronics fail.
\newpage
\restoregeometry    % so it does not affect the rest of the pages'''

# ---------- END DOCUMENT INITIALIZATION ----------
    return tex

def endPDF():
    tex = r"""
\end{document}"""
    return tex

#===========================================================

# Note: the Milky Way's north galactic pole is at
#   RA  = 12h 51m 26.282s    (J2000)
#   DEC = 27deg 07' 42.01"   (J2000)
# or SHA = 167.1404916, DEC = 27.1283361
# Note: our Sun lies 56.75 lightyears north of the galactic midplane.

# thanks to Robert Martin Ayers (http://www.robertmartinayers.org/) for an
# algorithm that works (unlike https://en.wikipedia.org/wiki/Galactic_coordinate_system)

twopi = 2 * math.pi
todegrees = 180.0/math.pi
toradians = math.pi/180.0

GtoJ = [
   -0.0548755604,  0.4941094279, -0.8676661490,
   -0.8734370902, -0.4448296300, -0.1980763734,
   -0.4838350155,  0.7469822445,  0.4559837762]

def Transform( radec, matrix ): # returns a radec array of two elements

    r0 = [ 
    math.cos(radec[0]) * math.cos(radec[1]),
    math.sin(radec[0]) * math.cos(radec[1]),
    math.sin(radec[1]) ]
    
    s0 = [
    r0[0]*matrix[0] + r0[1]*matrix[1] + r0[2]*matrix[2], 
    r0[0]*matrix[3] + r0[1]*matrix[4] + r0[2]*matrix[5], 
    r0[0]*matrix[6] + r0[1]*matrix[7] + r0[2]*matrix[8] ]
 
    r = math.sqrt( s0[0]*s0[0] + s0[1]*s0[1] + s0[2]*s0[2] )

    result = [ 0.0, 0.0 ]
    result[1] = math.asin( s0[2]/r )    # dec in range -90 to +90
    cosaa = (s0[0]/r) / math.cos(result[1] )
    sinaa = (s0[1]/r) / math.cos(result[1] )
    result[0] = math.atan2( sinaa, cosaa )
    if ( result[0] < 0.0 ):
        result[0] = result[0] + twopi
    return result

def glon2ec(ldeg):
# convert galactic longitude to equatorial coordinates
# thanks to Robert Martin Ayers (http://www.robertmartinayers.org/) for an algorithm that works!

    lon = ldeg*toradians    # radians
    radec3 = [lon, 0.0]
    xradec = Transform(radec3, GtoJ)
    ra  = xradec[0]*todegrees
    dec = xradec[1]*todegrees

    return ra, dec

# global variables >>> decmin, decmax, shamin, shamax
def galactic_plane():
# Create bspline curve coordinates in cm to plot

# the Galactic Plane ranges from about 62.8°N to 62.8°S declination in equatorial coordinates
# It crosses SHA 60° 30°N, SHA 90° 23.4392794°5, SHA 240° 30°S, SHA 270° 23.4392794°N
#     in the equatorial plane (data from 2010)
# There can be zero to two galactic plane elements (partial curves) within the plot boundaries
# Construction begins with the LEFT plot border ... increasing SHA ... up to the right plot border.

    DEBUG_gp = False    # 'True' to turn on print statements
    plotscale = sf/10.0 # 1.39 cm to 10 degrees equirectangular
    xoff = x_o * plotscale
    mw  = []        # Milky Way plot list (first element)
    mw2 = []        # Milky Way plot list (second element)
    tX = 0.0        # coordinates for "Galactic Plane" text
    tY = 0.0

    # find equatorial DEClination of galactic plane at left plot border (shamin)
    n = 0
    penustep = 0    # penultimate step
    laststep = 0    # preceding   step
    # two tiny initial steps to determine if SHAdiff is increasing or not...
    step = 0.5      # search LEFT (with DECREASING SHA)...
    ldeg = 117.0    # ... from galactic longitude 117° (& latitude 0°) = SHA 359.977
    minSHAdiff = 360
    lastSHAdiff = 360   # preceding   SHAdiff
    penuSHAdiff = 360   # penultimate SHAdiff
    prevSHA = 360       # preceding   sha
    penuSHA = 360       # penultimate sha
    dec2 = None
    sha2 = None
    SHAdiffdecreasing = False       # only flips once to 'True'
    mode = "search"

    while n < 100:      # arbitrary limit to avoid infinite loop
        ra, dec = glon2ec(ldeg)
        sha = 360.0 - ra
        SHAdiff = abs(sha - shamin)
        SHAdif2 = abs(sha - shamin - 360)
        if SHAdif2 < SHAdiff: SHAdiff = SHAdif2
        if DEBUG_gp: print("{} {:5.1f}  sha= {:7.3f}  SHAdiff= {:7.3f} step {}".format(mode,ldeg,sha,SHAdiff,step))
        mode = "search"

        if n > 0 and SHAdiff > lastSHAdiff:     # SHAdiff increasing
            if n == 1:
                step = 20   # large step if SHAdiff *initially* increasing

        if n > 0 and SHAdiff < lastSHAdiff:     # SHAdiff decreasing
            if n == 1:
                step = 20 if SHAdiff >= 50 else 10
                if SHAdiff < 30: step = 5
                if SHAdiff < 11: step = 1
            if n > 1:
                if step > 10 and SHAdiff < 50: step = 10
                if step > 5 and SHAdiff < 30: step = 5
                if step > 1 and SHAdiff < 11: step = 1
            minSHAdiff = SHAdiff
            GPlon = ldeg    # remember the GP longitude that's closest to shamin (the left plot border)
            dec2 = dec
            sha2 = sha
            SHAdiffdecreasing = True

        if SHAdiffdecreasing:
            if SHAdiff > lastSHAdiff:
                if step > 0.5:
                    ldeg -= laststep + penustep # revert the last 2 steps
                    SHAdiff = penuSHAdiff   # revert value
                    sha   = penuSHA         # revert value
                    step = 0.5              # & try smaller steps
                    mode = "revert"
                else: break

        penuSHAdiff = lastSHAdiff
        lastSHAdiff = SHAdiff
        penustep = laststep
        laststep = step
        penuSHA = prevSHA
        prevSHA = sha
        ldeg += step        # increase GP longitude (decrease SHA)
        if ldeg >= 360: ldeg -= 360
        n += 1
    
    if DEBUG_gp: print("GP dec at SHA = {:7.3f} (~shamin) is {:7.3f}".format(sha2,dec2))
    decLEFT = dec2 if decmin <= dec2 <= decmax else None

    # <<<<<<<<<<<<<<<< find STARTING point of galactic plane curve...
    if decLEFT == None:
        # >>>>>> galactic plane DOES NOT CROSS the left plot border... <<<<<<

        n = 100      # max steps (arbitrary limit)
        laststep = 0
        GPlon1 = GPlon  # remember starting GP longitude
        step = -5       # search RIGHT (with INCREASING SHA)...
        ldeg = GPlon    # ... from LEFT plot border
        GPlon = None
        prevSHA = 360
        mode = "search3"

        while n > 0:
            ra, dec = glon2ec(ldeg)
            sha = 360.0 - ra
            prevSHA = sha
            # check if within SHA & DEC plot range
            if DEBUG_gp: print("{} {:5.1f}  DEC= {:7.3f}  step {}".format(mode,ldeg,dec,step))
            mode = "search3"
            if validSHA(shamin, sha, shamax):
                if decmin <= dec <= decmax:
                    GPlon = ldeg            # remember the closest GP longitude
                    if step == -5:
                        ldeg -= laststep    # revert the last step
                        step = -0.5         # & try smaller steps
                        mode = "revert3"
                    else: break
            laststep = step
            ldeg += step        # decrease GP longitude
            if ldeg < 0: ldeg += 360
            if abs(ldeg - GPlon1) < 0.01:
                GPlon = None
                break # limit search to one GP longitude revolution
            n -= 1

        if GPlon == None:
            return mw, mw2, tX, tY

        # select start of curve to print "Galactic Plane"...
        ra, dec = glon2ec(GPlon)    # start of curve
        sha = 360.0 - ra
        if DEBUG_gp: print("start of GP curve: sha = {:7.3f}".format(sha))
        # next line is rqrd for decmin <= -60° and shamin >= 170°
        if x_o >= 0 and sha > shamax: sha -= 360.0       # when x offset is positive
        tX = ((math.floor(sha / 30.0) * 30.0) + 15.0)/10.0
        tX += x_o/10.0
        if tX == 19.5: tX -= 3.0
        if tX == -0.5: tX = 0.0
        if tX == -1.0: tX += 3.0
        tY = decmax/10 if dec > 0 else decmin/10
        if DEBUG_gp: print("tX = {:.2f}   tY = {:.2f}".format(tX, tY))

    # >>>>>>>>>>>>>>>> PLOT galactic plane curve element...
    
    # NOTE: the *first* value may be just outside the valid SHA range,
    #       (even just below 360° where the rest are > 0°, e.g. -0.023)
    #       however, accept it anyway if the curve begans with shamin!
    firstValue = True
    FAILldeg = None
    UPTOsha = None
    UPTOdec = None
    ldeg = GPlon
    lastldeg = ldeg
    n = 0
    step = -5   # search RIGHT (with INCREASING SHA)

    while n < 100:      # arbitrary limit to avoid infinite loop
        ra, dec = glon2ec(ldeg)
        sha = 360.0 - ra
        PLOTsha = sha
        # when x offset is positive and > zero!
        if n == 0:
            if DEBUG_gp: print("PLOTsha-360: {} {}".format(not validSHA(shamin, sha, shamax),SHAleftofzero(sha)))
            if not validSHA(shamin, sha, shamax) and SHAleftofzero(sha):
                PLOTsha -= 360.0    # if first value is just outside the plot left border
        if x_o >= 0 and PLOTsha > shamax: PLOTsha -= 360.0  # rqrd for shamin >= 170°
        # check if within SHA & DEC plot range
        if decmin < dec < decmax and (firstValue or validSHA(shamin, sha, shamax)):
            if DEBUG_gp: print("PLOT   {:5.1f} DEC= {:7.3f} SHA= {:7.3f} step {}".format(ldeg, dec, PLOTsha, step))
            UPTOsha = sha
            UPTOdec = dec
            x  = "(%04.3f, %04.3f)" %(PLOTsha*plotscale + xoff, dec*plotscale)
            mw.append(x)
        else:
            if DEBUG_gp: print("NOPLOT {:5.1f} DEC= {:7.3f} SHA= {:7.3f} step {}".format(ldeg, dec, PLOTsha, step))
            if validSHA(shamin, sha, shamax): FAILldeg = ldeg
            if step == -5:
                ldeg = lastldeg     # ignore this step
                step = -0.5         # try a smaller step
            else: break
        lastldeg = ldeg
        ldeg += step        # decrease GP longitude
        if ldeg < 0: ldeg += 360
        firstValue = False
        n += 1

    if decLEFT != None:
        # select end of curve to print "Galactic Plane"...
        # check if galactic plane reaches decmax or decmin...
        if abs(UPTOdec - decmax) < 1.0 or abs(UPTOdec - decmin) < 1.0:
            # next line is rqrd for decmax <= 50° and 215° <= shamin <= 300° (approx.)
            if x_o >= 0 and UPTOsha > shamax: UPTOsha -= 360.0  # when x offset is positive
            tX = ((math.floor(UPTOsha / 30.0) * 30.0) + 15.0)/10.0
            tX += x_o/10.0
            if tX == 19.5: tX -= 3.0
            if tX == -0.5: tX = 0.0
            if tX == -1.0: tX += 3.0
            tY = decmax/10 if UPTOdec > 0 else decmin/10
            if DEBUG_gp: print("tX = {:.2f}   tY = {:.2f}".format(tX, tY))

    restSHA = shamax - UPTOsha
    if DEBUG_gp: print("UPTOsha= {:7.3f}  shamax= {}".format(UPTOsha,shamax))
    if shamax < UPTOsha: restSHA += 360
    if DEBUG_gp: print("restSHA = {:7.3f}".format(restSHA))

    if FAILldeg == None:
        if DEBUG_gp: print()
        return mw, mw2, tX, tY

    # >>>>>>>>>>>>>>>> search for a second element of galactic plane curve...
    if restSHA > 5:
        n = 72      # max steps (arbitrary limit)
        step = -5          # search RIGHT (with INCREASING SHA)...
        ldeg = FAILldeg    # ... from last galactic longitude OUTSIDE PLOT BOUNDARIES
        GPlon = None
        mode = "search4"
        while n > 0:
            ra, dec = glon2ec(ldeg)
            sha = 360.0 - ra
            # check if within SHA & DEC plot range
            if DEBUG_gp: print("{} {:5.1f}  DEC= {:7.3f}  step {}".format(mode,ldeg,dec,step))
            mode = "search4"
            if not validSHA(shamin, sha, shamax): break
            if decmin <= dec <= decmax:
                if step == -5:
                    ldeg = lastldeg     # ignore this step
                    step = -1           # & try smaller steps
                    mode = "revert4"
                else:
                    GPlon = ldeg
                    break
            lastldeg = ldeg     # remember the last GP longitude
            ldeg += step        # decrease GP longitude
            if ldeg < 0: ldeg += 360
            n -= 1

    # >>>>>>>>>>>>>>>> PLOT second element of galactic plane curve...
        if GPlon != None:
            ldeg = GPlon
            n = 72      # max steps (arbitrary limit)
            step = -5   # search RIGHT (with INCREASING SHA)
            while n > 0:
                ra, dec = glon2ec(ldeg)
                sha = 360.0 - ra
                PLOTsha = sha
                # check if within SHA & DEC plot range
                if decmin < dec < decmax and validSHA(shamin, sha, shamax):
                    if DEBUG_gp: print("PLOT2  {:5.1f} DEC= {:7.3f} SHA= {:7.3f} step {}".format(ldeg, dec, PLOTsha, step))
                    x  = "(%04.3f, %04.3f)" %(sha*plotscale + xoff, dec*plotscale)
                    mw2.append(x)
                else:
                    if DEBUG_gp: print("NOPLOT {:5.1f} DEC= {:7.3f} SHA= {:7.3f} step {}".format(ldeg, dec, PLOTsha, step))
                    if step == -5:
                        ldeg = lastldeg     # ignore this step
                        step = -0.5         # try a smaller step
                    else: break
                lastldeg = ldeg
                ldeg += step        # decrease GP longitude
                if ldeg < 0: ldeg += 360
                n -= 1

    if DEBUG_gp: print()
    return mw, mw2, tX, tY

#===========================================================

# global variables >>> d00, decmin, decmax, sharng, stars_LD
def showLD(obj, xyMoon=[0.0, 0.0], c='red', hh=0, drawLD=False):
    # connect the Moon to a target object with a straight line
    objname = ""
    out = ""
    s = [None] * 5
    d = [None] * 5

    if len(obj) == 3:
        if obj == "ven":
            objname = "Venus"
            s, d = venusGHA(d00)
        elif obj == "mar":
            objname = "Mars"
            s, d = marsGHA(d00)
        elif obj == "jup":
            objname = "Jupiter"
            s, d = jupiterGHA(d00)
        elif obj == "sat":
            objname = "Saturn"
            s, d = saturnGHA(d00)
        elif obj == "sun":
            objname = "Sun"
            s, d = sunGHA(d00)
        else: return out, None, None

        sha = s[hh]     # pick 00h (hh = 0) or 24h (hh = 4)
        dec = d[hh]     # pick 00h (hh = 0) or 24h (hh = 4)
        #print(objname, sha, dec)

    if len(obj) == 4:
        for line in ld_stardata.navstars.strip().split('\n'):
            x1 = line.index(',')
            objname = line[:x1]
            line = line[x1+1:]
            x2 = line.index(',')
            objnum = line[:x2]
            line = line[x2+1:]
            x3 = line.index(',')
            HIPnum = line[:x3]
            Hpmag = line[x3+1:]
            if objname.startswith(obj): break

        if objname == "": return out, None, None, None, None
        navn = int(objnum)
        name, sha, dec, mag = getstar(objname)
        #print(name, sha, dec, mag)

        global stars_LD
        for item in stars_LD:
            if item[1] == navn: item[2] = True  # True if used for LD

    offX = outofbounds_sha(sha)     # True or False
    Xsha = ext_sha(sha)     # adjust SHA to give correct X-asis coordinate
#    if Xsha != sha: print("  {:13} Xsha= {:7.3f} offX {}".format(objname+":",Xsha, offX))

    xObj = (x_o + Xsha) * sf / 10.0
    yObj = dec * sf / 10.0
    #print(" {:13} x={:7.3f}  y={:7.3f}   {}".format(objname+":",xObj/sf,yObj/sf,offX))
    x0 = (x_o + Xsha) / 10.0    # effective X-axis coordinate of object (on or off plot)

    if not drawLD:      # if only SHA and DEC are required...
        return objname, sha, dec, x0, offX
#   ----------------------------------------------------------

    if config.debug_showLD:
        print("Line to {} is coloured {}".format(objname, c))
    # clip area is the plot boundary
    x1 = 0.0
    y1 = decmin * sf / 10.0
    x2 = sharng * sf / 10.0
    y2 = decmax * sf / 10.0

    dp = "thick,"             # default is 'thin' 0.4pt
    out += r"""
\begin{{scope}}
  \clip ({:.3f},{:.3f}) rectangle ({:.3f},{:.3f});
  \draw[{}{}] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});
\end{{scope}}""".format(x1, y1, x2, y2, dp, c, xObj, yObj, xyMoon[0], xyMoon[1])

    offY = outofbounds_dec(dec)     # -1, 0 or +1
    if (not offX and offY == 0) or objname == "": return out

#   ----------------------------------------------------------
    # add the target object name on the LD line if it's beyond a plot boundary
    crossHor = False
    crossVert = False
    x_max = sharng / 10.0
    y_max = decmax / 10.0
    y_min = decmin / 10.0

    # direction of movement
    dx = xyMoon[0] - xObj
    dy = xyMoon[1] - yObj
    ang = math.atan(dy/dx)
    rot = "%0.3f" %(ang*todegrees)

    # first check if the object is beyond a vertical *AND* horizontal border...
    if offX and offY != 0:      # object beyond a vertical and horizontal border
        # determine which border the line crosses...
        yCross = yObj - (xObj * dy/dx)
        #print(yCross/sf)
        if y_min < yCross/sf < y_max:
            # crosses left (vertical) border
            crossVert = True
        else:
            # crosses lower or upper (horizontal) border
            crossHor = True
        #print("{} offplot: rotate {} Hor {} Vert {}".format(objname,ang*todegrees,crossHor,crossVert))

    if crossVert or (offX and offY == 0):      # object beyond left or right border
        #print(" {} offplot: rotate {}".format(objname,ang*todegrees))
        txtsep = -0.2       # place object name above line
        # coordinates to fix start of object name
        if xObj < 0:
            x3 = 0.1 * sf
            anchor = "west"
        else:
            x3 = (x_max - 0.1) * sf
            anchor = "east"
        y3 = yObj + (x3-xObj)*math.tan(ang)
        #print(x3, y3)
        x = x3 + (txtsep*math.sin(ang))
        y = y3 - (txtsep*math.cos(ang))
        
    if crossHor or (not offX and offY != 0):  # object beyond top or bottom border
        #print("{} offplot: rotate {}".format(objname,ang*todegrees))
        txtsep = -0.2       # place object name above line
        # coordinates to fix start of object name
        if offY < 0:
            y3 = (y_min + 0.1) * sf
            anchor = "west" if ang > 0 else "east"
        else:
            y3 = (y_max - 0.1) * sf
            anchor = "east" if ang > 0 else "west"
        x3 = xObj - (yObj-y3)/math.tan(ang)
        #print(" OFFPLOT: x3 = {:.3f};  y3 = {:.3f} offY = {}  {}".format(x3/sf, y3/sf, offY, anchor))
        x = x3 + (txtsep*math.sin(ang))
        y = y3 - (txtsep*math.cos(ang))

    out += r"""
  \draw[color=%s,anchor=%s] (%0.3f,%0.3f) node[rotate=%s,font=\%s] {%s};""" %(c, anchor, x, y, rot, navstar_fs, objname)

    return out

# global variables >>> shamin, sharng
def set_X_offset(txt = "\n"):
    # ---------- SET THE X-AXIS PLOT OFFSET ----------

    global x_o, shamin, sharng
    x_o = 360 - shamin          # SHA x_offset POSITIVE (for 170 <= shamin < 360)
    # SHA 0° is within plot and not first SHA, but possibly the last (rightmost)
    #    i.e. SHAs < 360° are plotted

    if x_o > sharng: x_o -= 360 # SHA x_offset NEGATIVE (for 0 < shamin < 170)
    # SHAs within plot range are all increasing (left to right) 

    if shamin == 0: x_o = 0     # SHA 0° is first (leftmost) value

    if txt == None: return

    print(" {} SHA scale from {} to {}; sharng = {}; x_o = {}".format(txt, shamin, shamax, sharng, x_o))
    return
    
# <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> 
# <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> 
# <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> 

# global variables >>> d00, decmin, decmax, shamin, shamax, sharng, planet_x, stars_LD
def buildchart(LDlist, H0list, SGNlist, onlystars, quietmode, page1=False):
    #global shamin, shamax, sharng, decmin, decmax, x_max, y_max, y_min, stars_LD
    global shamin, shamax, sharng, decmin, decmax
    global planet_x, stars_LD
    planet_x = []   # empty list of planets added (to check if they partially overlap)
    stars_LD = []   # empty list of LD stars (to print at bottom of page)

    datestr = d00.strftime("%d %b %Y")

    # --- SET THE X-AXIS PLOT OFFSET ---
    set_X_offset(None if quietmode else "\n PLOT")

    if not quietmode:
        print(" PLOT DEC scale from {} to {}".format(decmin, decmax))
        #print(" SHA scale is from {} to {}".format(shamin, shamax))
        #print(" exclude SHA from {} to {}".format(shamax, shamin))
        #print(" X-offset 'x_o' = {}  SHA range = {}".format(x_o,sharng))

    # tikz line thickness...
    # ultra thin    = 0.1pt
    # very thin     = 0.2pt
    # thin          = 0.4pt (default)
    # semithick     = 0.6pt
    # thick         = 0.8pt
    # very thick    = 1.2pt
    # ultra thick   = 1.6pt

    # parameters for 'A4/Letter Landscape'
    #bb = "line width=1.85pt"    # bounding box thickness
    bb = "ultra thick"          # bounding box thickness
    ecliptic_indentA = 8.20   # for 'ECLIPTIC'
    ecliptic_indentB = -5.0   # for 'ECLIPTIC'
    ecliptic_raiseB = -2.1

    tex = ""

    if not page1:
        tex += r"""
\newpage"""

    # A4/Letter landscape (center vertically)
    tex += r"""
  \hspace{0pt}
  \vfill"""
    
    tex += r"""
\begin{center}                  % center picture horizontally
\begin{tikzpicture}"""

# --------------------------------------------------------------
# first draw the galactic plane (so it is in the background)
    mw, mw2, tX, tY = galactic_plane()

    if len(mw) > 0:
        tex += r"""
% plot galactic plane first element (so it's in the background)
  \draw[dashed,very thick,color=Tan] plot[smooth,tension=0.5] coordinates{
"""
        for ndx in range(len(mw)):
            tex += r"""%s """ %mw[ndx]
        tex += r"""};"""

    if len(mw2) > 0:
        tex += r"""
% plot galactic plane second element (so it's in the background)
  \draw[dashed,very thick,color=Tan] plot[smooth,tension=0.5] coordinates{
"""
        for ndx in range(len(mw2)):
            tex += r"""%s """ %mw2[ndx]
        tex += r"""};"""
    if tY != 0:
        if tY > 0:
            tYg = (tY + 0.38)*sf
            tYp = (tY + 0.16)*sf
        else:
            tYg = (tY - 0.17)*sf
            tYp = (tY - 0.39)*sf
        tX0 = tX*sf # + x_o*sf/10
        tex += r"""
  \node[color=darkTan,font=\{}] at ({:.3f},{:.3f}) {{Galactic}};
  \node[color=darkTan,font=\{}] at ({:.3f},{:.3f}) {{Plane}};""".format(
navstar_fs,tX0,tYg,
navstar_fs,tX0,tYp)

# --------------------------------------------------------------
# draw plot inner vertical lines & horizontal borders with ticks
    tex += r"""
% draw plot inner vertical lines & horizontal borders with tickmarks..."""
    x = 0
    xmax = sharng / 10.0
    ymax = decmax / 10.0
    ymin = decmin / 10.0
    sha = shamin
    o5 = sha % 10           # 0 or 5

    while x <= xmax:
        #print(x, o5, sha)
        if x == 0 or x == xmax or sha % 30 == 0:
            # draw a vertical line
            tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
x*sf,ymin*sf,x*sf,ymax*sf)
        if sha % 30 == 0:
            # upper & lower SHA axis value
            tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\textbf {{{:d}°}}}};
  \node[font=\{}] at ({:.3f},{:.3f}) {{\textbf {{{:d}°}}}};""".format(
title_fs,x*sf,(ymax+0.28)*sf,sha,
title_fs,x*sf,(ymin-0.28)*sf,sha)
        if not (sha % 30 == 0) and not (x == 0 or x == xmax):
            # draw tick marks on upper & lower plot borders
            tex += r"""
  \draw[thick] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});
  \draw[thick] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
x*sf,ymax*sf,x*sf,ymax*sf-sf/7,
x*sf,ymin*sf,x*sf,ymin*sf+sf/7)
        if o5 > 0:
            x += 0.5            # initial step 
            sha = shaadd(sha,5)
            o5 = 0
        elif xmax - x == 0.5:   # final step
            x += 0.5
            sha = shaadd(sha,5)
        else:
            x += 1
            sha = shaadd(sha,10)

# -------------------------------------------------------------------
# draw plot inner horizontal lines & vertical borders with tick marks
    tex += r"""
% draw plot inner horizontal lines & vertical borders with tickmarks..."""
    y = ymin
    dec = decmin
    o5 = dec % 10           # 0 or 5
    while y <= ymax:
        #print(y, o5, dec)
        if y == ymin or y == ymax or dec % 30 == 0:
            # draw a horizontal line
            tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
0,y*sf,xmax*sf,y*sf)
        if dec % 10 == 0:
            # left DEC axis value
            tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.7}}[1.0]{{\textbf {{{}°}}}}}};""".format(
title_fs,-sf/4.09,y*sf,abs(dec))
        if not (dec % 30 == 0) and not (y == ymin or y == ymax):
            # draw tick marks on left & right plot borders
            tex += r"""
  \draw[thick] (0.0,{:.3f}) -- ({:.3f},{:.3f});
  \draw[thick] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
y*sf,sf/7,y*sf,
xmax*sf,y*sf,xmax*sf-sf/7,y*sf)

        if o5 > 0:
            y += 0.5            # initial step 
            dec += 5
            o5 = 0
        elif ymax - y == 0.5:   # final step
            y += 0.5
            dec += 5
        else:
            y += 1
            dec += 10

# --------------------------------------------------------------
# now plot the ecliptic from 0° to 180° over the plot area

    eps = 23.43927945   # eps = 23° 26' 21".406 for 2010.
    tex += r"""
% plot the ecliptic from 0° to 180°
\begin{{scope}}
  \clip ({:.3f},{:.3f}) rectangle ({:.3f},{:.3f});
  \pgfsetlinewidth{{0.5pt}}
  \pgfsetstrokecolor{{Teal}}
  \pgfsetdash{{{{0.2cm}}{{0.2cm}}{{0.02cm}}{{0.2cm}}}}{{0pt}}
  \pgfpathmoveto{{\pgfpoint{{{:.3f}cm}}{{0cm}}}}
  \pgfpathsine{{\pgfpoint{{{:.3f}cm}}{{{:.3f}cm}}}}
  \pgfpathcosine{{\pgfpoint{{{:.3f}cm}}{{{:.3f}cm}}}}
  \pgfusepath{{stroke}}
  \pgfsetlinewidth{{0.15mm}}
  \draw [decorate,decoration={{text along path,raise=0.45ex,text align={{left indent={:.3f}cm}},text={{|\gangnamstyle|ECLIPTIC}}}}] ({:.3f}cm,{:.3f}cm) sin ({:.3f}cm,{:.3f}cm);
  \pgfsetstrokecolor{{Black}}
\end{{scope}}""".format(
0,ymin*sf,xmax*sf,ymax*sf,
x_o/10*sf,
9*sf,-eps*sf/10,
9*sf,eps*sf/10,
ecliptic_indentA,x_o/10*sf,0.0,(x_o+90)/10*sf,-eps*sf/10)

# now plot the ecliptic from 180° to 360° over the plot area
    xx_o = x_o + 180 if x_o <= 0 else x_o - 180
    tex += r"""
% plot the ecliptic from 180° to 360°
\begin{{scope}}
  \clip ({:.3f},{:.3f}) rectangle ({:.3f},{:.3f});
  \pgfsetlinewidth{{0.5pt}}
  \pgfsetstrokecolor{{Teal}}    % change to Teal
  \pgfsetdash{{{{0.2cm}}{{0.2cm}}{{0.02cm}}{{0.2cm}}}}{{0pt}}
  \pgfpathmoveto{{\pgfpoint{{{:.3f}cm}}{{0cm}}}}
  \pgfpathsine{{\pgfpoint{{{:.3f}cm}}{{{:.3f}cm}}}}
  \pgfpathcosine{{\pgfpoint{{{:.3f}cm}}{{{:.3f}cm}}}}
  \pgfusepath{{stroke}}
  \pgfsetlinewidth{{0.15mm}}
  \draw [decorate,decoration={{text along path,raise={:.1f}ex,text align={{left indent={:.3f}cm}},text={{|\gangnamstyle|ECLIPTIC}}}}] ({:.3f}cm,{:.3f}cm) cos ({:.3f}cm,{:.3f}cm);
  \pgfsetstrokecolor{{Black}}
\end{{scope}}""".format(
0,ymin*sf,xmax*sf,ymax*sf,
xx_o/10*sf,
9*sf,eps*sf/10,
9*sf,-eps*sf/10,
ecliptic_raiseB,ecliptic_indentB,(xx_o+90)/10*sf,eps*sf/10,(xx_o+180)/10*sf,0.0)

# ------------------- B O R D E R  lines --------------------

  # NOTE: adding -0.6pt is not necessary with "-- cycle" ...
    tex += r"""
% draw thick bounding box
\begin{{scope}}[{}]
  \draw plot coordinates {{({:.3f},{:.3f}) ({:.3f},{:.3f}) ({:.3f},{:.3f}) ({:.3f},{:.3f})}} -- cycle;
\end{{scope}}""".format(
bb,-sf/1.8,ymin*sf-sf/1.8,
-sf/1.8,ymax*sf+sf/1.8,
xmax*sf+sf/2.2,ymax*sf+sf/1.8,
xmax*sf+sf/2.2,ymin*sf-sf/1.8)

# ------------- Text outside B O R D E R  lines -------------

    tex += r"""
% text outside border lines
  \node[font=\{}] at ({:.3f},{:.3f}) {{SIDEREAL HOUR ANGLE}};
  \node[font=\{}, anchor=east] at ({:.3f},{:.3f}) {{\textcopyright\enspace 2022 Andrew Bauer}};
  \node[font=\{}] at ({:.3f},{:.3f}) {{\textbf{{LUNAR DISTANCE (SHA {}° to {}°)\quad{}}}}};
  \node[rotate=90,font=\{}] at ({:.3f},0.0) {{DECLINATION}};
  \node[rotate=90,font=\{}] at ({:.3f},{:.3f}) {{South}};
  \node[rotate=90,font=\{}] at ({:.3f},{:.3f}) {{North}};""".format(
title_fs,(xmax/2)*sf,(ymin-0.89)*sf,
navstar_fs,(xmax)*sf,(ymin-0.89)*sf,
title_fs,(xmax/2)*sf,(ymax+0.84)*sf,shamin,shamax,datestr,
title_fs,-0.9*sf,
ns_fs,-0.9*sf,-2.67*sf,
ns_fs,-0.9*sf,2.67*sf)

# -------------------- B O R D E R  end ---------------------

    tex += getc("Tucana")

    tex += getc("Pisces")

    tex += getc("Pegasus",['del','alf','bet','gam','eps'])

    tex += addstar("Alpheratz",1,'blue','right,xshift=-0.3ex,yshift=-2.0ex','xshift=0.3ex')
    tex += addstar("Markab",57,'blue','right','yshift=-1.7ex')
    tex += addstar("Scheat",0,'black','right,xshift=0.0ex,yshift=-0.5ex')
    tex += addstar("Algenib",0,'black','right,xshift=0.0ex,yshift=-1.7ex')
    tex += addstar("Enif",54,'blue','above,yshift=0.4ex')

    tex += getc("Aquarius",['alf','bet'])
    tex += addstar("Sadalmelik",0,'black','right,xshift=-1.0ex,yshift=1.5ex')
    tex += addstar("Sadalsuud",0,'black','right,xshift=0.0ex,yshift=1.5ex')

    tex += getc("Grus",['alf'])
    tex += addstar("Al Na'ir",55,'blue','below,yshift=-0.4ex')

    tex += getc("Piscis Austrinus",['alf'],'consGrey')
    tex += addstar("Fomalhaut",56,'blue','left,xshift=1.0ex,yshift=2.2ex','xshift=0.8ex,yshift=-0.6ex')

    tex += getc("Lacerta")

    tex += getc("Cepheus",['alf'])
    tex += addstar("Alderamin",0,'black','below,xshift=0.5ex,yshift=0.3ex')

    tex += getc("Indus")

    tex += getc("Capricornus",['del'])
    tex += addstar("Deneb Algedi",0,'black','left')

    tex += getc("Delphinus")

    tex += getc("Cygnus",['alf','gam','bet'])
    tex += addstar("Deneb",53,'blue','right,xshift=0.6ex,yshift=-0.4ex','xshift=2.4ex,yshift=2.3ex')
    tex += addstar("Sadr",0,'black','right,yshift=1.0ex')
    tex += addstar("Albireo",0,'black','left')

    tex += getc("Sagitta")

    tex += getc("Aquila",['alf','bet','gam'])
    tex += addstar("Altair",51,'blue','above,xshift=-3.2ex,yshift=0.1ex','xshift=1.2ex,yshift=-0.4ex')
    tex += addstar("Alshain",0,'black','left,xshift=0.0ex,yshift=-0.1ex')
    tex += addstar("Tarazed",0,'black','right,xshift=0.0ex,yshift=1.0ex')

    tex += getc("Microscopium")

    tex += getc("Octans")

    tex += getc("Pavo",['alf'])
    tex += addstar("Peacock",52,'blue','right,xshift=0.2ex,yshift=0.0ex','xshift=-0.2ex,yshift=1.0ex')

    tex += getc("Lyra",['alf'])
    tex += addstar("Vega",49,'blue','right,xshift=0.3ex,yshift=0.0ex','xshift=2.8ex,yshift=-2.5ex')

    tex += getc("Sagittarius",['eps','sig'])
    tex += addstar("Nunki",50,'blue','left,xshift=0.0ex,yshift=1.6ex')
    tex += addstar("Kaus Aust.",48,'blue','left,xshift=-4.0ex,yshift=-1.6ex','xshift=-5.0ex')

    tex += getc("Serpens_Cauda",[],'PastelOrange')

    tex += getc("Hercules",['alf'])
    tex += addstar("Rasalgethi",0,'black','right,xshift=0.0ex,yshift=1.1ex')

    tex += getc("Ophiuchus",['alf','bet','eta'])
    tex += addstar("Rasalhague",46,'blue','above,xshift=-2.5ex,yshift=0.2ex','xshift=1.5ex')
    tex += addstar("Cebalrai",0,'black','right,xshift=0.0ex,yshift=1.0ex')
    tex += addstar("Sabik",44,'blue','right,xshift=0.2ex,yshift=0.0ex')

    tex += getc("Ara")

    tex += getc("Scorpius",['alf','lam'],'consGrey')
    tex += addstar("Antares",42,'blue','right,xshift=0.2ex,yshift=-1.1ex','yshift=1.6ex')
    tex += addstar("Shaula",45,'blue','left,xshift=0.6ex,yshift=1.8ex','xshift=-2.5ex,yshift=-2.9ex')
    tex += adddot("HIP78727")

    tex += getc("Draco",['gam','eta'])
    tex += addstar("Eltanin",47,'blue','left,xshift=-0.1ex,yshift=0.2ex','xshift=-0.8ex,yshift=-1.6ex')
    tex += addstar("Athebyne",0,'black','left')
    tex += getc("Draco2",['the'])

    tex += getc("Tri. Aust.",['alf'])
    tex += addstar("Atria",43,'blue','right,xshift=-0.3ex,yshift=-1.0ex')

    tex += getc("Serpens_Caput",['alf'],'PastelOrange')
    tex += addstar("Unukalhai")

    tex += getc("Cor. Bor.",['alf'])
    tex += addstar("Alphecca",41,'blue','right,xshift=-0.2ex,yshift=-1.3ex','xshift=0.0ex,yshift=1.6ex')

    tex += getc("Libra",['alf'])
    tex += addstar("Zuben'ubi",39,'blue','right,xshift=0.2ex,yshift=-0.8ex','xshift=5.0ex,yshift=-3.5ex')

    tex += getc("Apus")

    tex += getc("Lupus")

    tex += getc("Centaurus",['alf','bet','the'])
    tex += addstar("Hadar",35,'blue','right,xshift=0.4ex')
    tex += addstar("Menkent",36,'blue','right,xshift=0.3ex,yshift=0.0ex','yshift=0.7ex')
    tex += addstar("Rigil Kent.",38,'blue','below,yshift=-0.4ex')

    tex += getc("Ursa_Minor",['alf','bet'])
    tex += addstar("Kochab",40,'blue','right,xshift=0.0ex,yshift=-1.4ex')
    tex += addstar("Polaris",0,'black','right,xshift=0.2ex,yshift=0.5ex')

    tex += getc("Boötes",['alf','eps'])
    tex += addstar("Arcturus",37,'blue','right,xshift=0.3ex,yshift=1ex','yshift=0ex')
    tex += addstar("Izar")

    tex += getc("Canes Venatici")

    tex += getc("Virgo",['alf','eps'])
    tex += addstar("Spica",33,'blue','right,xshift=0.2ex,yshift=0.0ex','xshift=2.2ex,yshift=-2.2ex')
    tex += addstar("Vindemiatrix",0,'black','left,xshift=0.0ex,yshift=0.0ex')

    tex += getc("Hydra2",[],'ColumbiaBlue')

    tex += getc("Coma_Berenices")

    tex += getc("Corvus",['gam'])
    tex += addstar("Gienah",29,'blue','above,xshift=1.4ex,yshift=0.2ex')

    tex += getc("Musca")

    tex += getc("Crux",['alf','gam'])
    tex += addstar("Acrux",30,'blue','above,xshift=0.4ex,yshift=0.2ex')
    tex += addstar("Gacrux",31,'blue','left,xshift=-0.3ex,yshift=0.6ex')

    tex += getc("Crater")

    tex += getc("Ursa Major",['eps','alf','eta','zet','bet','gam','del','ggg'])
    tex += addstar("Alioth",32,'blue','left,xshift=0.0ex,yshift=1.0ex','yshift=-1.7ex')
    tex += addstar("Dubhe",27,'blue','left,yshift=1.0ex')
    tex += addstar("Alkaid",34,'blue')
    tex += addstar("Mizar",0,'black','right,yshift=-0.8ex')  # partially overlaid by Alcor
    tex += addstar("Alcor",0,'black','left')
    tex += addstar("Megrez",0,'black','left,yshift=1.0ex')
    tex += addstar("Phecda",0,'black','left,yshift=-0.2ex')
    tex += addstar("Merak",0,'black','left,yshift=0.8ex')
    #tex += addstar("Muscida",0,'black')
    #tex += addstar("Talitha",0,'black','left')

    tex += adddot("HIP55203")

    tex += getc("Leo",['bet','alf','gam'])
    tex += addstar("Denebola",28,'blue','right,xshift=0.0ex,yshift=-1.3ex','xshift=1.4ex,yshift=1.9ex')
    tex += addstar("Regulus",26,'blue','left,xshift=-0.2ex,yshift=0.0ex','xshift=-1.7ex,yshift=-2.0ex')
    tex += addstar("Algieba",0,'black','right,xshift=0.0ex,yshift=-0.2ex')

    tex += getc("Sextans")

    tex += getc("Hydra",['alf'],'ColumbiaBlue')
    tex += addstar("Alphard",25,'blue')

    tex += getc("Cancer")

    tex += getc("Chamaeleon")

    # place before 'Puppis' (it connects to 'Puppis zet')
    tex += getc("Pyxis",['Pze'])

    tex += getc("Lynx")

    tex += getc("Volans")

    # place before 'Vela' (it connects to 'Vela gam' & 'Vela del')
    # place before 'Puppis' (it connects to 'Puppis nu.')
    tex += getc("Carina",['alf','bet','eps','VEg','VEd','Pnu'])
    tex += addstar("Canopus",17,'blue','right,xshift=0.4ex,yshift=-0.6ex','yshift=0.6ex')
    tex += addstar("Avior",22,'blue','below,xshift=0.0ex,yshift=-0.3ex')
    tex += addstar("Miaplacidus",24,'blue','right,xshift=0.1ex,yshift=-0.4ex')

    # place before 'Vela' (it connects to 'Vela gam')
    tex += getc("Puppis",[],'consGrey')

    tex += getc("Vela",['lam'],'OliveDrab')
    tex += addstar("Suhail",23,'blue','above,xshift=1.6ex,yshift=0.2ex')

    tex += getc("Monoceros")

    tex += getc("Canis Minor",['alf'])
    tex += addstar("Procyon",20,'blue','right,xshift=0.2ex,yshift=-0.3ex')
    
    tex += getc("Gemini",['bet','gam'])
    tex += addstar("Pollux",21,'blue','left,xshift=-0.2ex,yshift=1.3ex')
    tex += addstar("Alhena",0,'black','xshift=3.8ex,yshift=0.0ex')
    tex += addstar("Castor",0,'black','above')

    tex += getc("Canis_Major",['alf','eps'])
    tex += addstar("Sirius",18,'blue','right,xshift=0.3ex,yshift=1.6ex','xshift=6.1ex,yshift=4.0ex')
    tex += addstar("Adhara",19,'blue','right,xshift=0.4ex,yshift=0.8ex','xshift=1.9ex,yshift=-2.4ex')

    tex += getc("Orion",['bet','gam','eps','alf','kap'])
    tex += addstar("Rigel",11,'blue','right,xshift=0.8ex,yshift=-0.8ex','xshift=6.6ex,yshift=-3.2ex')
    tex += addstar("Bellatrix",13,'blue','right,xshift=-0.5ex,yshift=1.7ex','xshift=5.5ex,yshift=-1.3ex')
    tex += addstar("Alnilam",15,'blue','left,xshift=-1.2ex,yshift=-0.5ex','xshift=-6.4ex,yshift=-2.9ex')
    tex += addstar("Betelgeuse",16,'blue','left,xshift=-0.4ex,yshift=0.5ex','xshift=-5.9ex,yshift=-1.5ex')
    tex += addstar("Saiph",0,'black','xshift=3.6ex,yshift=-0.2ex')

    tex += getc("Columba")
    
    tex += getc("Dorado")

    tex += getc("Lepus")

    # place before 'Taurus' (they both share 'Elnath')
    tex += getc("Auriga",['alf','gam','bet'])
    tex += addstar("Capella",12,'blue','left,xshift=-0.3ex,yshift=0.3ex')
    tex += addstar("Menkalinan",0,'black','left,yshift=-0.3ex')

    tex += getc("Camelopardalis")

    tex += getc("Taurus",['alf','bet','eta'])
    tex += addstar("Aldebaran",10,'blue','left,xshift=-0.4ex','xshift=-3.4ex,yshift=2.1ex')
    tex += addstar("Elnath",14,'blue','right,xshift=2.0ex,yshift=-0.2ex','xshift=-0.1ex,yshift=-0.3ex')
    tex += addstar("Alcyone",0,'black','right,yshift=1.0ex')
    tex += addtext("Alcyone","(Pleiades)",'black','right,yshift=-1.0ex')

    tex += getc("Reticulum")

    tex += getc("Eridanus",['alf','the'])
    tex += addstar("Achernar",5,'blue','right,xshift=0.3ex')
    tex += addstar("Acamar",7,'blue','above,yshift=0.4ex')

    tex += getc("Hydrus")

    tex += getc("Cetus",['bet','alf'])
    tex += addstar("Diphda",4,'blue','right,xshift=0.0ex,yshift=-0.2ex','yshift=-1.2ex')
    tex += addstar("Menkar",8,'blue','below,xshift=0.0ex,yshift=-0.2ex','xshift=-1.2ex')

    tex += getc("Perseus",['alf','bet'])
    tex += addstar("Mirfak",9,'blue','right,xshift=-0.1ex,yshift=-1.4ex','yshift=0.8ex')
    tex += addstar("Algol",0,'black')

    tex += getc("Aries",['alf','bet'])
    tex += addstar("Hamal",6,'blue','right,xshift=-0.5ex,yshift=2.2ex')
    tex += addstar("Sheratan",0,'black','left,xshift=-0.4ex')

    tex += getc("Phoenix",['alf'])
    tex += addstar("Ankaa",2,'blue','right,xshift=0.2ex,yshift=0.0ex','yshift=0.8ex')

    tex += getc("Sculptor")

    tex += getc("Triangulum")

    tex += getc("Cassiopeia",['alf','bet'])
    tex += addstar("Schedar",3,'blue','left,xshift=0.0ex,yshift=-0.3ex','xshift=0.4ex')
    tex += addstar("Caph",0,'black','above')

    tex += getc("Andromeda",['alf','bet','gam'])
    tex += addstar("Mirach",0,'black','left')
    tex += addstar("Almach",0,'black','left')

    if not onlystars:
        # our solar system (closest objects last)
        tex += addSUN()
        tex += addPLANET("Venus")
        tex += addPLANET("Mars")
        tex += addPLANET("Jupiter")
        tex += addPLANET("Saturn")

        newMoon = True if len(LDlist) == 0 else False
        texMoon, xyMoon00, xyMoon24 = addMOON(newMoon)
        tex += texMoon
    else: texMoon = ""

    #   colours for the 8 max. Lunar Distance Moon-to-object connecting lines
    LDcolour = ['Dark chestnut', 'Celestial blue', 'Rose pink', 'Green (pigment)', 'Orange (color wheel)', 'Lavender indigo', 'Gold (metallic)', 'Dark turquoise']

    #   maintain object colour from page to page. It's confusing if the same
    #       object has a different colour on the next day (= next page)
    global PREVobjects      # list of previous LD objects
    global PREVobjColour    # list of previous LD object-colour tuples (object, offset in LDcolour[0 to 7])
    ColourObj = []          # curent list of colour assinment tuples (for this day)
    ColourInUse = [False] * len(LDcolour)

    # draw Lunar Distance lines (connect a celestial object to the Moon)
    if texMoon != "":
        # first collect all colour assignments on the same object from the previous day in ColourObj
        for LDobj in LDlist:
            if LDobj in set(PREVobjects):
                j = PREVobjects.index(LDobj)
                lastObj = PREVobjColour[j]
                ColourObj.append((LDobj, lastObj[1]))
                ColourInUse[lastObj[1]] = True
        # now all the colour assignments from the previous day are "reserved"
        i = 0
        for LDobj in LDlist:
            if LDobj in set(PREVobjects):   # grab an assigned colour ...
                j = PREVobjects.index(LDobj)
                lastObj = PREVobjColour[j]
                ObjCol = lastObj[1]
            else:                           # ... if none, assign a new colour
                ObjCol = ColourInUse.index(False)
                ColourObj.append((LDobj, ObjCol))
                ColourInUse[ObjCol] = True

            take24 = True if H0list[i].find("circ") == -1 else False
            # Moon coordinates (at 00h or 24h) for the LD line
            xyMoon = xyMoon24 if take24 else xyMoon00
            hh = 4 if take24 else 0    # 4 = 24h; 0 = 00h for Sun and planets
            tex += showLD(LDobj, xyMoon, LDcolour[ObjCol], hh, True)
            if SGNlist[i] == u"\u00B1":     # plus-minus symbol
                tex += showLD(LDobj, xyMoon24, LDcolour[ObjCol], 2, True)
            i += 1

        PREVobjColour = ColourObj                   # save colour assignments for the next page
        PREVobjects = [co[0] for co in ColourObj]   # save list of LD objects for the next page
        # Note: PREVobjects has the same contents as 'LDlist' but in a sequence that matches PREVobjColour

        if config.debug_strategy:
            print("ColourObj:\n{}".format(ColourObj))

# ------------- Text outside B O R D E R  lines -------------

    txt = ""
    n = 0       # output 4 maximum
    # first output the navigational stars used as an LD target
    for item in stars_LD:
        if n > 3: break
        if item[2]:         # if used as a LD object (connected to the Moon)
            n += 1
            txt += r"""\fontfamily{phv}\%s\color{airforceBlue}\textbf{%s}\fontfamily{cmr}\color{black}\%s = {%s}\quad""" %(navnum_fs,item[1],navstar_fs,item[0])

    for item in stars_LD:
        if n > 3: break
        if not item[2]:     # if not used as a LD object (connected to the Moon)
            n += 1
            txt += r"""\fontfamily{phv}\%s\color{airforceBlue}\textbf{%s}\fontfamily{cmr}\color{black}\%s = {%s}\quad""" %(navnum_fs,item[1],navstar_fs,item[0])

    if txt != "":
        tex += r"""
  \node[anchor=west] at (%0.3f,%0.3f) {%s};""" %(-sf/1.8,(ymin-0.89)*sf,txt)
# -------------- terminate TikZ picture --------------

    tex += r"""
\end{tikzpicture}
\end{center}"""

    # A4/Letter landscape (center vertically)
    tex += r"""
  \vfill
  \hspace{0pt}"""
    return tex

#--------------------------
#   external entry point
#--------------------------

# global variables >>> d00, decmin, decmax, PREVobjColour, PREVobjects, shamin, shamax, sharng, t00
def makeLDcharts(first_day, strat, daystoprocess, outfile, ts, onlystars, quietmode):

    global d00, t00, shamin, shamax, sharng, decmin, decmax, PREVobjColour, PREVobjects
    init_A4(ts, first_day)    # initialize variables

    DEBUG_m2 = False            # 'True' to print each LD object

    PREVobjects = []        # list of LD objects from previous day
    PREVobjColour = []      # list of LD object-colour tuples from previous day

    d00 = first_day
##    print("first_day = {}; type = {}".format(first_day,type(first_day)))
##    print("d00 = {}; type = {}".format(d00,type(d00)))

    # A4     = 210mm x 297mm (8.27 x 11.69 in)
    # Letter = 8.5 x 11 in   (216mm x 279mm)
    if config.pgsz == "A4": # parameters for A4 Landscape
        ori = "a4paper,landscape"
        tm = "5mm"
        bm = "5mm"
        lm = "2mm"
        rm = "2mm"
        tm1 = "15mm"    # first page...
        bm1 = "15mm"
        lm1 = "10mm"
        rm1 = "10mm"
        parsep = "[12pt]"
    else:                   # parameters for Letter Landscape
        ori = "letterpaper,landscape"
        tm = "5mm"
        bm = "5mm"
        lm = "2mm"
        rm = "2mm"
        tm1 = "13mm"    # first page...
        bm1 = "13mm"
        lm1 = "10mm"
        rm1 = "10mm"
        parsep = "[8pt]"

    outfile.write(beginPDF(ori,tm,bm,lm,rm))
    firstpage = False

    if not config.DPonly:
        outfile.write(Page1(tm1,bm1,lm1,rm1,parsep))
        firstpage = True

    # determine most suitable LD target objects
    while daystoprocess > 0:
        if not quietmode: print()
        print('------ Process: {} ------'.format(d00.strftime("%d %b %Y")))

        winner = "A"
        LDlist = []
        LDargs = False
        SHAlist = []
        DEClist = []
        t00 = ts.utc(d00.year, d00.month, d00.day, 0, 0, 0)    # update global variable

        shaMoon, decMoon = moonGHA(d00)
        #print("Moon 00h sha = {}, dec = {}".format(shaMoon[0], decMoon[0]))
        #print("Moon 12h sha = {}, dec = {}".format(shaMoon[1], decMoon[1]))
        #print("Moon 24h sha = {}, dec = {}".format(shaMoon[2], decMoon[2]))

        # IMPORTANT: the Moon still needs to be included on the chart ...
        #    in case all LD targets are to one side (left, right, above or below)
        SHAlist.append(shaMoon[0])
        SHAlist.append(shaMoon[2])
        DEClist.append(decMoon[0])
        DEClist.append(decMoon[2])

#   ---------------- A: try with Moon centered and DEC -55 to + 55 ----------------

        if not quietmode:
            print("\n A tactic... SHA: Moon centered DEC: -55 to +55")
        # set defaults for X- and Y-axis ...
        sharng = 190
        shalo = shaMoon[0] - (sharng/2.0)
        if shalo < 0: shalo += 360
        shamin = math.floor(shalo/5.0) * 5  # round to lower 5
        #shamax = math.ceil(shahi/5.0) * 5   # round to higher 5
        shamax = shamin + sharng
        if shamax >= 360: shamax -= 360
        x_max = sharng / 10
        if shamin < 0: shamin += 360
        set_X_offset(None if quietmode else "  try")    # --- SET THE X-AXIS PLOT OFFSET ---

        # define default DEC range, e.g. for New Moon
        decmin = -55
        y_min = math.floor(decmin/5.0) / 2.0    # round to lower 0.5
        decmax = 55
        y_max = math.ceil(decmax/5.0) / 2.0     # round to higher 0.5

        # check for out-of-bounds target objects
        inbounds = 0
        oobLEFT = 0
        oobRIGHT = 0
        oobLOW = 0
        oobHIGH = 0

        LDlist, H0list, SGNlist = LDstrategy('B')
        for item in LDlist:
            if item in LDtargets:
                objname, sha, dec, x0, offX = showLD(item)
                SHAlist.append(sha)
                DEClist.append(dec)
                u = outofbounds_dec(dec)
                v = outsideplot(sha)
                if DEBUG_m2: print(" A {:13} sha= {:7.3f} v= {} x0= {}".format(objname+":",sha, v, x0))
                if outofbounds_sha(sha):
                    if v == -1: oobLEFT += 1
                    if v == +1: oobRIGHT += 1
                    continue
                elif u == -1: oobLOW += 1
                elif u == +1: oobHIGH += 1
                else: inbounds += 1

        LDlist_Swth, LDlist_Smin, LDlist_Smax = group_width(SHAlist)
        LDlist_Dmid, LDlist_Dmin, LDlist_Dmax = group_range(DEClist)

        ##print(".LDlist = {}".format(LDlist))
        if not quietmode:
            print("   {} LD objects: {} within plot; {} LEFT; {} RIGHT; {} LOW; {} HIGH".format(len(LDlist),inbounds,oobLEFT,oobRIGHT,oobLOW,oobHIGH))
            #print(" A LD objects: SHA width= {:7.3f}  SHA_min={:7.3f}  SHA_max={:7.3f}".format(LDlist_Swth,LDlist_Smin,LDlist_Smax))
            #print(" A LD objects: DEC mid= {:7.3f}  DEC_min={:7.3f}  DEC_max={:7.3f}".format(LDlist_Dmid,LDlist_Dmin,LDlist_Dmax))

#   ---------------- B: if all objects within plot (or New Moon), center DEC only   ----------------
#   ---------------- B: else, try RIGHT-ALIGNED plot & centered DEC ----------------

        # adjust SHA range
        if inbounds == len(LDlist):     # no SHA adjustment if all objects within plot
            winner = "B"
            if not quietmode:
                print("\n B tactic... SHA: ok (all within plot) DEC: objects centered; +80 max; -80 min")
            just = 0                # justification: CENTERED
            excess = 190 - LDlist_Swth
            shalo = LDlist_Smin - excess/2
            if shalo < 0: shalo += 360
            shamin = math.floor(shalo/5.0) * 5  # round to lower 5
            shamax = shamin + 190
            if shamax >= 360: shamax -= 360
        elif inbounds < len(LDlist):    # some objects are off-plot... e.g. 01.10.2021 (1 LOW)
            winner = "B"
            if LDlist_Swth < 190:       # center plot if SHA width under 190°
                if not quietmode:
                    print("\n B tactic... SHA: objects centered DEC: objects top-aligned; +80 max; -80 min")
                just = 0                # justification: CENTERED
                excess = 190 - LDlist_Swth
                shalo = LDlist_Smin - excess/2
                if shalo < 0: shalo += 360
                shamin = math.floor(shalo/5.0) * 5  # round to lower 5
                shamax = shamin + 190
                if shamax >= 360: shamax -= 360
                # due to rounding down, 27 Sep 2022 is an example where this is needed:
                if LDlist_Smax > shamax: shamin, shamax = sha_inc(shamin, shamax)
            else:
                if not quietmode:
                    print("\n B tactic... SHA: objects right-aligned DEC: objects centered; +80 max; -80 min")
                # RIGHT-ALIGNED: adjust the plot range to end with LDlist_smax...
                just = +1               # justification: RIGHT-ALIGNED
                shahi = LDlist_Smax
                shamax = math.ceil(shahi/5.0) * 5   # round to higher 5
                shamin = shamax - sharng
                if shamin < 0: shamin += 360
                # ensure right-alignment includes the Moon at 24h !!!
                while not validSHA(shamin,shaMoon[2],shamax):
                    # decrement the range until it includes the Moon...
                    shamax = shaadd(shamax,-5.0)
                    shamin = shaadd(shamin,-5.0)
        set_X_offset(None if quietmode else "  try")    # --- SET THE X-AXIS PLOT OFFSET ---

        # adjust DEC range
        if len(LDlist) > 0:
            winner = "B"
            if oobHIGH == 0:
                y_mid = int(LDlist_Dmid/5.0) / 2.0  # round to nearest 0.5
                if y_mid > 2.5: y_mid = 2.5         # KEEP decmin > -80
                if y_mid < -2.5: y_mid = -2.5       # KEEP decmax < +80
                y_min = y_mid - 5.5
                decmin = int(y_min * 10)
                y_max = y_mid + 5.5
                decmax = int(y_max * 10)
            else:       # oobHIGH > 0
                y_max = int(LDlist_Dmax/5.0) / 2.0  # round to nearest 0.5
                if y_max > 8: y_max = 8             # KEEP decmax < +80
                if y_max < 3: y_max = 3             # KEEP decmin > -80
                decmax = int(y_max * 10)
                y_min = y_max - 11
                decmin = int(y_min * 10)

        # recalculate 'out-of-bounds'
        inbounds = 0
        oobLEFT = 0
        oobRIGHT = 0
        oobLOW = 0
        oobHIGH = 0
        x_left = x_max      # leftmost x in plot range
        x_right = 0.0       # rightmost x in plot range
        obj_left = ""       # leftmost object in plot range
        obj_right = ""      # rightmost object in plot range
        i_sun = -1          # index of sun in LDlist (invalid value)
        XmaxLD = 0.0        # maximum X-axis length object-to-Moon
        xMoon = getMOON(d00)

        i = 0               # index in LDlist
        for item in LDlist:
            if item in LDtargets:
                objname, sha, dec, x0, offX = showLD(item)
                if objname == "Sun": i_sun = i
                i += 1
                if not offX:        # if within plot range
                    if x0 < x_left:
                        x_left = x0
                        obj_left = objname
                    if x0 > x_right:
                        x_right = x0
                        obj_right = objname
                u = outofbounds_dec(dec)
                v = outsideplot(sha)
                if DEBUG_m2: print("B {:13} sha= {:7.3f} v= {:2d} x0= {}".format(objname+":",sha,v,x0))
                nn = XaxisLD(xMoon, sha, 'right')   # LD X-axis length RIGHT of Moon
                if nn > XmaxLD: XmaxLD = nn
                if outofbounds_sha(sha):
                    if v == -1: oobLEFT += 1
                    if v == +1: oobRIGHT += 1
                    continue
                elif u == -1: oobLOW += 1
                elif u == +1: oobHIGH += 1
                else: inbounds += 1

        tupleB1 = shamin, shamax, decmin, decmax    # remember this attempt
        tupleB2 = inbounds, oobLEFT, oobRIGHT, oobLOW, oobHIGH, XmaxLD, obj_left, obj_right
        if not quietmode:
            print("   {} LD objects: {} within plot; {} LEFT; {} RIGHT; {} LOW; {} HIGH".format(len(LDlist),inbounds,oobLEFT,oobRIGHT,oobLOW,oobHIGH))
            #print("obj_right = {}  obj_left = {}  i_sun = {}".format(obj_right, obj_left, i_sun))

#   ---------------- C: try LEFT-ALIGNED plot (& centered DEC) ----------------

        if just != 0:                   # if not all objects on the plot
            
            if not quietmode:
                print("\n C tactic... SHA: objects left-aligned DEC: objects centered")
            # LEFT-ALIGNED: adjust the plot range to begin with LDlist_smin...
            just = -1               # justification: LEFT-ALIGNED
            shalo = LDlist_Smin
            shamin = math.floor(shalo/5.0) * 5  # round to lower 5
            shamax = shamin + 190
            if shamax >= 360: shamax -= 360
            # ensure left-alignment includes the Moon at 0h !!!
            #        (19 Aug 2038 is critical)
            while not validSHA(shamin,shaMoon[0],shamax):
                # increment the range until it includes the Moon...
                shamax = shaadd(shamax,+5.0)
                shamin = shaadd(shamin,+5.0)
            set_X_offset(None if quietmode else "  try")  # --- SET THE X-AXIS PLOT OFFSET ---

            # adjust DEC range
            if len(LDlist) > 0:
                y_mid = int(LDlist_Dmid/5.0) / 2.0    # round to nearest 0.5
                if y_mid > 2.5: y_mid = 2.5
                if y_mid < -2.5: y_mid = -2.5
                y_min = y_mid - 5.5
                decmin = int(y_min * 10)
                y_max = y_mid + 5.5
                decmax = int(y_max * 10)

            # recalculate 'out-of-bounds'
            inbounds2 = 0
            oobLEFT2 = 0
            oobRIGHT2 = 0
            oobLOW2 = 0
            oobHIGH2 = 0
            x_left2 = x_max     # leftmost x in plot range
            x_right2 = 0.0      # rightmost x in plot range
            obj_left2 = ""      # leftmost object in plot range
            obj_right2 = ""     # rightmost object in plot range
            i_sun2 = -1         # index of sun in LDlist (invalid value)
            XmaxLD2 = 0.0       # maximum X-axis lengths object-to-Moon
            xMoon2 = getMOON(d00)

            i = 0               # index in LDlist
            for item in LDlist:
                if item in LDtargets:
                    objname, sha, dec, x0, offX = showLD(item)
                    if objname == "Sun": i_sun2 = i
                    i += 1
                    if not offX:        # if within plot range
                        if x0 < x_left:
                            x_left2 = x0
                            obj_left2 = objname
                        if x0 > x_right:
                            x_right2 = x0
                            obj_right2 = objname
                    u = outofbounds_dec(dec)
                    v = outsideplot(sha)
                    if DEBUG_m2: print("C {:13} sha= {:7.3f} v= {:2d} x0= {}".format(objname+":",sha,v,x0))
                    nn = XaxisLD(xMoon2, sha, 'left')   # LD X-axis lengths LEFT of Moon
                    if nn > XmaxLD2: XmaxLD2 = nn
                    if outofbounds_sha(sha):
                        if v == -1: oobLEFT2 += 1
                        if v == +1: oobRIGHT2 += 1
                        continue
                    elif u == -1: oobLOW2 += 1
                    elif u == +1: oobHIGH2 += 1
                    else: inbounds2 += 1

            tupleC1 = shamin, shamax, decmin, decmax    # remember this attempt
            tupleC2 = inbounds2, oobLEFT2, oobRIGHT2, oobLOW2, oobHIGH2, XmaxLD2
            if not quietmode:
                print("   {} LD objects: {} within plot; {} LEFT; {} RIGHT; {} LOW; {} HIGH".format(len(LDlist),inbounds2,oobLEFT2,oobRIGHT2,oobLOW2,oobHIGH2))
                #print("obj_right2 = {}  obj_left2 = {}  i_sun2 = {}".format(obj_right2, obj_left2, i_sun2))

            # pick attempt "B" or "C"...
            if inbounds > inbounds2:        # if first try was better
                winner = "B"
                shamin, shamax, decmin, decmax = tupleB1    # revert to previous values
                inbounds, oobLEFT, oobRIGHT, oobLOW, oobHIGH, XmaxLD, obj_left, obj_right = tupleB2
                set_X_offset(None)          # --- RESET THE X-AXIS PLOT OFFSET ---
            elif inbounds == inbounds2:
                #print(" LD X-axis max: {:2f} RIGHT-aligned; {:2f} LEFT-aligned".format(XmaxLD, XmaxLD2))
                if XmaxLD < XmaxLD2:        # if first try was better
                    winner = "B"
                    shamin, shamax, decmin, decmax = tupleB1    # revert to previous values
                    inbounds, oobLEFT, oobRIGHT, oobLOW, oobHIGH, XmaxLD, obj_left, obj_right = tupleB2
                    set_X_offset(None)      # --- RESET THE X-AXIS PLOT OFFSET ---
                else:
                    winner = "C"
                    inbounds, oobLEFT, oobRIGHT, oobLOW, oobHIGH, XmaxLD = tupleC2
            else:
                winner = "C"
                inbounds, oobLEFT, oobRIGHT, oobLOW, oobHIGH, XmaxLD = tupleC2

            tupleW1 = shamin, shamax, decmin, decmax    # remember the winner
            tupleW2 = inbounds, oobLEFT, oobRIGHT, oobLOW, oobHIGH, XmaxLD
            #print("obj_right = {}  obj_left = {}".format(obj_right, obj_left))

#   ---------------- D: omit the Sun if...                       ----------------
#   ---------------- D:   it's a rightmost or leftmost LD object ----------------
#   ---------------- D: center plot if LD SHA width < plot range ----------------
#   ---------------- D: else LEFT-JUSTIFY plot                   ----------------

        # try placing the Sun off the plot (it's easy to find in the sky)
        delSun = False
        if just != 0 and len(LDlist) >= 2 and inbounds < len(LDlist):
            if obj_right == "Sun" or obj_left == "Sun":
                del SHAlist[i_sun + 2]
                del DEClist[i_sun + 2]
                delSun = True
            if obj_right2 == "Sun" or obj_left2 == "Sun":
                del SHAlist[i_sun2 + 2]
                del DEClist[i_sun2 + 2]
                delSun = True

        if delSun:

            LDlist_Swth, LDlist_Smin, LDlist_Smax = group_width(SHAlist)
            LDlist_Dmid, LDlist_Dmin, LDlist_Dmax = group_range(DEClist)

            # adjust SHA range
            if LDlist_Swth < 190:       # center plot if SHA width under 190°
                if not quietmode:
                    print("\n D tactic... ignore Sun SHA: objects centered DEC: objects centered")
                excess = 190 - LDlist_Swth
                shalo = LDlist_Smin - excess/2
                if shalo < 0: shalo += 360
                shamin = math.floor(shalo/5.0) * 5  # round to lower 5
                shamax = shamin + 190
                if shamax >= 360: shamax -= 360
                # due to rounding down, 31 Aug 2022 is an example where this is needed:
                if LDlist_Smax > shamax: shamin, shamax = sha_inc(shamin, shamax)
            else:
                # adjust the plot range to begin with LDlist_smin...
                if not quietmode:
                    print("\n D tactic... ignore Sun SHA: objects left-aligned DEC: objects centered")
                shalo = LDlist_Smin
                shamin = math.floor(shalo/5.0) * 5  # round to lower 5
                shamax = shamin + 190
                if shamax >= 360: shamax -= 360
                if LDlist_Smax > shamax: shamin, shamax = sha_inc(shamin, shamax)
            set_X_offset(None if quietmode else "  try")  # --- SET THE X-AXIS PLOT OFFSET ---

            # adjust DEC range
            if len(LDlist) > 0:
                y_mid = int(LDlist_Dmid/5.0) / 2.0    # round to nearest 0.5
                if y_mid > 2.5: y_mid = 2.5
                if y_mid < -2.5: y_mid = -2.5
                y_min = y_mid - 5.5
                decmin = int(y_min * 10)
                y_max = y_mid + 5.5
                decmax = int(y_max * 10)

            # recalculate 'out-of-bounds'
            inbounds3 = 0
            oobLEFT3 = 0
            oobRIGHT3 = 0
            oobLOW3 = 0
            oobHIGH3 = 0
            XmaxLD3 = 0.0         # maximum X-axis lengths object-to-Moon
            xMoon3 = getMOON(d00)

            for item in LDlist:
                if item in LDtargets:
                    objname, sha, dec, x0, offX = showLD(item)
                    if not offX:        # if within plot range
                        if x0 < x_left:
                            x_left = x0
                            obj_left = objname
                        if x0 > x_right:
                            x_right = x0
                            obj_right = objname
                    u = outofbounds_dec(dec)
                    v = outsideplot(sha)
                    if DEBUG_m2: print("D {:13} sha= {:7.3f} v= {:2d} x0= {}".format(objname+":",sha,v,x0))
                    nn = XaxisLD(xMoon3, sha, 'left')   # LD X-axis lengths LEFT of Moon
                    if nn > XmaxLD3: XmaxLD3 = nn
                    if outofbounds_sha(sha):
                        if v == -1: oobLEFT3 += 1
                        if v == +1: oobRIGHT3 += 1
                        continue
                    elif u == -1: oobLOW3 += 1
                    elif u == +1: oobHIGH3 += 1
                    else: inbounds3 += 1

#                tupleD1 = shamin, shamax, decmin, decmax    # remember this attempt
            tupleD2 = inbounds3, oobLEFT3, oobRIGHT3, oobLOW3, oobHIGH3, XmaxLD3 # remember this attempt
            if not quietmode:
                print("   {} LD objects: {} within plot; {} LEFT; {} RIGHT; {} LOW; {} HIGH".format(len(LDlist),inbounds3,oobLEFT3,oobRIGHT3,oobLOW3,oobHIGH3))

            # pick attempt "B/C" or "D"...
            if inbounds > inbounds3:        # if earlier try was better
                shamin, shamax, decmin, decmax = tupleW1    # revert to previous values
                inbounds, oobLEFT, oobRIGHT, oobLOW, oobHIGH, XmaxLD = tupleW2
                set_X_offset(None)          # --- RESET THE X-AXIS PLOT OFFSET ---
            elif inbounds == inbounds3:
                winner = "D"
                inbounds, oobLEFT, oobRIGHT, oobLOW, oobHIGH, XmaxLD = tupleD2
            else:
                winner = "D"
                inbounds, oobLEFT, oobRIGHT, oobLOW, oobHIGH, XmaxLD = tupleD2

        if not quietmode:
            print(" "+winner+" tactic chosen"+"\n")
            #print("decmin = ",decmin,"decmax =",decmax)
            print(" LDlist = {}".format(LDlist))
            print(" {} LD objects: {} within plot; {} LEFT; {} RIGHT; {} LOW; {} HIGH".format(len(LDlist),inbounds,oobLEFT,oobRIGHT,oobLOW,oobHIGH))
            print(" LD objects: SHA width= {:7.3f}  SHA_min={:7.3f}  SHA_max={:7.3f}".format(LDlist_Swth,LDlist_Smin,LDlist_Smax))
            print(" LD objects: DEC mid  = {:7.3f}  DEC_min={:7.3f}  DEC_max={:7.3f}".format(LDlist_Dmid,LDlist_Dmin,LDlist_Dmax))

        outfile.write(buildchart(LDlist, H0list, SGNlist, onlystars, quietmode, firstpage))

        if DEBUG_m2:
            print(" PLOT RANGE:  x_min = 0; x_max = {};  y_min = {};  y_max = {}".format(x_max, y_min, y_max))
        firstpage = False
        daystoprocess -= 1
        d00 += timedelta(days=1)

    outfile.write(endPDF())