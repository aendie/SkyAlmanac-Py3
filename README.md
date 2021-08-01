# SkyAlmanac-Py3

SkyAlmanac-Py3 is a Python 3 script that creates the daily pages of the Nautical Almanac **using the UT1 timescale** :smiley:. Official Nautical Almanacs employ a UT timescale (equivalent to UT1).
These are tables that are needed for celestial navigation with a sextant. Although you are strongly advised to purchase the official Nautical Almanac, this program will reproduce the tables with no warranty or guarantee of accuracy.

SkyAlmanac-Py3 was developed with the intention of having identical output format as SFalmanac-Py3. It is a hybrid version based on two astronomical libraries:  

* the older Ephem library:  https://rhodesmill.org/pyephem/
* the newer Skyfield library: https://rhodesmill.org/skyfield/

It uses the star database in Skyfield, which is based on data from the Hipparcos Catalogue. Ephem is used for calculating twilight (actual, civil and nautical sunrise/sunset) and moonrise/moonset. As a consequence, it is **four times faster** than SFalmanac (which uses Skyfield for almost everything).

**NOTE: the Python Package Index (PyPI) edition is here:** https://pypi.org/project/skyalmanac/  
**Users are encouraged to install the PyPI edition instead.**  
NOTE: a 100% [Ephem](https://rhodesmill.org/pyephem/)-based version of SkyAlmanac is available here: https://github.com/aendie/Pyalmanac-Py3

An aim of this development was to maintain:

* **identical PDF output formatting with a similar control program**  
	 It is then possible to display both generated tables (using Ephem or Skyfield astronomical libraries) and compare what has changed by flipping between the two tabs in Adobe Acrobat Reader DC.
	 Anything that has changed flashes, thereby drawing your attention to
	 it. This crude and simple method is quite effective in highlihgting data that might need further attention.

The results have been crosschecked with USNO data to some extent.  
(However, constructive feedback is always appreciated.)

**UPDATE: Nov 2019**

Declination formatting has been changed to the standard used in Nautical Almanacs. In each 6-hour block of declinations, the degrees value is only printed on the first line if it doesn't change. It is printed whenever the degrees value changes. The fourth line has two dots indicating "ditto". This applies to all planet declinations and for the sun's declination, but not to the moon's declination as this is continuously changing.

This also includes some very minor changes and an improved title page for the full almanac with two star charts that indicate the equatorial navigational stars.

**UPDATE: Jan 2020**

The Nautical Almanac tables now indicate if the sun never sets or never rises; similarly if the moon never sets or never rises. For better performance, the *SunNeverSets* or *SunNeverRises* state is determined only by the month of year and hemisphere. (This is reliable for the set of latitudes printed in the Nautical Almanac tables.) The code also has cosmetic improvements.  
P.S. The *Overfull \hbox in paragraph...* messages can be ignored - the PDF is correctly generated.

**UPDATE: Feb 2020**

The main focus was on cleaning up the TeX code and eliminating the *Overfull/Underfull hbox/vbox* messages. Other minor improvements were included.

**UPDATE: Mar 2020**

A new parameter in *config.py* enables one to choose between A4 and Letter-sized pages. A [new approach](https://docs.python.org/3/whatsnew/3.0.html#pep-3101-a-new-approach-to-string-formatting) to string formatting has been implemented:
the [old](https://docs.python.org/2/library/stdtypes.html#string-formatting) style Python string formatting syntax has been replaced by the [new](https://docs.python.org/3/library/string.html#format-string-syntax) style string formatting syntax. 

**UPDATE: Jun 2020**

The Equation Of Time is shaded whenever EoT is negative indicating that apparent solar time is slow compared to mean solar time (mean solar time > apparent solar time).
It is possible to extend the maximum year beyond 2050 by choosing a different ephemeris in *config.py*.
Bugfix applied to correct the Meridian Passage times.

**UPDATE: Jul 2020**

A new option has been added into *config.py*: *moonimg = True* will display a graphic image of the moon phase (making the resulting PDF slightly larger). Use *moonimg = False* to revert to the previous format without the graphic moon image.

**UPDATE: Feb 2021**

Minor changes are included here to this original (non-PyPI) edition to reflect some of the adaptation that was required (e.g. integrate *increments.py* into *skyalmanac.py* as Option 5) to create a PyPI (Python Package Index) edition making this original (non-PyPI) and the PyPI editions similar. Both editions create identical almanacs and the [PyPI edition](https://pypi.org/project/skyalmanac/) is the preferred choice for users.

**UPDATE: Mar 2021**

UT is the timescale now employed in the almanac.

Two new options have been added into *config.py*: *useIERS = True* instructs Skyfield (if >= 1.31) to download Earth orientation data from IERS (International Earth Rotation and Reference Systems Service). *ageIERS = 30* instructs Skyfield to download fresh data from IERS if older tham that number of days. This implies greater accuracy for the generated almanacs (if Skyfield >= 1.31).

Note that although you may be using the *de421.bsp* ephemeris (valid from 1900 to 2050), the IERS currently specifies the validity of Earth Orientation Parameters (EOP) from 2nd January 1973 to 
15th May 2022. Refer to the [IERS web site](https://www.iers.org/IERS/EN/Home/home_node.html) for current information.

**UPDATE: Apr 2021**

A double moonrise or moonset on the same day is now highlighted for better legibility. Event Time tables can now be generated - these are the tables containing data in hours:minutes:seconds, e.g. sunrise, sunset, moonrise, moonset and Meridian Passage.
Accuracy to to the second of time is not required for navigational purposes, but may be used to compare accuracy with other algorithms. Some internal technical enhancements and minor changes to text are also included.

**UPDATE: May 2021**

The indication of objects (Sun or Moon) continuously above or below the horizon has been corrected.

Regarding Moon Data: ".. .." has been added to indicate that the moonrise/moonset event occurs the following day (at the specified latitude). If there is no moonrise/moonset for two or more consecutive days, black boxes indicate "moon below horizon"; white boxes indicate "moon above horizon". This brings it in line with Nautical Almanacs. (Previously they were only displayed when there was no moonrise *and* no moonset on a single day.)

Correction to Sun Data: "Sun continually above/below horizon" now shown if it applies to both Sunrise and Sunset, or *additionally* to both Civil Twilight Start & End; or *additionally* to both Astronomical Twilight Start & End, i.e. as two, four or six events per day and latitude. This brings it in line with Nautical Almanacs.

&emsp;:smiley:&ensp;SkyAlmanac is now available on DockerHub [here](https://hub.docker.com/repository/docker/aendie/skyalmanac).&ensp;:smiley:

The DockerHub image contains a Linux-based OS, TeX Live, the application code, and third party Python imports (including the astronomical libraries). It can be executed "in a container" on Windows 10 Pro, macOS or a Linux-based OS.

**UPDATE: Jul 2021**

The PDF filenames have been revised:

* modna_\<starting date or year\>.pdf: for Nautical Almanacs in modern style
* modst_\<starting date or year\>.pdf: for Sun Tables in modern style
* tradna_\<starting date or year\>.pdf: for Nautical Almanacs in traditional style
* tradst_\<starting date or year\>.pdf: for Sun Tables in traditional style

One command line argument may be appended to the run command:

* -v to invoke verbose mode (send pdfTeX execution steps to the console)
* -log to preserve the log file
* -tex to preserve the tex file

de430t and de440 ephemerides have been added to *config.py*.

## Requirements

&emsp;Computation is done by the free Ephem and Skyfield libraries.  
&emsp;Typesetting is typically done by MiKTeX or TeX Live.  
&emsp;These need to be installed:

* Python v3.4 or higher (the latest version is recommended)
* Skyfield 1.35 (see the Skyfield Changelog)
* Pandas >= 1.0 (to load the Hipparcos catalog; tested: 1.0.3 and 1.1.4)
* Ephem >=3.7.6
* MiKTeX&ensp;or&ensp;TeX Live

## Files required in the execution folder:

* &ast;.py
* Ra.jpg
* croppedmoon.png
* A4chart0-180_P.pdf
* A4chart180-360_P.pdf

&emsp;If upgrading from an older version of Skyfield to 1.31 or higher, these files may be deleted:  
&emsp;**deltat.data** and **deltat.preds**

### INSTALLATION GUIDELINES on Windows 10:

&emsp;Tested on Windows 10 Pro, Version 20H2 with an AMD Ryzen 7 3700X 8-Core Processor  

&emsp;Install Python 3.9.1 (should be in the system environment variable PATH, e.g. )  
&emsp;&ensp;**C:\\Python39\Scripts;C:\\Python39;** .....  
&emsp;Install MiKTeX 21.1 from https://miktex.org/  
&emsp;When MiKTeX first runs it will require installation of additional packages.  
&emsp;Run Command Prompt as Administrator, go to your Python folder and execute, e.g.:

&emsp;**cd C:\\Python39**  
&emsp;**python.exe -m pip install --upgrade pip**  
&emsp;... for a first install (it's preferable to install *wheel* first):  
&emsp;**pip3 install wheel**  
&emsp;**pip3 uninstall pyephem ephem**  
&emsp;**pip3 install ephem**  
&emsp;**pip3 install skyfield**  
&emsp;**pip3 install pandas**  
&emsp;... if already installed, check for upgrades explicitly:  
&emsp;**pip3 install --upgrade ephem skyfield pandas**  

&emsp;Put the required files for SkyAlmanac in a new folder, run Command Prompt in that folder and start with:  
&emsp;**py -3 skyalmanac.py**

&emsp;If using MiKTeX 21 or higher, executing 'option 5' (Increments and Corrections) will probably fail with  
&emsp;**! TeX capacity exceeded, sorry [main memory size=3000000].**  
&emsp;To resolve this problem (assuming MiKTeX has been installed for all users),  
&emsp;open a Command Prompt as Administrator and enter:  
&emsp;**initexmf --admin --edit-config-file=pdflatex**  
&emsp;This opens **pdflatex.ini** in Notepad. Add the following line:  
&emsp;**extra_mem_top = 1000000**  
&emsp;and save the file. Problem solved. For more details go [here](https://tex.stackexchange.com/questions/438902/how-to-increase-memory-size-for-xelatex-in-miktex/438911#438911)


### INSTALLATION GUIDELINES on Ubuntu 19.10 or 20.04:

&emsp;Ubuntu 18.04 and higher come with Python 3 preinstalled,  
&emsp;however pip may need to be installed:  
&emsp;**sudo apt install python3-pip**

&emsp;Install the following TeX Live package:  
&emsp;**sudo apt install texlive-latex-extra**

&emsp;Install the required astronomical libraries etc.:  
&emsp;**pip3 install wheel**  
&emsp;**pip3 uninstall pyephem ephem**  
&emsp;**pip3 install ephem**  
&emsp;**pip3 install skyfield**  
&emsp;**pip3 install pandas**  

&emsp;Put the SkyAlmanac files in a folder and start with:  
&emsp;**python3 skyalmanac.py**  


### INSTALLATION GUIDELINES on MAC:

&emsp;Every Mac comes with python preinstalled.  
&emsp;(Please choose this version of SkyAlmanac if Python 3.* is installed.)  
&emsp;You need to install the Skyfield (and Ephem) library to use SFalmanac.  
&emsp;Type the following commands at the commandline (terminal app):

&emsp;**sudo easy_install pip**  
&emsp;**pip install wheel**  
&emsp;**pip uninstall pyephem ephem**  
&emsp;**pip install ephem**  
&emsp;**pip install skyfield**  
&emsp;**pip install pandas**  

&emsp;If this command fails, your Mac asks you if you would like to install the header files.  
&emsp;Do so - you do not need to install the full IDE - and try again.

&emsp;Install TeX/LaTeX from http://www.tug.org/mactex/

&emsp;Now you are almost ready. Put the SkyAlmanac files in any directory and start with:  
&emsp;**python skyalmanac**  
&emsp;or  
&emsp;**./skyalmanac**
