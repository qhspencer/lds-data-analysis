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
#pl.style.use('fivethirtyeight')
pl.style.use('bmh')
import matplotlib.dates as mdates
pl.rcParams['figure.max_open_warning'] = 50

search_file = 'search_data.json'
output_dir = '/mnt/d/Quentin/'

print "Loading data"
searches = json.load(open(search_file))

if 1:
    group = 'year'
    daterange = [1971, 2019]
    yaxis_str = 'uses per year'
else:
    group = 'date'
    daterange = [datetime.date(1971, 1, 1),
                 datetime.date(2019, 4, 1)]
    yaxis_str = 'uses per conference'

dfs = []
for file in glob.glob('data/*.json'):
    dfs.append(pandas.read_json(file))

df_all = pandas.concat(dfs).reset_index()

# Create date column
df_all['date'] = pandas.to_datetime(df_all['month'].map(str) + '/' + df_all['year'].map(str))
df_all['year'] = df_all['date'].dt.year

# Clean up strings:
# standardize author names and remove titles
# remove or replace unneeded characters in body
df_all = df_all.replace(
    {'author': clean_author_dict,
     'body': {'\t|\n':'', u'\u2013':'-'}}, regex=True)

df_all = title_cleanup(df_all)
pres = get_current_president(df_all)
df_all = df_all.join(pres, 'date')
#df_all['tail'] = df_all['body'].str[-31:].str.lower()

talks_only = get_only_talks(df_all)
talk_counts = talks_only.groupby('date').count()['year'].to_frame('talks')


# Process references
ref_df = get_scripture_refs(df_all)

sw_counts = get_ref_counts(ref_df, group)
sw_counts.columns = sw_counts.columns.get_level_values(1)
sw_counts.columns.name = 'Standard Work'

ref_freq = ref_df.groupby('ref').count()[group].to_frame('uses')
num_refs = 20
top_refs = ref_freq.sort_values('uses').iloc[-num_refs:][::-1]


fig, ax = pl.subplots(figsize=(12,5))
sw_counts.plot(ax=ax)
ax.set_xlim(daterange)
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
pl.grid(axis='y')
pl.title('Most-cited scriptures')
pl.ylabel('total references')
pl.savefig(output_dir + 'toprefs.png')


fig, ax = pl.subplots(figsize=(12,5))
quotes = df_all['body'].str.count(u'\u201d')
scriptures = df_all['scripture_references'].map(len)
qpc = df_all.assign(quotes=quotes, scriptures=scriptures)[
    [group, 'quotes', 'scriptures']].groupby(group).mean()
qpc.plot(ax=ax)
ax.set_xlim(daterange)
pl.title('quotes per talk')
pl.savefig(output_dir + 'quotes.png')


fig, ax = pl.subplots(figsize=(12,5))
pres_df = talks_only['date'].to_frame('date')
president_list = talks_only['president'].unique().tolist()
dead_pres_list = ['Joseph Smith', 'Brigham Young', 'John Taylor',
                  'Wilford Woodruff', 'Lorenzo Snow',
                  'Joseph F. Smith', 'Heber J. Grant',
                  'George Albert Smith', 'David O. McKay']
for pres in president_list + dead_pres_list:
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
for pres in president_list + dead_pres_list:
    if pres in dead_pres_list:
        s = sum(pres_refs[pres])/float(len(pres_refs.index.unique()))
    else:
        pres_start = min(talks_only[talks_only['president']==pres]['date'])
        pres_end = max(talks_only[talks_only['president']==pres]['date'])+datetime.timedelta(200)
        n_confs = sum(pres_refs.index>pres_end)
        if n_confs:
            s = sum(pres_refs[pres_refs.index>pres_end][pres])/float(n_confs)
        else:
            s = 0
    pres_cites.append([pres,s])
ps = pandas.DataFrame(pres_cites, columns=('pres', 'cites')).set_index('pres')
ps = ps[ps['cites']>0].sort_values('cites', ascending=False)

fig, ax = pl.subplots(figsize=(12,5))
ax.bar(range(len(ps)), ps.values, align='center')
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
all_words = talks_only.body.map(lambda x:len(x.split(' ')))
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



###
recent_apostles = talks_only[(talks_only['author_title'].str.contains('Twelve')) |
                             (talks_only['author_title']=='President of the Church')]['author'].unique()

all_q15 = list(set(recent_apostles.tolist() + list(prior_apostles) +
                   president_list + dead_pres_list))

all_q12 = list(set(recent_apostles.tolist() + list(prior_apostles)) -
               set(president_list + dead_pres_list))

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
        post_ratio = sum(cites_post)/float(n_confs)
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


