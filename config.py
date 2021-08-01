#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

#   Copyright (C) 2021  Andrew Bauer

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

# ================ EDIT LINES IN THIS SECTION ONLY ================

# choose an ephemeris (ephndx = 0, 1 or 2):
#   0   de421.bsp   1900 to 2050
#   1   de405.bsp   1600 to 2200
#   2   de406.bsp   1000 to 2750 (Equation of Time may show ??:?? after 2750)
#   3   de430t.bsp  1550 to 2650
#   4   de440.bsp   1550 to 2650
ephndx = 0

pgsz = 'A4'     # page size 'A4' or 'Letter' (global variable)
moonimg = True  # 'True' to include a moon image; otherwise 'False'
useIERS = True  # 'True' to download finals2000A.all; 'False' to use built-in UT1 tables
ageIERS = 30    # download a new finals2000A.all version after 'ageIERS' days if useIERS=True

# ================ DO NOT EDIT LINES BELOW HERE ================
# Docker-related stuff...
dockerized = False   # 'True' to build this app to run in a Docker-Linux container
# NOTE: config.py has been "Dockerized" by use of environment variables in .env

# Docker Container subfolder for creating PDF files (and optionally a LOG file)
# This folder must be mapped to a Named Volume as part of the 'docker run' command:
#   e.g.    -v "%cd%\pdf":/app/tmp      in a Windows host system
#   e.g.    -v $(pwd)/pdf:/app/tmp      in a macOS/Linux host system
docker_pdf = "tmp"
docker_prefix  = docker_pdf + "/" if dockerized else ""  # docker image is based on Linux
docker_postfix = "/" + docker_pdf if dockerized else ""  # docker image is based on Linux
# ==============================================================
# define global variables
logfileopen = False
ephemeris = [['de421.bsp',1900,2050],['de405.bsp',1600,2200],['de406.bsp',1000,2750],['de430t.bsp',1550,2650],['de440.bsp',1550,2650]]
tbls = ''		# table style (global variable)
decf = ''		# Declination format (global variable)

# list of latitudes to include for Sunrise/Sunset/Twilight/Moonrise/Moonset...
lat = [72,70,68,66,64,62,60,58,56,54,52,50,45,40,35,30,20,10,0,-10,-20,-30,-35,-40,-45,-50,-52,-54,-56,-58,-60]

# open/write/close a log file
def initLOG():
    global errors
    errors = 0
    global logfile
    logfile = open(docker_prefix + 'debug.log', mode="w", encoding="utf8")
    global logfileopen
    logfileopen = True

# write to log file
def writeLOG(text):
    logfile.write(text)
    return

# close log file
def closeLOG():
    logfileopen = False
    logfile.close()
    return
