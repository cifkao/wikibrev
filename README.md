Wikibrev
========
Wikibrev is a tool for extracting abbreviations and their expansions from Wikipedia dumps in the [ZIM file format] (http://www.openzim.org).

Installation
------------
Wikibrev requires [Python 2.x] (https://www.python.org/), [zimlib] (http://www.openzim.org/wiki/Zimlib) and libmagic.

To install Wikibrev, download the sources and run:

    python setup.py install

Usage
-----
Wikibrev is run from the terminal:

    wikibrev [-h] [--tmp TMPDIR] ACTION [ARGS...]

Options:
* `-h`, `--help`  
  show help and exit
* `--tmp TMPDIR`  
  the path to a temporary directory

### Actions
#### zim2list

    wikibrev zim2list [-h] [-t THREADS] INPUT [OUTPUT]

This is the easiest way to use Wikibrev. A ZIM dump is read from `INPUT` and a list of abbreviations is written to
the standard output (or `OUTPUT`, if specified). The output is in the TSV format, with an abbreviation and its
expansion on each line, separated by a tab.

Options:
* `-h`, `--help`  
  show help and exit
* `-t THREADS`, `--threads THREADS`  
  the maximum number of threads to use (default: 8)
