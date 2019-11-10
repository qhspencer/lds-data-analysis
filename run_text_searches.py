#!/usr/bin/python

import pandas
import os
import glob
import json
import datetime
import argparse
from data_utils import *

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as pl
import matplotlib.dates as mdates

parser = argparse.ArgumentParser()
parser.add_argument('--mpl-style', dest='mpl_style', type=str, default='bmh',
                    choices=['bmh', 'fivethirtyeight'], help='style package for matplotlib plots')
parser.add_argument('--output-dir', dest='output_dir', type=str, default='.',
                    help='path for saving output files')
parser.add_argument('--search-data', dest='search_data', type=str, default='search_data.json',
                    help='JSON file containing search data')
parser.add_argument('--time-axis', dest='time_axis', type=str, default='year',
                    choices=['year', 'conf'], help='specifies spacing of time axis')
parser.add_argument('--norm', dest='norm', type=str, default='conf',
                    choices=['words', 'conf'], help='specifies normalization factor')
parser.add_argument('--smooth', dest='smooth', type=int, default=None,
                    help='size of window for smoothing')
args = parser.parse_args()

# This needs to be set high if a large number of plots are being generated
pl.rcParams['figure.max_open_warning'] = 50
pl.style.use(args.mpl_style)

search_file = args.search_data
output_dir = args.output_dir + '/'

print "Loading data"
searches = json.load(open(search_file))

first_year = 1971
last_year = datetime.date.today().year + 1
if args.time_axis == 'year':
    group = 'year'
    daterange = [first_year, last_year]
    yaxis_str = 'uses per year'
elif args.time_axis == 'conf':
    group = 'date'
    daterange = [datetime.date(first_year, 1, 1),
                 datetime.date(last_year, 4, 1)]
    yaxis_str = 'uses per conference'
if args.norm == 'words':
    yaxis_str = 'uses per million words'

df_all = load_data()
talks_only = get_only_talks(df_all)
talk_counts = talks_only.groupby('date').count()['year'].to_frame('talks')

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
        if args.norm == 'conf':
            results[l] = talks_only.assign(matches=matches).groupby(group).sum()['matches']
        else:
            sums = talks_only.assign(matches=matches).groupby(group).sum()
            results[l] = sums['matches']/sums['word_count']*1e6

    if 'include sum' in search.keys() and search['include sum']=='true':
        results['all combined'] = results.sum(1)

    fig, ax = pl.subplots(figsize=(12,5))
    if args.smooth==None:
        results.plot(ax=ax)
    else:
        results.rolling(args.smooth, min_periods=1, center=True).mean().plot(ax=ax)

    ax.set_xlim(daterange)
    if 'start year' in search.keys():
        ax.set_xlim(left=datetime.date(search['start year'], 4, 1))
    ax.set_ylim(bottom=0)
    pl.ylabel(yaxis_str)
    if 'title' in search.keys():
        pl.title(search['title'])
    pl.savefig(output_dir + search['file'] + '.png')

