import matplotlib.pyplot as pl
from data_utils import *

apostle_data = load_apostle_data()

def add_president_terms(color='#cfcfcf'):
    presidents = apostle_data[~apostle_data['sdate_p'].isna()]
    pres_terms = presidents[['name', 'sdate_p', 'dod']].set_index('name')
    for pr in ['George Albert Smith', 'Joseph Fielding Smith', 'Spencer W. Kimball',
               'Howard W. Hunter', 'Thomas S. Monson']:
        pl.axvspan(pres_terms.loc[pr, 'sdate_p'], pres_terms.loc[pr, 'dod'], color=color, alpha=1, lw=0.5, ec='k')
