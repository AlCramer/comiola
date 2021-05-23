# README #

COMIOLA is a animation tool for turning comics and other graphic art
into .mp4 videos.

### Installation ###

#### Windows 10 ####
Click [here](https://drive.google.com/file/d/1YgTZp8Nq8WLeIFe_my64_ED-JB5iXzb7/view?usp=sharing) to download the installer for Comiola.
It will be named "comiola_winX.X", where "X.X" is the version
number. When the download is complete, double click the downloaded file
to install Comiola. 

#### Mac, Linux ####
Comiola is written in Python, so you must have Python 3 installed
on your machine. If you need to install it, here's a 
[link to python.org](python.org/downloads).

Python programs are run from the terminal. 
To install Comiola, open a terminal window and enter 
these commands:

python -m pip install imageio    
python -m pip install imageio-ffmpeg    
python -m pip install comiola 

To start Comiola, enter this command:

python -m comiola.py 

#### Dev Notes: Windows Installer ####
We use "pyinstaller" to create a standalone app for Windows,
and "Inno Setup"  
([download here](https://inno-setup.en.uptodown.com/windows)
to create the installer program. Steps are:

1. From root directory of the distribution, run "run_pyinstaller.bat".
That will run pyinstaller with correct options.

2. Again from root directory, double click the Inno Setup script 
"innosetup.iss". That will bring up Inno Setup. From top menu,
select Build/Compile. That will create the installer in 
"Output/comiola_win0.1.exe". 


### Who do I talk to? ###

Al Cramer ac2.71828@gmail.com
