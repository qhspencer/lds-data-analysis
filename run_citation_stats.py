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
parser.add_argument('--norm', dest='norm', type=str, default='conf',
                    choices=['words', 'conf'], help='specifies normalization factor')
args = parser.parse_args()

# This needs to be set high if a large number of plots are being generated
pl.rcParams['figure.max_open_warning'] = 50
pl.style.use(args.mpl_style)

output_dir = args.output_dir + '/'
print "Loading data"

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


# Process references
ref_df = get_scripture_refs(df_all)

sw_counts = get_ref_counts(ref_df, group)
if args.norm == 'words':
    sw_counts = sw_counts.divide(talks_only.groupby(group).sum()['word_count'], 0)*1e6
    ylabel = 'references per million words'
else:
    ylabel = 'references per conference'
sw_counts.columns = sw_counts.columns.get_level_values(1)
sw_counts.columns.name = 'Standard Work'

ref_freq = ref_df.groupby('ref').count()[group].to_frame('uses')
num_refs = 20
top_refs = ref_freq.sort_values('uses').iloc[-num_refs:][::-1]


#######################################
fig, ax = pl.subplots(figsize=(12,5))
#sw_counts.plot(ax=ax)
sw_counts.rolling(5, min_periods=1, center=True).mean().plot(ax=ax)
ax.set_xlim(daterange)
#ax.xaxis.set_minor_locator(mdates.YearLocator(1, month=4))
#ax.xaxis.set_major_locator(mdates.YearLocator(5, month=4))
#ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
pl.legend(sw_counts.columns, ncol=2, loc='upper left')
pl.title('Scripture citations by standard work')
pl.ylabel(ylabel)
pl.savefig(output_dir + 'refs.png')


#######################################
fig, ax = pl.subplots(figsize=(12,5))
#top_refs.plot.bar(ax=ax)
ax.bar(range(num_refs), top_refs['uses'], align='center')
ax.set_xlim([-0.5, num_refs-0.5])
pl.xticks(range(num_refs), top_refs.index, rotation=45, ha='right')
pl.subplots_adjust(bottom=0.25)
pl.grid(axis='y')
pl.title('Most-cited scriptures')
pl.ylabel('total references')
pl.savefig(output_dir + 'toprefs.png')


#######################################
fig, ax = pl.subplots(figsize=(12,5))
quotes = df_all['body'].str.count(u'\u201d')
scriptures = df_all['scripture_references'].map(len)
qpc = df_all.assign(quotes=quotes, scriptures=scriptures)[
    [group, 'quotes', 'scriptures']].groupby(group).mean()
qpc.plot(ax=ax)
ax.set_xlim(daterange)
pl.title('quotes per talk')
pl.savefig(output_dir + 'quotes.png')


#######################################
fig, ax = pl.subplots(figsize=(12,5))
pres_df = talks_only['date'].to_frame('date')
apostle_data = load_apostle_data()
president_list = ['Joseph Smith'] + \
    apostle_data[~apostle_data['sdate_p'].isna()]['name'].to_list()
for pres in president_list:
    pres_df[pres] = talks_only['body'].str.count(pres)>0
    if pres == 'Joseph Smith':
        pres_df[pres] |= talks_only['body'].str.count('Prophet Joseph')>0
    elif 'Smith' not in pres:
        pres_df[pres] |= talks_only['body'].str.count('President ' + pres.split(' ')[-1])>0
pres_refs = pres_df.groupby('date').sum()
if group == 'year':
    prplot = pres_refs.reset_index().assign(year=pres_refs.reset_index()['date'].dt.year).groupby('year').sum()
else:
    prplot = pres_refs
prplot[president_list].plot(ax=ax)
ax.set_xlim(daterange)
pl.legend(president_list, ncol=3, loc='upper center')
pl.ylabel('references per conference')
pl.title('References to presidents of the church')
pl.savefig(output_dir + 'presidents.png')


pres_cites = []
for pres in president_list:
    if pres in dead_pres_list:
        s = sum(pres_refs[pres])/float(len(pres_refs.index.unique()))
    else:
        pres_start = min(talks_only[talks_only['president']==pres]['date'])
        pres_end = max(talks_only[talks_only['president']==pres]['date']) + datetime.timedelta(200)
        n_confs = sum(pres_refs.index>pres_end)
        if n_confs:
            s = sum(pres_refs[pres_refs.index>pres_end][pres])/float(n_confs)
        else:
            s = 0
    pres_cites.append([pres,s])
ps = pandas.DataFrame(pres_cites, columns=('pres', 'cites')).set_index('pres')
ps = ps[ps['cites']>0].sort_values('cites', ascending=False)

fig, ax = pl.subplots(figsize=(12,5))
ax.bar(range(len(ps)), ps['cites'], align='center')
ax.set_xlim([-0.5, len(ps)-0.5])
pl.xticks(range(len(ps)), ps.index, rotation=45, ha='right')
pl.subplots_adjust(bottom=0.30)
pl.grid(axis='x')
pl.title('Most mentioned prophets after death')
pl.ylabel('average reference per conference')
pl.savefig(output_dir + 'toppres.png')


#################################################
pres_cites_all = []
for pres in president_list[:-1]:
    pres_start = min(talks_only[talks_only['president']==pres]['date'])
    pres_end = max(talks_only[talks_only['president']==pres]['date'])
    confs_during = (pres_refs.index <= pres_end) & (pres_refs.index >= pres_start)
    confs_post = pres_refs.index > pres_end + datetime.timedelta(200)
    nc_post = sum(confs_post)
    pres_cites_all.append(
        [pres,
         sum(pres_refs[confs_during][pres])/float(sum(confs_during)),
         sum(pres_refs[confs_post][pres])/float(nc_post) if nc_post else 0])
ps_all = pandas.DataFrame(
    pres_cites_all,
    columns=('pres', 'cites_during', 'cites_post')).set_index('pres')
#################################################

#####
# Kimball
pres = '(Spencer W. Kimball|President Kimball|Spencer Kimball)'
book = "Miracle of Forgiveness"
kimb_refs = talks_only.date.to_frame('date')
kimb_refs['year'] = talks_only.year
kimb_refs['name references'] = talks_only.body.str.count(pres)>0
talk_refs = talks_only.body.str.contains(book)
ref_refs = talks_only.references.map(lambda x: any(book in y for y in x))
kimb_refs['book references'] = talk_refs | ref_refs
kimb_results = kimb_refs.groupby(group).sum()[['name references', 'book references']]

fig, ax = pl.subplots(figsize=(12,5))
kimb_results.plot(ax=ax)
ax.set_xlim(daterange)
pl.grid(axis='y')
pl.title('Spencer W. Kimball references')
pl.ylabel('number per year')
pl.savefig(output_dir + 'kimball.png')

#####

quote_words = talks_only.body.str.findall(u'(\u201c[^\u201d]*\u201d)').map(lambda x: len(' '.join(x).split(' ')))
all_words = talks_only.word_count
quote_frac = talks_only.assign(quote_frac=quote_words/all_words).groupby(group).mean()['quote_frac']
fig, ax = pl.subplots(figsize=(12,5))
quote_frac.plot(ax=ax)
ax.set_xlim(daterange)
pl.grid(axis='y')
pl.title('Fraction of talks that are quotations')
pl.ylabel('average quoted portion of talk')
pl.savefig(output_dir + 'quotefrac.png')


talk_count = talks_only.groupby(group).count()['index'].to_frame('talks')
words = talks_only['body'].map(lambda x: len(x.split()))
word_count = talks_only.assign(words=words).groupby(group).mean()['words']
total = word_count*talk_count['talks']
fig, ax = pl.subplots(figsize=(12,5))
word_count.plot(ax=ax)
ax.set_xlim(daterange)
pl.grid(axis='y')
pl.title('Average talk length')
pl.ylabel('words')
pl.savefig(output_dir + 'talks_conf.png')


all_q15 = ['Joseph Smith'] + apostle_data['name'].to_list()
all_q12 = list(set(all_q15) - set(president_list))

apo_counts = []
for apo in all_q12:
    all_citations = talks_only.body.str.count(apo)>0
    cite_count = talks_only[all_citations].groupby('date').count()['year']
    if apo in talks_only.author.unique():
        first_talk = min(talks_only[talks_only['author']==apo]['date'])
        last_talk = max(talks_only[talks_only['author']==apo]['date'])
        cites_all = cite_count.index >= first_talk
        cites_post = cite_count.index > last_talk+datetime.timedelta(200)
        all_ratio = sum(cite_count)/float(len(talk_counts[talk_counts.index>=first_talk]))
        n_confs = sum(talk_counts.index>last_talk+datetime.timedelta(200))
        if n_confs:
            post_ratio = sum(cites_post)/float(n_confs)
        else:
            post_ratio = 0
    else:
        all_ratio = sum(cite_count)/float(len(talk_counts))
        post_ratio = all_ratio

    apo_counts.append([apo, all_ratio, post_ratio])

apo_cites = pandas.DataFrame(apo_counts, columns=('name', 'all', 'post')).fillna(0)
all_cites = ps.append(apo_cites[apo_cites.post>0.5][['name','post']].set_index('name')).fillna(0)
all_cites['total']=all_cites.sum(1)
ac_final = all_cites.sort_values('total', ascending=False).drop('total', 1)
ac_final.columns = ('Presidents', 'Apostles')

fig, ax = pl.subplots(figsize=(12,5))
ac_final = ac_final[1:]
ax.bar(range(len(ac_final)), ac_final.Presidents, color='#d62728', align='center')
ax.bar(range(len(ac_final)), ac_final.Apostles, bottom=ac_final.Presidents, align='center')
ax.set_xlim([-0.5, len(ac_final)-0.5])
pl.xticks(range(len(ac_final)), ac_final.index, rotation=45, ha='right')
pl.subplots_adjust(bottom=0.30)
pl.grid(axis='x')
pl.legend(ac_final.columns)
pl.title('Posthumous mentions of past leaders')
pl.ylabel('average references per conference')
pl.savefig(output_dir + 'influencers.png')


####
df_all['refcount'] = df_all.references.str.len()
ref_counts = df_all.groupby(group).mean()['refcount']
fig, ax = pl.subplots(figsize=(12,5))
ref_counts.plot(ax=ax)
ax.set_xlim(daterange)
pl.grid(axis='y')
pl.title('Citations per talk')
pl.ylabel('average citations per talk')
pl.savefig(output_dir + 'citations_per_talk.png')



#####

def get_other_refs(text):
    return [a for a in all_q15 if a in text]

talks_only = talks_only.assign(all_refs=talks_only.body.map(get_other_refs))
refs_tmp = talks_only.all_refs.apply(pandas.Series).stack().to_frame('ref')
all_refs = refs_tmp.reset_index(0).join(talks_only, on='level_0')[['date', 'year', 'author', 'ref']]
ref_counts = all_refs.groupby(['author', 'ref']).count()['date'].to_frame('ref_count')
talk_counts = talks_only.author.value_counts().to_frame('talk_count')
talk_counts.index.name = 'author'
ref_counts = ref_counts.join(talk_counts)
ref_ratio = (ref_counts.ref_count/ref_counts.talk_count).to_frame('ratio').reset_index()
ref_ratio_q15 = ref_ratio[ref_ratio.author.isin(all_q15)]


###########
#import nltk
words = talks_only.body.str.lower().str.findall(u'[a-z\u2019]+').apply(pandas.Series).stack()
words = words.str.replace(u'\u2019s', '').to_frame('words')

skipwords = (
    u'the', u'of', u'and', u'to', u'in', u'a', u'that', u'i', u'we', u'is',
    u'for', u'he', u'you', u'our', u'his', u'be', u'it', u'as', u'are',
    u'with', u'have', u'this', u'was', u'not', u'will', u'they', u'all',
    u'my', u'us', u'who', u'by', u'on', u'their', u'from',
    u'but', u'your', u'when', u'or', u'one', u'them',
    u'him', u'which', u'had', u'can', u'do', u'me', u'has',
    u'there', u'what', u'were', u'if', u'would', u'so', u'at',
    u'an', u'said', u'those', u'may', u'been', u'know', u'these',
    u'her', u'more', u'shall', u'no', u'many', u'unto',
    u'come', u'she', u'then', u'how', u'through', u'upon',
    u'into', u'ye', u'than', u'also', u'up', u'could')

words = words[~words.words.isin(' '.join(all_q15).lower().split(' '))]
words = words[~words.words.isin(skipwords)]
wordyear = words.reset_index(0).join(talks_only, on='level_0')[['year', 'words']]

wordfreq_1970 = wordyear[wordyear.year<1980]['words'].value_counts().to_frame('count')
wordfreq_1980 = wordyear[(wordyear.year>=1980) & (wordyear.year<1990)]['words'].value_counts().to_frame('count')
wordfreq_1990 = wordyear[(wordyear.year>=1990) & (wordyear.year<2000)]['words'].value_counts().to_frame('count')
wordfreq_2000 = wordyear[(wordyear.year>=2000) & (wordyear.year<2010)]['words'].value_counts().to_frame('count')
wordfreq_2010 = wordyear[(wordyear.year>=2010)]['words'].value_counts().to_frame('count')
wordfreq_1970['rank'] = wordfreq_1970.reset_index().index
wordfreq_1980['rank'] = wordfreq_1980.reset_index().index
wordfreq_1990['rank'] = wordfreq_1990.reset_index().index
wordfreq_2000['rank'] = wordfreq_2000.reset_index().index
wordfreq_2010['rank'] = wordfreq_2010.reset_index().index

wordfreq_all = wordfreq_1970.join(wordfreq_1980, how='inner', lsuffix='1970', rsuffix='1980')
wordfreq_all = wordfreq_all.join(wordfreq_1990, how='inner', rsuffix='1990')
wordfreq_all = wordfreq_all.join(wordfreq_2000, how='inner', rsuffix='2000')
wordfreq_all = wordfreq_all.join(wordfreq_2010, how='inner', rsuffix='2010')
wordfreq_all.columns = ['count1970', 'rank1970', 'count1980', 'rank1980',
                        'count1990', 'rank1990', 'count2000', 'rank2000',
                        'count2010', 'rank2010']
wordfreq_ranks = wordfreq_all[['rank1970', 'rank1980', 'rank1990', 'rank2000', 'rank2010']]
wordfreq_counts = wordfreq_all[['count1970', 'count1980', 'count1990', 'count2000', 'count2010']]

wordfreq_delta = wordfreq_ranks.subtract(wordfreq_ranks.mean(1), 0)
wordfreq_delta_norm = (wordfreq_delta.abs().max(1)/wordfreq_delta.reset_index().index).sort_values(ascending=False)
significant_changes = wordfreq_delta_norm[:20]

common_words = wordfreq_counts.mean(1).sort_values()[::-1][:2000].index
wfc_common = wordfreq_counts.loc[common_words]
change_ratio = wfc_common.count1970.divide(wfc_common.count2010, 1).sort_values()


