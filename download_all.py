#!/usr/bin/python
# -*- coding: utf-8

from lxml import html
import requests
import re
import json
from data_utils import *


enc = json.JSONEncoder()
url_base = 'https://www.lds.org'
for year in range(1980, 2019):
    for month in range(4, 11, 6):
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
            author = clean_join_strings(tree.xpath(
                "//*[@class='article-author__name' or @class='article-author']/text()"))
            author = re.sub('By |Presented by ', '', author)
            author_title = clean_join_strings(tree.xpath(
                "//*[@class='article-author__title']/text()"))
            strings = clean_strings(tree.xpath(
                "//div[@class='article-content']//text()"))
            # Remove strings that are numbers, which are assumed to be footnote links
            strings = [s for s in strings if not s.isdigit()]
            body = re.sub(' +', ' ', ' '.join(strings).strip())
            scripture_refs = clean_strings(tree.xpath(
                "//a[@class='scripture-ref']//text()"))
            all_refs = [s for s in clean_strings(''.join(
                tree.xpath("//*[@class='notes']//li//text()")).split('\n')) if s!='']

            out_list.append({'year':year, 'month':month, 'title':title,
                             'author':author, 'author_title':author_title, 'body':body,
                             'references':all_refs, 'scripture_references':scripture_refs})

            print u'downloaded "{0}", {1}'.format(title, author)

            outfile = 'data/{0}.{1:02d}.json'.format(year, month)
            with open(outfile, 'w') as outfile:
                outfile.write(enc.encode(out_list))
