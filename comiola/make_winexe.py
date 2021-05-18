import subprocess
import os
import zipfile
import scripts

# This script calls pyinstaller to create the windows standalone
# executable for comiola.  It assumes pyinstaller is on your path.
# If not, open a cmd line window and type something like this:
# 
# SET PATH=%PATH%;"C:\Users\Al\AppData\Local\Programs\Python\Python38-32\Scripts"
# 
# The script produces an output file, "comiola.zip". To install comiola
# on windows, you should:
# 1. create a folder for the installation;
# 2. download comiola.zip and extract its contents into that folder.
# 
# To run comiola, go to that folder and double-click the file "comiola".

# Note: there are bugs with pyinstaller + python packages "webbrowser" and
# "imageio" (Python V3.8).
# 1. By annotating pyonstaller's "spec" file, we should be able to create
# a completely self-contained "comiola.exe" file.  But this breaks
# "webbrowser", hence the work-around that requires the zip file.
# 2. We should be able to call pyinstaller with the "-w" option, which
# prevents background .exe window from popping up behind main gui window.
# But -w option breaks imageio.

 
# run pyinstaller. This creates the folder "dist", containing 
# "./dist/comiola.exe"

# run pyinstaller
subprocess.call(
    'pyinstaller --onefile --name comiola __main__.py',
    shell=True)

# write the zip file
fn = 'comiola-win-%s.zip' % scripts.version
with zipfile.ZipFile(fn,'w') as zf:
    zf.write("dist/comiola.exe", "comiola.exe")
    for fn in os.listdir('faq'):
        zf.write(os.path.join('faq',fn), 'faq/%s' % fn )
    for fn in os.listdir('res'):
        zf.write(os.path.join('res',fn), 'res/%s' % fn )
    zf.close()

