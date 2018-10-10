#!/usr/bin/python

import pandas
import os
import glob
import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as pl
pl.style.use('fivethirtyeight')
import matplotlib.dates as mdates

#dfs = [pandas.read_json(file) for file in os.listdir('data')]
dfs = []
#for file in os.listdir('data'):
#    dfs.append(pandas.read_json(file))
for file in glob.glob('data/*.json'):
    dfs.append(pandas.read_json(file))

df_all = pandas.concat(dfs)
df_all['date'] = pandas.to_datetime(df_all['month'].map(str) + '/' + df_all['year'].map(str))

# strip titles from names
df_all['author'] = df_all['author'].str.replace('^(President|Elder|Bishop) ', '')
df_all['author'] = df_all['author'].str.replace('Wm.', 'William')
df_all = df_all.reset_index()

searches = ({'file':'revelation',
             'include':'revelation'},
            {'file':'cp',
             'include':'covenant path'},
            {'file':'keys',
             'include':'keys'},
            {'file':'satan',
             'include':'(satan|lucifer)'},
            {'file':'savior',
             'include':'the savior'},
            {'file':'jesus',
             'include':'jesus',
             'exclude':'church of jesus christ'},
            {'file':'mormon',
             'include':'mormon',
             'exclude':'book of mormon'},
            {'file':'grace',
             'include':'grace'},
            {'file':'tm',
             'include':'tender (mercy|mercies)'})

for search in searches:
    matches = df_all['body'].str.lower().str.count(search['include'])
    if 'exclude' in search.keys():
        matches -= df_all['body'].str.lower().str.count(search['exclude'])

    #results = df_all.assign(matches=matches)[matches>0][['date', 'author', 'matches']]

    results = df_all.assign(matches=matches).groupby('date').sum()['matches']

    fig, ax = pl.subplots(figsize=(12,5))
    #results.plot.bar(ax=ax)

    ax.bar(results.index, results, width=120)
    ax.xaxis.set_minor_locator(mdates.YearLocator(1, month=3))
    ax.xaxis.set_major_locator(mdates.YearLocator(5, month=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.set_xlim([datetime.date(1971, 1, 1),
                 datetime.date(2019, 4, 1)])
    pl.ylabel('uses per conference')
    pl.title('Uses of "{0:s}"'.format(search['include']))
    pl.savefig('/mnt/d/Quentin/' + search['file'] + '.png')



refs = df_all['body'].str.findall('\(.*?[0-9].*?\)')
rdf = refs.apply(pandas.Series).stack().to_frame()
