#!/usr/bin/python

import pandas
import os
import gc
import glob
import json
import datetime
import argparse
from data_utils import *
import nltk
import pickle

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
# There is not yet sufficient data to measure the 2020 decade, so remove it:
talks_only = talks_only[talks_only['date']<='2020-01-01']
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
    'into', 'ye', 'than', 'also', 'up', 'could', 'see']

# Get all names of apostles
apostle_data = load_apostle_data()
apostle_list = apostle_data['name'].str.lower().to_list()
names = [n for n in set(' '.join(apostle_list).split(' ')) if len(n)>2]
names += [s.lower().replace('.', '') for s in apostle_list]

for a in apostle_list:
    s = a.lower().replace('.', '').split(' ')
    names += [' '.join(s[:-1]), ' '.join(s[1:])]

# Words that show up in results that aren't interesting
misc_words = ['twenty', 'thousand', 'simply', 'hundred', 'described', 'area', 'eighty', 'italics']
skip_words = short_words + names + misc_words
    

def decade_analysis(dataframe, N, min_length=None, min_total=200):

    if min_length==None:
        min_length = 6+(N-1)*2 if N>1 else 5

    if N==1:
        print('single word analysis')
        df = dataframe
        col = 'words'
    else:
        print(str(N) + '-gram analysis')
        df = dataframe[['decade']].join(
            dataframe.words.apply(lambda x: [' '.join(y) for y in
                                             nltk.ngrams(x, N)]).to_frame('Ngrams'))
        col = 'Ngrams'
    vals = df[col].apply(pandas.Series).stack().to_frame('value')
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
print('processing words')
talks_only['decade'] = talks_only['year'].dt.year.divide(10).astype(int)*10
replace_list = (("'s ", rsqm+"s "), ("n't ", "n"+rsqm+"t "),
                ("'ll", rsqm+"ll"), ("'ve", rsqm+"ve"))

for old, new in replace_list:
    talks_only['body'] = talks_only['body'].str.replace(old, new)
talks_only['words'] = talks_only.body.str.lower().str.findall(u'[a-z'+rsqm+']+')

read_from_disk = True
if not read_from_disk:
    ngram_tables = []
    for N in range(1, 8):
        ngram_tables.append(decade_analysis(talks_only, N))
        gc.collect()

    pickle.dump(ngram_tables, open('ngram_tables.pkl', 'wb'))
    print('wrote ngram_tables.pkl')
else:
    ngram_tables = pickle.load(open('ngram_tables.pkl', 'rb'))

all_ngrams = pandas.concat(ngram_tables, 0).sort_values('ratio', ascending=False)

def get_subsets(string):
    ss = string.split(' ')
    return [val for sublist in [[' '.join(y) for y in nltk.ngrams(ss, n)]
                                for n in range(2,len(ss))] for val in sublist]

# Results that are either redundant or uninteresting
subset_phrases = [
    'in the sacred name of jesus christ',
    'the atonement of jesus christ',
    'family home evening',
    'i should like to',
    'testify in the',
]
to_remove = [
    # references
    'italics added',
    'emphasis added',
    'hymns no',
    'in conference report',
    'bookcraft',
    'liahona',
    # uninteresting
    'allows',
    'testify in the',
    'brethren and sisters i',
    'my brethren and sisters',
    'invite you',
    'the challenges',
    'loving heavenly',
    'commitment to',
    'the constitution',
    'priesthood holder'
]
startswith_words = ['see', 'ensign', 'testify', 'of the']
endswith_words = ['amen', 'of', 'to', 'around', 'the']
for w in startswith_words:
    to_remove.extend(all_ngrams[all_ngrams.index.str.startswith(w + ' ')].index.to_list())
for w in endswith_words:
    to_remove.extend(all_ngrams[all_ngrams.index.str.endswith(' ' + w)].index.to_list())
for ph in subset_phrases:
    to_remove.extend(get_subsets(ph))

all_ngrams.drop(all_ngrams[all_ngrams.index.isin(to_remove)].index, inplace=True)
all_ngrams['peak'] = all_ngrams[[x for x in all_ngrams.columns if type(x)==int]].idxmax(axis=1)
all_ngrams[all_ngrams['ratio']>20].to_pickle('top_ngrams.pkl')
