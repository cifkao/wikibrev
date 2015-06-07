#!/usr/bin/env python
import sys
import os
import codecs
import argparse
import tempfile
import shutil
import gzip
import sqlite3
from contextlib import closing
from autozip import AutoZip
from ask import ask_yes_no
from link_extractor import extract_links
from abbrev_processor import make_abbrevs


def compress_file(fname_in, fname_out):
    f_in = open(fname_in, 'rb')
    f_out = gzip.open(fname_out, 'wb')
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()

def database_to_text(dbpath, out_f):
    with closing(sqlite3.connect(dbpath)) as dbconn:
        db = dbconn.cursor()
        abbrevs = db.execute('select distinct abbr, exp from abbrev order by lower(abbr) asc')
        for (abbr, exp) in abbrevs:
            out_f.write(abbr)
            out_f.write('\t')
            out_f.write(exp)
            out_f.write('\n')

def ask_overwrite(fname):
    if os.path.exists(fname):
        if ask_yes_no(sys.stderr, fname + " already exists; do you wish to overwrite?"):
            os.remove(fname)
        else:
            print >>sys.stderr, 'Aborting'
            return False
    return True

UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)
sys.stderr = UTF8Writer(sys.stderr)

parser = argparse.ArgumentParser(
        description="""
        Collect abbreviations from Wikipedia.
        """)
parser.add_argument('--tmp', default=None, help='temporary files directory path')
subparsers = parser.add_subparsers(title='actions', dest='action')

parser_links = subparsers.add_parser('zim2db',
        help="""
        Read a ZIM dump and produce a database of articles and links to potential abbreviations.
        """)
parser_links.add_argument('input', metavar='INPUT', help='a ZIM dump')
parser_links.add_argument('output', metavar='OUTPUT', help='the resulting SQLite database')
parser_links.add_argument('-c', '--compress', action='store_true', help='compress the database using gzip')
parser_links.add_argument('-t', '--threads', type=int, default=8, help='the number of threads to use (default: 8)')

parser_abbrevs = subparsers.add_parser('db2abbr-db',
        help="""
        Read a database of articles and links and add abbreviations to it.
        """)
parser_abbrevs.add_argument('input', metavar='INPUT', help='a SQLite database, possibly compressed using gzip')

parser_links_abbrevs = subparsers.add_parser('zim2abbr-db',
        help="""
        Read a ZIM dump and produce a database of articles, links and abbreviations.
        """)
parser_links_abbrevs.add_argument('input', metavar='INPUT', help='a ZIM dump')
parser_links_abbrevs.add_argument('output', metavar='OUTPUT', help='the resulting SQLite database')
parser_links_abbrevs.add_argument('-c', '--compress', action='store_true', help='compress the database using gzip')
parser_links_abbrevs.add_argument('-t', '--threads', type=int, default=8, help='the number of threads to use (default: 8)')

parser_list = subparsers.add_parser('abbr-db2list',
        help="""
        Output a database of abbreviations in plain text form.
        """)
parser_list.add_argument('input', metavar='INPUT', help='an SQLite database')
parser_list.add_argument('output', metavar='OUTPUT', nargs='?', default='-', help='an output file')

parser_links_abbrevs_list = subparsers.add_parser('zim2list',
        help="""
        Read a ZIM dump and produce a list of abbreviations in plain text form.
        """)
parser_links_abbrevs_list.add_argument('input', metavar='INPUT', help='a ZIM dump')
parser_links_abbrevs_list.add_argument('output', metavar='OUTPUT', nargs='?', default='-', help='an output file')
parser_links_abbrevs_list.add_argument('-t', '--threads', type=int, default=8, help='the number of threads to use (default: 8)')

args = parser.parse_args()

tmpdir = tempfile.mkdtemp(dir=args.tmp)

try:
    if args.action == 'zim2db':
        if not ask_overwrite(args.output):
            sys.exit(0)

        if not args.compress:
            extract_links(args.input, args.output, args.threads)
        else:
            dbpath = os.path.join(tmpdir, 'db.db')
            extract_links(args.input, dbpath, args.threads)
            print >>sys.stderr
            print >>sys.stderr, 'Compressing database'
            compress_file(dbpath, args.output)

    elif args.action == 'db2abbr-db':
        with AutoZip(args.input, tmpdir) as dbpath:
            make_abbrevs(dbpath)

    elif args.action == 'zim2abbr-db':
        if not ask_overwrite(args.output):
            sys.exit(0)

        if args.compress:
            dbpath = os.path.join(tmpdir, 'abbr-db.db')
        else:
            dbpath = args.output

        extract_links(args.input, dbpath, args.threads)
        print >>sys.stderr
        make_abbrevs(dbpath)

        if args.compress:
            print >>sys.stderr
            print >>sys.stderr, 'Compressing database'
            compress_file(dbpath, args.output)

    elif args.action == 'abbr-db2list':
        if args.output == '-':
            out_f = sys.stdout
        else:
            if not ask_overwrite(args.output):
                sys.exit(0)
            out_f = UTF8Writer(open(args.output, 'w'))

        with AutoZip(args.input, tmpdir, readonly=True) as dbpath:
            database_to_text(dbpath, out_f)

        if out_f is not sys.stdout:
            out_f.close()

    elif args.action == 'zim2list':
        if args.output == '-':
            out_f = sys.stdout
        else:
            if not ask_overwrite(args.output):
                sys.exit(0)
            out_f = UTF8Writer(open(args.output, 'w'))

        dbpath = os.path.join(tmpdir, 'abbr-db.db')

        extract_links(args.input, dbpath, args.threads)
        print >>sys.stderr
        make_abbrevs(dbpath)
        print >>sys.stderr
        database_to_text(dbpath, out_f)

        if out_f is not sys.stdout:
            out_f.close()

finally:
    shutil.rmtree(tmpdir)
