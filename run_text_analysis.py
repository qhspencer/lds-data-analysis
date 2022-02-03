#!/usr/bin/python

import pandas
import gc
from data_utils import *
import nltk
import pickle

read_from_disk = True
ngram_table_file = 'ngram_tables.pkl'
time_group = 'time_period'
similarity_threshold = 0.8

print("Loading data")
talk_data = get_only_talks(load_data()).copy()
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
    

def decade_analysis(dataframe, N, min_length=None, min_total=200, time_group='decade'):

    if min_length==None:
        min_length = 6+(N-1)*2 if N>1 else 5

    if N==1:
        print('single word analysis')
        df = dataframe
        col = 'words'
    else:
        print(str(N) + '-gram analysis')
        df = dataframe[[time_group]].join(
            dataframe.words.apply(lambda x: [' '.join(y) for y in
                                             nltk.ngrams(x, N)]).to_frame('Ngrams'))
        col = 'Ngrams'
    vals = df[col].apply(pandas.Series).stack().to_frame('value')
    vals = vals[vals['value'].str.len()>=min_length]
    vals.index = vals.index.get_level_values(0)
    vals = vals.join(dataframe[[time_group]])

    wc = vals.groupby([time_group, 'value']).size().to_frame('count').reset_index()
    wc = wc[(~wc['value'].isin(skip_words)) &
            (~wc['value'].str.contains('president')) &
            (~wc['value'].str.contains('deseret')) &
            (wc['value'].str.len()>2)]

    dec_table = wc.pivot(index='value', columns=time_group, values='count').fillna(0.999)
    dec_table['total'] = dec_table.sum(1)
    dec_table = dec_table[dec_table['total']>=min_total]
    dec_table['max_val'] = dec_table.drop(columns='total').max(1)
    dec_table['min_val'] = dec_table.min(1)
    dec_table['ratio'] = dec_table['max_val']/dec_table['min_val']
    gc.collect()
    return dec_table

###########
print('processing words')

# Time groupings version 1: calculate decade
talk_data['decade'] = talk_data['year'].dt.year.divide(10).astype(int)*10

# Time groupings version 2: divide the time period in 3
min_date = talk_data['date'].min()
max_date = talk_data['date'].max()
threshold1 = min_date + (max_date-min_date)/3
threshold2 = max_date - (max_date-min_date)/3
groups = [talk_data['date']<threshold1,
          (talk_data['date']>=threshold1) & (talk_data['date']<threshold2),
          talk_data['date']>=threshold2]
for gr in groups:
    years = talk_data[gr]['date'].dt.year
    talk_data.loc[gr, 'time_period'] = '{0:d}-{1:d}'.format(years.min(), years.max())

# ensure we're using the same apostrophe characters in all strings
replace_list = (("'s ", rsqm+"s "), ("n't ", "n"+rsqm+"t "),
                ("'ll", rsqm+"ll"), ("'ve", rsqm+"ve"))
for old, new in replace_list:
    talk_data['body'] = talk_data['body'].str.replace(old, new)
talk_data['words'] = talk_data.body.str.lower().str.findall(u'[a-z'+rsqm+']+')

if read_from_disk and os.path.exists(ngram_table_file):
    print('loading ' + ngram_table_file)
    ngram_tables = pickle.load(open(ngram_table_file, 'rb'))
else:
    ngram_tables = []
    for N in range(1, 8):
        ngram_tables.append(decade_analysis(talk_data, N, time_group=time_group))
        gc.collect()

    pickle.dump(ngram_tables, open(ngram_table_file, 'wb'))
    print('wrote ' + ngram_table_file)

all_ngrams = pandas.concat(ngram_tables, axis=0).sort_values('ratio', ascending=False)

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
# Add words that are subsets of longer phrases if they have nearly as many usages
all_ngrams['words'] = all_ngrams.index.str.split(' ').str.len()
for word, row in all_ngrams.iterrows():
    if all_ngrams[(all_ngrams['total']>row['total']*similarity_threshold) &
                  (all_ngrams['words']>row['words'])].index.str.contains(word).sum():
        to_remove.append(word)
to_remove = list(set(all_ngrams.index).intersection(set(to_remove)))
all_ngrams.drop(index=to_remove, inplace=True)

time_cols = sorted(talk_data[time_group].unique())
all_ngrams['peak'] = all_ngrams[time_cols].idxmax(axis=1)
all_ngrams[all_ngrams['ratio']>10].to_pickle('top_ngrams.pkl')
