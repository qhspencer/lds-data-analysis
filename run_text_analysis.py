#!/usr/bin/python

import pandas
import os
import gc
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
parser.add_argument('--norm', dest='norm', type=str, default='conf',
                    choices=['words', 'conf'], help='specifies normalization factor')
args = parser.parse_args()

output_dir = args.output_dir + '/'
print("Loading data")
talks_only = get_only_talks(load_data()).copy()
gc.collect()

short_words = [
    'the', 'of', 'and', 'to', 'in', 'a', 'that', 'i', 'we', 'is',
    'for', 'he', 'yo', 'our', 'his', 'be', 'it', 'as', 'are',
    'with', 'have', 'this', 'was', 'not', 'will', 'they', 'all',
    'my', 'us', 'who', 'by', 'on', 'their', 'from', 'we'+rsqm+'re',
    'it'+rsqm+'s', 'didn'+rsqm+'t', 'don'+rsqm+'t', 'i'+rsqm+'ll',
    'i'+rsqm+'m', 'can'+rsqm+'t', 'isn'+rsqm+'t', 'i'+rsqm+'ve',
    'doesn'+rsqm+'t', 'couldn'+rsqm+'t', 'you'+rsqm+'re',
    'we'+rsqm+'ll', 'you'+rsqm+'ll', 'we'+rsqm+'ve',
    'but', 'your', 'when', 'or', 'one', 'them',
    'him', 'which', 'had', 'can', 'do', 'me', 'has',
    'there', 'what', 'were', 'if', 'would', 'so', 'at',
    'an', 'said', 'those', 'may', 'been', 'know', 'these',
    'her', 'more', 'shall', 'no', 'many', 'unto',
    'come', 'she', 'then', 'how', 'through', 'upon',
    'into', 'ye', 'than', 'also', 'up', 'could']

# Get all names of apostles
apostle_data = load_apostle_data()
apostle_list = apostle_data['name'].str.lower().to_list()
names = [n for n in set(' '.join(apostle_list).split(' ')) if len(n)>2]
names += [s.lower().replace('.', '') for s in apostle_list]

for a in apostle_list:
    s = a.lower().replace('.', '').split(' ')
    names += [' '.join(s[:-1]), ' '.join(s[1:])]

# Words that show up in results that aren't interesting
misc_words = ['twenty', 'thousand', 'simply', 'hundred', 'described', 'area', 'eighty']
skip_words = short_words + names + misc_words
    

def decade_analysis(dataframe, column, min_length=5, min_total=200):
    vals = dataframe[column].apply(pandas.Series).stack().to_frame('value')
    vals = vals[vals['value'].str.len()>=min_length]
    vals.index = vals.index.get_level_values(0)
    vals = vals.join(dataframe[['decade']])

    wc = vals.groupby(['decade', 'value']).size().to_frame('count').reset_index()
    wc = wc[(~wc['value'].isin(skip_words)) &
            (~wc['value'].str.contains('president')) &
            (~wc['value'].str.contains('deseret')) &
            (wc['value'].str.len()>2)]

    dec_table = wc.pivot(index='value', columns='decade', values='count').fillna(0.999)
    dec_table['total'] = dec_table.sum(1)
    dec_table = dec_table[dec_table['total']>=min_total]
    dec_table['max_val'] = dec_table.drop('total', 1).max(1)
    dec_table['min_val'] = dec_table.min(1)
    dec_table['ratio'] = dec_table['max_val']/dec_table['min_val']
    gc.collect()
    return dec_table

###########
import nltk
print('processing words')
talks_only['decade'] = talks_only['year'].dt.year.divide(10).astype(int)*10
replace_list = (("'s ", rsqm+"s "), ("n't ", "n"+rsqm+"t "),
                ("'ll", rsqm+"ll"), ("'ve", rsqm+"ve"))

for old, new in replace_list:
    talks_only['body'] = talks_only['body'].str.replace(old, new)
talks_only['words'] = talks_only.body.str.lower().str.findall(u'[a-z'+rsqm+']+')
talks_only['3grams'] = talks_only.words.apply(lambda x: [' '.join(y) for y in nltk.ngrams(x, 3)])
talks_only['4grams'] = talks_only.words.apply(lambda x: [' '.join(y) for y in nltk.ngrams(x, 4)])

print('single word analysis')
single_word_table = decade_analysis(talks_only, 'words')
print('2-gram analysis')
double_word_table = decade_analysis(talks_only[['decade']].join(
    talks_only.words.apply(lambda x: [' '.join(y) for y in nltk.ngrams(x, 2)]).to_frame('2grams')),
    '2grams', 8)
print('3-gram analysis')
triple_word_table = decade_analysis(talks_only[['decade']].join(
    talks_only.words.apply(lambda x: [' '.join(y) for y in nltk.ngrams(x, 3)]).to_frame('3grams')),
    '3grams', 10)
print('4-gram analysis')
quad_word_table = decade_analysis(talks_only[['decade']].join(
    talks_only.words.apply(lambda x: [' '.join(y) for y in nltk.ngrams(x, 4)]).to_frame('4grams')),
    '4grams', 12)

