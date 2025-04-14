#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  9 16:14:37 2024

@author: Xingyun Wu

Initial: 6/9/2024
Latest: 6/17/2024
"""

import os
import pandas as pd
import numpy as np
import itertools
import time
import seaborn as sns
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


# work directory
os.chdir('/Users/xywu/OneDrive - Johns Hopkins/ra/HPC_climate')
os.chdir('C:/Users/xwu70/OneDrive - Johns Hopkins/ra/HPC_climate')

## load full climate data
# Lingxin's harmonized data: converted into csv in Stata
dt = pd.read_csv('data/processed_data/v_all_h.csv')
print(dt.groupby('year').size())
print(list(dt.columns))
# # alternative: my climate data
# dt = pd.read_csv('data/processed_data/climate_all_2010to2021.csv')

## inspect precipitation
sns.FacetGrid(data = dt, col = 'year', 
              col_wrap = 3).map(sns.histplot, 'prcp_abv95')
# convert to prop
dt['prcp_prop_abv95'] = dt['prcp_abv95'] / 365
set(np.isinf(dt['prcp_prop_abv95']))
sns.FacetGrid(data = dt, col = 'year', 
              col_wrap = 3).map(sns.histplot, 'prcp_prop_abv95')

## inspect heat
sns.FacetGrid(data = dt, col = 'year', 
              col_wrap = 3).map(sns.histplot, 'hte_abv95')
# convert to prop
dt['hte_prop_abv95'] = dt['hte_abv95'] / 365
set(np.isinf(dt['hte_prop_abv95']))
sns.FacetGrid(data = dt, col = 'year', 
              col_wrap = 3).map(sns.histplot, 'hte_prop_abv95')

## inspect drought
sns.FacetGrid(data = dt, col = 'year', 
              col_wrap = 3).map(sns.histplot, 'drought_severe')
dt.loc[dt['year'] == 2021, 'drought_severe'].describe()
# convert to prop
dt['drt_prop_abvsev'] = dt['drought_severe'] / 100


## check for harmonized ctyfips
# load merged county data
mycty = pd.read_csv('data/processed_data/climate_all_2010to2021.csv')
mycty.columns
lcty = sorted(list(set(mycty.ctyfips)))
# check consistency of ctyfips
lcty2 = sorted(list(set(dt.fips)))
[x for x in lcty if x not in lcty2] # [15005]
[x for x in lcty2 if x not in lcty] # none


"""
D index: D = 1/2 * \sum_{i = 1}^{J}{|a_i / A - b_i / B|}
"""

# slice climate data
dt.shape # 37692
dt = dt[['fips', 'year', 'prcp_prop_abv95', 'hte_prop_abv95', 
         'drt_prop_abvsev']].copy(deep = True)
dt = dt.loc[(dt['fips'] // 1000 != 2) & (dt['fips'] // 1000 != 15), :]
dt.shape # 37296
dt.groupby('year').size() # 3129 non-AK/HI counties throughout


# sort climate data
dt.sort_values(by = ['fips', 'year'], axis = 0, 
               ignore_index = True, inplace = True)

# inspect corr
dt.iloc[0, :]
cmt_corr = dt[['prcp_prop_abv95', 'hte_prop_abv95', 'drt_prop_abvsev']].corr('pearson')
print(cmt_corr)

# unique combinations of counties
ctydf = list(itertools.combinations(sorted(list(set(dt.fips))), 2))
ctydf = [[x[0], x[1]] for x in ctydf]
ctydf = pd.DataFrame(ctydf, columns = ['i_fips', 'j_fips'])
ctydf.shape
ctydf.iloc[:5, :]

# construct index
d_cdc = dict()
for yr in range(2010, 2022):
    # initiate timer
    start = time.time()
    print(yr)
    tmp = ctydf.copy(deep = True)
    # slice climate data
    tdf = dt[dt['year'] == yr].copy(deep = True)
    # tdf = tdf.loc[(tdf['stfips'] != 2) & (tdf['stfips'] != 15), :]
    # merge-in climate for i
    tmp = pd.merge(left = tmp, right = tdf[['fips', 'prcp_prop_abv95', 
                                            'hte_prop_abv95', 'drt_prop_abvsev']], 
                    how = 'left', left_on = 'i_fips', right_on = 'fips')
    tmp.rename(columns = {'prcp_prop_abv95': 'i_prcp', 
                          'hte_prop_abv95': 'i_hte',
                          'drt_prop_abvsev': 'i_drt'}, inplace = True)
    # merge-in climate for j
    tmp = pd.merge(left = tmp, right = tdf[['fips', 'prcp_prop_abv95', 
                                            'hte_prop_abv95', 'drt_prop_abvsev']], 
                    how = 'left', left_on = 'j_fips', right_on = 'fips')
    tmp.rename(columns = {'prcp_prop_abv95': 'j_prcp', 
                          'hte_prop_abv95': 'j_hte',
                          'drt_prop_abvsev': 'j_drt'}, inplace = True)
    # calculate
    tmp['d_climate'] = 1/2 * (abs(tmp['i_prcp'] - tmp['j_prcp'])
                              + abs(tmp['i_hte'] - tmp['j_hte']) 
                              + abs(tmp['i_drt'] - tmp['j_drt']))
    # turn fips to integer
    tmp[['i_fips', 'j_fips']] = tmp[['i_fips', 'j_fips']].astype(int)
    tmp['year'] = yr
    # attach to dict
    d_cdc[str(yr)] = tmp[['i_fips', 'j_fips', 'year', 'd_climate']].copy(deep = True)
    # check timer
    stop = time.time()
    print('Time elapsed: {}\n'.format(stop - start))


# concat df in dict
print(d_cdc.keys())
fnl = pd.concat([v for k, v in d_cdc.items()])
print(fnl.columns)

# output
fnl.to_csv('Climate-c2c-IRS/processed data/climate_d_index.csv', index = False)

# distribution
sns.FacetGrid(data = fnl, col = 'year', 
              col_wrap = 3).map(sns.histplot, 'd_climate', binwidth = 0.05)


