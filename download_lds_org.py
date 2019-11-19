#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from lxml import html
import requests
import re
import json
import datetime
from data_utils import *

if len(sys.argv)>1 and sys.argv[1]=='-o':
    overwrite = True
else:
    overwrite = False

start_date = 1971
end_date = datetime.date.today().year + 1
enc = json.JSONEncoder()
url_base = 'https://www.churchofjesuschrist.org'
for year in range(start_date, end_date):
    for month in [4, 10]:
        outfile = 'data_lds_org/{0}.{1:02d}.json'.format(year, month)
        if overwrite or not os.path.exists(outfile):
            url = '{0}/general-conference/{1}/{2:02d}?lang=eng'.format(url_base, year, month)
            print(url)
            print('=== processing conference: {0:d}-{1:02d}'.format(year, month))

            page = requests.get(url)
            tree = html.fromstring(page.content)
            links = tree.xpath("//a[@class='lumen-tile__link']/@href")
            talks = [l for l in links if '/media' not in l]

            out_list = []
            for t in talks:
                page = requests.get(url_base + t)
                page.encoding = 'UTF-8'
                tree = html.fromstring(page.text)
                title = clean_join_strings(tree.xpath("//*[@id='title1' or @id='subtitle1']//text()"))
                if title!='':
                    # Note: checking some older talks showed the author tags may be different.
                    # Need to check those and update as needed.
                    author = clean_join_strings(tree.xpath("//*[@class='byline']/*[@id='p1' or @id='author1']/text()"))
                    author = re.sub('By |Presented by ', '', author)
                    author_title = clean_join_strings(tree.xpath("//*[@class='byline']/*[@id='p2' or @id='author2']/text()"))
                    body = clean_strings(tree.xpath("//div[@class='body-block']//text()[not(parent::sup)]"))
                    # Remove strings that are numbers, which are assumed to be footnote links
                    #strings = [s for s in strings if not s.isdigit()]
                    #body = re.sub(' +', ' ', ' '.join(strings).strip())
                    scripture_refs = clean_strings(tree.xpath("//a[@class='scripture-ref']//text()"))
                    all_refs = []
                    cur_ref = ''
                    for ref_str in clean_strings(tree.xpath("//*[@class='notes']//li//text()")):
                        cur_ref += ref_str
                        if ref_str.endswith('.'):
                            all_refs.append(cur_ref)
                            cur_ref = ''
                    json_str = enc.encode({'year':year, 'month':month, 'title':title,
                                           'author':author, 'author_title':author_title, 'body':body,
                                           'references':all_refs, 'scripture_references':scripture_refs})

                    wc = len(' '.join(body).split(' '))
                    print('{0:s} ({1:s}) "{2:s}" (word count: {3:d})'.format(author, author_title, title, wc))
                    out_list.append(json_str)

            with open(outfile, 'w') as fh:
                fh.write('\n'.join(out_list))
                print("wrote:", outfile)
