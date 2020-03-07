#!/usr/bin/python
# -*- coding: utf-8

import requests
from lxml import html
import pandas
import datetime

# This URL opens the Wikipedia page listing all of the apostles in edit mode, which
# is useful because the text in the edit window is relatively easy to parse. Another
# useful URL for the history of the Q12 is:
# https://en.wikipedia.org/wiki/Chronology_of_the_Quorum_of_the_Twelve_Apostles_(LDS_Church)
wiki_url = 'https://en.wikipedia.org/w/index.php?title=List_of_members_of_the_Quorum_of_the_Twelve_Apostles_(LDS_Church)&action=edit'
output_file = 'data/apostles.json'

page = requests.get(wiki_url)
tree = html.fromstring(page.content)
wiki_text = tree.xpath("//textarea/text()")
df = pandas.DataFrame(wiki_text[0].split('\n'), columns=('col',))

df = df[df.col.str.startswith(' |')]
df = df.col.str.split('=', 1, expand=True)
df.columns = ('key', 'val')

df = df[~df.val.isna()]
df.key = df.key.str.strip(' |')
df = df[~df.key.isin(('PD_image', 'alt', 'caption'))]
df['name'] = df[df.key=='name']['val'].str.strip()
df['name'] = df.name.fillna(method='ffill')
# Standardize names
df = df.replace({'name': {'Stephen L Richards': 'Stephen L. Richards',
                          'Franklin D. Richards I': 'Franklin D. Richards'}})

df2 = df.set_index('name')
df3 = df2.reset_index()

dob_regex = '(\|[0-9]*\|[0-9]*\|[0-9]*)'
date_fmt = '|%Y|%m|%d'
dobs = df2[df2.key=='birth_date']['val'].str.extract(dob_regex, expand=False)
dob = pandas.to_datetime(dobs, format=date_fmt).to_frame('dob').drop_duplicates()

dods = df2[df2.key=='death_date']['val'].str.extract(dob_regex, expand=False)
dod = pandas.to_datetime(dods, format=date_fmt).to_frame('dod').drop_duplicates()

posidx = df3[df3.key.str.contains('position_or_quorum') &
             df3.val.str.contains('Apostle') &
             ~df3.val.str.contains('Assistant')]
df4 = ('start_date' + posidx.key.str[-1]).to_frame().join(posidx[['name']])

merged = pandas.merge(df3, df4, on=('name', 'key'))
merged['sdate'] = pandas.to_datetime(merged.val.str.extract(dob_regex, expand=False), format=date_fmt)
sdate = merged[['name', 'sdate']].sort_values(['name', 'sdate']).groupby('name').first().sort_values('sdate')

apostle_data = dob.join(dod).join(sdate)
apostle_data['edate'] = apostle_data['dod']

#notes = df2[df2.key=='list_notes'].val.str.replace('[\[|\]]', '').to_frame('notes')
#apostle_data = apostle_data.join(notes).drop_duplicates()

# Add small time offsets for cases where 2 apostles are called the same day to establish correct seniority
dateoffset = datetime.timedelta(0, 1)
apostle_data.loc['Lorenzo Snow', 'sdate'] += dateoffset
apostle_data.loc['Erastus Snow', 'sdate'] += dateoffset*2
apostle_data.loc['Franklin D. Richards', 'sdate'] += dateoffset*3
apostle_data.loc['John Henry Smith', 'sdate'] += dateoffset
apostle_data.loc['Heber J. Grant', 'sdate'] += dateoffset
apostle_data.loc['Anthon H. Lund', 'sdate'] += dateoffset
apostle_data.loc['Abraham H. Cannon', 'sdate'] += dateoffset*2
apostle_data.loc['Abraham O. Woodruff', 'sdate'] += dateoffset
apostle_data.loc['Orson F. Whitney', 'sdate'] += dateoffset
apostle_data.loc['David O. McKay', 'sdate'] += dateoffset*2
apostle_data.loc['Ezra Taft Benson', 'sdate'] += dateoffset
apostle_data.loc['David A. Bednar', 'sdate'] += dateoffset
apostle_data.loc['Gary E. Stevenson', 'sdate'] += dateoffset
apostle_data.loc['Dale G. Renlund', 'sdate'] += dateoffset*2
apostle_data.loc['Ulisses Soares', 'sdate'] += dateoffset

# Remove start dates for those who never were part of the seniority list
remove_list = ['Jedediah M. Grant', 'Joseph Angell Young', 'Daniel H. Wells']
apostle_data.loc[remove_list, 'sdate'] = None
apostle_data.loc[apostle_data['sdate'].isna(), 'edate'] = None

# Set end dates for those who left the quorum by means other than death
# These could probably be extracted from the raw data.
apostle_data.loc['John F. Boynton', 'edate'] = datetime.datetime(1837, 12, 3)
apostle_data.loc['William E. McLellin', 'edate'] = datetime.datetime(1838, 5, 11)
apostle_data.loc['William Smith', 'edate'] = datetime.datetime(1845, 10, 6)
apostle_data.loc['Albert Carrington', 'edate'] = datetime.datetime(1885, 11, 7)
apostle_data.loc['John Willard Young', 'edate'] = datetime.datetime(1891, 10, 3)
apostle_data.loc['Moses Thatcher', 'edate'] = datetime.datetime(1896, 4, 6)
apostle_data.loc['John W. Taylor', 'edate'] = datetime.datetime(1905, 10, 28)
apostle_data.loc['Matthias F. Cowley', 'edate'] = datetime.datetime(1905, 10, 28)
apostle_data.loc['Richard R. Lyman', 'edate'] = datetime.datetime(1943, 11, 12)

# Set alternate start dates to reflect their eventual seniority status
apostle_data.loc['Orson Pratt', 'sdate'] = datetime.datetime(1839, 6, 27)
apostle_data.loc['Orson Hyde', 'sdate'] = datetime.datetime(1839, 6, 27)
apostle_data.loc['Brigham Young Jr.', 'sdate'] = datetime.datetime(1868, 10, 9)

apostle_data = apostle_data.sort_values('sdate', na_position='first')

# Compute start/end dates for presidents of the church
pres_data = apostle_data.reset_index()
pres_data = pres_data[~pres_data['sdate'].isna()]
pres_data.loc[pres_data.name=='Brigham Young', 'sdate_p'] = datetime.datetime(1847, 12, 27)
pres_data.loc[pres_data.name=='Brigham Young', 'edate_p'] = pres_data.loc[pres_data.name=='Brigham Young', 'edate']
cur_idx = pres_data.first_valid_index()

while pres_data.loc[cur_idx, 'edate'] < datetime.datetime.today():
    pres_data.drop(pres_data[pres_data['sdate_p'].isna() &
                             (pres_data['edate']<pres_data['edate_p'].max())].index, inplace=True)
    idx = pres_data[pres_data['sdate_p'].isna()].first_valid_index()
    pres_data.loc[idx, 'sdate_p'] = pres_data.loc[cur_idx, 'edate_p'] + datetime.timedelta(1)
    pres_data.loc[idx, 'edate_p'] = pres_data.loc[idx, 'edate']
    cur_idx = idx

pres_data.drop(pres_data[pres_data['sdate_p'].isna()].index, inplace=True)
pres_data = pres_data[['name', 'sdate_p', 'edate_p']].set_index('name')

apostle_data = apostle_data.join(pres_data)


with open(output_file, 'w') as fp:
    fp.write(apostle_data.reset_index().to_json(
        orient='records', date_format='iso', lines=True))

# load command:
# df=pandas.read_json(output_file, orient='records', lines=True,
#                     convert_dates=['dob', 'dod', 'sdate', 'edate', 'sdate_p', 'edate_p'])
