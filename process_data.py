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

search_file = 'search_data.json'
output_dir = '/mnt/d/Quentin/'

print "Loading data"
searches = json.load(open(search_file))

if 0:
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

#for search in [searches[2]]:
for search in searches:
    print 'running search:', search['search']
    if 'case sensitive' in search.keys() and search['case sensitive']=='true':
        cs = True
    else:
        cs = False
    results = pandas.DataFrame()

    for s in search['search']:
        if cs:
            matches = df_all['body'].str.count(s['include'])
        else:
            matches = df_all['body'].str.lower().str.count(s['include'])
        if 'exclude' in s.keys():
            for excl_str in s['exclude']:
                if cs:
                    matches -= df_all['body'].str.count(excl_str)
                else:
                    matches -= df_all['body'].str.lower().str.count(excl_str)

        results[s['label']] = df_all.assign(matches=matches).groupby(group).sum()['matches']

    fig, ax = pl.subplots(figsize=(12,5))
    results.plot(ax=ax)
    #ax.bar(results.index, results, width=120)

    #ax.xaxis.set_minor_locator(mdates.YearLocator(1, month=3))
    #ax.xaxis.set_major_locator(mdates.YearLocator(5, month=3))
    #ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    ax.set_xlim(daterange)
    pl.ylabel(yaxis_str)
    #pl.title('Uses of "{0:s}"'.format(search['include']))
    pl.savefig(output_dir + search['file'] + '.png')


# Process references
ref_df = get_refs(df_all)

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
talks_only = get_only_talks(df_all)
pres_df = talks_only['date'].to_frame('date')
president_list = talks_only['president'].unique().tolist()
dead_pres_list = ['Joseph Smith', 'Brigham Young', 'John Taylor',
                  'Wilford Woodruf', 'Lorenzo Snow',
                  'Joseph F. Smith', 'Heber J. Grant',
                  'George Albert Smith', 'David O. McKay']
for pres in president_list + dead_pres_list:
    pres_df[pres] = talks_only['body'].str.count(pres)
    if pres == 'Joseph Smith':
        pres_df[pres] += talks_only['body'].str.count('Prophet Joseph')
    elif 'Smith' not in pres:
        pres_df[pres] += talks_only['body'].str.count('President ' + pres.split(' ')[-1])
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
        pres_end = max(talks_only[talks_only['president']==pres]['date'])
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
all_apostles = talks_only[(talks_only['author_title'].str.contains('Twelve')) |
                          (talks_only['author_title']=='President of the Church')]['author'].unique()

