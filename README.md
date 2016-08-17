# XShell
Lightweight shell emulation to exploit XXE

## Goal
The goal of this tool is to ease the pentester's work by letting him concentrate only the important things: files to leak!

## Usage
The script can be used as is or you can pass it a `.ini` file which will set some internal variables.
To launch your first attack, you only need to set two variables:
- `leak_url` which is the URL on which the attack will be carried out
- `payload` which must be a valid Python dictionary (or a path to a file containing one) that contains all needed parameters that will be sent in the request (POST or GET)


## TODO
- use JSON instead of Python dict (I'm too lazy for now)
- add base payloads (for OOB exploitation, or examples with some wrappers, get some inspiration from [XXE Ceaht Sheet](http://web-in-security.blogspot.fr/2016/03/xxe-cheat-sheet.html) and [XXEinjector](https://github.com/enjoiz/XXEinjector))
- add cookie usage
- add GET option

## Known problems
- problems with `~` path
- problems with path/file autocomplete
- problems with differentiation between files and directories
- all lines leaked by `ls` command are added to the autocomplete list (means the list can have a **HUGE** memory footprint)
