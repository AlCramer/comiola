cd ./comiola
pyinstaller --onefile -w -F -i "comiola.ico" --name comiola.exe __main__.py
rem pyinstaller --onefile -w -F -i "comiola.ico" my.py
cd ..
rem set innopath=C:\Program Files (x86)\Inno Setup 6
rem "%innopath%"\compil32 /cc .\innosetup.iss

