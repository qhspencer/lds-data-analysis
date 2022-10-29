import matplotlib.pyplot as pl
from data_utils import *

apostle_data = load_apostle_data()

def add_president_terms(color='#cfcfcf'):
    presidents = apostle_data[~apostle_data['sdate_p'].isna()]
    pres_terms = presidents[['name', 'sdate_p', 'dod']].set_index('name')
    for pr in ['George Albert Smith', 'Joseph Fielding Smith', 'Spencer W. Kimball',
               'Howard W. Hunter', 'Thomas S. Monson']:
        pl.axvspan(pres_terms.loc[pr, 'sdate_p'], pres_terms.loc[pr, 'dod'], color=color, alpha=1, lw=0.5, ec='k')

def add_president_names(yval=0):
    pres = apostle_data[~apostle_data['sdate_p'].isna()].copy()
    # calculate "middle" of term
    pres.loc[94, 'edate_p'] = '2023-01-01'
    pres['term_middle'] = pres['sdate_p'] + (pres['edate_p'] - pres['sdate_p'])/2
    pres_mid_term = pres.set_index('name')['term_middle']

    ax = pl.gca()
    for pr in ['George Albert Smith', 'David O. McKay', 'Spencer W. Kimball', 'Ezra Taft Benson',
               'Gordon B. Hinckley', 'Thomas S. Monson']:
        ax.annotate(pr.split(' ')[-1],
                    (pres_mid_term[pr], yval),
                    size='small', ha='center', va='bottom')