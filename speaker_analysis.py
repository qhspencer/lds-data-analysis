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
parser.add_argument('--data-source', dest='ds', type=str, default='all')
args = parser.parse_args()

# This needs to be set high if a large number of plots are being generated
pl.rcParams['figure.max_open_warning'] = 50
pl.style.use(args.mpl_style)

output_dir = args.output_dir + '/'
print "Loading data"
df_all = load_data(source=args.ds)

talks_only = get_only_talks(df_all)
talks_only = talks_only.assign(President=0)
talks_only['not_president'] = talks_only['author']!=talks_only['president']
for pres in talks_only['president'].unique():
    pres2 = 'President ' + pres.split(' ')[-1]
    pres_idx = talks_only['president']==pres
    talks_only.loc[pres_idx, 'President'] = talks_only[pres_idx].body.str.count(pres) + \
                                            talks_only[pres_idx].body.str.count(pres2)

president_list = talks_only['president'].unique().tolist()
apostle_list = [
    #'Russell M. Nelson',
    'Ulisses Soares', 'Dieter F. Uchtdorf', 'Henry B. Eyring', 'M. Russell Ballard',
    'Neil L. Andersen', 'Jeffrey R. Holland', 'Gary E. Stevenson', 'Dallin H. Oaks',
    'Dale G. Renlund', 'Quentin L. Cook', 'D. Todd Christofferson',
    'Gerrit W. Gong', 'David A. Bednar', 'Ronald A. Rasband']
dead_apostle_list = [
    'Boyd K. Packer', 'Neal A. Maxwell', 'Bruce R. McConkie', 'James E. Faust']
dead_pres_list = president_list
#dead_pres_list.remove('Russell M. Nelson')

#####

speaker_refs = talks_only[['year', 'month', 'author_title', 'author', 'word_count', 'President', 'not_president']]
speaker_refs = speaker_refs.assign(Jesus=talks_only.body.str.count('Jesus') + \
                                   talks_only.body.str.count('Christ') - \
                                   talks_only.body.str.count('Jesus Christ') + \
                                   talks_only.body.str.count('Savior') - \
	                           talks_only.body.str.count('[Cc]hurch of Jesus Christ') - \
                                   talks_only.body.str.count('Jesus Christ.{0,20} [Aa]men') - \
                                   talks_only.body.str.count('Jesus is the Christ'))
speaker_refs = speaker_refs.assign(Satan=talks_only.body.str.count('Satan') + \
                                   talks_only.body.str.count('Lucifer') + \
                                   talks_only.body.str.count('the [Dd]evil') + \
                                   talks_only.body.str.count('the [Aa]dversary'))
speaker_refs = speaker_refs.assign(grace=talks_only.body.str.count('(grace|mercy|mercies|merciful)'))
speaker_refs = speaker_refs.assign(works=talks_only.body.str.count(
    '(obey|obedient|qualify|qualified|worthy|worthiness)'))


col_list = ['Jesus', 'Satan', 'grace', 'works', 'President']

speaker_sum = speaker_refs.groupby('author').sum().drop('not_president', 1)
speaker_sum['word_count_np'] = speaker_refs[speaker_refs['not_president']].groupby('author').sum()['word_count']
speaker_averages = speaker_sum[col_list].divide(speaker_sum['word_count'], 0)*1000
speaker_averages['President'] = speaker_sum['President']/speaker_sum['word_count_np']*1000
## This version normalizes by talk rather than by word count
#speaker_averages = speaker_refs.groupby('author').mean()

talk_counts = talks_only.groupby('author').count()['index'].to_frame()
talk_counts.columns = ['count']
speaker_averages = speaker_averages.join(talk_counts).fillna(0)

q15_averages = speaker_averages[speaker_averages.index.isin(apostle_list)]
pres_averages = speaker_averages[speaker_averages.index.isin(dead_pres_list)]
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
    ['Renlund', 'Rasband', 'Monson', 'Cook', 'Hinckley', 'Bednar', 'Faust', 'Nelson',
     'Hunter', 'Smith', 'Stevenson', 'Benson', 'McKay', 'McConkie', 'Oaks', 'Holland',
     'Uchtdorf', 'Andersen'], 'ha'] = 'left'
note_data.loc[
    ['Christofferson', 'Cook', 'Oaks', 'Hinckley', 'Eyring', 'Faust', 'Lee',
     'Holland', 'Andersen', 'Soares', 'Stevenson', 'Monson', 'Ballard', 'Kimball'], 'va'] = 'top'
titlestr = 'Jesus and Satan references (per 1000 words)\n by recent apostles and church presidents'
create_fig('Jesus', 'Satan', note_data, titlestr, 'jesus_vs_satan.png')

##############################

note_data['ha'] = 'left'
note_data['va'] = 'bottom'
note_data['r'] = 0
note_data.loc[['Gong', 'Soares', 'Monson', 'Maxwell', 'Benson', 'Smith', 'Ballard'], 'ha'] = 'right'
note_data.loc[['Hinckley', 'McConkie', 'Ballard'], 'ha'] = 'center'
note_data.loc[['Renlund', 'Hunter', 'Ballard', 'Bednar', 'Lee', 'Benson', 'Maxwell', 'Hinckley'], 'va'] = 'top'
note_data.loc[['Benson', 'Eyring'], 'r'] = 20
note_data.loc[['Oaks', 'Christofferson', 'Maxwell'], 'r'] = 10
titlestr = 'Jesus and church president references (per 1000 words)\n by recent apostles and church presidents'
create_fig('Jesus', 'President', note_data, titlestr, 'jesus_vs_pres.png')

##############################

note_data['ha'] = 'left'
note_data['va'] = 'bottom'
note_data['r'] = 0
note_data.loc[note_data['grace']>1.0, 'ha'] = 'right'
note_data.loc[['Christofferson', 'Monson', 'McConkie', 'Hunter', 'Maxwell',
               'Hinckley', 'Grant', 'Andersen', 'McKay', 'Faust', 'Smith'], 'va'] = 'top'
note_data.loc[['Hinckley'], 'ha'] = 'center'
note_data.loc[['Ballard', 'Kimball'], 'r'] = 5
note_data.loc[['Lee'], 'r'] = 10
titlestr = 'grace and works references (per 1000 words)\n by recent apostles and church presidents'
create_fig('grace', 'works', note_data, titlestr, 'grace_vs_works.png')

