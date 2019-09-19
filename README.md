# BF-Yield.py

Simple python script I wrote to help predict yield from using the Black Forge AFK farm exploit in Destiny 2. Scripted it because I got tired of doing the math to predict yield every time.

I coded this with Windows in mind because honestly if you're playing D2, survey says you have a Windows machine.

## Running/Compiling

Literally nothing special. No dependencies to install (unless you want to compile). Just run `bf-yield.py` and give it how much planetary materials you have.

Added all these other files (icons, etc.) because I wanted to compile it into a .exe using pyinstaller and put it on GitHub. (I guess also so I can use it as a template for future reference?)

If you DO want to compile the app yourself, here's the commands I used:

```bash
pip install pyinstaller
pyinstaller -F -i icons/appicon.ico --version-file file_version_info.txt bf-yield.py
```

-----

*This project is Licensed under the GNU General Public License. Copyright (C) 2019 Andrew "Azure-Agst" Augustine*
