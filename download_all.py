#!/usr/bin/python
# -*- coding: utf-8

from lxml import html
import requests
import re
import json

def clean_join_strings(strings):
    replace_table = [(u'\xa0', ' '),
                     (u'\u2019', u'’'),
                     (u'\u201c', u'“'),
                     (u'\u201d', u'”')]
    val = ' '.join(strings).strip()
    for old, new in replace_table:
        val = val.replace(old, new)
    return val

enc = json.JSONEncoder()
url_base = 'https://www.lds.org'
for year in range(1973, 2019):
    for month in range(4, 11, 6):
        print 'loading', year, month
        url = '{0}/general-conference/{1}/{2:02d}?lang=eng'.format(url_base, year, month)

        page = requests.get(url)
        tree = html.fromstring(page.content)
        links = tree.xpath("//a[@class='lumen-tile__link']/@href")
        talks = [l for l in links if 'media' not in l]

        out_list = []
        for t in talks:
            print 'downloading', t
            page = requests.get(url_base + t)
            tree = html.fromstring(page.text)

            title = clean_join_strings(tree.xpath("//h1[@class='title']//text()"))
            author = clean_join_strings(tree.xpath("//*[@class='article-author__name' or @class='article-author']/text()"))
            author = re.sub('By |Presented by ', '', author)
            author_title = clean_join_strings(tree.xpath("//*[@class='article-author__title']/text()"))
            strings = tree.xpath("//div[@class='article-content']//text()")
            body = re.sub(' +', ' ', ' '.join(strings).strip())

            out_list.append({'year':year, 'month':month, 'title':title,
                             'author':author, 'author_title':author_title, 'body':body})

            #print u'loaded "{0}", {1}, {2}'.format(title, author, author_title)

            outfile = 'data/{0}.{1:02d}.json'.format(year, month)
            with open(outfile, 'w') as outfile:
                outfile.write(enc.encode(out_list))
