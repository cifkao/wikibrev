#!/usr/bin/env python
from __future__ import unicode_literals
import sqlite3
import os
import sys
import codecs
import re
from autozip import AutoZip
from contextlib import closing

re_whitespace = re.compile(r'\s+')
re_whitespace_only = re.compile(r'^\s*$')
re_token = re.compile(r'\s*(([^\W\d_]|[0-9]|-)+\.?|[\W\d_])\s*')

re_letter = re.compile(r"[^\W\d_]", re.UNICODE)
re_non_alnum = re.compile(r'\W', re.UNICODE)
re_html_ext = re.compile(r'\.html?$')
re_brackets = re.compile(r'\s*\(.*\)\s*')

def tokenize(txt):
    return re_whitespace.sub(' ', re_token.sub(r' \1', txt).strip())

def check_abbr(abbr, exp):
    # remove brackets (incl. contents)
    abbr = re_brackets.sub('', abbr)
    exp = re_brackets.sub('', exp)

    if len(abbr) == len(exp):
        return False

    if len(abbr) > len(exp):
        abbr, exp = exp, abbr

    abbr = tokenize(abbr)
    exp = tokenize(exp)

    abbr_letters = ''.join(re_letter.findall(abbr)).lower()
    exp_letters = ''.join(re_letter.findall(exp)).lower()

    abbr_alnum = re_non_alnum.sub('', abbr).lower()
    exp_alnum = re_non_alnum.sub('', exp).lower()

    abbr_words = re_non_alnum.sub(' ', abbr).lower().split()
    exp_words = re_non_alnum.sub(' ', exp).lower().split()

    # too short:
    if len(abbr) < 2:
        return False
    # not containing any letters:
    if len(abbr_letters) == 0:
        return False
    # too long:
    # if len(abbr) > 3*len(exp_words):
    #     return False
    # same number of words:
    # if len(abbr_words) == len(exp_words):
    #     return False
    # exp contains all letters from abbr, in the same order, as a substring:
    if abbr_letters in exp_letters:
        return False
    # all words from abbr are in exp:
    if set(abbr_words).issubset(set(exp_words)):
        return False


    j = 0
    for w in exp_words:
        if j == 0:
            # the first letter of the abbreviation must match the
            # first letter of a word
            if w[0] == abbr_alnum[0]:
                # it matches, so move to the next character in both strings
                j = 1
                w = w[1:]
            else: continue

        for c in w:
            if j >= len(abbr_alnum): break
            if abbr_alnum[j] == c: j += 1

    if j >= len(abbr): return True

    return False

def get_abbr(abbr, exp, idx):
    abbr = re_brackets.sub('', abbr)
    exp = re_brackets.sub('', exp)

    if len(abbr) > len(exp):
        abbr, exp = exp, abbr
    
    return (idx, abbr, exp)

if __name__ == '__main__':
    UTF8Writer = codecs.getwriter('utf8')
    sys.stdout = UTF8Writer(sys.stdout)

    dbpath = '/a/LRC_TMP/cifka/articles.db'
    
    with AutoZip(dbpath, tmpdir='/mnt/h/tmp', readonly=True) as auto_dbpath:
        with closing(sqlite3.connect(auto_dbpath)) as dbconn:
            db = dbconn.cursor()
            db.execute('drop table if exists abbrev')
            db.execute("""create table abbrev (article_id integer,
                                               abbr text not null,
                                               exp text not null,
                                               foreign key (article_id) references article(id),
                                               unique(article_id, abbr, exp))""")
 

            def abbrevs():
                db2 = dbconn.cursor() # the other cursor is being used for inserting, must use a different one!
                links = db2.execute('select distinct L.text, A.title, A.id from link L join article a on L.tgt_id = A.id')

                n_done = 0
                for (a, b, idx) in links:
                    if check_abbr(a, b):
                        yield get_abbr(a, b, idx)
                        n_done += 1

                        if n_done % 1000 == 0:
                            print n_done, 'abbrevs collected'
                            sys.stdout.flush()
                print 'Done processing links'

                redirs = db2.execute('select distinct A.title, R.title, A.id from article A join article R on A.redirect_id = R.id')

                for (a, b, idx) in redirs:
                    if check_abbr(a, b):
                        yield get_abbr(a, b, idx)
                        n_done += 1

                        if n_done % 1000 == 0:
                            print n_done, 'abbrevs collected'
                print 'Done processing redirects'

            db.executemany('insert or ignore into abbrev values(?,?,?)', abbrevs())
            dbconn.commit()
