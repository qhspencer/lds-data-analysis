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
parser.add_argument('--time-axis', dest='time_axis', type=str, default='year',
                    choices=['year', 'conf'], help='specifies spacing of time axis')
parser.add_argument('--data-source', dest='ds', type=str, default='file')
args = parser.parse_args()

# This needs to be set high if a large number of plots are being generated
pl.rcParams['figure.max_open_warning'] = 50
pl.style.use(args.mpl_style)

output_dir = args.output_dir + '/'
print("Loading data")
df_all = load_data(source=args.ds)

talks_only = get_only_talks(df_all)
speaker_averages = get_speaker_refs(talks_only)

president_list = talks_only['president'].unique().tolist()
apostle_list = talks_only[(talks_only['date']==talks_only.iloc[-1]['date']) & \
                          (talks_only['rank']>1) & (talks_only['rank']<20)]['author'].unique().tolist()
dead_apostle_list = ['Boyd K. Packer', 'Neal A. Maxwell', 'Bruce R. McConkie', 'James E. Faust']

q15_averages = speaker_averages[speaker_averages.index.isin(apostle_list)]
pres_averages = speaker_averages[speaker_averages.index.isin(president_list)]
prev_q15_averages = speaker_averages[speaker_averages.index.isin(dead_apostle_list)]

note_data = q15_averages.append(pres_averages).append(prev_q15_averages).assign(ha='right', va='bottom')
note_data = note_data.assign(last_name=note_data.index.map(lambda x: x.split(' ')[-1]))
note_data.loc['George Albert Smith', 'last_name'] = 'GASmith'
note_data = note_data.reset_index().set_index('last_name')

def create_fig(col0, col1, note_data, titlestr, filename):

    fig, ax = pl.subplots(figsize=(6,5))
    msize = 30
    q15_averages.plot.scatter(col0, col1, ax=ax, s=msize)
    pres_averages.plot.scatter(col0, col1, ax=ax, c='red', s=msize)
    prev_q15_averages.plot.scatter(col0, col1, ax=ax, c='magenta', s=msize)
    
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    for ln, data in note_data.iterrows():
        ax.annotate(data['author'], data[[col0, col1]], rotation=data['r'],
                    ha=data['ha'], va=data['va'], size='x-small')

    ax.set_autoscale_on(False)
    pl.plot([0,3], [0,3], c=[0.7,0.7,0.7])
    pl.title(titlestr, size='medium')
    pl.savefig(output_dir + filename)


#############################

note_data['ha'] = 'right'
note_data['va'] = 'bottom'
note_data['r'] = 0
note_data.loc[
    ['Renlund', 'Monson', 'Cook', 'Hinckley', 'Bednar', 'Faust', 'Nelson', 'Eyring',
     'Hunter', 'Smith', 'Stevenson', 'McConkie', 'Oaks', 'Holland',
     'Uchtdorf', 'Andersen'], 'ha'] = 'left'
note_data.loc[
    ['Christofferson', 'Cook', 'Oaks', 'Hinckley', 'Faust', 'McKay', 'Benson',
     'Holland', 'Andersen', 'Soares', 'Monson', 'Ballard', 'Kimball'], 'va'] = 'top'
titlestr = 'Jesus and Satan references (per 1000 words)\n by recent apostles and church presidents'
create_fig('Jesus', 'Satan', note_data, titlestr, 'jesus_vs_satan.png')

##############################

note_data['ha'] = 'left'
note_data['va'] = 'bottom'
note_data['r'] = 0
note_data.loc[['Gong', 'Cook', 'McKay', 'Lee', 'Soares', 'Kimball', 'Benson', 'Smith', 'Ballard'], 'ha'] = 'right'
note_data.loc[['Hinckley'], 'ha'] = 'center'
note_data.loc[['Cook', 'Renlund', 'Monson', 'Hunter', 'Ballard', 'Lee', 'Maxwell', 'Kimball', 'Hinckley'], 'va'] = 'top'
note_data.loc[['Eyring', 'Holland'], 'r'] = 15
note_data.loc[['GASmith'], 'r'] = 10
note_data.loc[['Oaks', 'Christofferson', 'Bednar'], 'r'] = 5
titlestr = 'Jesus and church president references (per 1000 words)\n by recent apostles and church presidents'
create_fig('Jesus', 'President', note_data, titlestr, 'jesus_vs_pres.png')

##############################

note_data['ha'] = 'left'
note_data['va'] = 'bottom'
note_data['r'] = 0
note_data.loc[note_data['grace']>1.2, 'ha'] = 'right'
note_data.loc[['Christofferson', 'Monson', 'McConkie', 'Hunter', 'Maxwell', 'Uchtdorf',
               'Hinckley', 'Andersen', 'McKay', 'Faust', 'Smith'], 'va'] = 'top'
note_data.loc[['Hinckley'], 'ha'] = 'center'
note_data.loc[['Oaks', 'Cook'], 'r'] = 5
note_data.loc[['Lee', 'Ballard'], 'r'] = 10
titlestr = 'grace and works references (per 1000 words)\n by recent apostles and church presidents'
create_fig('grace', 'works', note_data, titlestr, 'grace_vs_works.png')

