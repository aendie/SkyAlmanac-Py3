# Skyalmanac-Py3

Skyalmanac-Py3 is a Python 3 script that creates the daily pages of the Nautical Almanac as well as Lunar Distance tables and charts.
The daily pages are needed for celestial navigation with a sextant. Although you are strongly advised to purchase the official Nautical Almanac, this program will reproduce the tables with no warranty or guarantee of accuracy.

Skyalmanac-Py3 was developed with the intention of having identical output format as Pyalmanac-Py3 to facilitate manual observation of data discrepancies.
Also it is based entirely on the newer Skyfield astronomical library: https://rhodesmill.org/skyfield/. Skyalmanac uses the star database in Skyfield, which is based on data from the Hipparcos Catalogue.

**Users are encouraged to install the Python Package Index (PyPI) edition to be found here:**  
https://pypi.org/project/skyalmanac/  

The results have been crosschecked with USNO data to some extent.  

**THE OLDER Skyalmanac HAS BEEN TOTALLY REPLACED**

Please note that Skyalmanac *was* originally an interim 'hybrid' version that was required to overcome performance deficiencies in SFalmanac in single-processing mode. The introduction of multiprocessing overcame these deficiencies to such an extent that the 'hybrid' version was no longer required (and was no longer maintained). 

That 'hybrid' version has now been discarded and Skyalmanac now contains all the latest features of SFalmanac - so SFalmanac and Skyalmanac are now practically identical. (Newcomers typically chose Skyalmanac for its name without being aware it's obsolete.) Looking forward, Skyalmanac will be the future product of choice but for the time being both will be maintained in parallel.

The Update History below has been taken over from SFalmanac...

**UPDATE: Nov 2019**

Declination formatting has been changed to the standard used in Nautical Almanacs. In each 6-hour block of declinations, the degrees value is only printed on the first line if it doesn't change. It is printed whenever the degrees value changes. The fourth line has two dots indicating "ditto". This applies to all planet declinations and for the sun's declination, but not to the moon's declination as this is continuously changing.

This also includes some very minor changes and an improved title page for the full almanac with two star charts that indicate the equatorial navigational stars.

**UPDATE: Jan 2020**

The Nautical Almanac tables now indicate if the sun never sets or never rises; similarly if the moon never sets or never rises. For better performance, the *SunNeverSets* or *SunNeverRises* state is determined only by the month of year and hemisphere. (This is reliable for the set of latitudes printed in the Nautical Almanac tables.) The code also has cosmetic improvements.  
P.S. The *Overfull \hbox in paragraph...* messages can be ignored - the PDF is correctly generated.

**UPDATE: Feb 2020**

The main focus was on cleaning up the TeX code and eliminating the *Overfull/Underfull hbox/vbox* messages. Other minor improvements were included. A Skyfield issue with days that have no moonrise or moonset at a specific latitude was resolved.

**UPDATE: Mar 2020**

A new parameter in *config.py* enables one to choose between A4 and Letter-sized pages. A [new approach](https://docs.python.org/3/whatsnew/3.0.html#pep-3101-a-new-approach-to-string-formatting) to string formatting has been implemented:
the [old](https://docs.python.org/2/library/stdtypes.html#string-formatting) style Python string formatting syntax has been replaced by the [new](https://docs.python.org/3/library/string.html#format-string-syntax) style string formatting syntax. 

**UPDATE: Jun 2020**

The Equation Of Time is shaded whenever EoT is negative indicating that apparent solar time is slow compared to mean solar time (mean solar time > apparent solar time).
It is possible to extend the maximum year beyond 2050 by choosing a different ephemeris in config.py.
Bugfix applied to correct the Meridian Passage times.

**UPDATE: Jul 2020**

A new option has been added into config.py: *moonimg = True* will display a graphic image of the moon phase (making the resulting PDF slightly larger). Use *moonimg = False* to revert to the previous format without the graphic moon image.

**UPDATE: Feb 2021**

Minor changes are included here to this original (non-PyPI) edition to reflect some of the adaptation that was required (e.g. integrate *increments.py* into *skyalmanac.py* as Option 5) to create a PyPI (Python Package Index) edition making this original (non-PyPI) and the PyPI editions similar. Both editions create identical almanacs and the [PyPI edition](https://pypi.org/project/skyalmanac/) is the preferred choice for users.

**UPDATE: Mar 2021**

UT is the timescale now employed in the almanac.

Two new options have been added into config.py: *useIERS = True* instructs Skyfield (if >= 1.31) to download Earth orientation data from IERS (International Earth Rotation and Reference Systems Service). *ageIERS = 30* instructs Skyfield to download fresh data from IERS if older tham that number of days. This implies greater accuracy for the generated almanacs (if Skyfield >= 1.31).

Note that although you may be using the *de421.bsp* ephemeris (valid from 1900 to 2050), the IERS currently specifies the validity of Earth Orientation Parameters (EOP) from 2nd January 1973 to 
15th May 2022. Refer to the [IERS web site](https://www.iers.org/IERS/EN/Home/home_node.html) for current information.

**UPDATE: Apr 2021**

A double moonrise or moonset on the same day is now highlighted for better legibility. Event Time tables can now be generated - these are the tables containing data in hours:minutes:seconds, e.g. sunrise, sunset, moonrise, moonset and Meridian Passage.
Accuracy to to the second of time is not required for navigational purposes, but may be used to compare accuracy with other algorithms. Some internal technical enhancements and minor changes to text are also included. For example, moonrise and moonset times now take into account the lunar distance from the Earth (which varies slightly).

**UPDATE: May 2021**

The indication of objects (Sun or Moon) continuously above or below the horizon has been corrected.

Regarding Moon Data: ".. .." has been added to indicate that the moonrise/moonset event occurs the following day (at the specified latitude). If there is no moonrise/moonset for two or more consecutive days, black boxes indicate "moon below horizon"; white boxes indicate "moon above horizon". This brings it in line with Nautical Almanacs. (Previously they were only displayed when there was no moonrise *and* no moonset on a single day.)

The additional calculations required are compensated with a transient Moon Data buffer store that always holds the latest five adjacent days of moon data, eliminating any need to recalculate data for the next or previous day (to determine if "moon above/below horizon" spans a minimum of two days.)

Correction to Sun Data: "Sun continually above/below horizon" now shown if it applies to both Sunrise and Sunset, or *additionally* to both Civil Twilight Start & End; or *additionally* to both Astronomical Twilight Start & End, i.e. as two, four or six events per day and latitude. This brings it in line with Nautical Almanacs.

&emsp;:smiley:&ensp;Skyalmanac is now available on DockerHub [here](https://hub.docker.com/repository/docker/aendie/skyalmanac).&ensp;:smiley:

The DockerHub image contains a Linux-based OS, TeX Live, the application code, and third party Python imports (including the astronomical libraries). It can be executed "in a container" on Windows 10 Pro, macOS or a Linux-based OS.

**UPDATE: Jun 2021**

This version introduces multiprocessing and thus a gain in performance. Single-processing is also a selectable option, if required. Testing has been successfully performed on Windows 10 and Ubuntu 20.04 LTS. (No testing can be performed on Mac OS.) Compared to single-processing ...

* Creation (excluding conversion to PDF) of a 6-day Nautical Almanac is 4x faster on Windows 10; 2x faster on Linux.
* Creation (excluding conversion to PDF) of 6-day Event Time Tables is almost 5x faster on Windows 10; 3x faster on Linux.

Windows 10 uses up to 8 threads; Linux uses up to 12 threads in parallel. Testing was performed on a PC with an AMD Ryzen 7 3700X 8-Core (16 threads) Processor. Windows & Mac OS spawn new processes; Linux forks new processes (the code is compatible with both techniques and will also run on CPUs with fewer cores/threads).

This performance gain infers that there is practically no justification to use the *original* Skyalmanac, which was an interim solution to overcome the poor performance in SFalmanac at the cost of marginally poorer accuracy in event times (sunset/twilight/sunrise; moonrise/moonset).

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

**UPDATE: Nov 2021**

* Enhanced User Interface includes the possibility to generate tables starting at any valid date, or for any month (within -12/+11 months from today).
* It now checks if there is an Internet connection before attempting to update the Earth Orientation Parameters (EOP) from IERS.
* Minor cosmetic improvements ('d'-correction in italics; greek 'nu' replaces 'v'-correction; Minutes-symbol added to SD and d)

Increased accuracy due to the following minor improvements:
* Moon phase (percent illumination) is based on midnight (as opposed to midday)
* Star positions are based on midnight (as opposed to midday)
* Sun's SD (semi-diameter) is based on midnight (as opposed to mid-day)
* Moon v and d for hour ‘n’ are based on “hour ‘n+1’ minus hour ‘n’” as opposed to “hour ‘n’ + 30 minutes minus hour ‘n’ – 30 minutes”
* Moon HP is based on a “volumetric mean radius of earth = 6371.0” as opposed to an “equatorial radius of earth = 6378.0 km”
* Moon SD (semi-diameter) is based on a “volumetric mean radius of moon = 1737.4 km” as opposed to an “equatorial radius of moon = 1738.1 km”
* Planet magnitudes for Venus and Jupiter are obtained from Skyfield (>= 1.26), despite it still being a prototype function

The PDF filenames have been revised (again):

* NAmod_\<starting date or month or year\>.pdf: for Nautical Almanacs in modern style
* STmod_\<starting date or month or year\>.pdf: for Sun Tables in modern style
* NAtrad_\<starting date or month or year\>.pdf: for Nautical Almanacs in traditional style
* STtrad_\<starting date or month or year\>.pdf: for Sun Tables in traditional style

BUGFIX (solved here and in PyPI skyalmanac 1.6.1):  
The first day in a Nautical Almanac did not initialize the moon state 'above or below horizon' when there was no Moonrise or Moonset at some latitudes on that day in Multiprocessing mode (only).

BUGFIX (solved here and in PyPI skyalmanac 1.6.2):  
The Moon Declination on the last hour of the day did not indicate 'N' or 'S' when it had just changed, i.e. since 22h. This rare case occurs, for example, on 14th Jun 2024 and 15th Oct 2024.

BUGFIX (solved here and in PyPI skyalmanac 1.6.3):  
Two import statements (essential for Linux and MacOS) were missing.

**UPDATE: Apr 2022**

Lunar Distance tables have been added as a new option.

Skyfield relies on the IERS, the International Earth Rotation Service, for accurate measurements of UT1 and for the schedule of leap seconds that keeps UTC from straying more than 0.9 seconds away from UT1.

However the IERS server is currently undergoing maintenance and thus unavailable, which causes Skyalmanac to fail. This version first tests if the IERS server is available and otherwise downloads the EOP (Earth Orientation Parameters) data from USNO (US Naval Observatory) instead.

BUGFIX: Event Time tables no longer fail on 24.08.2063 (Lower Transit).

**UPDATE: May 2022**

Lunar Distance charts have been added as a new option to complement the Lunar Distance tables.

Skyalmanac in DockerHub has been updated to match this May 2022 release:
https://hub.docker.com/r/aendie/skyalmanac

The PDF filenames have been revised (again), where 'A4' (or 'Letter') is the selected papersize:

* NAmod(A4)_\<starting date or month or year\>.pdf: for Nautical Almanacs in modern style
* STmod(A4)_\<starting date or month or year\>.pdf: for Sun Tables in modern style
* NAtrad(A4)_\<starting date or month or year\>.pdf: for Nautical Almanacs in traditional style
* STtrad(A4)_\<starting date or month or year\>.pdf: for Sun Tables in traditional style

PATCH1: Sun SD added to Lunar Distance tables when appropriate

**UPDATE: Aug 2022**

The 'fancyhdr' LaTeX package is now used to format header and footer lines on a page. This is a more professional solution with added features. Footer lines now contain left-, center- and right-justified text.

BUGFIX (solved here and in PyPI skyalmanac 1.9):
Previously execution could hang when aborting a multiprocessing task (in nautical.py or eventtables.py) on entering Ctrl-C to kill all processes.

**UPDATE: Sep 2022**

* Three locations are tried to obtain *finals2000A.all* IERS EOP data
* The LaTeX *fancyhdr* package is employed when MiKTeX (or a TeX Live version >= 2020) is detected.
* Better support for Letter-sized pages.
* Skyalmanac no longer requires the Ephem astronomical library.
* Hipparcos data (*hip_main.dat*) and one ephemeris (*de421.bsp*) are included in the PyPI package.
* Command line options:
    * -v   ... 'verbose': to send pdfTeX output to the terminal
    * -q   ... quiet mode for LD charts
    * -sky ... stars only in LD charts
    * -log ... to keep the log file
    * -tex ... to keep the tex file
    * -old ... old formatting without the 'fancyhdr' package
    * -a4  ... A4 papersize
    * -let ... Letter papersize
    * -dpo ... data pages only
    * -sbr ... square brackets in Unix filenames

**UPDATE: Oct 2022**

* UNIX filenames include parentheses unless option '-sbr' is specified
* Date with ordinal number (e.g. 3rd Oct) added into Lunar Distance table

BUGFIX (solved here and in PyPI skyalmanac 1.11.1):
A Lunar Distance chart can now be created for 19 August 2038

## Requirements

&emsp;Most of the computation is done by the free Skyfield library.  
&emsp;Typesetting is done typically by MiKTeX or TeX Live.  
&emsp;Here are the requirements/recommendations:

* Python v3.4 or higher (v3.10.x is recommended)
* Skyfield >= 1.31 (the latest is recommended; see the Skyfield Changelog)
* Pandas >= 1.0 (to decode the Hipparcos catalog; tested: 1.0.3 and 1.1.4)
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

&emsp;Tested on Windows 10 Pro, Version 21H2 with an AMD Ryzen 7 3700X 8-Core Processor  

&emsp;Install Python 3.10.6 (should be in the system environment variable PATH, e.g. )  
&emsp;&ensp;**C:\\Python310\Scripts;C:\\Python310;** .....  
&emsp;Install MiKTeX 22.7 from https://miktex.org/  
&emsp;When MiKTeX first runs it will require installation of additional packages.  
&emsp;Run Command Prompt as Administrator, go to your Python folder and execute, e.g.:

&emsp;**cd C:\\Python310**  
&emsp;**python.exe -m pip install --upgrade pip**  
&emsp;... for a first install (it's preferable to install *wheel* first):  
&emsp;**pip3 install wheel**  
&emsp;**pip3 install skyfield**  
&emsp;**pip3 install pandas**  
&emsp;... if already installed, check for upgrades explicitly:  
&emsp;**pip3 install --upgrade skyfield pandas**  

&emsp;Put the required files for Skyalmanac in a new folder, run Command Prompt in that folder and start with:  
&emsp;**py -3 skyalmanac.py**

&emsp;If using MiKTeX 21 or higher, executing 'option 6' (Increments and Corrections) will probably fail with  
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
&emsp;**pip3 install skyfield**  
&emsp;**pip3 install pandas**  

&emsp;Put the Skyalmanac files in a folder and start with:  
&emsp;**python3 skyalmanac.py**  


### INSTALLATION GUIDELINES on Mac OS:

&emsp;Every Mac comes with python preinstalled.  
&emsp;(Please choose this version of Skyalmanac if Python 3.* is installed.)  
&emsp;You need to install the Ephem and Skyfield libraries to use Skyalmanac.  
&emsp;Type the following commands at the commandline (terminal app):

&emsp;**sudo easy_install pip**  
&emsp;**pip install wheel**  
&emsp;**pip install skyfield**  
&emsp;**pip install pandas**  

&emsp;If this command fails, your Mac asks you if you would like to install the header files.  
&emsp;Do so - you do not need to install the full IDE - and try again.

&emsp;Install TeX/LaTeX from http://www.tug.org/mactex/

&emsp;Now you are almost ready. Put the Skyalmanac files in any directory and start with:  
&emsp;**python skyalmanac**  
&emsp;or  
&emsp;**./skyalmanac**
