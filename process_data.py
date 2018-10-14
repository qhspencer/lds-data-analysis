#!/usr/bin/python

import pandas
import os
import glob
import json
import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as pl
pl.style.use('fivethirtyeight')
import matplotlib.dates as mdates

searches = json.load(open('search_data.json'))

#dfs = [pandas.read_json(file) for file in os.listdir('data')]
dfs = []
#for file in os.listdir('data'):
#    dfs.append(pandas.read_json(file))
for file in glob.glob('data/*.json'):
    dfs.append(pandas.read_json(file))

df_all = pandas.concat(dfs)
df_all['date'] = pandas.to_datetime(df_all['month'].map(str) + '/' + df_all['year'].map(str))

# strip titles from names
df_all['author'] = df_all['author'].str.replace('^(President|Elder|Bishop) ', '')
df_all['author'] = df_all['author'].str.replace('Wm.', 'William')
df_all = df_all.reset_index()

# remove unneeded characters
df_all['body'] = df_all['body'].str.replace('\t|\n', '')
df_all['tail'] = df_all['body'].str[-31:].str.lower()

for search in [searches[2]]:
#for search in searches:
    results = pandas.DataFrame()

    for s in search['search']:
        matches = df_all['body'].str.lower().str.count(s['include'])
        if 'exclude' in s.keys():
            for excl_str in s['exclude']:
                matches -= df_all['body'].str.lower().str.count(excl_str)

        results[s['label']] = df_all.assign(matches=matches).groupby('date').sum()['matches']

    fig, ax = pl.subplots(figsize=(12,5))
    ax.xaxis.set_minor_locator(mdates.YearLocator(1, month=3))
    ax.xaxis.set_major_locator(mdates.YearLocator(5, month=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    results.plot.bar(ax=ax, width=2)

    #ax.bar(results.index, results, width=120)
    #ax.set_xlim([datetime.date(1971, 1, 1),
    #             datetime.date(2019, 4, 1)])
    pl.ylabel('uses per conference')
    #pl.title('Uses of "{0:s}"'.format(search['include']))
    pl.savefig('/mnt/d/Quentin/' + search['file'] + '.png')


# Process references

# retrieve from body text using regular expression and create new dataframe
refs = df_all['body'].str.findall('\(.*?[0-9].*?\)')
rdf = refs.apply(pandas.Series).stack().to_frame('ref')
ref_df = rdf.reset_index(0).join(df_all, on='level_0')[['date', 'author', 'ref']]

# strip extra characters from references and delete things that don't look like references
ref_df = ref_df[ref_df['ref'].str.contains(':')]
ref_df['ref'] = ref_df['ref'].str.strip('( ).')

# split multiple references
needs_split = ref_df['ref'].str.contains(';')
non_split = ref_df[~needs_split]
to_split = ref_df[needs_split].reset_index()
split_refs = to_split['ref'].str.split(';').apply(pandas.Series).stack().to_frame('ref')
srdf = split_refs.reset_index(0).join(to_split[['date', 'author']], on='level_0')[['date', 'author', 'ref']]

ref_df = pandas.concat([non_split, srdf[srdf['ref'].str.contains(':')]])
ref_df['ref'] = ref_df['ref'].str.strip(' ')

# replace strings with standardized versions
replace = {'Doctrine and Covenants':'D&C',
           u'Joseph Smith\u2014History':u'JS\u2014H',
           'Joseph Smith Translation': 'JST',
           'Articles of Faith':'A of F',
           'Moroni':'Moro.',
           'Helaman':'Hel.',
           'Nephi':'Ne.',
           'Genesis':'Gen.',
           'Exodus':'Ex.',
           'Leviticus':'Lev.',
           'Numbers':'Num.',
           'Deuteronomy':'Deut.',
           'Isaiah':'Isa.',
           'Jeremiah':'Jer.',
           'Daniel':'Dan.',
           'Malachi':'Mal.',
           'Matthew':'Matt.',
           'Romans':'Rom.',
           'Corinthians':'Cor.',
           'Ephesians':'Eph.',
           'Galatians':'Gal.',
           'Timothy':'Tim.',
           'Hebrews':'Heb.',
           'Peter':'Pet.',
           'Revelation':'Rev.',
           '^(S|s)ee ':'',
           'see also ':'',
           'from ':'',
           ' [in the Bible appendix]':''}

for k, v in replace.iteritems():
    ref_df['ref'] = ref_df['ref'].str.replace(k, v)

# get rid of short strings (probably footnotes) and long references
ref_df = ref_df[(ref_df['ref'].str.len()>2) & (ref_df['ref'].str.len()<44)]

ref_df['book'] = ref_df['ref'].str.replace(' [0-9]*\:[-0-9]*','')
ref_df['len'] = ref_df['ref'].str.len()
