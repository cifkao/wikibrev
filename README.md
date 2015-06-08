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

#### zim2db

    wikibrev zim2db [-h] [-c] [-t THREADS] INPUT OUTPUT
    
Read a ZIM dump from `INPUT` and an intermediate database of articles and links is created in `OUTPUT`.

Options:
* `-h`, `--help`  
  show help message and exit
* `-c`, `--compress`  
  compress the database using gzip
* `-t THREADS`, `--threads THREADS`  
  the maximum number of threads to use (default: 8)

#### db2abbr-db

    wikibrev db2abbr-db [-h] INPUT

Read a database (possibly compressed) created by _zim2db_, collect abbreviations from it and add them to the database.


Options:
* `-h`, `--help`  
  show help message and exit

#### zim2abbr-db

    wikibrev zim2abbr-db [-h] [-c] [-t THREADS] INPUT OUTPUT

The _zim2db_ and _db2abbr-db_ steps combined into one action. A ZIM dump is read from `INPUT` and a database of articles, links and abbreviations is created in `OUTPUT`.

Options:
* `-h`, `--help`  
  show help message and exit
* `-c`, `--compress`  
  compress the database using gzip
* `-t THREADS`, `--threads THREADS`  
  the maximum number of threads to use (default: 8)

#### abbr-db2list

    wikibrev abbr-db2list [-h] INPUT [OUTPUT]
    
Read a database of abbreviations (possibly compressed) from `INPUT` and output it in the same format as _zim2list_.
    
Options:
* `-h`, `--help`  
  show help message and exit
