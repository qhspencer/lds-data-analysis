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
args = parser.parse_args()

# This needs to be set high if a large number of plots are being generated
pl.rcParams['figure.max_open_warning'] = 50
pl.style.use(args.mpl_style)

search_file = args.search_data
output_dir = args.output_dir
time_axis = 'year'

print "Loading data"
searches = json.load(open(search_file))

first_year = 1971
last_year = datetime.date.today().year + 1
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

    ax.set_xlim(daterange)
    pl.ylabel(yaxis_str)
    if 'title' in search.keys():
        pl.title(search['title'])
    pl.savefig(output_dir + search['file'] + '.png')

