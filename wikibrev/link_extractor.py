from __future__ import unicode_literals
import os
import sys
import codecs
import time
import re
import urllib
from collections import deque
import multiprocessing
import Queue
import shutil
import tempfile
import sqlite3
import unzim
from HTMLParser import HTMLParser

class WikiHTMLParser(HTMLParser):
    t = time.time()

    index = None

    is_link = False
    link_url = None
    link_text = ''
    links = []

    is_paragraph = False

    elem_stack = deque()
    forb_depth = 0

    re_forbidden_tag = re.compile(r'^(head|script)$')
    re_forbidden_class = re.compile(r'\b(reference|hatnote)\b')
    re_forbidden_id = re.compile(r'^(cite_.*|coordinates)$')

    re_whitespace = re.compile(r'\s*')
    re_whitespace_only = re.compile(r'^\s*$')
    re_token = re.compile(r'\s*(([^\W\d_]|-)+|[\W\d_])\s*')
    
    re_letter = re.compile(r"[^\W\d_]", re.UNICODE)
    re_html_ext = re.compile(r'\.html?$')
    re_brackets = re.compile(r'\s*\(.*\)\s*')

    def handle_starttag(self, tag, attrs):
        self.elem_stack.append(tag)

        attrs = dict(attrs)
        classes = []
        if 'class' in attrs:
            classes = attrs['class'].split()

        if self.is_forbidden(tag, attrs):
            self.forb_depth += 1

        if tag == 'a':
            if self.forb_depth == 0 and 'external' not in classes and 'href' in attrs:
                self.is_link = True
                self.link_url = attrs['href']
        elif tag == 'p':
            self.is_paragraph = True

    def handle_endtag(self, tag):
        while len(self.elem_stack) > 0:
            top = self.elem_stack.pop()
            if self.forb_depth > 0:
                self.forb_depth -= 1
            if top == tag:
                break

        if tag == 'a' and self.is_link:
            if not self.link_url.startswith('#'):
                url = self.link_url.split('/')[-1].split('#')[-1].strip()
                title = self.re_html_ext.sub('', urllib.unquote(url)).replace('_', ' ') # not necessarily the exact title!
                
                if self.check_abbr_triv(self.link_text, title):
                    self.links += [(self.index, url, self.link_text)]
            self.is_link = False
            self.link_url = None
            self.link_text = ''
        elif tag == 'p':
            self.is_paragraph = False

    def handle_data(self, data):
        if self.is_link:
            self.link_text += data.strip()

        # if self.is_paragraph and self.forb_depth == 0 and not self.re_whitespace_only.match(data):
        #     sys.stdout.write(data)
        #     sys.stdout.write(' ')

    def is_forbidden(self, tag, attrs):
        return ('class' in attrs and self.re_forbidden_class.search(attrs['class'])) or \
                ('id' in attrs and self.re_forbidden_id.match(attrs['id'])) or \
                self.re_forbidden_tag.match(tag)


    def check_abbr_triv(self, abbr, exp):
        # remove brackets (incl. contents)
        abbr = self.re_brackets.sub('', abbr)
        exp = self.re_brackets.sub('', exp)

        if len(abbr) == len(exp):
            return False

        if len(abbr) > len(exp):
            (abbr, exp) = (exp, abbr)

        # too long or too short:
        if len(abbr) < 2:
            return False
        # not containing any letters:
        if not self.re_letter.search(abbr) or not self.re_letter.search(exp):
            return False

        return True


    def tokenize(self, txt):
        return re_token.sub(r' \1', txt).strip()

    def parse_page(self, index, data):
        self.index = index

        self.feed(data)
        links = self.links

        self.is_link = False
        self.is_paragraph = False
        self.links = []
        self.forb_depth = 0
        self.reset()

        return {'index': index, 'links': links}


def thread_init():
    global parser
    parser = WikiHTMLParser()

def process_article(index, data, result_q):
    try:
        result_q.put(parser.parse_page(index, data))
    except:
        print >>sys.stderr, "Error during parsing:", sys.exc_info()
        result_q.put(None)
        raise

def extract_links(zim_path, db_path, n_threads):
    dump = unzim.File(zim_path).articles()

    dbconn = sqlite3.connect(db_path)
    db = dbconn.cursor()

    try:
        db.execute("""create table article (id integer primary key,
                                            title text not null unique,
                                            url text not null unique,
                                            redirect_id integer,
                                            linktarget integer)""")
        db.execute('create index article_redirect_id on article(redirect_id)')
        db.execute("""create table link (article_id integer not null,
                                         tgt_id integer,
                                         tgt_url text not null,
                                         text text not null,
                                         foreign key (article_id) references article(id),
                                         foreign key (tgt_id) references article(id),
                                         unique(article_id, tgt_url, text))""")
        db.execute('create index link_tgt_id on link(tgt_id)')
        db.execute('create index link_text on link(text)')

        t = time.time()

        print >>sys.stderr, "Reading and processing articles"
        pool = multiprocessing.Pool(n_threads, initializer=thread_init, maxtasksperchild=1000)
        mgr = multiprocessing.Manager()
        result_q = mgr.Queue()

        max_in_queue = 1000

        n_read = 0
        n_done = 0
        n_redirs = 0
        n_links = 0
        done_reading = False
        while not done_reading or n_done < n_read:
            if not done_reading and (n_read - n_done) < max_in_queue:
                try:
                    a = dump.next()
                    if a.ns == 'A':
                        if a.redirect_index is not None:
                            n_redirs += 1
                        try:
                            db.execute('insert into article values (?,?,?,?,?)', (a.index, a.title, a.long_url.split('/')[-1], a.redirect_index, a.linktarget))
                        except sqlite3.IntegrityError as e:
                            print >>sys.stderr, 'Integrity error:', unicode(e) + ';', 'article', (a.index, a.title, a.long_url), 'not inserted!'

                        if a.redirect_index is None: # and not a.linktarget:
                            pool.apply_async(process_article, args=(a.index, a.data, result_q))
                            n_read += 1

                            if n_read % 500 == 0:
                                dbconn.commit()
                except StopIteration:
                    done_reading = True
                    print >>sys.stderr, "Finished reading articles"

            try:
                while n_done < n_read:
                    r = result_q.get(False)
                    db.executemany('insert or ignore into link values (?,null,?,?)', r['links'])
                    
                    n_links += db.rowcount

                    n_done += 1
                    if n_done % 2000 == 0:
                        dbconn.commit()
                    if n_done % 2000 == 0:
                        print >>sys.stderr, n_done, 'done'
                        print >>sys.stderr, 'speed:', n_done/(time.time()-t), 'per second'
                        print >>sys.stderr, 'time per article:', (time.time()-t)/n_done
                        sys.stdout.flush()
            except Queue.Empty:
                if done_reading:
                    time.sleep(0.01)


        dbconn.commit()

        print >>sys.stderr, 'Processed', n_read, 'articles'
        print >>sys.stderr, n_links, 'links'
        print >>sys.stderr, n_redirs, 'redirects'
        print >>sys.stderr, 'Took', time.time()-t, 's'
        t = time.time()

        print >>sys.stderr
        print >>sys.stderr, "Resolving links"
        
        db.execute('update link set tgt_id = (select id from article where url = link.tgt_url)')
        dbconn.commit()

        print >>sys.stderr, 'Resolved', db.rowcount, 'links'
        print >>sys.stderr, 'Took', time.time()-t, 's'
        t = time.time()

        print >>sys.stderr 
        print >>sys.stderr, "Removing unresolved links"

        db.execute('delete from link where tgt_id is null')
        dbconn.commit()

        print >>sys.stderr, 'Removed', db.rowcount, 'links'
        print >>sys.stderr, 'Took', time.time()-t, 's'
    finally:
        dbconn.close()
