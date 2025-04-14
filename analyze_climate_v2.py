#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 23 10:58:41 2024

Analyze climate risk longitudinal patterns and dissimilarity between counties

@author: Xingyun Wu

Initial: 5/23/2024
Latest: 5/30/2024
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


"""
inspect
"""

# load data
dt = pd.read_csv('Climate-c2c-IRS/climate/climate_selected_2010to2021.csv')
print(dt.columns)

# availability
dt.info()
print('')
# by year
for i in range(2010, 2022):
    print({'Year = {}, non-missing:'.format(i)})
    print(dt[dt['year'] == i].info())
    print('')

# inspect AL
dt[dt['stfips'] == 2].shape
# inspect HI
dt[dt['stfips'] == 15].shape
# inspect CDC-USDM drought
dt[dt['drought_>=severe'].isnull()] # Alaska 02063, 02066
# inspect CDC tornado
dt[dt['tornado_>=EF2'].isnull()] # Alaska 02261
# inspect CDC-EPA air
set(dt.loc[dt['pm2.5_over35'].isnull(), 'stfips']) # all states
set(dt.loc[dt['pm2.5_over35'].isnull(), 'year']) # all year
for i in range(2010, 2021):
    print(i)
    print(set(dt.loc[(dt['year'] == i) & (dt['pm2.5_over35'].isnull()), 'stfips']))
    print(set(dt.loc[(dt['year'] == i) & (dt['pm2.5_over35'].isnull()), 'ctyfips']))
    print('')
# inspect EPA drought
for i in range(2010, 2020):
    print(i)
    print(set(dt.loc[(dt['year'] == i) & (dt['drought'].isnull()), 'stfips']))
    print(set(dt.loc[(dt['year'] == i) & (dt['drought'].isnull()), 'ctyfips']))



'''
air
'''

t0 = dt.pivot(index = ['stfips', 'stname', 'ctyfips', 'ctyname'], 
              columns = 'year', 
              values = ['pm2.5_epa', 'pm2.5_naqqs', 'o3_naqqs'])
t0.info()
t0.describe().T
t1 = t0.describe().T
t0.columns
dt['pm2.5_naqqs'].describe()
t2 = t0['pm2.5_naqqs'].describe()

# distribution of PM2.5 by year
sns.FacetGrid(data = dt, col = 'year', col_wrap = 3).map(sns.histplot, 'pm2.5_epa')

# pm2.5 annual avg. concentration
dt['pm2.5_rank'] = np.where(
    dt['pm2.5_epa'] < 9, 0, np.where(
    dt['pm2.5_epa'] < 15, 1, np.where(
    dt['pm2.5_epa'].isnull(), np.nan, 2))) 
dt['pm2.5_rank'] = dt['pm2.5_rank'].astype('Int64')
# summarize by year
dt.groupby(['year', 'pm2.5_rank']).size()
# duration of extreme short-exposure by rank
sns.FacetGrid(data = dt, col = 'year', hue = 'pm2.5_rank', col_wrap = 3).map(sns.histplot, 'pm2.5_naqqs')

# pm2.5 exposure
dt.groupby('year').agg(pct90 = ('pm2.5_naqqs', lambda x: x.quantile(0.90)),
                       pct95 = ('pm2.5_naqqs', lambda x: x.quantile(0.95)),
                       pct98 = ('pm2.5_naqqs', lambda x: x.quantile(0.98)))
dt['pm2.5_expsr'] = dt['']


## longitudinal trends
# rank
sns.lineplot(data = dt, x = 'year', y = 'pm2.5_rank', hue = 'ctyfips')
# pm2.5 concentration
sns.lineplot(data = dt, x = 'year', y = 'pm2.5_epa', hue = 'ctyfips')


## plot summary
spm = pd.DataFrame(dt.groupby(['year', 'pm2.5_rank']).size())
spm.rename(columns = {0: 'freq'}, inplace = True)
spm.reset_index(drop = False, inplace = True)
print(spm.columns)
sns.lineplot(data = spm, x = 'year', y = 'freq', hue = 'pm2.5_rank')



"""
classification tree
"""

import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage

print(dt.columns)
X = dt.loc[dt['year'] == 2015, ['hurricane', 'tropical_storm', 'tornado',
                                'drought', 'landslide', 'wildfire']].copy(deep = True)
X.reset_index(drop = True, inplace = True)
plt.hist(X['drought'])
X.loc[X['drought'].isnull(), 'drought'] = np.nanmedian(X['drought'])
X = X.transpose()
X.index


linkage_data = linkage(X, method = 'complete', metric='cosine')
linkage_data.shape
dendrogram(linkage_data)
plt.show()


dt.columns
corr = dt[['prcp_rank', 'hte_rank', 'drought_>=severe', 'tornado_>=EF2', 
           'pm2.5_over35', 'hurricane', 'tropical_storm', 'tornado', 
           'drought', 'landslide', 'wildfire']].corr(method = 'pearson')



"""
D index: D = 1/2 * \sum_{i = 1}^{J}{|a_i / A - b_i / B|}
"""

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


"""
use anxiliary function to construct D
"""

def get_D(df, varlist, trange = [2010, 2021], outname = ''):
    '''
    Input:
        df: data frame with all variables and time range
        varlist: a list of variable names to construct D
        trange: a list with two elements for year range
    
    Output:
        rv: a data frame with i, j, year, D
    '''
    # unique counties
    ctylst = sorted(list(set(df.fips)))
    print('Number of unique counties: {}\n'.format(len(ctylst)))
    
    # unique combinations of counties
    basedf = list(itertools.combinations(ctylst, 2))
    basedf = [[x[0], x[1]] for x in basedf]
    basedf = pd.DataFrame(basedf, columns = ['i_fips', 'j_fips'])
    print('Dimension of base df: {}\n'.format(basedf.shape))

    # construct index
    d = dict()
    for yr in range(trange[0], trange[1] + 1):
        # initiate timer
        start = time.time()
        print(yr)
        tmp = basedf.copy(deep = True)
        # slice climate data
        tdf = df[df['year'] == yr].copy(deep = True)
        
        # merge-in variables for i
        tmp = pd.merge(left = tmp, right = tdf[['fips'] + varlist], 
                        how = 'left', left_on = 'i_fips', right_on = 'fips')
        for var in varlist:
            tmp.rename(columns = {var: 'i_' + var}, inplace = True)
        # merge-in variables for j
        tmp = pd.merge(left = tmp, right = tdf[['fips'] + varlist], 
                        how = 'left', left_on = 'j_fips', right_on = 'fips')
        for var in varlist:
            tmp.rename(columns = {var: 'j_' + var}, inplace = True)
        
        # calculate
        l_abs = []
        # abs
        for k in range(len(varlist)):
            tmp['abs' + str(k)] = abs(tmp['i_' + varlist[k]] - tmp['j_' + varlist[k]])
            l_abs.append('abs' + str(k))
        # sum abs
        tmp['sum'] = tmp[l_abs].sum(axis = 1)
        # divided by 2
        tmp['d_' + outname] = 1/2 * tmp['sum']
       
        # turn fips to integer
        tmp[['i_fips', 'j_fips']] = tmp[['i_fips', 'j_fips']].astype(int)
        tmp['year'] = yr
        # attach to dict
        d[str(yr)] = tmp[['i_fips', 'j_fips', 'year', 'd_' + outname]].copy(deep = True)
        
        # check timer
        stop = time.time()
        print('Time elapsed: {}\n'.format(stop - start))

    # concat df in dict
    print(d.keys())
    rv = pd.concat([v for k, v in d.items()])
    print('Dimension of output: {}\nColumn names: {}'.format(rv.shape, list(rv.columns)))
    
    # output
    return rv


# test on climate
clmt = get_D(dt, ['prcp_prop_abv95', 'hte_prop_abv95', 'drt_prop_abvsev'], 
             [2010, 2021], 'climate')
# clmt.equals(fnl) # equivalent to the df constructed with specific coding, but slower
clmt.to_csv('Climate-c2c-IRS/processed data/climate_d_index.csv', index = False)


## other items
dt = pd.read_csv('data/processed_data/v_all_h.csv')
dt = dt.loc[(dt['fips'] // 1000 != 2) & (dt['fips'] // 1000 != 15), :]
print(len(set(dt.fips))) # 3108
print(list(dt.columns))

# popn age
l_age = ['age_under5', 'age5_9', 'age10_14', 'age15_19', 'age20_24', 'age24_29',
         'age30_34', 'age35_39', 'age40_44', 'age45_49', 'age50_54', 'age55_59',
         'age60_64', 'age65_69', 'age70_74', 'age75_79', 'age80_84', 'age85_above']
dt[l_age].describe()
d_age = get_D(dt, l_age, [2010, 2021], 'age')

# edu
l_edu = ['edu1', 'edu2', 'edu3', 'edu4']
dt[l_edu].describe()
d_edu = get_D(dt, l_edu, [2010, 2021], 'edu')

# HH income
l_inc = ['hhinc_pct1', 'hhinc_pct2', 'hhinc_pct3', 'hhinc_pct4', 'hhinc_pct5',
         'hhinc_pct6', 'hhinc_pct7', 'hhinc_pct8', 'hhinc_pct9' ,'hhinc_pct10',
         'hhinc_pct11', 'hhinc_pct12', 'hhinc_pct13', 'hhinc_pct14',
         'hhinc_pct15']
dt[l_inc].describe()
d_inc = get_D(dt, l_inc, [2010, 2021], 'inc')

# housing crowdedness
l_crd = ['occupant1', 'occupant2', 'occupant3', 'occupant4', 'occupant5']
dt[l_crd].describe()
d_crd = get_D(dt, l_crd, [2010, 2021], 'crwd')
d_crd.shape # 57939336

## output
# merge
d_age.shape[0] == d_edu.shape[0]
popn = d_age.merge(d_edu, how = 'outer', on = ['i_fips', 'j_fips', 'year'])
popn.shape[0] == d_inc.shape[0]
popn = popn.merge(d_inc, how = 'outer', on = ['i_fips', 'j_fips', 'year'])
popn.shape[0] == d_crd.shape[0]
popn = popn.merge(d_crd, how = 'outer', on = ['i_fips', 'j_fips', 'year'])
d_age.shape[0] == popn.shape[0]
popn.columns
# save
popn.to_csv('Climate-c2c-IRS/processed data/pop_d_index.csv', index = False)


# merge with climate
popn.shape[0] == clmt.shape[0] # True
popn = popn.merge(clmt, how = 'outer', on = ['i_fips', 'j_fips', 'year'])


# correlation among the 4 population indices
popn[['d_age', 'd_edu', 'd_inc', 'd_crwd', 'd_climate']].describe().round(2)
popn[['d_age', 'd_edu', 'd_inc', 'd_crwd', 'd_climate']].corr('pearson').round(2)


