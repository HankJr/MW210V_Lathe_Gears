# MW210V_Lathe_Gears
Calculate / determine gear sets for feedrates and thread cutting on the MW210V and similar lathes. Inspired by the program by Matthias Wandel <https://github.com/Matthias-Wandel/lathe-thread-gears>, but apart from a handful lines of code, completely different.

The gear tables on these lathes aren't great. Missing feedrates, inaccurate rates, it's pretty bad.

This Python program will check all possible combinations that are possible with the collection of gears you have available, and gives you the nearset approximations of the feedrates you specify.

Results are written to stdout, as well as a logfile. Data (gears available, feedrates desired, lathe specifics &c.) can be entered into the code, entered on the command line, or saved in a config file that is read at startup.
