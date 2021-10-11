#!/usr/bin/python
# -*- coding: utf-8

import os
import re
import sys
from lxml import html
from selenium import webdriver
import time
import datetime
from data_utils import *
import json
import argparse
enc = json.JSONEncoder()

parser = argparse.ArgumentParser()
parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                    help='overwrite stored results if present')
parser.add_argument('--start-year', dest='start_year', type=int, default=1942,
                    help='year to start downloads')
args = parser.parse_args()

if sys.platform=='linux': # This will return "linux" on both Linux and WSL systems
    # To install the Chrome driver and X server required for WSL, see the instructions
    # at https://www.gregbrisebois.com/posts/chromedriver-in-wsl2/
    driver = webdriver.Chrome()
else: # MacOS: use Safari driver
    driver = webdriver.Safari()

def parse_talk(tree, year, month):
    xp_prefix = "//div[@id='centercolumn']"
    exclude_cites = '''[not(ancestor::*[@class='kicker']) and
                        not(ancestor::span[contains(@class, 'ccontainer lparen')]) and
                        not(ancestor::span[contains(@class, 'ccontainer lbrack')]) and
                        not(ancestor::*[contains(@id, 'reference')]) and
                        not(ancestor::*[@class='noteMarker'])]'''
    title = clean_join_strings(tree.xpath(xp_prefix + "//p[@class='gctitle']//text()"))
    if title!='': # old format
        author = clean_join_strings(tree.xpath(xp_prefix + "//p[@class='gcspeaker']//text()"))
        author_title = clean_join_strings(tree.xpath(xp_prefix + "//p[@class='gcspkpos']//text()"))
        bib = clean_join_strings(tree.xpath(xp_prefix + "//p[@class='gcbib']//text()"))
        body = clean_strings(tree.xpath(xp_prefix + "//div[@class='gcbody']//text()" + exclude_cites))
    else: # new format
        title = clean_join_strings(tree.xpath(xp_prefix + "//h1//text()"))
        header = clean_strings(tree.xpath(xp_prefix + "//div[@class='byline']//p//text()"))
        if len(header)==2:
            author, author_title = header
        elif len(header)==1:
            author = header[0]
            author_title = ''
        else:
            author = ''
            author_title = ''
        author = re.sub('By |Presented by ', '', author)
        body = clean_strings(tree.xpath(xp_prefix + "//div[@id='primary' or @class='body-block']//text()" + exclude_cites))

    if author_title=='':
        if author.startswith('President '):
            author_title = 'President of the Church'
        if author.startswith('Bishop '):
            author_title = 'Presiding Bishop'

    scripture_refs = [ref for ref in clean_strings(
        tree.xpath(xp_prefix + "//*[@class='citation']//text()")) if ref!='']

    return enc.encode({'year':year, 'month':month, 'title':title,
                       'author':author, 'author_title':author_title, 'body':body,
                       'scripture_references':scripture_refs})

monthdict = {'April': 4, 'October': 10}

url_base = 'https://scriptures.byu.edu/#:'
years = range(args.start_year-1830,
              datetime.date.today().year-1829)
for year in years:
    hyear = hex(year)[2:]
    for mstr in ('', '8'):
        # create conference URL, which is based on the hex version of the year since 1830
        url = url_base + ':g' + mstr + hyear
        print(url)
        # Load URL and pause 2 seconds. This number may need to be increased, depending
        # on the computer and the connection, but has generally been sufficient for testing
        driver.get(url)
        time.sleep(3)
        html_txt = driver.execute_script("return document.body.innerHTML")
        tree = html.fromstring(html_txt)
        # Parse the XML tree to find links to each talk in the conference
        # Trying to click the links directly via the selenium library has
        # produced incorrect results, but I found that all of the GC talk
        # links are called using the getTalk() function, so I get the numbers
        # and convert them directly to URLs
        lctext = tree.xpath('//span[@class="largecrumb"]//text()')

        # Get year and month from page text
        year_month_str = [s for s in lctext if ndash in s][0]
        print('=== processing conference:', year_month_str)
        year, month = year_month_str.split(ndash)
        year = int(year)
        month = monthdict[month]

        outfile = 'data_byu_edu/{0}.{1:02d}.json'.format(year, month)
        if args.overwrite or not os.path.exists(outfile):
            talk_list = tree.xpath('//a/@onclick[contains(.,"getTalk(\'")]')
            json_data = []
            for t in talk_list:
                intval = int(re.findall("'[0-9]*'", t)[0].strip("'"))
                hexval = hex(intval)[2:]
                print('downloading talk #{:d} ({:s})'.format(intval, hexval))
                talk_url = url_base + 't' + hexval
                driver.get(talk_url)
                time.sleep(2)
                html_txt = driver.execute_script("return document.body.innerHTML")
                tree = html.fromstring(html_txt)
                json_str = parse_talk(tree, year, month)

                talk_data = json.loads(json_str)
                wc = len(' '.join(talk_data['body']).split(' '))
                print('{0:s} ({1:s}) "{2:s}" (word count: {3:d})'.format(
                    talk_data['author'], talk_data['author_title'], talk_data['title'], wc))
                json_data.append(json_str)

            with open(outfile, 'w') as fh:
                fh.write('[' + ',\n'.join(json_data) + ']')
                print("wrote:", outfile)
