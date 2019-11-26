# SkyAlmanac-Py3

SkyAlmanac-Py3 is a Python 3 script that creates the daily pages of the Nautical Almanac. These are tables that are needed for celestial navigation with a sextant. Although you are strongly advised to purchase the official Nautical Almanac, this program will reproduce the tables with no warranty or guarantee of accuracy.

SkyAlmanac-Py3 was developed with the intention of having identical output format as SFalmanac-Py3. It is a hybrid version based on two astronomical libraries:  

* the older PyEphem library:  https://rhodesmill.org/pyephem/
* the newer Skyfield library: https://rhodesmill.org/skyfield/

It uses the star database in Skyfield, which is based on data from the Hipparcos Catalogue. PyEphem is used for calculating twilight (actual, civil and nautical sunrise/sunset) and moonrise/moonset. As a consequence, it is **four times faster** than SFalmanac (which uses Skyfield for almost everything).

NOTE: two scripts are included (both can be run): 'skyalmanac.py' and 'increments.py'  
NOTE: a Python 2.7 script with identical functionality can be found at:  https://github.com/aendie/SkyAlmanac-Py2  
NOTE: a 100% [PyEphem](https://rhodesmill.org/pyephem/) version of SkyAlmanac is available here: https://github.com/aendie/Pyalmanac-Py3

An aim of this development was to maintain:

* **identical PDF output formatting with a similar control program**  
	 It is then possible to display both generated tables (from PyEphem, Skyfield and SkyAlmanac) and compare what has changed by flipping between the two tabs in Adobe Acrobat Reader DC.
	 Anything that has changed flashes, thereby drawing your attention to
	 it. This crude and simple method is quite effective in highlihgting data that might need further attention.

The results have been crosschecked with USNO data to some extent.  
(However, constructive feedback is always appreciated.)

**UPDATE: Nov 2019**

Declination formatting has been changed to the standard used in Nautical Almanacs. In each 6-hour block of declinations, the degrees value is only printed on the first line if it doesn't change. It is printed whenever the degrees value changes. The fourth line has two dots indicating "ditto". This applies to all planet declinations and for the sun's declination, but not to the moon's declination as this is continuously changing.

This also includes some very minor changes and an improved title page for the full almanac with two star charts that indicate the equatorial navigational stars.

## Requirements

&nbsp;&nbsp;&nbsp;&nbsp;Computation is done by the free PyEphem and Skyfield libraries.  
&nbsp;&nbsp;&nbsp;&nbsp;Typesetting is done by LaTeX or MiKTeX so you first need to install:

* Python v3.4 or higher (the latest version is recommended)
* Skyfield 1.15 (tested version)
* Pandas (to load the Hipparcos catalog; tested: 0.24.2, 0.25.3)
* PyEphem 3.7.6 or 3.7.7
* TeX/LaTeX&nbsp;&nbsp;or&nbsp;&nbsp;MiKTeX
  
&nbsp;&nbsp;&nbsp;&nbsp;When MiKTeX first runs it will require installation of additional packages.  
&nbsp;&nbsp;&nbsp;&nbsp;Ignore all messages output by pdftex - SkyAlmanac is running correctly.  

### INSTALLATION GUIDELINES on Windows 10:

&nbsp;&nbsp;&nbsp;&nbsp;Install Python 3.8 (add python.exe to path)  
&nbsp;&nbsp;&nbsp;&nbsp;Install MiKTeX 2.9 from https://miktex.org/  
&nbsp;&nbsp;&nbsp;&nbsp;Run Command Prompt as Administrator, go to your Python folder and execute, e.g.:

&nbsp;&nbsp;&nbsp;&nbsp;**cd C:\\Python38-32**  
&nbsp;&nbsp;&nbsp;&nbsp;**pip install --upgrade pip**  
&nbsp;&nbsp;&nbsp;&nbsp;... for a first install:  
&nbsp;&nbsp;&nbsp;&nbsp;**pip install pyephem**  
&nbsp;&nbsp;&nbsp;&nbsp;... if already installed, check for upgrade explicitly:  
&nbsp;&nbsp;&nbsp;&nbsp;**pip install --upgrade pyephem**
&nbsp;&nbsp;&nbsp;&nbsp;**pip install skyfield**  
&nbsp;&nbsp;&nbsp;&nbsp;**pip install pandas**  
&nbsp;&nbsp;&nbsp;&nbsp;Put the SkyAlmanac files in a new folder, go there and start with:  
&nbsp;&nbsp;&nbsp;&nbsp;**py -3 skyalmanac.py**


### INSTALLATION GUIDELINES on Linux:

&nbsp;&nbsp;&nbsp;&nbsp;Install your platform's Python- and LaTeX distribution.  
&nbsp;&nbsp;&nbsp;&nbsp;Remember to choose python 3.4 or higher and install all develpment header files.  
&nbsp;&nbsp;&nbsp;&nbsp;Run at the command line:

&nbsp;&nbsp;&nbsp;&nbsp;**pip install pyephem**  
&nbsp;&nbsp;&nbsp;&nbsp;**pip install skyfield**  
&nbsp;&nbsp;&nbsp;&nbsp;**pip install pandas**  

&nbsp;&nbsp;&nbsp;&nbsp;Put the SkyAlmanac files in any directory and start with:  
&nbsp;&nbsp;&nbsp;&nbsp;**python skyalmanac**  
&nbsp;&nbsp;&nbsp;&nbsp;or  
&nbsp;&nbsp;&nbsp;&nbsp;**./skyalmanac**


### INSTALLATION GUIDELINES on MAC:

&nbsp;&nbsp;&nbsp;&nbsp;Every Mac comes with python preinstalled.  
&nbsp;&nbsp;&nbsp;&nbsp;(Please choose this version of SkyAlmanac if Python 3.* is installed.)  
&nbsp;&nbsp;&nbsp;&nbsp;You need to install the Skyfield (and PyEphem) library to use SFalmanac.  
&nbsp;&nbsp;&nbsp;&nbsp;Type the following commands at the commandline (terminal app):

&nbsp;&nbsp;&nbsp;&nbsp;**sudo easy_install pip**  
&nbsp;&nbsp;&nbsp;&nbsp;**pip install pyephem**  
&nbsp;&nbsp;&nbsp;&nbsp;**pip install skyfield**  
&nbsp;&nbsp;&nbsp;&nbsp;**pip install pandas**  

&nbsp;&nbsp;&nbsp;&nbsp;If this command fails, your Mac asks you if you would like to install the header files.  
&nbsp;&nbsp;&nbsp;&nbsp;Do so - you do not need to install the full IDE - and try again.

&nbsp;&nbsp;&nbsp;&nbsp;Install TeX/LaTeX from http://www.tug.org/mactex/

&nbsp;&nbsp;&nbsp;&nbsp;Now you are almost ready. Put the SkyAlmanac files in any directory and start with:  
&nbsp;&nbsp;&nbsp;&nbsp;**python skyalmanac**  
&nbsp;&nbsp;&nbsp;&nbsp;or  
&nbsp;&nbsp;&nbsp;&nbsp;**./skyalmanac**
