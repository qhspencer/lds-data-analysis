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

print "Loading data"
searches = json.load(open(search_file))

if 1:
    group = 'year'
    daterange = [1971, 2019]
    yaxis_str = 'uses per year'
else:
    group = 'date'
    daterange = [datetime.date(1971, 1, 1),
                 datetime.date(2019, 4, 1)]
    yaxis_str = 'uses per conference'

dfs = []
for file in glob.glob('data/*.json'):
    dfs.append(pandas.read_json(file))

df_all = pandas.concat(dfs).reset_index()

# Create date column
df_all['date'] = pandas.to_datetime(df_all['month'].map(str) + '/' + df_all['year'].map(str))
df_all['year'] = df_all['date'].dt.year

# Clean up strings:
# standardize author names and remove titles
# remove or replace unneeded characters in body
df_all = df_all.replace(
    {'author': clean_author_dict,
     'body': {'\t|\n':'', u'\u2013':'-'}}, regex=True)

df_all = title_cleanup(df_all)
pres = get_current_president(df_all)
df_all = df_all.join(pres, 'date')
#df_all['tail'] = df_all['body'].str[-31:].str.lower()

talks_only = get_only_talks(df_all)
talk_counts = talks_only.groupby('date').count()['year'].to_frame('talks')

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
    #pl.title('Uses of "{0:s}"'.format(search['include']))
    pl.savefig(output_dir + search['file'] + '.png')

