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
print("Loading data")
df_all = load_data()

first_year = df_all.year.min()
last_year = df_all.year.max()
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

talks_only = get_only_talks(df_all)
talk_counts = talks_only.groupby('date').count()['year'].to_frame('talks')


# Process references
ref_df = get_scripture_refs(df_all)

sw_counts = get_ref_counts(ref_df, group)
if ref_df.iloc[-1].date.month<=6:
    sw_counts = sw_counts[:-1]
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
pl.grid(axis='x')
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
pres_df = talks_only[['date', 'year', 'decade']].copy()
apostle_data = load_apostle_data()
president_list = apostle_data[~apostle_data['sdate_p'].isna()]['name'].to_list()
recent_president_list = talks_only['president'].unique()
for pres in president_list:
    idx = talks_only['president']==pres
    lastname = pres.split(' ')[-1]
    if pres=='Joseph Smith':
        altstr = 'Prophet Joseph(?! Smith)'
    elif lastname=='Smith': # "President Smith" is too ambiguous
        altstr = '-----'
    else:
        altstr = 'President ' + lastname
    pres_df[pres] = talks_only['body'].str.count(pres) + \
                    talks_only['body'].str.count(altstr)
    pres_df.loc[idx, 'current'] = talks_only.loc[idx, 'body'].str.count(pres) + \
                                  talks_only.loc[idx, 'body'].str.count(altstr)
pres_refs = pres_df.groupby(group).sum()
pres_refs = pres_refs.divide(talks_only.groupby(group).sum()['word_count'], 0)*1e6
pres_refs[recent_president_list].plot(ax=ax)
ax.set_xlim(daterange)
pl.legend(recent_president_list, ncol=3, loc='upper center')
pl.ylabel('references per million words')
pl.title('References to presidents of the church')
pl.savefig(output_dir + 'presidents.png')

fig, ax = pl.subplots(figsize=(12,5))
pres_refs['current'].plot(ax=ax)
ax.set_xlim(daterange)
pl.ylabel('references per million words')
#pl.ylabel('references per conference')
pl.title('References to the current president of the church')
pl.savefig(output_dir + 'cur_pres.png')

#results[l] = sums['matches']/sums['word_count']*1e6

pres_cites = []
prior_pres_list = set(president_list) - set(recent_president_list)
for pres in president_list:
    pres_data = apostle_data[apostle_data['name']==pres].iloc[0]
    pres_idx = pres_df.date > pres_data['edate_p'] + datetime.timedelta(180)
    pres_avg = 0 if pres_idx.sum()==0 else \
               pres_df[pres_idx][pres].sum()/talks_only[pres_idx]['word_count'].sum()*1e6
    pres_cites.append([pres, pres_avg, pres_data['edate_p']])
ps = pandas.DataFrame(pres_cites, columns=('pres', 'cites', 'death')).set_index('pres')
ps = ps[ps['cites']>0].sort_values('cites', ascending=False)

fig, ax = pl.subplots(figsize=(12,5))
ax.bar(range(len(ps)), ps['cites'], align='center')
ax.set_xlim([-0.5, len(ps)-0.5])
pl.xticks(range(len(ps)), ps.index, rotation=45, ha='right')
pl.subplots_adjust(bottom=0.30)
pl.grid(axis='x')
pl.title('Most mentioned prophets after death')
#pl.ylabel('average reference per conference')
pl.ylabel('average references per million words')
pl.savefig(output_dir + 'toppres.png')


#################################################
pres_cites_all = []
recent_pres_list = talks_only['president'].unique().tolist()
for pres in recent_pres_list[:-1]:
    pres_data = apostle_data[apostle_data['name']==pres].iloc[0]
    confs_during = (pres_refs.index <= pres_data['edate_p']) & (pres_refs.index >= pres_data['sdate_p'])
    confs_post = pres_refs.index > pres_data['edate_p'] + datetime.timedelta(180)
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
#pres = '(Spencer W. Kimball|President Kimball|Spencer Kimball)'
#book = "Miracle of Forgiveness"
#kimb_refs = talks_only.date.to_frame('date')
#kimb_refs['year'] = talks_only.year
#kimb_refs['name references'] = talks_only.body.str.count(pres)>0
#talk_refs = talks_only.body.str.contains(book)
#ref_refs = talks_only.references.map(lambda x: any(book in y for y in x))
#kimb_refs['book references'] = talk_refs | ref_refs
#kimb_results = kimb_refs.groupby(group).sum()[['name references', 'book references']]
#
#fig, ax = pl.subplots(figsize=(12,5))
#kimb_results.plot(ax=ax)
#ax.set_xlim(daterange)
#pl.grid(axis='y')
#pl.title('Spencer W. Kimball references')
#pl.ylabel('number per year')
#pl.savefig(output_dir + 'kimball.png')

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


all_q15 = apostle_data['name'].to_list()
all_q12 = list(set(all_q15) - set(president_list))

apo_counts = []
for apo in all_q12:
    citations = talks_only.body.str.count(apo)
    apo_data = apostle_data[apostle_data['name']==apo].iloc[0]
    all_idx = talks_only.date > apo_data['sdate']
    post_idx = talks_only.date > apo_data['edate'] + datetime.timedelta(180)
    all_ratio = 0 if all_idx.sum()==0 else \
                citations[all_idx].sum()/talks_only[all_idx]['word_count'].sum()*1e6
    post_ratio = 0 if post_idx.sum()==0 else \
                 citations[post_idx].sum()/talks_only[post_idx]['word_count'].sum()*1e6
    apo_counts.append([apo, all_ratio, post_ratio, apo_data['edate']])

apo_cites = pandas.DataFrame(apo_counts, columns=('name', 'all', 'post', 'death')).fillna(0)
append_rows = apo_cites[apo_cites.post>10].set_index('name')[['post', 'death']]
ps.columns = ('Presidents', 'death')
append_rows.columns = ('Apostles', 'death')
all_cites = ps.append(append_rows, sort=False).fillna(0)
all_cites['total'] = all_cites.sum(1)
ac_final = all_cites.sort_values('total', ascending=False).drop(['total', 'death'], 1)

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
pl.ylabel('references per million words')
pl.savefig(output_dir + 'influencers.png')

ac_chron = all_cites.sort_values('death').drop(['total', 'death'], 1)
ac_chron = ac_chron[1:]
fig, ax = pl.subplots(figsize=(12,5))
ax.bar(range(len(ac_chron)), ac_chron.Presidents, color='#d62728', align='center')
ax.bar(range(len(ac_chron)), ac_chron.Apostles, bottom=ac_chron.Presidents, align='center')
ax.set_xlim([-0.5, len(ac_chron)-0.5])
pl.xticks(range(len(ac_chron)), ac_chron.index, rotation=45, ha='right')
pl.subplots_adjust(bottom=0.30)
pl.grid(axis='x')
pl.legend(ac_chron.columns)
pl.title('Posthumous mentions of past leaders')
pl.ylabel('references per million words')
pl.savefig(output_dir + 'influencers_chron.png')


####
#df_all['refcount'] = df_all.references.str.len()
#ref_counts = df_all.groupby(group).mean()['refcount']
#fig, ax = pl.subplots(figsize=(12,5))
#ref_counts.plot(ax=ax)
#ax.set_xlim(daterange)
#pl.grid(axis='y')
#pl.title('Citations per talk')
#pl.ylabel('average citations per talk')
#pl.savefig(output_dir + 'citations_per_talk.png')



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


