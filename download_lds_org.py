#!/usr/bin/python
# -*- coding: utf-8

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
url_base = 'https://www.lds.org'
for year in range(start_date, end_date):
    for month in range(4, 11, 6):
        outfile = 'data/{0}.{1:02d}.json'.format(year, month)
        if overwrite or not os.path.exists(outfile):
            print 'loading', year, month
            url = '{0}/general-conference/{1}/{2:02d}?lang=eng'.format(url_base, year, month)

            page = requests.get(url)
            tree = html.fromstring(page.content)
            links = tree.xpath("//a[@class='lumen-tile__link']/@href")
            talks = [l for l in links if 'media' not in l]

            out_list = []
            for t in talks:
                page = requests.get(url_base + t)
                tree = html.fromstring(page.text)

                title = clean_join_strings(tree.xpath(
                    "//h1[@class='title']//text()"))
                if title!='':
                    author = clean_join_strings(tree.xpath(
                        "//*[@class='article-author__name' or @class='article-author']/text()"))
                    author = re.sub('By |Presented by ', '', author)
                    author_title = clean_join_strings(tree.xpath(
                        "//*[@class='article-author__title']/text()"))
                    body = clean_strings(tree.xpath(
                        "//div[@class='article-content']//p//text()"))
                    # Remove strings that are numbers, which are assumed to be footnote links
                    #strings = [s for s in strings if not s.isdigit()]
                    #body = re.sub(' +', ' ', ' '.join(strings).strip())
                    scripture_refs = clean_strings(tree.xpath(
                        "//a[@class='scripture-ref']//text()"))
                    all_refs = [s for s in clean_strings(''.join(
                        tree.xpath("//*[@class='notes']//li//text()")).split('\n')) if s!='']

                    out_list.append({'year':year, 'month':month, 'title':title,
                                     'author':author, 'author_title':author_title, 'body':body,
                                     'references':all_refs, 'scripture_references':scripture_refs})

                    print u'downloaded "{0}", {1}'.format(title, author)

            with open(outfile, 'w') as fh:
                fh.write(enc.encode(out_list))
                print "wrote:", outfile
