import pandas
import datetime
import glob
import re

ndash = u'\u2013'
mdash = u'\u2014'
nbsp = u'\xa0'
rsqm = u'\u2019'

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


clean_author_dict = {
    '^(President|Elder|Bishop|Sister|Brother) ': '',
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
}

def load_data(source='all'):
    dfs = []
    byu_edu_list = glob.glob('data_byu_edu/*.json')
    lds_org_list = glob.glob('data_lds_org/*.json')
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
        print file
        dfs.append(pandas.read_json(file))

    df_all = pandas.concat(dfs).reset_index()
    df_all.body = df_all.body.map(lambda x: ' '.join(x))

    # Create date column
    df_all['date'] = pandas.to_datetime(df_all['month'].map(str) + '/' + df_all['year'].map(str))
    df_all['year'] = df_all['date'].dt.year.map(lambda x: datetime.date(x, 6, 1))
    df_all['decade'] = df_all['date'].dt.year.map(lambda x: datetime.date(int(x/10)*10 + 5, 1, 1))

    # Clean up strings:
    # standardize author names and remove titles
    # remove or replace unneeded characters in body
    df_all = df_all.replace(
        {'author': clean_author_dict,
         'body': {'\t|\n':'', ndash:'-', '  ':' '}}, regex=True)
    df_all = title_cleanup(df_all)
    df_all['word_count'] = df_all.body.str.count(' ') + 1

    # get current president from apostle data
    apostle_data = pandas.read_json('data/apostles.json', orient='records', lines=True,
                                    convert_dates=['dob', 'dod', 'sdate', 'edate', 'sdate_p', 'edate_p'])
    pres_list = apostle_data[~apostle_data.sdate_p.isna()].reset_index()[['name', 'sdate_p']]
    cb = pandas.cut(df_all.date, pres_list.sdate_p.append(pandas.Series(datetime.datetime.today())), labels=False)
    cur_pres = pandas.merge(cb.to_frame('p_idx'), pres_list, left_on='p_idx', right_index=True)['name']
    df_all['president'] = cur_pres

###### still in progress
#    #((apostle_data['name']==rec['author']) & (apostle_data['sdate']<rec['date']+datetime.timedelta(10)))
#    #((apostle_data['name']==rec['author']) & (apostle_data['sdate']<rec['date']+datetime.timedelta(10)))
#
#    dates = df_all['date'].drop_duplicates()
#    print('computing ranks')
#    df_all['rank'] = 100
#    for idx in range(len(df_all)):
#        rec = df_all.loc[idx]
#        dt = rec['date'] + datetime.timedelta(10)
#        q15 = apostle_data[(apostle_data.sdate<dt) &
#                           ((apostle_data.edate>dt) | (apostle_data.edate.isna()))].sort_values('sdate')
#        q15_rank = q15.set_index('name')['sdate'].rank()
#        if rec['author'] in q15_rank.index:
#            df_all[idx, 'rank'] = int(q15_rank[rec['author']])
#
#        from IPython.core.debugger import set_trace
#        set_trace()

    return df_all

prior_apostles = (
    'Thomas B. Marsh',
    'David W. Patten',
    'Brigham Young',
    'Heber C. Kimball',
    'Orson Hyde',
    'William E. McLellin',
    'Parley P. Pratt',
    'Luke Johnson',
    'William Smith',
    'Orson Pratt',
    'John F. Boynton',
    'Lyman E. Johnson',
    'John E. Page',
    'John Taylor',
    'Wilford Woodruff',
    'George A. Smith',
    'Willard Richards',
    'Lyman Wight',
    'Amasa Lyman',
    'Ezra T. Benson',
    'Charles C. Rich',
    'Lorenzo Snow',
    'Erastus Snow',
    'Franklin D. Richards I',
    'George Q. Cannon',
    'Joseph F. Smith',
    'Brigham Young Jr.',
    'Albert Carrington',
    'Moses Thatcher',
    'Francis M. Lyman',
    'John Henry Smith',
    'George Teasdale',
    'Heber J. Grant',
    'John W. Taylor',
    'Marriner W. Merrill',
    'Anthon H. Lund',
    'Abraham H. Cannon',
    'Matthias F. Cowley',
    'Abraham O. Woodruff',
    'Rudger Clawson',
    'Reed Smoot',
    'Hyrum M. Smith',
    'George Albert Smith',
    'Charles W. Penrose',
    'George F. Richards',
    'Orson F. Whitney',
    'David O. McKay',
    'Anthony W. Ivins',
    'Joseph Fielding Smith',
    'James E. Talmage',
    'Stephen L Richards',
    'Richard R. Lyman',
    'Melvin J. Ballard',
    'John A. Widtsoe',
    'Joseph F. Merrill',
    'Charles A. Callis',
    'J. Reuben Clark',
    'Alonzo A. Hinckley',
    'Albert E. Bowen',
    'Sylvester Q. Cannon',
    'Harold B. Lee',
    'Spencer W. Kimball',
    'Ezra Taft Benson',
    'Mark E. Petersen',
    'Matthew Cowley',
    'Henry D. Moyle',
    'Delbert L. Stapley',
    'Marion G. Romney',
    'LeGrand Richards',
    'Adam S. Bennion',
    'Richard L. Evans',
    'George Q. Morris',
    'Hugh B. Brown',
    'Howard W. Hunter',
    'Gordon B. Hinckley',
    'N. Eldon Tanner',
    'Thomas S. Monson',
    'Boyd K. Packer',
    'Marvin J. Ashton',
    'Bruce R. McConkie',
    'L. Tom Perry',
    'David B. Haight',
    'James E. Faust',
    'Neal A. Maxwell',
    'Russell M. Nelson',
    'Dallin H. Oaks',
    'M. Russell Ballard',
    'Joseph B. Wirthlin',
    'Richard G. Scott',
    'Robert D. Hales',
    'Jeffrey R. Holland',
    'Henry B. Eyring')




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

    ref_df['book'] = ref_df['ref'].str.replace(' [0-9]*\:[-0-9, ]*','').str.strip(' ')


    standard_work_dict = {
        'A of F':'PGP', u'JS'+mdash+'H':'PGP', 'Moses':'PGP', 'Abr.':'PGP', u'JS'+mdash+'M':'PGP',
        '1 Ne.':'BoM', '2 Ne.':'BoM', 'Jacob':'BoM', 'Enos':'BoM',
        'Jarom':'BoM', 'Omni':'BoM', 'Mosiah':'BoM', 'Alma':'BoM',
        'Hel.':'BoM', '3 Ne.':'BoM', '4 Ne.':'BoM','Morm.':'BoM',
        'Ether':'BoM', 'Moro.':'BoM', 'W of M':'BoM',
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
        'Matt.':'NT', 'Mark':'NT', 'Luke':'NT', 'John':'NT', 'Acts':'NT',
        'Rom.':'NT', '1 Cor.':'NT', '2 Cor.':'NT', 'Eph.':'NT',
        'Gal.':'NT', 'James':'NT', 'Heb.':'NT', '1 Tim.':'NT',
        '2 Tim.':'NT', '1 Pet.':'NT', '2 Pet.':'NT', '1 Jn.':'NT',
        '2 Jn.':'NT', '3 Jn.':'NT', 'Titus':'NT', '1 Thes.':'NT',
        '2 Thes.':'NT', 'Phil.':'NT', 'Jude':'NT', 'Col.':'NT',
        'Philem.':'NT',
        'Rev.':'NT',
        'JST, Matt.':'NT', 'Matt.footnote a':'NT',
        'JST, Gen.':'OT', 'JST, Mark':'NT'}

    ref_df['sw'] = ref_df['book'].replace(standard_work_dict)
    return ref_df

#ref_df['len'] = ref_df['ref'].str.len()


def get_ref_counts(ref_df, group):
    swlist = ['OT', 'NT', 'BoM', 'D&C', 'PGP']

    sw_refs = ref_df[ref_df['sw'].isin(swlist)]
    return sw_refs.groupby([group, 'sw']).count()['author'].to_frame('count').unstack()


def title_cleanup(df):
    apostle = 'Of the Quorum of the Twelve Apostles'
    asst = 'Assistant to the Quorum of the Twelve Apostles'
    pres = 'President of the Church'
    bish = 'Presiding Bishop'
    bish1 = 'First Counselor in the Presiding Bishopric'
    seventy = 'Of the First Quorum of the Seventy'
    first = 'First Counselor in the First Presidency'
    rspres = 'Relief Society General President'
    df.loc[(df['author']=='Thomas S. Monson') &
           (df['author_title']=='') &
           (df['date']>datetime.date(2012, 1, 1)),
           'author_title'] = pres
    df.loc[(df['author']=='Russell M. Nelson') &
           (df['author_title']=='') &
           (df['date']>datetime.date(2018, 1, 1)),
           'author_title'] = pres
    df.loc[(df['author']=='Gordon B. Hinckley') &
           (df['author_title']=='') &
           (df['date']>datetime.date(2007, 1, 1)),
           'author_title'] = pres
    df.loc[(df['author']=='Gordon B. Hinckley') &
           (df['author_title']=='') &
           (df['date']<datetime.date(1981, 6, 1)),
           'author_title'] = apostle
    df.loc[(df['author']=='Joseph Fielding Smith') &
           (df['author_title']==''),
           'author_title'] = pres
    df.loc[(df['author']=='Harold B. Lee') &
           (df['author_title']=='') &
           (df['date']>datetime.date(1972, 6, 1)),
           'author_title'] = pres
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
           (df['date']>datetime.date(1978, 6, 1)),
           'author_title'] = apostle
    df.loc[(df['author']=='James E. Faust') &
           (df['author_title']=='') &
           (df['date']>datetime.date(1976, 6, 1)),
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
           (df['date']>datetime.date(1985, 6, 1)),
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
