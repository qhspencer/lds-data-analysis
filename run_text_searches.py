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

ta_dict = {'year': 'year',
           'conf': 'date',
           'five': '5 year period',
           'decade': 'decade'}
nm_dict = {'words': 'uses per million words',
           'conf': 'uses per conference'}

parser = argparse.ArgumentParser()
parser.add_argument('--mpl-style', dest='mpl_style', type=str, default='bmh',
                    choices=['bmh', 'fivethirtyeight'], help='style package for matplotlib plots')
parser.add_argument('--output-dir', dest='output_dir', type=str, default='.',
                    help='path for saving output files')
parser.add_argument('--search-data', dest='search_data', type=str, default='search_data.json',
                    help='JSON file containing search data')
parser.add_argument('--time-axis', dest='time_axis', type=str, default='year',
                    choices=ta_dict.keys(), help='specifies spacing of time axis')
parser.add_argument('--norm', dest='norm', type=str, default='words',
                    choices=nm_dict.keys(), help='specifies normalization factor')
parser.add_argument('--smooth', dest='smooth', type=int, default=None,
                    help='size of window for smoothing')
args = parser.parse_args()

# This needs to be set high if a large number of plots are being generated
pl.rcParams['figure.max_open_warning'] = 50
pl.style.use(args.mpl_style)
prop_cycle = pl.rcParams['axes.prop_cycle']

search_file = args.search_data
output_dir = args.output_dir + '/'

print("Loading data")
searches = json.load(open(search_file))

talks_only = get_only_talks(load_data())
talks_only['5 year period'] = talks_only['date'].dt.year.map(lambda x: datetime.date(int(x/5)*5+2, 6, 1))

end_date = talks_only.date.max()
daterange = [datetime.date(talks_only.date.min().year, 1, 1),
             datetime.date(end_date.year, end_date.month+2, 30+1*(end_date.month>6))]

group = ta_dict[args.time_axis]
yaxis_str = nm_dict[args.norm]


for search in searches:
    results = text_search(talks_only, search, group, args.norm)

    fig, ax = pl.subplots(figsize=(12,5))
    if args.smooth==None:
        results.plot(ax=ax)
    else:
        ax.set_prop_cycle(prop_cycle[:len(results.columns)])
        results.rolling(args.smooth, min_periods=1, center=True).mean().plot(ax=ax)
        results.plot(ax=ax, style='.', legend=False)

    ax.set_xlim(daterange)
    #ax.xaxis.set_major_locator(mdates.YearLocator(10))
    #ax.xaxis.set_minor_locator(mdates.YearLocator(5))
    if 'start year' in search.keys():
        ax.set_xlim(left=datetime.date(search['start year'], 4, 1))
    ax.set_ylim(bottom=0)
    pl.ylabel(yaxis_str)
    if 'title' in search.keys():
        pl.title(search['title'])
    pl.savefig(output_dir + search['file'] + '.png')

