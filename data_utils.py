import pandas

def get_refs(all_data):
    # Retrieve from body text using regular expression and create new dataframe
    refs = all_data['body'].str.findall('\(.?[0-9]*.*?\)')
    rdf = refs.apply(pandas.Series).stack().to_frame('ref')
    # delete things that don't look like references
    rdf = rdf[rdf['ref'].str.contains('\:')]
    # replace strings with standardized versions
    replace = {
        'Doctrine and Covenants':'D&C',
        u'Joseph Smith\u2014History':u'JS\u2014H',
        'Joseph Smith Translation': 'JST',
        'Articles of Faith':'A of F',
        'Abraham':'Abr.',
        'Mormon':'Morm.',
        'Moroni':'Moro.',
        'Helaman':'Hel.',
        'Nephi':'Ne.',
        'Genesis':'Gen.',
        'Exodus':'Ex.',
        'Leviticus':'Lev.',
        'Numbers':'Num.',
        'Deuteronomy':'Deut.',
        'Joshua':'Josh.',
        'Samuel':'Sam.',
        'Psalms':'Ps.',
        'Proverbs':'Prov.',
        'Ecclesiastes':'Eccl.',
        'Isaiah':'Isa.',
        'Ezekiel':'Ezek.',
        'Jeremiah':'Jer.',
        'Daniel':'Dan.',
        'Malachi':'Mal.',
        'Matthew':'Matt.',
        'Romans':'Rom.',
        'Corinthians':'Cor.',
        'Ephesians':'Eph.',
        'Galatians':'Gal.',
        'Philippians':'Phil.',
        'Philip.':'Phil.',
        'Timothy':'Tim.',
        'Hebrews':'Heb.',
        'Peter':'Pet.',
        '1 John':'1 Jn.',
        'Psalm':'Ps.',
        'Revelation':'Rev.',
        'see also':'',
        'see ':'',
        'See ':'',
        'from ':'',
        'also ':'',
        'in ':'',
        'In ':'',
        '\[in the Bible appendix\]':''}

    rdf = rdf.replace({'ref':replace}, regex=True)
    ref_df = rdf.reset_index(0).join(all_data, on='level_0')[['date', 'author', 'ref']]

    # strip extra characters from references and delete things that don't look like references
    ref_df['ref'] = ref_df['ref'].str.strip('( ).')

    # split multiple references
    needs_split = ref_df['ref'].str.contains(';')
    non_split = ref_df[~needs_split]
    to_split = ref_df[needs_split].reset_index()
    split_refs = to_split['ref'].str.split(';').apply(pandas.Series).stack().to_frame('ref')
    srdf = split_refs.reset_index(0).join(
        to_split[['date', 'author']],
        on='level_0')[['date', 'author', 'ref']]

    ref_df = pandas.concat([non_split, srdf])
    ref_df = ref_df[ref_df['ref'].str.contains('\:')]
    ref_df['ref'] = ref_df['ref'].str.strip(' ')

    # get rid of short strings (probably footnotes) and long references
    ref_df = ref_df[(ref_df['ref'].str.len()>2) & (ref_df['ref'].str.len()<40)]

    ref_df['book'] = ref_df['ref'].str.replace(' [0-9]*\:[-0-9, ]*','').str.strip(' ')


    standard_work_dict = {
        'A of F':'PGP', u'JS\u2014H':'PGP', 'Moses':'PGP', 'Abr.':'PGP', u'JS\u2014M':'PGP',
        '1 Ne.':'BoM', '2 Ne.':'BoM', 'Jacob':'BoM', 'Enos':'BoM',
        'Jarom':'BoM', 'Omni':'BoM', 'Mosiah':'BoM', 'Alma':'BoM',
        'Hel.':'BoM', '3 Ne.':'BoM', '4 Ne.':'BoM','Morm.':'BoM',
        'Ether':'BoM', 'Moro.':'BoM',
        'Gen.':'OT', 'Ex.':'OT', 'Lev.':'OT', 'Num.':'OT', 'Deut.':'OT',
        '1 Sam.':'OT', '2 Sam.':'OT', '1 Chr.':'OT', '2 Chr.':'OT',
        'Eccl.':'OT', '1 Kgs.':'OT', '2 Kgs.':'OT', 'Esth.':'OT',
        'Ruth':'OT', 'Zech.':'OT', 'Joel':'OT', 'Micah':'OT',
        'Ps.':'OT', 'Prov.':'OT', 'Josh.':'OT', 'Judg.':'OT',
        'Mal.':'OT', 'Isa.':'OT', 'Jer.':'OT', 'Dan.':'OT',
        'Amos':'OT', 'Ezek.':'OT', 'Job':'OT', 'Hosea':'OT',
        'Ezra':'OT',
        'Matt.':'NT', 'Mark':'NT', 'Luke':'NT', 'John':'NT', 'Acts':'NT',
        'Rom.':'NT', '1 Cor.':'NT', '2 Cor.':'NT', 'Eph.':'NT',
        'Gal.':'NT', 'James':'NT', 'Heb.':'NT', '1 Tim.':'NT',
        '2 Tim.':'NT', '1 Pet.':'NT', '2 Pet.':'NT', '1 Jn.':'NT',
        '2 Jn.':'NT', '3 Jn.':'NT', 'Titus':'NT', '1 Thes.':'NT',
        '2 Thes.':'NT', 'Phil.':'NT', 'Jude':'NT', 'Col.':'NT',
        'Rev.':'NT'}

    ref_df['sw'] = ref_df['book'].replace(standard_work_dict)
    return ref_df

#ref_df['len'] = ref_df['ref'].str.len()


def get_ref_counts(ref_df):
    swlist = ['OT', 'NT', 'BoM', 'D&C', 'PGP']

    sw_refs = ref_df[ref_df['sw'].isin(swlist)]
    return sw_refs.groupby(['date', 'sw']).count()['author'].to_frame('count').unstack()
        


