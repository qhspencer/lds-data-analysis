#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from lxml import html
import requests
import re
import json
import base64
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
        date_in_future = datetime.date(year, month, 1) > datetime.date.today()
        if (overwrite or not os.path.exists(outfile)) and not date_in_future:
            url = '{0}/study/general-conference/{1}/{2:02d}?lang=eng'.format(url_base, year, month)
            print(url)
            print('=== processing conference: {0:d}-{1:02d}'.format(year, month))

            page = requests.get(url)
            tree = html.fromstring(page.content)
            fullstring = [s for s in tree.xpath('//script//text()') if '__INITIAL_STATE__' in s][0]
            b64string = fullstring.split('"')[1]
            json_data = json.loads(base64.b64decode(b64string))
            session_data = json_data['reader']['bookStore'][f'/eng/general-conference/{year}/{month:02}']['entries']
            talk_lists = [session['section']['entries'] for session in session_data
                          if 'section' in session.keys()]
            talk_urls = [talk['content']['uri'] for talks in talk_lists for talk in talks]

            out_list = []
            for t in talk_urls:
                page = requests.get(url_base + t)
                page.encoding = 'UTF-8'
                page_text = page.text.replace(u'\ufeff', '')
                tree = html.fromstring(page_text)
                title = clean_join_strings(tree.xpath("//title/text()"))
                if title!='':
                    # Note: checking some older talks showed the author tags may be different.
                    # Need to check those and update as needed.
                    author = clean_join_strings(tree.xpath("//*[@class='author-name']/text()"))
                    author = re.sub('By |Presented by ', '', author)
                    author_title = clean_join_strings(tree.xpath("//*[@class='author-role']/text()"))
                    if author_title=='' and author.startswith('President '):
                        author_title = 'President of the Church'
                    body = clean_strings(tree.xpath("//div[@class='body-block']//text()[not(parent::sup)]"))
                    scripture_refs = tree.xpath("//a[@class='scripture-ref']//text()")
                    all_refs = [x.text_content() for x in tree.xpath("//footer[@class='notes']//li")]
                    json_str = enc.encode({'year':year, 'month':month, 'title':title,
                                           'author':author, 'author_title':author_title, 'body':body,
                                           'references':all_refs, 'scripture_references':scripture_refs})

                    wc = len(' '.join(body).split(' '))
                    print('{0:s} ({1:s}) "{2:s}" (word count: {3:d})'.format(author, author_title, title, wc))
                    out_list.append(json_str)

            with open(outfile, 'w') as fh:
                fh.write('[' + ',\n'.join(out_list) + ']')
                print("wrote:", outfile)
