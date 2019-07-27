#!/usr/bin/python

import pandas
import os
import glob
import json
import datetime
from data_utils import *

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as pl
#pl.style.use('fivethirtyeight')
pl.style.use('bmh')
import matplotlib.dates as mdates
pl.rcParams['figure.max_open_warning'] = 50

search_file = 'search_data.json'
output_dir = '/mnt/d/Quentin/'
time_axis = 'conf'

print "Loading data"
searches = json.load(open(search_file))

first_year = 1971
last_year = datetime.date.today().year #+ 1
if time_axis == 'year':
    group = 'year'
    daterange = [first_year, last_year]
    yaxis_str = 'uses per year'
elif time_axis == 'conf':
    group = 'date'
    daterange = [datetime.date(first_year, 1, 1),
                 datetime.date(last_year, 4, 1)]
    yaxis_str = 'uses per conference'


df_all = load_data()
talks_only = get_only_talks(df_all)
talk_counts = talks_only.groupby('date').count()['year'].to_frame('talks')
#df_all['tail'] = df_all['body'].str[-31:].str.lower()


#for search in [searches[2]]:
for search in searches:
    print 'running search:', search['search']
    if 'case sensitive' in search.keys() and search['case sensitive']=='true':
        cs = True
    else:
        cs = False
    results = pandas.DataFrame()

    for s in search['search']:
        if cs:
            matches = talks_only['body'].str.count(s['include'])
        else:
            matches = talks_only['body'].str.lower().str.count(s['include'])
        if 'exclude' in s.keys():
            for excl_str in s['exclude']:
                if cs:
                    matches -= talks_only['body'].str.count(excl_str)
                else:
                    matches -= talks_only['body'].str.lower().str.count(excl_str)

        if 'label' in s.keys():
            l = s['label']
        else:
            l = s['include']
        results[l] = talks_only.assign(matches=matches).groupby(group).sum()['matches']

    fig, ax = pl.subplots(figsize=(12,5))
    results.plot(ax=ax)
    #ax.bar(results.index, results, width=120)

    #ax.xaxis.set_minor_locator(mdates.YearLocator(1, month=3))
    #ax.xaxis.set_major_locator(mdates.YearLocator(5, month=3))
    #ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    ax.set_xlim(daterange)
    pl.ylabel(yaxis_str)
    if 'title' in search.keys():
        pl.title(search['title'])
    pl.savefig(output_dir + search['file'] + '.png')

