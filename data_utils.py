import pandas
import numpy
import datetime
import glob
import re
import os

ndash = u'\u2013'
mdash = u'\u2014'
nbsp = u'\xa0'
rsqm = u'\u2019'
ldqm = u'\u201c'
rdqm = u'\u201d'
shy = u'\xad'

cur_dir = os.path.dirname(__file__)
apostle_data_loc = cur_dir + '/data/apostles.json'
membership_data_loc = cur_dir + '/data/membership_history.csv'

def replace_vals(string):
    replace_table = {nbsp:' ',
                     u'\u00a0':' ',
                     ndash:'-',
                     '\n':' '}

    for old, new in replace_table.items():
        string = string.replace(old, new)
    return string

def clean_strings(strings):
    '''clean an array of strings by stripping white space from the beginning
    and end, and removing empty strings from the array'''
    cleaned = [replace_vals(s.strip()) for s in strings]
    return [s for s in cleaned if s!='']

def clean_join_strings(strings):
    return ' '.join(clean_strings(strings)).strip()

def shorten_name(name_str):
    '''Converts first name to initial in order to shorten the string'''
    no_jr = name_str.replace(', Jr.', '')
    split_name = no_jr.split(' ')
    return ' '.join([split_name[0][0] + '.'] + split_name[1:])


clean_author_dict = {
    '^(President|Elder|Bishop|Sister|Brother|Patriarch) ': '',
    '.* Grant Bangerter': 'W. Grant Bangerter',
    'Wm.': 'William',
    'Elaine Cannon':'Elaine A. Cannon',
    'Charles Didier':'Charles A. Didier',
    'Jose L. Alonso':u'Jos\xe9 L. Alonso',
    'H Goaslind':'H. Goaslind',
    '^H. Goaslind':'Jack H. Goaslind',
    'Goaslind$':'Goaslind, Jr.',
    'Larry Echo Hawk':'Larry J. Echo Hawk',
    'Ardeth Greene Kapp': 'Ardeth G. Kapp',
    'William Rolfe Kerr': 'W. Rolfe Kerr',
    '^O. Samuelson': 'Cecil O. Samuelson',
    'Mary Ellen Smoot': 'Mary Ellen W. Smoot',
    'Ellen W. Smoot': 'Mary Ellen W. Smoot',
    'Michael J. Teh':'Michael John U. Teh',
    'Teddy E. Brewerton':'Ted E. Brewerton',
    'William L. Critchlow, Jr.':'William J. Critchlow, Jr.',
    'M. Russell Ballard, Jr.': 'M. Russell Ballard',
    'Legrand R. Curtis, Jr.': 'Legrand R. Curtis',
    'Franklin Dewey Richards': 'Franklin D. Richards',
    'Stephen L Richards': 'Stephen L. Richards',
    'Albert Theodore Tuttle': 'A. Theodore Tuttle',
    '(?<=[^,]) Jr.':', Jr.'
}

standard_work_dict = {
    # Pearl of Great Price
    'A of F':'PGP', u'JS'+mdash+'H':'PGP', 'Moses':'PGP',
    'Abr.':'PGP', u'JS'+mdash+'M':'PGP',
    # Book of Mormon
    '1 Ne.':'BoM', '2 Ne.':'BoM', 'Jacob':'BoM', 'Enos':'BoM',
    'Jarom':'BoM', 'Omni':'BoM', 'Mosiah':'BoM', 'Alma':'BoM',
    'Hel.':'BoM', '3 Ne.':'BoM', '4 Ne.':'BoM','Morm.':'BoM',
    'Ether':'BoM', 'Moro.':'BoM', 'W of M':'BoM',
    # Old Testament
    'Gen.':'OT', 'Ex.':'OT', 'Lev.':'OT', 'Num.':'OT', 'Deut.':'OT',
    '1 Sam.':'OT', '2 Sam.':'OT', '1 Chr.':'OT', '2 Chr.':'OT',
    'Eccl.':'OT', '1 Kgs.':'OT', '2 Kgs.':'OT', 'Esth.':'OT',
    'Ruth':'OT', 'Zech.':'OT', 'Joel':'OT', 'Micah':'OT',
    'Ps.':'OT', 'Prov.':'OT', 'Josh.':'OT', 'Judg.':'OT',
    'Mal.':'OT', 'Isa.':'OT', 'Jer.':'OT', 'Dan.':'OT',
    'Amos':'OT', 'Ezek.':'OT', 'Job':'OT', 'Hosea':'OT',
    'Ezra':'OT', 'Obad.':'OT', 'Neh.':'OT', 'Esth.':'OT',
    'Jonah':'OT', 'Hab.':'OT', 'Nahum':'OT', 'Zeph.':'OT',
    'Hag.':'OT', 'Lam.':'OT', 'Song':'OT',
    # New Testament
    'Matt.':'NT', 'Mark':'NT', 'Luke':'NT', 'John':'NT', 'Acts':'NT',
    'Rom.':'NT', '1 Cor.':'NT', '2 Cor.':'NT', 'Eph.':'NT',
    'Gal.':'NT', 'James':'NT', 'Heb.':'NT', '1 Tim.':'NT',
    '2 Tim.':'NT', '1 Pet.':'NT', '2 Pet.':'NT', '1 Jn.':'NT',
    '2 Jn.':'NT', '3 Jn.':'NT', 'Titus':'NT', '1 Thes.':'NT',
    '2 Thes.':'NT', 'Phil.':'NT', 'Jude':'NT', 'Col.':'NT',
    'Philem.':'NT',
    'Rev.':'NT',
    # JST stuff
    'JST, Matt.':'NT', 'Matt.footnote a':'NT',
    'JST, Gen.':'OT', 'JST, Mark':'NT'}

def load_apostle_data():
    date_cols = ['dob', 'dod', 'sdate', 'edate', 'sdate_p', 'edate_p']
    df = pandas.read_json(apostle_data_loc, orient='records', lines=True, convert_dates=date_cols)
    return df

def load_membership_data():
    mem = pandas.read_csv(membership_data_loc)
    mem['Membership'] = mem['Membership'].str.replace('(\[.*\]|,)', '', regex=True).astype(int)
    return mem[['Year', 'Membership']]

def load_data(source='file'):
    pkl_file = cur_dir + '/conference_data.pkl'
    if source=='file' and os.path.exists(pkl_file):
        print('loading ' + pkl_file)
        return pandas.read_pickle(pkl_file)
    if source=='file':
        source = 'all'
        save_file = True
    else:
        save_file = False
    dfs = []
    byu_edu_list = glob.glob(cur_dir + '/data_byu_edu/*.json')
    lds_org_list = glob.glob(cur_dir + '/data_lds_org/*.json')
    if source=='byu':
        source_list = byu_edu_list
    elif source=='lds':
        source_list = lds_org_list
    elif source=='all':
        # Use BYU as primary, and fill in missing from lds.org
        source_list = byu_edu_list
        source_list += [f for f in lds_org_list if not
                        any(map(lambda x: re.findall('/[0-9]{4}.[0-9]{2}', f)[0] in x, source_list))]
    for file in source_list:
        print(file)
        dfs.append(pandas.read_json(file))

    df_all = pandas.concat(dfs, sort=False).reset_index()
    # Remove all uppercase strings (used for section headings in some of the
    # BYU files.
    bodies = df_all['body'].map(lambda x: ' '.join([y for y in x if not y.isupper()]))
    df_all['body'] = bodies.str.replace('(?<=\w)\'(?=\w)', rsqm, regex=True) \
                               .str.replace("s' ", "s"+rsqm+" ", regex=False)

    # Create date column
    df_all['date'] = pandas.to_datetime(df_all['month'].map(str) + '/' + df_all['year'].map(str), utc=True)
    df_all['year'] = df_all['date'].dt.year.map(lambda x: pandas.to_datetime(datetime.date(x, 7, 1), utc=True))
    df_all['decade'] = df_all['date'].dt.year.map(lambda x: pandas.to_datetime(datetime.date(int(x/10)*10 + 5, 1, 1), utc=True))

    # Clean up strings:
    # standardize author names and remove titles
    # remove or replace unneeded characters in body
    df_all = df_all.replace(
        {'author': clean_author_dict,
         'body': {'\t|\n':'', ndash:'-', '  ':' '}}, regex=True)
    df_all['word_count'] = df_all.body.str.count(' ') + 1

    # get current president from apostle data
    apostle_data = load_apostle_data()
    pres_list = apostle_data[~apostle_data.sdate_p.isna()].reset_index()[['name', 'sdate_p']]

    date_list = pres_list.sdate_p.append(pandas.Series(pandas.to_datetime(datetime.datetime.today(), utc=True)))
    cb = pandas.cut(df_all.date, date_list, labels=False)
    cur_pres = pandas.merge(cb.to_frame('p_idx'), pres_list, left_on='p_idx', right_index=True)['name']
    df_all['president'] = cur_pres
    df_all = title_cleanup(df_all)

    offset = pandas.to_timedelta(20, unit='days')
    dates = df_all['date'].drop_duplicates()
    print('computing ranks')
    df_all['rank'] = 100

    sdict = {}
    for dt in dates:
        adf = apostle_data[(apostle_data['sdate']<dt+offset) &
                           ((apostle_data['edate']>dt) | (apostle_data['edate'].isna()))]
        sdict.update({dt: {b:a+1 for a, b in adf.reset_index()['name'].iteritems()}})

    for idx in df_all.index:
        rdict = sdict[df_all.loc[idx, 'date']]
        auth = df_all.loc[idx, 'author']
        if auth in rdict.keys():
            df_all.loc[idx, 'rank'] = rdict[auth]

    # Assign speaker gender based on author_title field, and then
    # fill in a few with insufficient data to automatically guess it.
    print('assigning author_gender field')
    df_all = df_all.assign(author_gender='')
    df_all.loc[df_all['author'].isin(apostle_data['name'].values), 'author_gender'] = 'M'

    m_list = ['Seventy', 'Twelve', 'Apostle', 'Bishop', 'First Presidency', 'Patriarch',
              'President of the Church', 'Young Men', 'Sunday School', 'President.*Stake']
    f_list = ['Relief Society', 'Young Women', 'Primary']
    for m_str in m_list:
        df_all.loc[df_all['author_title'].str.contains(m_str), 'author_gender'] = 'M'
    for f_str in f_list:
        df_all.loc[df_all['author_title'].str.contains(f_str), 'author_gender'] = 'F'

    # Everyone in these date ranges without an assigned gender is male
    m_date_ranges = (('19500101', '19720101'), ('19820101', '19860101'), ('19800101', '19810101'))
    for start_date, end_date in m_date_ranges:
        df_all.loc[(df_all['author_gender']=='') &
                   (df_all['date']>=start_date) &
                   (df_all['date']<=end_date), 'author_gender'] = 'M'

    # Assign one more, and the remaining cases were all female
    df_all.loc[df_all['author']=='Enzo Serge Petelo', 'author_gender'] = 'M'
    df_all.loc[(df_all['author_gender']==''), 'author_gender'] = 'F'

    
    if save_file:
        df_all.to_pickle(pkl_file)
        print('wrote ' + pkl_file)
    return df_all

def load_decade_word_counts():
    '''return a dataframe containing word counts of general conference by decade back to 1850'''
    return pandas.read_table(cur_dir + '/data/general_counts.txt').set_index('decade')

def get_scripture_word_counts():
    '''return a dataframe containing word counts for all of the LDS standard works'''
    # I don't remember the sources for this data. I should find it and cite it eventually.
    scripture_word_counts = {'Bible (KJV)': 783137,
                             'Book of Mormon': 267846,
                             'Doctrine and Covenants': 115658,
                             'Pearl of Great Price': 28366}
    return pandas.Series(scripture_word_counts).to_frame('words')

def load_temple_data():
    '''load a set of data on the temples'''
    # Load and preprocess data
    td1 = pandas.read_csv(cur_dir + '/data/temples1.csv', header=[0])
    td2 = pandas.read_csv(cur_dir + '/data/temples2.csv', header=[0,1])
    td1.drop(columns=td1.columns[0], inplace=True)
    td2.drop(columns=td2.columns[0], inplace=True)
    td2.columns = td2.columns.map(lambda x: ' '.join(x) if x[0]!=x[1] else x[0])
    td = td1.merge(td2, on=['#', 'Status', 'Name'])
    td.columns = td.columns.str.replace(shy, '')

    ########## data cleanup ###############
    # clean up column names to be more self-explanatory
    column_changes = {'Site': 'site', 'Floor':'area', 'Ht':'height',
                      'Rm':'ordinance rooms', 'SR':'sealing rooms',
                      'VC':"Visitor's center"}
    td = td.rename(columns=column_changes)

    #   - get numbers out of the status
    #   - remove "edit" string that appears at the end of many of the names
    #   - remove footnotes from various date and related fields
    footnote_regex = '\[[0-9]*\]'
    fn = {footnote_regex:''} # the footnote removal dict
    td = td.replace({'Name': {' *[\n]edit$':''},
                     'Status': {'^[0-9]*':''},
                     'Groundbreaking date': {'(No formal groundbreaking|'+footnote_regex+')':''},
                     'Groundbreaking by': fn,
                     'Dedication date': {'(TBD|'+footnote_regex+')':''},
                     'Dedication by': fn,
                     'Style': fn,
                     'Designer': fn}, regex=True)

    # import dates into datetime format
    dt_cols = ['Announcement date', 'Groundbreaking date', 'Dedication date']
    for col in dt_cols:
        td[col] = pandas.to_datetime(td[col])

    td['area'] = td['area'].str.replace(nbsp, ' ').str.split(' ').str[0].str.replace(',', '').astype(float)
    td['site'] = td['site'].str.replace(nbsp, ' ').str.split(' ').str[0].str.replace(',', '').astype(float)
    td['area'] = td['area'].astype(float)

    # Get rid of NaN values in Style
    td.loc[td['Style'].isna(), 'Style'] = ''
    return td


def get_scripture_refs(all_data):
    # Retrieve from body text using regular expression and create new dataframe
    refs = all_data['scripture_references']
    rdf = refs.apply(pandas.Series).stack().to_frame('ref')
    # delete things that don't look like references
    rdf = rdf[rdf['ref'].str.contains('\:')]
    # replace strings with standardized versions
    replace = {
        'Doctrine and Covenants':'D&C',
        'octrine and Covenants':'D&C',
        'Doctine and Covenants':'D&C',
        u'Joseph Smith'+mdash+'History':u'JS'+mdash+'H',
        u'Joseph Smith'+mdash+'Matthew':u'JS'+mdash+'M',
        'Joseph Smith Translation': 'JST',
        'Articles of Faith':'A of F',
        'Abraham':'Abr.',
        'Words of Mormon':'W of M',
        'Mormon':'Morm.',
        'Moroni':'Moro.',
        'Moro ':'Moro. ',
        'Helaman':'Hel.',
        'Nephi':'Ne.',
        'Genesis':'Gen.',
        'Exodus':'Ex.',
        'Leviticus':'Lev.',
        'Numbers':'Num.',
        'Deuteronomy':'Deut.',
        'Joshua':'Josh.',
        'Judges':'Judg.',
        'Samuel':'Sam.',
        'Chronicles':'Chr.',
        'Kings':'Kgs.',
        'Psalms':'Ps.',
        'Ps ':'Ps.',
        'Proverbs':'Prov.',
        'Ecclesiastes':'Eccl.',
        'Esther':'Esth.',
        'Isaiah':'Isa.',
        'Ezekiel':'Ezek.',
        'Jeremiah':'Jer.',
        'Obadiah':'Obad.',
        'Daniel':'Dan.',
        'Zechariah':'Zech.',
        'Nehemiah':'Neh.',
        'Malachi':'Mal.',
        'Matthew':'Matt.',
        'Matt ':'Matt. ',
        'Romans':'Rom.',
        'Corinthians':'Cor.',
        'Ephesians':'Eph.',
        'Galatians':'Gal.',
        'Colossians':'Col.',
        'Philippians':'Phil.',
        'Thessalonians':'Thes.',
        'Philip\.':'Phil.',
        'Timothy':'Tim.',
        'Hebrews':'Heb.',
        'Peter':'Pet.',
        '1 John':'1 Jn.',
        '2 John':'2 Jn.',
        '3 John':'3 Jn.',
        'Psalm':'Ps.',
        'Revelation':'Rev.',
        'Rev ':'Rev.'}

    rdf = rdf.replace({'ref':replace}, regex=True)
    ref_df = rdf.reset_index(0).join(all_data, on='level_0')[['date', 'year', 'author', 'ref']]

    # strip extra characters from references and delete things that don't look like references
    ref_df['ref'] = ref_df['ref'].str.rstrip('.:;])')

    # split multiple references
#    needs_split = ref_df['ref'].str.contains(';')
#    non_split = ref_df[~needs_split]
#    to_split = ref_df[needs_split].reset_index()
#    split_refs = to_split['ref'].str.split(';').apply(pandas.Series).stack().to_frame('ref')
#    srdf = split_refs.reset_index(0).join(
#        to_split[['date', 'author']],
#        on='level_0')[['date', 'author', 'ref']]
#
#    ref_df = pandas.concat([non_split, srdf])
#    ref_df = ref_df[ref_df['ref'].str.contains('\:')]
#    ref_df['ref'] = ref_df['ref'].str.strip(' ')

    # get rid of short strings (probably footnotes) and long references
#    ref_df = ref_df[(ref_df['ref'].str.len()>2) & (ref_df['ref'].str.len()<40)]

    ref_df['book'] = ref_df['ref'].str.replace(' [0-9]*\:[-0-9, ]*', '', regex=True).str.strip(' ')
    ref_df['sw'] = ref_df['book'].replace(standard_work_dict)
    return ref_df

#ref_df['len'] = ref_df['ref'].str.len()


def get_ref_counts(ref_df, group):
    swlist = ['OT', 'NT', 'BoM', 'D&C', 'PGP']

    sw_refs = ref_df[ref_df['sw'].isin(swlist)]
    return sw_refs.groupby([group, 'sw']).size().to_frame('count').unstack()

dtutc = lambda x: pandas.to_datetime(x, utc=True)

def title_cleanup(df):
    apostle = 'Of the Quorum of the Twelve Apostles'
    asst = 'Assistant to the Quorum of the Twelve Apostles'
    pres = 'President of the Church'
    bish = 'Presiding Bishop'
    bish1 = 'First Counselor in the Presiding Bishopric'
    seventy = 'Of the First Quorum of the Seventy'
    first = 'First Counselor in the First Presidency'
    rspres = 'Relief Society General President'

    df.loc[df['author']==df['president'], 'author_title'] = pres

    df.loc[(df['author']=='Howard W. Hunter') &
           (df['author_title']==''),
           'author_title'] = apostle
    df.loc[(df['author']=='Thomas S. Monson') &
           (df['author_title']==''),
           'author_title'] = apostle

    apostle_list = ('Marvin J. Ashton', 'Bruce R. McConkie',
                    'LeGrand Richards', 'Delbert L. Stapley',
                    'Mark E. Petersen', 'Richard L. Evans',
                    'Hugh B. Brown')
    for apo in apostle_list:
        df.loc[df['author']==apo, 'author_title'] = apostle
    df.loc[(df['author']=='James E. Faust') &
           (df['author_title']=='') &
           (df['date']>dtutc('1978-06-01')),
           'author_title'] = apostle
    df.loc[(df['author']=='James E. Faust') &
           (df['author_title']=='') &
           (df['date']>dtutc('1976-06-01')),
           'author_title'] = seventy
    df.loc[(df['author']=='James E. Faust') &
           (df['author_title']==''),
           'author_title'] = asst

    df.loc[df['author']=='N. Eldon Tanner', 'author_title'] = first
    df.loc[df['author']=='Marion G. Romney', 'author_title'] = apostle
    # Romney 1st pres
    df.loc[(df['author']=='David B. Haight') &
           (df['author_title']==''), 'author_title'] = asst

    seventy_list = ('A. Theodore Tuttle', 'Paul H. Dunn',
                    'Loren C. Dunn', 'Vaughn J. Featherstone',
                    'Hartman Rector, Jr.', 'Franklin D. Richards',
                    'Marion D. Hanks', 'Rex D. Pinegar', 'Robert L. Simpson',
                    'J. Thomas Fyans', 'Carlos E. Asay', 'S. Dilworth Young',
                    'Dean L. Larsen', 'W. Grant Bangerter',
                    'Adney Y. Komatsu', 'Robert L. Backman',
                    'Charles A. Didier', 'Jacob de Jager')
    for sev in seventy_list:
        df.loc[df['author']==sev, 'author_title'] = seventy
    # add pres. bish. for featherstone

    df.loc[df['author']=='Barbara B. Smith', 'author_title'] = rspres
    df.loc[df['author']=='Elaine L. Jack', 'author_title'] = rspres

    df.loc[df['author']=='Victor L. Brown', 'author_title'] = bish
    df.loc[df['author']=='H. Burke Peterson', 'author_title'] = bish1
    df.loc[(df['author']=='H. Burke Peterson') &
           (df['date']>dtutc('1985-06-01')),
           'author_title'] = seventy

    # Many more to go still ...
    return df

def get_only_talks(df):
    exclude_list = (
        'Sustaining of Church Officers',
        'The Church Audit Committee Report',
        'Church Finance Committee Report',
        'Church Auditing Department Report',
        'Church Auditing Committee Report',
        'Church Officers Sustained',
        'Statistical Report',
        'Solemn Assembly'
        )

    return df[df['title'].str.contains(
        '|'.join(exclude_list))==False]

def get_speaker_refs(df, data=None):
    talks_only = df.assign(President=0)
    talks_only['not_president'] = talks_only['rank']>1

    for pres in talks_only['president'].unique():
        pres2 = 'President ' + pres.split(' ')[-1]
        pres_idx = talks_only['president']==pres
        talks_only.loc[pres_idx, 'President'] = talks_only[pres_idx].body.str.count(pres) + \
                                                talks_only[pres_idx].body.str.count(pres2)

    speaker_refs = talks_only[['year', 'month', 'decade', 'author_title', 'author',
                               'word_count', 'President', 'not_president']]
    speaker_refs = speaker_refs.assign(
        Jesus=talks_only.body.str.count('Jesus') + \
        talks_only.body.str.count('Christ') - \
        talks_only.body.str.count('Jesus Christ') + \
        talks_only.body.str.count('Savior') + \
        talks_only.body.str.count('Redeemer') + \
        talks_only.body.str.count('Master') - \
	talks_only.body.str.count('[Cc]hurch of Jesus Christ') - \
        talks_only.body.str.count('Jesus Christ.{0,20} [Aa]men') - \
        talks_only.body.str.count('Jesus is the Christ'))
    speaker_refs = speaker_refs.assign(
        Satan=talks_only.body.str.count('Satan') + \
        talks_only.body.str.count('Lucifer') + \
        talks_only.body.str.count('the [Dd]evil') + \
        talks_only.body.str.count('the [Aa]dversary'))
    speaker_refs = speaker_refs.assign(
        Joseph=talks_only.body.str.count('Prophet Joseph(?! Smith)') + \
        talks_only.body.str.count('Joseph Smith'))

    if data==None:
        data = {'grace': ['grace', 'mercy', 'mercies', 'merciful'],
                'works': ['obey', 'obedient', 'qualify', 'qualified', 'worthy', 'worthiness']}
    for key, val_list in data.items():
        speaker_refs[key] = talks_only.body.str.count('('+'|'.join(val_list)+')')

    col_list = ['Jesus', 'Satan', 'President', 'Joseph'] + list(data.keys())
    speaker_sum = speaker_refs.groupby('author').sum().drop(columns=['not_president'])
    speaker_sum['word_count_np'] = speaker_refs[speaker_refs['not_president']].groupby('author').sum()['word_count']
    speaker_averages = speaker_sum[col_list].divide(speaker_sum['word_count'], 0)*1000
    speaker_averages['President'] = speaker_sum['President']/speaker_sum['word_count_np']*1000

    # include decade
    #speaker_sum2 = speaker_refs.groupby(['author', 'decade']).sum().drop('not_president', 1)
    #speaker_sum2['word_count_np'] = speaker_refs[speaker_refs['not_president']].groupby(
    #    ['author', 'decade']).sum()['word_count']
    #speaker_sum2 = speaker_sum2.reset_index()
    #q15_sum2 = speaker_sum2[speaker_sum2['author'].isin(apostle_list)].set_index(
    #    ['author', 'decade']).drop(['month'], 1)
    #talk_count = talks_only.groupby(['author', 'decade']).size().to_frame('talk_count')
    #q15_averages2 = (q15_sum2[col_list].divide(q15_sum2['word_count'], 0)*1000).join(talk_count)
    #speaker_averages2 = speaker_sum2[col_list].divide(speaker_sum2['word_count'], 0)*1000

    talk_counts = talks_only.groupby('author').count()['index'].to_frame()
    talk_counts.columns = ['count']
    speaker_averages = speaker_averages.join(talk_counts).fillna(0)

    return speaker_averages

def top_users(talk_data, search_string, N=10, before=None, after=None):
    matches = talk_data.body.str.lower().str.count(search_string).to_frame(
        'matches').join(talk_data[['author', 'date']])
    matches = matches[matches['matches']>0]
    if before!=None:
        if type(before)==int:
            before = str(before) + '-12-31'
        matches = matches[matches['date']<=before]
    if after!=None:
        if type(after)==int:
            after = str(after) + '-01-01'
        matches = matches[matches['date']>=after]
    results = matches.groupby('author').sum().sort_values('matches', ascending=False)
    results['fraction'] = results['matches']/results['matches'].sum()
    return results[:N]

def first_users(talk_data, search_string, N=10, before=None, after=None):
    matches = talk_data.body.str.count(search_string).to_frame(
        'matches').join(talk_data[['author', 'date']])
    matches = matches[matches['matches']>0]
    if before!=None:
        if type(before)==int:
            before = str(before) + '-12-31'
        matches = matches[matches['date']<=before]
    if after!=None:
        if type(after)==int:
            after = str(after) + '-01-01'
        matches = matches[matches['date']>=after]
    matches = matches.sort_values('date').set_index('date')
    matches.index = pandas.DatetimeIndex(matches.index).strftime('%B %Y')
    return matches[:N]

def get_context(talk_data, search_string, before=10, after=10):
    matches = talk_data.body.str.count(search_string)
    regex = '.{{{0:d}}}{1:s}.{{{2:d}}}'.format(before, search_string, after)
    refs = talk_data[matches>0].body.str.findall(regex).apply(pandas.Series).stack().to_frame('ref')
    refs.index = refs.index.get_level_values(0)
    return refs.join(talk_data)[['date', 'author', 'ref']]

def top_contexts(talk_data, search_string, before=1, after=1, N=10):
    word = '[A-Za-z]*'
    search_string = (word + ' ')*before + search_string + (' ' + word)*after
    matches = talk_data.body.str.lower().str.count(search_string)
    refs = talk_data[matches>0].body.str.lower().str.findall(search_string).apply(pandas.Series).stack().to_frame('ref')
    counts = refs.groupby('ref').size().sort_values(ascending=False).to_frame('count')
    counts['fraction'] = counts['count']/counts['count'].sum()
    return counts[:N]

def text_search(talk_data, search_data, group='year', norm='words', spacer=' ', quiet=False):
    if type(search_data)==str:
        search = {'search': [{'include': search_data}]}
    else:
        search = search_data

    if not quiet:
        print('running search:', search['search'])
    if 'case sensitive' in search.keys() and search['case sensitive']=='true':
        cs = True
    else:
        cs = False
    results = pandas.DataFrame()

    for s in search['search']:
        if cs:
            matches = talk_data['body'].str.count(s['include'])
        else:
            matches = talk_data['body'].str.lower().str.count(s['include'])
        if 'exclude' in s.keys():
            for excl_str in s['exclude']:
                if cs:
                    matches -= talk_data['body'].str.count(excl_str)
                else:
                    matches -= talk_data['body'].str.lower().str.count(excl_str)

        if 'label' in s.keys():
            l = s['label']
        else:
            l = s['include']
        if 'top_user' in search.keys() and search['top_user'].lower()=='true':
            author_counts = talk_data.join(
                matches.to_frame('matches')).groupby('author')['matches'].sum()
            l += '{0:s}[{1:s} {2:.0f}%]'.format(
                spacer,
                shorten_name(author_counts.idxmax()),
                author_counts.max()/author_counts.sum()*100)
        if norm == 'date':
            results[l] = talk_data.assign(matches=matches).groupby(group).sum()['matches']
        else:
            sums = talk_data.assign(matches=matches).groupby(group).sum()
            results[l] = sums['matches']/sums['word_count']*1e6
        if 'author analysis' in search.keys() and search['author analysis']=='true':
            author_count = talk_data.join(matches.to_frame('matches')).groupby('author').sum()['matches']
            print(author_count.sort_values().to_frame(l)[:-6:-1])

    if 'include sum' in search.keys() and search['include sum']=='true':
        results['all combined'] = results.sum(1)

    return results
