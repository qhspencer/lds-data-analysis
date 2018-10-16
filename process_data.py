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
pl.style.use('fivethirtyeight')
import matplotlib.dates as mdates

search_file = 'search_data.json'
output_dir = '/mnt/d/Quentin/'
searches = json.load(open(search_file))

#dfs = [pandas.read_json(file) for file in os.listdir('data')]
dfs = []
#for file in os.listdir('data'):
#    dfs.append(pandas.read_json(file))
for file in glob.glob('data/*.json'):
    dfs.append(pandas.read_json(file))

df_all = pandas.concat(dfs).reset_index()

# Create date column
df_all['date'] = pandas.to_datetime(df_all['month'].map(str) + '/' + df_all['year'].map(str))

# Clean up strings:
# standardize author names and remove titles
# remove or replace unneeded characters in body
df_all = df_all.replace({'author': {'^(President|Elder|Bishop|Sister|Brother) ': '',
                                    '.* Grant Bangerter': 'W. Grant Bangerter',
                                    'Wm.': 'William',
                                    'Elaine Cannon':'Elaine A. Cannon',
                                    'Charles Didier':'Charles A. Didier',
                                    'Jose L. Alonso':u'Jos\xe9 L. Alonso',
                                    'H Goaslind':'H. Goaslind',
                                    '^H. Goaslind':'Jack H. Goaslind',
                                    'Goaslind$':'Goaslind, Jr.',
                                    'Larry Echo Hawk':'Larry J. Echo Hawk',
                                    'Ardeth Greene Kapp': 'Ardeth G. Kapp',
                                    'William Rolfe Kerr': 'W. Rolfe Kerr',
                                    '^O. Samuelson': 'Cecil O. Samuelson',
                                    'Mary Ellen Smoot': 'Mary Ellen W. Smoot',
                                    'Ellen W. Smoot': 'Mary Ellen W. Smoot',
                                    'Michael J. Teh':'Michael John U. Teh',
                                    'Teddy E. Brewerton':'Ted E. Brewerton'},
                         'body': {'\t|\n':'',
                                  u'\u2013':'-'}}, regex=True)
df_all['tail'] = df_all['body'].str[-31:].str.lower()

#for search in [searches[2]]:
for search in searches:
    results = pandas.DataFrame()

    for s in search['search']:
        matches = df_all['body'].str.lower().str.count(s['include'])
        if 'exclude' in s.keys():
            for excl_str in s['exclude']:
                matches -= df_all['body'].str.lower().str.count(excl_str)

        results[s['label']] = df_all.assign(matches=matches).groupby('date').sum()['matches']

    fig, ax = pl.subplots(figsize=(12,5))
    results.plot(ax=ax)
    #ax.bar(results.index, results, width=120)

    #ax.xaxis.set_minor_locator(mdates.YearLocator(1, month=3))
    #ax.xaxis.set_major_locator(mdates.YearLocator(5, month=3))
    #ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    ax.set_xlim([datetime.date(1971, 1, 1),
                 datetime.date(2019, 4, 1)])
    pl.ylabel('uses per conference')
    #pl.title('Uses of "{0:s}"'.format(search['include']))
    pl.savefig(output_dir + search['file'] + '.png')


# Process references
ref_df = get_refs(df_all)

sw_counts = get_ref_counts(ref_df)
sw_counts.columns = sw_counts.columns.get_level_values(1)
sw_counts.columns.name = 'Standard Work'

ref_freq = ref_df.groupby('ref').count()['date'].to_frame('uses')
num_refs = 20
top_refs = ref_freq.sort_values('uses').iloc[-num_refs:][::-1]


fig, ax = pl.subplots(figsize=(12,5))
sw_counts.plot(ax=ax)
ax.set_xlim([datetime.date(1971, 1, 1),
             datetime.date(2019, 4, 1)])
#ax.xaxis.set_minor_locator(mdates.YearLocator(1, month=4))
#ax.xaxis.set_major_locator(mdates.YearLocator(5, month=4))
#ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
pl.legend(sw_counts.columns, ncol=2, loc='upper left')
pl.title('Scripture citations by standard work')
pl.ylabel('references per conference')
pl.savefig(output_dir + 'refs.png')


fig, ax = pl.subplots(figsize=(12,5))
#top_refs.plot.bar(ax=ax)
ax.bar(range(num_refs), top_refs.values, align='center')
ax.set_xlim([-0.5, num_refs-0.5])
pl.xticks(range(num_refs), top_refs.index, rotation=45, ha='right')
pl.subplots_adjust(bottom=0.25)
pl.grid(axis='x')
pl.title('Most-cited scriptures')
pl.ylabel('total references')
pl.savefig(output_dir + 'toprefs.png')
