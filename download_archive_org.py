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

strlist = (
    'conferencereport1970sa',
    'conferencereport1970a',
    )
startyear = 1898
endyear = 1954 #1971

enc = json.JSONEncoder()
url_base = 'https://archive.org/download'
for year in range(endyear, startyear, -1): #range(startyear, endyear):
    print "downloading", year
    for month, urlstr in ((4, 'a'), (10, 'sa')):
        url = '{0}/conferencereport{1:d}{2}/conferencereport{1:d}{2}_djvu.txt'.format(url_base, year, urlstr)
        outfile = 'data/{0}.{1:02d}.txt'.format(year, month)

        text = requests.get(url).content
        if not text.startswith('<!DOCTYPE html>'):
            month_text = text[:re.search(str(year), text[:2000]).span()[0]].split('\n')[-1].split(' ')[0]
            if not ((month==4 and month_text.upper()!='APRIL') or (month==10 and month_text.upper()!='OCTOBER')):
                print "warning, month mismatch:", month_text

            with open(outfile, 'w') as fh:
                fh.write(text)
                print "wrote:", outfile
        else:
            print "no data available:", outfile



#text = [line.strip() for line in requests.get(url2).content.split('\n')]
