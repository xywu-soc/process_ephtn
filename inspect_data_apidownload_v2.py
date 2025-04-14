# -*- coding: utf-8 -*-
"""
Created on Mon Apr 29 15:22:09 2024

Process manually ==> API downloaded data from CDC EPHTN
    V0-1: Manual download because API doesn't work
        V0: for 2015 initial inspect only
        V1: process data for 2011-2020, manually downloaded for [2011, 2020]
    V2: API fixed, and the time frame extended to [2000, 2021] & select 

@author: Xingyun Wu, Johns Hopkins University
    xywu@jhu.edu
    
Initial: 5/30/2024
Latest: 6/12/2024
"""

import os
import re
import pandas as pd
import numpy as np
import random
import seaborn as sns

# work directory
os.chdir('/Users/xywu/OneDrive - Johns Hopkins/ra/HPC_climate/data/ephtn')
os.chdir('C:/Users/xwu70/OneDrive - Johns Hopkins/ra/HPC_climate/data/ephtn')


"""
drought 2000-2020 ==> 2010-2020
"""

os.listdir('drought')
os.listdir('drought/raw')

'''
process raw data
'''

## load data objects
dt = dict()
fld = os.listdir('drought/raw')
print(fld)
for item in [x for x in fld if 'csv' in x]:
    tdf = pd.read_csv('drought/raw/' + item)
    item = re.findall('^[a-z]+_[a-z]+_c[a-z]+', item)[0]
    dt[item] = tdf
# check objects
print(dt.keys())
print(tdf.columns)
del [tdf, item]


## reshape to wide
# inspect example object
print(list(dt['spei_numweek_cat'].columns))
dt['spei_numweek_cat'].iloc[0, :]
dt['spei_pctweek_cat'].iloc[0, :]
# implement
for k, v in dt.items():
    print(k)
    v.rename(columns = {'parentGeoId': 'stfips', 'parentGeo': 'stname', 
                        'parentGeoAbbreviation': 'stabbr',
                        'geoId': 'ctyfips', 'geo': 'ctyname',
                        'temporalId': 'year', 'dataValue': 'value', 
                        'Categorical Drought Severity': 'ctgy',
                        'Cumulative Drought Severity': 'ctgy'}, 
             inplace = True)
    # proceed with selected columns
    v = v[['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year', 'value', 'ctgy']]
    # reshape
    v = v.pivot(index = ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year'],
                columns = 'ctgy', values = 'value')
    v.rename(columns = {'Exceptional drought': 'cat4_exceptional',
                        'Extreme drought': 'cat3_extreme',
                        'Moderate drought': 'cat1_moderate',
                        'Severe drought': 'cat2_severe',
                        'Extreme drought or greater': 'cum3_extreme',
                        'Moderate drought or greater': 'cum1_moderate',
                        'Severe drought or greater': 'cum2_severe'}, 
             inplace = True)
    # select columns
    if 'cat1_moderate' in v.columns:
        v = v[['cat1_moderate', 'cat2_severe', 'cat3_extreme', 
               'cat4_exceptional']]
    else:
        v = v[['cum1_moderate', 'cum2_severe', 'cum3_extreme']]
    v.reset_index(drop = False, inplace = True)
    dt[k] = v
# remove temp parameters
del [k, v]


## merge measures from the same source
print(sorted(dt.keys()))
# spei: %
spei_pct = dt['spei_pctweek_cat'
              ].merge(dt['spei_pctweek_cum'], how = 'left',
                      on = ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year'])
for col in spei_pct.columns:
    if 'cat' in col or 'cum' in col:
        spei_pct.rename(columns = {col: 'spei_pct_' + col}, inplace = True)
# spei: num week
spei_num = dt['spei_numweek_cat'
              ].merge(dt['spei_numweek_cum'], how = 'left',
                      on = ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year'])
for col in spei_num.columns:
    if 'cat' in col or 'cum' in col:
        spei_num.rename(columns = {col: 'spei_num_' + col}, inplace = True)
# spei: max consecutive week
spei_max = dt['spei_nummax_cat'
              ].merge(dt['spei_nummax_cum'], how = 'left',
                      on = ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year'])
for col in spei_max.columns:
    if 'cat' in col or 'cum' in col:
        spei_max.rename(columns = {col: 'spei_max_' + col}, inplace = True)

# usdm: % week
usdm_pct = dt['usdm_pctweek_cat'
              ].merge(dt['usdm_pctweek_cum'], how = 'left',
                      on = ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year'])
for col in usdm_pct.columns:
    if 'cat' in col or 'cum' in col:
        usdm_pct.rename(columns = {col: 'usdm_pct_' + col}, inplace = True)
# usdm: num week
usdm_num = dt['usdm_numweek_cat'
              ].merge(dt['usdm_numweek_cum'], how = 'left',
                      on = ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year'])
for col in usdm_num.columns:
    if 'cat' in col or 'cum' in col:
        usdm_num.rename(columns = {col: 'usdm_num_' + col}, inplace = True)
# usdm: max num consecutive week
usdm_max = dt['usdm_nummax_cat'
              ].merge(dt['usdm_nummax_cum'], how = 'left',
                      on = ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year'])
for col in usdm_max.columns:
    if 'cat' in col or 'cum' in col:
        usdm_max.rename(columns = {col: 'usdm_max_' + col}, inplace = True)


## merge measures from diff sources
# spei
spei = spei_pct.merge(spei_num, how = 'outer', 
                      on = ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year'])
spei = spei.merge(spei_max, how = 'outer', 
                  on = ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year'])
print(spei.shape)
print(set(spei.stfips))
# usdm
usdm = usdm_pct.merge(usdm_num, how = 'outer',
                      on = ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year'])
usdm = usdm.merge(usdm_max, how = 'outer',
                  on = ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year'])
print(usdm.shape)
print(set(usdm.stfips))
usdm = usdm.loc[(usdm['stfips'] <= 56) , :] # (usdm['stfips'] != 2) & & (usdm['stfips'] != 15)
print(usdm.shape)
usdm.reset_index(drop = True, inplace = True)
# two sources together
drt = spei.merge(usdm, how = 'outer', on = ['stfips', 'stname', 'stabbr', 
                                            'ctyfips', 'ctyname', 'year'])
print(drt.columns)
print(drt.shape)
# select on year: 2010-2021
print(sorted(list(set(drt.year))))
drt = drt.loc[(drt['year'] >= 2010) & (drt['year'] <= 2021), :]
# output
drt.to_csv('drought/spei_usdm_2010to2021.csv', index = False)
del [spei_max, spei_num, spei_pct, usdm_max, usdm_num, usdm_pct, col]


'''
summarize trend
'''

# processed data
drt = pd.read_csv('drought/spei_usdm_2010to2021.csv')
print(drt.columns)

## summary table
# overall distribution
sdrt = drt[['usdm_pct_cat1_moderate', 'usdm_pct_cat2_severe', 
            'usdm_pct_cat3_extreme', 'usdm_pct_cat4_exceptional', 
            'usdm_pct_cum1_moderate', 'usdm_pct_cum2_severe', 
            'usdm_pct_cum3_extreme']].describe().map(lambda x: f"{x:0.1f}")
# by-year distribution
sdrt = drt.iloc[:, 4:].groupby('year').describe().map(lambda x: f"{x:0.1f}")
sdrt = sdrt.T
sdrt.to_csv('drought/spei_usdm_2011to2020_summary.csv', index = True)


## histogram: univariate dist
# categorical
sns.FacetGrid(data = drt, col = 'year', 
              col_wrap = 3).map(sns.histplot, 'usdm_pct_cat1_moderate')
sns.FacetGrid(data = drt, col = 'year', 
              col_wrap = 3).map(sns.histplot, 'usdm_pct_cat2_severe')
sns.FacetGrid(data = drt, col = 'year', 
              col_wrap = 3).map(sns.histplot, 'usdm_pct_cat3_extreme')
sns.FacetGrid(data = drt, col = 'year', 
              col_wrap = 3).map(sns.histplot, 'usdm_pct_cat4_exceptional')
# cumulative
sns.FacetGrid(data = drt, col = 'year', 
              col_wrap = 3).map(sns.histplot, 'usdm_pct_cum1_moderate', binwidth = 5)
sns.FacetGrid(data = drt, col = 'year', 
              col_wrap = 3).map(sns.histplot, 'usdm_pct_cum2_severe', binwidth = 5)
sns.FacetGrid(data = drt, col = 'year', 
              col_wrap = 3).map(sns.histplot, 'usdm_pct_cum3_extreme', binwidth = 5)


## lineplot: trend
sns.lineplot(data = drt, x = 'year', y = 'usdm_pct_cum1_moderate', estimator = 'mean')
sns.lineplot(data = drt, x = 'year', y = 'usdm_pct_cum1_moderate', 
             estimator = 'median', ci = None)
sns.lineplot(data = drt, x = 'year', y = 'usdm_pct_cum2_severe')
sns.lineplot(data = drt, x = 'year', y = 'usdm_pct_cum2_severe', 
             estimator = 'median', ci = None)
sns.lineplot(data = drt, x = 'year', y = 'usdm_pct_cum3_extreme')
sns.lineplot(data = drt, x = 'year', y = 'usdm_pct_cum3_extreme', 
             estimator = 'median', ci = None)


# # drought rank
# for i in range(drt.shape[0]):
#     tmax = drt.loc[i, ['usdm_cat1_moderate', 'usdm_cat2_severe', 
#                        'usdm_cat3_extreme', 'usdm_cat4_exceptional']].max()
#     if tmax > 0:
#          tcol = np.where(drt.loc[i, ['usdm_cat1_moderate', 'usdm_cat2_severe',
#                                      'usdm_cat3_extreme', 
#                                      'usdm_cat4_exceptional']] == tmax)
#          tcol = np.max(tcol)
#          drt.loc[i, 'usdm_rank'] = tcol + 1
#     else:
#          drt.loc[i, 'usdm_rank'] = 0
# del [i, tcol, tmax]
# set(drt['usdm_rank'])
# drt.groupby('usdm_rank').size()



"""
tornado 2010-2021
"""

os.listdir('tornado/raw')
fld = os.listdir('tornado/raw')
print(fld)

## load data
dt = dict()
for item in ['tornado/raw/' + x for x in fld if '.csv' in x]:
    print(item)
    tdf = pd.read_csv(item)
    tdf.rename(columns = {'parentGeoId': 'stfips', 'parentGeo': 'stname', 
                          'parentGeoAbbreviation': 'stabbr',
                          'geoId': 'ctyfips', 'geo': 'ctyname',
                          'temporalId': 'year', 'dataValue': 'value', 
                          'Individual Tornado Intensity Categories (EF-scale)': 'ctgy',
                          'Groups of Tornado Intensity Categories (EF-scale)': 'ctgy'}, 
               inplace = True)
    tdf = tdf[['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year', 
              'value', 'ctgy']]
    tdf = tdf.pivot(index = ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year'],
                    columns = 'ctgy', values = 'value')
    tdf.rename(columns = {'>=EF1 (EF1-EF5)': '>=EF1',
                          '>=EF2 (EF2-EF5)': '>=EF2',
                          '>=EF3 (EF3-EF5)': '>=EF3',
                          '>=EF4 (EF4-EF5)': '>=EF4',
                          'All Tornadoes (EF0-EF5)': 'all_tornado'},
               inplace = True)
    item = re.findall('numtnd_c[a-z]+', item)[0]
    dt[item] = tdf
    print(tdf.columns)
# remove temp parameters
del [fld, item, tdf]

# select contiguous states
print(dt.keys())
dt['numtnd_cat'].shape
dt['numtnd_cat'].columns
dt['numtnd_cum'].shape
dt['numtnd_cum'].columns

# merge
trd = dt['numtnd_cat'].merge(dt['numtnd_cum'], how = 'outer', 
                             left_index = True, right_index = True)
trd.reset_index(drop = False, inplace = True)
print(trd.shape)
# slicing for state
print(sorted(list(set(trd.stfips))))
print(trd.shape)
trd = trd.loc[(trd['stfips'] <= 56), :] # & (trd['stfips'] != 2) & (trd['stfips'] != 15)
print(trd.shape)
# slicing for year
print(sorted(list(set(trd.year))))
trd = trd.loc[(trd['year'] >= 2010) & (trd['year'] <= 2021), :]
print(trd.shape)
# output
trd.reset_index(drop = True, inplace = True)
trd.to_csv('tornado/tornado_2010to2021.csv', index = False)


'''
summary
'''

# check nan
print(trd.columns)
trd['EF0'].isnull().sum()
trd.info()


# table
print(trd.columns)
strd = trd.describe().map(lambda x: f"{x:0.1f}").T
# by-year distribution
strd = trd.iloc[:, 4:].groupby('year').describe().map(lambda x: f"{x:0.1f}")
strd = strd.T
strd.to_csv('tornado/tornado_2011to2020_summary.csv', index = True)


## viz longitudinal trends
# categorical
sns.FacetGrid(data = trd, col = 'year', col_wrap = 3
              ).map(sns.histplot, 'EF0', binwidth = 1)
sns.FacetGrid(data = trd, col = 'year', col_wrap = 3
              ).map(sns.histplot, 'EF1', binwidth = 1)
sns.FacetGrid(data = trd, col = 'year', col_wrap = 3
              ).map(sns.histplot, 'EF2', binwidth = 1)
sns.FacetGrid(data = trd, col = 'year', col_wrap = 3
              ).map(sns.histplot, 'EF3', binwidth = 1)
sns.FacetGrid(data = trd, col = 'year', col_wrap = 3
              ).map(sns.histplot, 'EF4')
sns.FacetGrid(data = trd, col = 'year', col_wrap = 3
              ).map(sns.histplot, 'EF5')
# cumulative
sns.FacetGrid(data = trd, col = 'year', col_wrap = 3
              ).map(sns.histplot, '>=EF1', binwidth = 1)
sns.FacetGrid(data = trd, col = 'year', col_wrap = 3
              ).map(sns.histplot, '>=EF2', binwidth = 1)
sns.FacetGrid(data = trd, col = 'year', col_wrap = 3
              ).map(sns.histplot, '>=EF3', binwidth = 1)
sns.FacetGrid(data = trd, col = 'year', col_wrap = 3
              ).map(sns.histplot, '>=EF4')
trd.groupby(['year', '>=EF4']).size()


## county-level trend for >=EF2 (NWS desc: class >= strong, impact >= significant)
ef2m = trd.pivot(index = ['stfips', 'stname', 'ctyfips', 'ctyname'],
                 columns = 'year', values = '>=EF2')
ef2m.reset_index(drop = False, inplace = True)
# plot 10 counties to look for possible trajectories, random
t0 = random.sample(list(set(ef2m.ctyfips)), 10)
t1 = trd[trd['ctyfips'].isin(t0)].copy(deep = True)
ax = sns.lineplot(data = t1, x = 'year', y = '>=EF2', hue = 'ctyfips')
sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))


# ## tornado rank
# trd.columns
# trd.reset_index(drop = False, inplace = True)
# for i in range(trd.shape[0]):
#     tmax = trd.loc[i, ['EF0', 'EF1', 'EF2', 'EF3', 'EF4', 'EF5']].max()
#     if tmax > 0:
#           tcol = np.where(trd.loc[i, ['EF0', 'EF1', 'EF2', 'EF3', 'EF4', 
#                                       'EF5']] == tmax)
#           tcol = np.max(tcol)
#           trd.loc[i, 'trd_rank'] = tcol + 1
#     else:
#           trd.loc[i, 'trd_rank'] = 0
# del [i, tcol, tmax]
# trd['trd_rank'] = trd['trd_rank'].astype(int)
# set(trd['trd_rank'])
# trd.groupby('trd_rank').size()



"""
air quality
pm2.5: EPA, NAQQS
    2011-2019: >= 3110 counties
    2020: only available for 534 counties
o3: NAQQS only
    2011-2019: >= 3108 counties
    2020: 3051 counties
"""

os.listdir('air')
fld = os.listdir('air/raw')

# process
dt = dict()
i = 0
for item in ['o3_naqqs', 'pm2.5_naqqs', 'pm2.5_epa']:
    print(item)
    i += 1
    tdf = pd.read_csv('air/raw/item29{}_annual_{}.csv'.format(i * 2, item))
    tdf.rename(columns = {'parentGeoId': 'stfips', 'parentGeo': 'stname', 
                          'parentGeoAbbreviation': 'stabbr',
                          'geoId': 'ctyfips', 'geo': 'ctyname',
                          'temporalId': 'year', 'dataValue': item},
               inplace = True)
    tdf = tdf[['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year', item]]
    dt[item] = tdf

# check county-year availability
dt['pm2.5_epa'].groupby('pm2.5_epa').size()
dt['pm2.5_naqqs'].groupby('pm2.5_naqqs').size()
dt['o3_naqqs'].groupby('o3_naqqs').size()

# merge
air = dt['pm2.5_epa'].merge(
    dt['pm2.5_naqqs'], how = 'outer',
    on = ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year'])
air = air.merge(
    dt['o3_naqqs'], how = 'outer', 
    on = ['stfips', 'stabbr', 'stname', 'ctyfips', 'ctyname', 'year'])

# slice by state
print(air.shape) # 62442
air = air.loc[(air['stfips'] <= 56), :] # & (air['stfips'] != 2) & (air['stfips'] != 15)
print(air.shape) # 62442

# slice by year
air = air.loc[(air['year'] >= 2010) & (air['year'] <= 2021), :]
air.shape # 34210

# check nan
air.info()
sair = air.pivot(
    index = ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname'],
    columns = 'year', values = ['pm2.5_epa', 'pm2.5_naqqs', 'o3_naqqs'])
sair.info()

# output
air.columns
air.to_csv('air/air_2010to2021.csv', index = False)


'''
summary: 
'''

air = pd.read_csv('air/air_2011to2020.csv')
print(air.columns)


## EPA
epa = air.pivot(index = ['stfips', 'stname', 'ctyfips', 'ctyname'],
                columns = 'year', values = ['pm2.5_epa'])
epa.columns
epa.columns = epa.columns.get_level_values('year')
epa.reset_index(drop = False, inplace = True)

# univariate distribution
sns.FacetGrid(data = air, col = 'year', col_wrap = 3
              ).map(sns.histplot, 'pm2.5_epa', binwidth = 0.5)

# longitudinal trend
# all
ax = sns.lineplot(data = air, x = 'year', y = 'pm2.5_epa', hue = 'ctyfips')
sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))
# sample
t0 = random.sample(list(set(air.ctyfips)), 10)
t1 = air[air['ctyfips'].isin(t0)].copy(deep = True)
ax = sns.lineplot(data = t1, x = 'year', y = 'pm2.5_epa', hue = 'ctyfips')
sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))


## NAQQS
air['pm2.5_naqqs'].describe()
set(air['pm2.5_naqqs'].values)
naq = air.pivot(index = ['stfips', 'stname', 'ctyfips', 'ctyname'],
                columns = 'year', values = ['pm2.5_naqqs'])
naq.columns
naq.columns = naq.columns.get_level_values('year')
naq.reset_index(drop = False, inplace = True)

# univariate distribution
sns.FacetGrid(data = air, col = 'year', col_wrap = 3
              ).map(sns.histplot, 'pm2.5_naqqs', binwidth = 0.5)

# longitudinal trend
# all
ax = sns.lineplot(data = air, x = 'year', y = 'pm2.5_naqqs', hue = 'ctyfips')
sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))
# sample
t0 = random.sample(list(set(air.ctyfips)), 10)
t1 = air[air['ctyfips'].isin(t0)].copy(deep = True)
ax = sns.lineplot(data = t1, x = 'year', y = 'pm2.5_naqqs', hue = 'ctyfips')
sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))


"""
precipitation: re-process due to extended year range
"""

os.listdir('precipitation')

# load data
pct = pd.read_csv('precipitation/item576_annual_precipitation_relative.csv')
pct.shape
list(pct.columns)
sorted(list(set(pct['temporalId']))) # 2000-2021

# extract percentile threshold
pct['threshold'] = pct['Relative Threshold'].str.extract('(\d+)').astype(int)
pct.loc[:5, ['geoId', 'temporalId', 'threshold']]
set(pct['threshold']) # {90, 95, 98, 99}
pct_sum = pd.DataFrame(pct.groupby(['geoId', 'temporalId']).size())
pct_sum.rename(columns = {0: 'count'}, inplace = True)
set(pct_sum['count']) # 4 rows per county-year
del pct_sum

# reshape data
pctout = pct.copy(deep = True)
pctout.columns
pctout = pctout[['parentGeoId', 'parentGeo', 'geoId', 'geo', 'dataValue', 'temporalId', 'threshold']]
pctout.rename(columns = {'geo': 'ctyname', 'geoId': 'ctyfips', 'parentGeo': 'stname', 
                         'parentGeoId': 'stfips', 'temporalId': 'year'}, 
              inplace = True)
pctout = pd.DataFrame(pctout.pivot(index = ['stfips', 'stname', 'ctyfips', 'ctyname', 'year'], 
                                   columns = 'threshold', values = 'dataValue'))
pctout.reset_index(drop = False, inplace = True)
set(pct.threshold)
pctout.rename(columns = {90: 'prcp_abv90', 95: 'prcp_abv95', 
                         98: 'prcp_abv98', 99: 'prcp_abv99'}, inplace = True)
# calculate graded counts
pctout['prcp_90to95'] = pctout['prcp_abv90'] - pctout['prcp_abv95']
pctout['prcp_95to98'] = pctout['prcp_abv95'] - pctout['prcp_abv98']
pctout['prcp_98to99'] = pctout['prcp_abv98'] - pctout['prcp_abv99']
# extract 2010-2021 data
pctout = pctout[pctout['year'].isin(range(2010, 2022))]
print(sorted(list(set(pctout.year))))

# output
pctout.columns
pctout.to_csv('precipitation/prcp_relative_2010to2021.csv', index = False)



"""
heat: re-process due to extended year range
"""

os.listdir('heat')

'''
day
'''
# number of precipitations with relative threshold, annual
htd = pd.read_csv('heat/raw/item423_annual_heat_day_relative.csv')
htd.shape
list(htd.columns)

# extract percentile threshold
htd.loc[:10, ['geoId', 'temporalId', 'Relative Threshold', 'Heat Metric']]
htd['threshold'] = htd['Relative Threshold'].str.extract('(\d+)').astype(int)
htd['metric'] = htd['Heat Metric'].str.extract('(Index|Temperature)')
set(htd['threshold']) # {90, 95, 98, 99}
set(htd['metric']) # {'Index', 'Temperature'}
htd_sum = pd.DataFrame(htd.groupby(['geoId', 'temporalId']).size())
htd_sum.rename(columns = {0: 'count'}, inplace = True)
set(htd_sum['count']) # 8 rows per county-year
del htd_sum

# reshape data
htdout = htd[htd['metric'] == 'Index'].copy(deep = True)
htdout.columns
htdout = htdout[['parentGeoId', 'parentGeo', 'geoId', 'geo', 'dataValue', 'temporalId', 'threshold']]
htdout.rename(columns = {'geo': 'ctyname', 'geoId': 'ctyfips', 'parentGeo': 'stname', 
                         'parentGeoId': 'stfips', 'temporalId': 'year'}, 
              inplace = True)
htdout = pd.DataFrame(htdout.pivot(index = ['stfips', 'stname', 'ctyfips', 'ctyname', 'year'], 
                                   columns = 'threshold', values = 'dataValue'))
htdout.reset_index(drop = False, inplace = True)
set(htd.threshold)
htdout.rename(columns = {90: 'htd_abv90', 95: 'htd_abv95', 
                         98: 'htd_abv98', 99: 'htd_abv99'}, inplace = True)
# calculate graded counts
htdout['htd_90to95'] = htdout['htd_abv90'] - htdout['htd_abv95']
htdout['htd_95to98'] = htdout['htd_abv95'] - htdout['htd_abv98']
htdout['htd_98to99'] = htdout['htd_abv98'] - htdout['htd_abv99']

# extract 2010-2021 data
htdout = htdout[htdout['year'].isin(range(2010, 2022))]

# # output
# htdout.to_csv('heat/heat_day_2010to2021.csv', index = False)


'''
event
'''

# number of precipitations with relative threshold, annual
hte = pd.read_csv('heat/raw/item425_annual_heat_event_relative.csv')
hte.shape
list(hte.columns)

# extract percentile threshold
hte.loc[:20, ['geoId', 'temporalId', 'Relative Threshold', 'Heat Metric', 'Minimum Duration Days']]
hte['threshold'] = hte['Relative Threshold'].str.extract('(\d+)').astype(int)
hte['duration'] = hte['Minimum Duration Days'].str.extract('(\d+)').astype(int)
hte['metric'] = hte['Heat Metric'].str.extract('(Index|Temperature)')
set(hte['threshold']) # {90, 95, 98, 99}
set(hte['duration']) # {2, 3}
set(hte['metric']) # {'Index', 'Temperature'}
hte_sum = pd.DataFrame(hte.groupby(['geoId', 'temporalId']).size())
hte_sum.rename(columns = {0: 'count'}, inplace = True)
set(hte_sum['count']) # 8 rows per county-year
del hte_sum

# reshape data
hteout = hte[(hte['metric'] == 'Index') & (hte['duration'] == 2)].copy()
hteout.columns
hteout = hteout[['parentGeoId', 'parentGeo', 'geoId', 'geo', 
                 'dataValue', 'temporalId', 'threshold']]
hteout.rename(columns = {'geo': 'ctyname', 'geoId': 'ctyfips', 
                         'parentGeo': 'stname', 'parentGeoId': 'stfips', 
                         'temporalId': 'year'}, 
              inplace = True)
hteout = pd.DataFrame(hteout.pivot(index = ['stfips', 'stname', 'ctyfips', 'ctyname', 'year'], 
                                   columns = 'threshold', values = 'dataValue'))
hteout.reset_index(drop = False, inplace = True)
set(hte.threshold)
hteout.rename(columns = {90: 'hte_abv90', 95: 'hte_abv95', 
                         98: 'hte_abv98', 99: 'hte_abv99'}, inplace = True)
# calculate graded counts
hteout['hte_90to95'] = hteout['hte_abv90'] - hteout['hte_abv95']
hteout['hte_95to98'] = hteout['hte_abv95'] - hteout['hte_abv98']
hteout['hte_98to99'] = hteout['hte_abv98'] - hteout['hte_abv99']

# extract 2010-2021 data
hteout = hteout[hteout['year'].isin(range(2010, 2022))]
# # output
# hteout.to_csv('heat/heat_event_2011to2021.csv', index = False)


'''
merge heat
'''

## inspect
# day
print(htdout.columns)
print(htdout.shape) # 37296
htdout.reset_index(drop = True, inplace = True)
# event (consecutive days >= 2)
print(hteout.columns)
print(hteout.shape) # 37296
hteout.reset_index(drop = True, inplace = True)

# merge
heat = htdout.merge(hteout, how = 'outer', 
                    on = ['stfips', 'stname', 'ctyfips', 'ctyname', 'year'])
print(heat.shape) # 37296

# output
heat.to_csv('heat/heat_day_and_event_2010to2021.csv', index = False)



"""
merge all processed CDC EPHTN measures
heat, precipitation, drought, tornado, air quality
"""

## load processed drought
drt = pd.read_csv('drought/spei_usdm_2010to2021.csv')
print(drt.shape)
print(drt.columns)
## check FIPS, check outdated first and updated second
# AK
2270 in set(drt.ctyfips) # F
2158 in set(drt.ctyfips) # T
# AK split
2261 in set(drt.ctyfips) # T
2063 in set(drt.ctyfips) # F
2066 in set(drt.ctyfips) # F
# South Dakota
46113 in set(drt.ctyfips) # T
46102 in set(drt.ctyfips) # F
# Virginia
51515 in set(drt.ctyfips) # F
51019 in set(drt.ctyfips) # T
# CT
9160 in set(drt.ctyfips) # F
9013 in set(drt.ctyfips) # T
9005 in set(drt.ctyfips) # T
drt_cols = [x for x in list(drt.columns) if x not in ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year']]
for yr in range(2010, 2022):
    print(yr)
    print(drt.loc[(drt['ctyfips'].isin([9013, 9005])) & (drt['year'] == yr), 
                  :].duplicated(drt_cols))
# 9013 and 9005 not identical


## load processed tornado
trd = pd.read_csv('tornado/tornado_2010to2021.csv')
print(trd.shape)
print(trd.columns)
## check FIPS, check outdated first and updated second
# AK replacement
2270 in set(trd.ctyfips) # F
2158 in set(trd.ctyfips) # T
# AK split
2261 in set(trd.ctyfips) # F
2063 in set(trd.ctyfips) # T
2066 in set(trd.ctyfips) # T
# check 2063 and 2066: identical
for yr in range(2010, 2022):
    print(yr)
    print(trd.loc[(trd['year'] == yr) & (trd['ctyfips'].isin([2063, 2066])), 
                  :].duplicated(
                      subset = ['EF0', 'EF1', 'EF2', 'EF3', 'EF4', 'EF5', 
                                '>=EF1', '>=EF2', '>=EF3', '>=EF4', 'all_tornado']))
# South Dakota
46113 in set(trd.ctyfips) # F
46102 in set(trd.ctyfips) # T
# Virginia
51515 in set(trd.ctyfips) # F
51019 in set(trd.ctyfips) # T
# CT
9160 in set(trd.ctyfips) # F
9013 in set(trd.ctyfips) # T
9005 in set(trd.ctyfips) # T
# check 9013 and 9005: differ
trd_cols = [x for x in list(trd.columns) if x not in ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year']]
for yr in range(2010, 2022):
    print(yr)
    print(trd.loc[(trd['ctyfips'].isin([9013, 9005])) & (trd['year'] == yr), 
                  :].duplicated(trd_cols))


## load processed air quality
air = pd.read_csv('air/air_2010to2021.csv')
print(air.shape)
print(air.columns)
## check FIPS, check outdated first and updated second
# AK replacement
2270 in set(air.ctyfips) # F
2158 in set(air.ctyfips) # F
# AK split
2261 in set(air.ctyfips) # F
2063 in set(air.ctyfips) # F
2066 in set(air.ctyfips) # F
# South Dakota
46113 in set(air.ctyfips) # T
46102 in set(air.ctyfips) # F
# Virginia
51515 in set(air.ctyfips) # F
51019 in set(air.ctyfips) # T
# CT
9160 in set(air.ctyfips) # F
9013 in set(air.ctyfips) # T
9005 in set(air.ctyfips) # T
air_cols = [x for x in list(air.columns) if x not in ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year']]
for yr in range(2010, 2022):
    print(yr)
    print(air.loc[(air['ctyfips'].isin([9013, 9005])) & (air['year'] == yr), 
                  :].duplicated(air_cols))


# load processed heat
heat = pd.read_csv('heat/heat_day_and_event_2010to2021.csv')
print(heat.shape)
print(len(set(heat.ctyfips))) # 3108
print(sorted(list(set(heat.year)))) # 2021 in data
print(heat.columns)
## check FIPS, check outdated first and updated second
# AL replacement
2270 in set(heat.ctyfips) # F
2158 in set(heat.ctyfips) # F
# AL split
2261 in set(heat.ctyfips) # F
2063 in set(heat.ctyfips) # F
2066 in set(heat.ctyfips) # F
# South Dakota
46113 in set(heat.ctyfips) # T
46102 in set(heat.ctyfips) # F
# Virginia
51515 in set(heat.ctyfips) # F
51019 in set(heat.ctyfips) # T
# CT
9160 in set(heat.ctyfips) # F
9013 in set(heat.ctyfips) # T
9005 in set(heat.ctyfips) # T
heat_cols = [x for x in list(heat.columns) if x not in ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year']]
for yr in range(2010, 2022):
    print(yr)
    print(heat.loc[(heat['ctyfips'].isin([9013, 9005])) & (heat['year'] == yr), 
                  :].duplicated(heat_cols))


## load processed precipitation
# load prcp
prcp = pd.read_csv('precipitation/prcp_relative_2010to2021.csv')
print(prcp.shape)
print(len(set(prcp.ctyfips))) # 3108
print(prcp.columns)
## check FIPS, check outdated first and updated second
# AL replacement
2270 in set(prcp.ctyfips) # F
2158 in set(prcp.ctyfips) # T
# AL split
2261 in set(prcp.ctyfips) # F
2063 in set(prcp.ctyfips) # F
2066 in set(prcp.ctyfips) # F
# South Dakota
46113 in set(prcp.ctyfips) # T
46102 in set(prcp.ctyfips) # F
# Virginia
51515 in set(prcp.ctyfips) # F
51019 in set(prcp.ctyfips) # T
# CT
9160 in set(prcp.ctyfips) # F
9013 in set(prcp.ctyfips) # T
9005 in set(prcp.ctyfips) # T
prcp_cols = [x for x in list(prcp.columns) if x not in ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year']]
for yr in range(2010, 2022):
    print(yr)
    print(prcp.loc[(prcp['ctyfips'].isin([9013, 9005])) & (prcp['year'] == yr), 
                  :].duplicated(prcp_cols))


'''
merge
'''

## drought + tornado
fnl = drt.merge(trd, how = 'outer', 
                on = ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year'])
print(fnl.shape) # 37740
tmp_nan = fnl[fnl.isnull().any(axis=1)] # 456 rows

# change Alaska counties
2270 in set(drt['ctyfips']) # True
drt.loc[drt['ctyfips'] == 2270, 'ctyname'] = 'Kusilvak Census Area'
drt.loc[drt['ctyfips'] == 2270, 'ctyfips'] = 2158
2270 in set(trd['ctyfips']) # True
trd.loc[trd['ctyfips'] == 2270, 'ctyname'] = 'Kusilvak Census Area'
trd.loc[trd['ctyfips'] == 2270, 'ctyfips'] = 2158
2063 in set(trd['ctyfips']) # True
2066 in set(trd['ctyfips']) # True
2261 in set(trd['ctyfips']) # False
trd.loc[trd['ctyfips'] == 2063, 'ctyname'] = 'Valdez-Cordova'
trd.loc[trd['ctyfips'] == 2063, 'ctyfips'] = 2261
trd.shape
trd.drop(trd[trd['ctyfips'] == 2066].index, inplace = True)
trd.shape

# change South Dakota, 2014: Shannon County (FIPS = 46113) renamed to Oglala Lakota County (FIPS = 46102)
# drought data uses old code ==> replace with new one
46113 in set(drt['ctyfips']) # True
46102 in set(drt['ctyfips']) # False
drt.loc[drt['ctyfips'] == 46113, 'stname'] = 'South Dakota'
drt.loc[drt['ctyfips'] == 46113, 'ctyname'] = 'Oglala Lakota'
drt.loc[drt['ctyfips'] == 46113, 'ctyfips'] = 46102
46113 in set(trd['ctyfips']) # False
46102 in set(trd['ctyfips']) # True

# change CT counties: harmonize 9013 and 9005
9013 in set(drt.ctyfips) # True
9005 in set(drt.ctyfips) # True
drt.columns
drt_cols = [x for x in list(drt.columns) if x not in 
            ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year']]
set(drt.year)
stid_val = drt.loc[drt['ctyfips'] == 9013, ['stfips', 'stname', 'stabbr']
                   ].drop_duplicates().values[0]
# for yr in range(2010, 2022):
#     drt.loc[drt.shape[0], ['stfips', 'stname', 'stabbr']] = stid_val
#     drt.loc[drt.shape[0] - 1, ['ctyfips', 'ctyname']] = [9160, 'Northwest Hills Planning Region']


## rerun merge after correction of ctyfips in drt and tnd
drt.shape
trd.shape
fnl = drt.merge(trd, how = 'outer', on = ['stfips', 'stname', 'stabbr', 
                                          'ctyfips', 'ctyname', 'year'])
print(fnl.shape) # 37704

## air
# check which code was used for the South Dakota county
46113 in set(air.ctyfips) # True
46102 in set(air.ctyfips) # False
2270 in set(air.ctyfips) # False
2158 in set(air.ctyfips) # False
# modify
air.loc[air['ctyfips'] == 46113, 'stname'] = 'South Dakota'
air.loc[air['ctyfips'] == 46113, 'ctyname'] = 'Oglala Lakota'
air.loc[air['ctyfips'] == 46113, 'ctyfips'] = 46102
# merge
print(fnl.shape) # 37704
fnl = fnl.merge(air, how = 'outer',
                on = ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year'])
print(fnl.shape) # 37704


## merge with heat
# check the SD county
46113 in set(heat.ctyfips) # True
46102 in set(heat.ctyfips) # False
2270 in set(heat.ctyfips) # False
2158 in set(heat.ctyfips) # False
# streamline
heat.loc[heat['ctyfips'] == 46113, 'stname'] = 'South Dakota'
heat.loc[heat['ctyfips'] == 46113, 'ctyname'] = 'Oglala Lakota'
heat.loc[heat['ctyfips'] == 46113, 'ctyfips'] = 46102
# merge
print(fnl.shape)
fnl = fnl.merge(heat, how = 'outer',
                on = ['stfips', 'stname', 'ctyfips', 'ctyname', 'year'])
print(fnl.shape)

## merge with precipitation
# check the SD county
46113 in set(prcp.ctyfips) # True
46102 in set(prcp.ctyfips) # False
2270 in set(prcp.ctyfips) # False
2158 in set(prcp.ctyfips) # False
# streamline
prcp.loc[prcp['ctyfips'] == 46113, 'stname'] = 'South Dakota'
prcp.loc[prcp['ctyfips'] == 46113, 'ctyname'] = 'Oglala Lakota'
prcp.loc[prcp['ctyfips'] == 46113, 'ctyfips'] = 46102
# merge
print(fnl.shape)
fnl = fnl.merge(prcp, how = 'outer',
                on = ['stfips', 'stname', 'ctyfips', 'ctyname', 'year'])
print(fnl.shape)

## output
# data
print(fnl.columns)
fnl.to_csv('modular/cdc_climate_all_2010to2021.csv', index = False)
# # codebook
# cdbk = pd.DataFrame(list(fnl.columns), columns = ['variable'])
# cdbk.columns
# cdbk.to_excel('modular/codebook_cdc_climate_all.xlsx', index = False)
# availability
fnl.info()



"""
natural hazards data from other official sources
1. EPA: % of county area affected, longitudinal, 2000-2019
2. FEMA-NRI: annualized average
"""

# work directory
os.chdir('/Users/xywu/OneDrive - Johns Hopkins/ra/HPC_climate/data/other_source')
os.chdir('C:/Users/xwu70/OneDrive - Johns Hopkins/ra/HPC_climate/data/other_source')

os.listdir()


'''
EPA
earthquake: only available for 2016, 2017, 2018
coastal flooding: only available for 2019
inland flooding: only available for 2019
'''

os.listdir('EPA_climate_historic_extensions')

# load data
epa = pd.read_excel('EPA_climate_historic_extensions/NatHazHistories_Dataset.xlsx',
                    na_values = -999)
print(epa.shape) # 64400
print(epa.columns)
print(epa.iloc[0, :])

# rename columns
epa.rename(columns = {'STATEFP': 'stfips', 'GEOID': 'ctyfips', 'YEAR': 'year',
                      'UNIT(S)': 'unit', 'NAME': 'ctyname',
                      'HURRICANE': 'hurricane', 
                      'TROPICAL STORM': 'tropical_storm', 
                      'TORNADO': 'tornado',
                      'LANDSLIDE': 'landslide', 
                      'WILDFIRE': 'wildfire',
                      'DROUGHT': 'drought', 
                      'COASTAL FLOODING': 'coastal_flooding',
                      'INLAND FLOODING': 'inland_flooding', 
                      'EARTHQUAKE': 'earthquake', 
                      'COUNTY AREA (SQKM)': 'area_sqkm'}, inplace = True)
epa.columns
# available value unit
set(epa.unit) # 'PERCENT_AREA'
epa = epa[['stfips', 'ctyfips', 'ctyname', 'year', 'area_sqkm',
           'hurricane', 'tropical_storm', 'tornado', 'landslide', 'wildfire',
           'drought', 'coastal_flooding', 'inland_flooding', 'earthquake']]

# keep continuous states only
set(epa.year)
print(epa.shape) # (64400, 14)
epa = epa.loc[#(epa['stfips'] != 2) & (epa['stfips'] != 15) & 
              (epa['stfips'] <= 56) & (epa['year'] >= 2010), :]
print(epa.shape) # 28278

# sort rows
epa.sort_values(by = ['stfips', 'ctyfips', 'year'], axis = 0, inplace = True,
                ignore_index = True)

## summary
epa.info()
epa.describe()
# available county & county-year
print(len(set(epa.ctyfips))) # 3142
cty_year = pd.DataFrame(epa.groupby('ctyfips').size())
cty_year.rename(columns = {0: 'num_year'}, inplace = True)
set(cty_year.num_year)
# availability for coastal flooding
t0 = epa.loc[-epa['coastal_flooding'].isnull(), :]
set(t0.year) # 2019
# availability for inland flooding
t1 = epa.loc[-epa['inland_flooding'].isnull(), :]
set(t1.year) # 2019
# availability for earthquake
t2 = epa.loc[-epa['earthquake'].isnull(), :]
set(t2.year) # 2016, 2017, 2018
len(set(t2.ctyfips)) # 3108
# availability for landslide
t3 = epa.loc[epa['landslide'].isnull(), :]
set(t3.year) # no 2019
# tornado
t4 = epa.loc[epa['tornado'].isnull(), :]
set(t4.year) # no 2019


## select fields to save
print(epa.shape) # (28278, 14)
print(epa.columns)
epa = epa[['stfips', 'ctyfips', 'ctyname', 'year', 'area_sqkm',
           'hurricane', 'tropical_storm', 'tornado', 'drought',
           'landslide', 'wildfire']]
print(epa.shape)

# streamline county FIPS code
46113 in set(epa.ctyfips) # false
46102 in set(epa.ctyfips) # true, updated FIPS code already
2270 in set(epa.ctyfips) # False
2158 in set(epa.ctyfips) # True, good to go
9160 in set(epa.ctyfips) # F
9013 in set(epa.ctyfips) # T
9005 in set(epa.ctyfips) # T
epa_cols = [x for x in list(epa.columns) if x not in ['stfips', 'stname', 'stabbr', 'ctyfips', 'ctyname', 'year']]
for yr in range(2010, 2022):
    print(yr)
    print(epa.loc[(epa['ctyfips'].isin([9013, 9005])) & (epa['year'] == yr),
                  :].duplicated(epa_cols))



# output
epa.to_csv('epa_extracted_2010to2019.csv', index = False)



"""
merge CDC & EPA
"""

os.chdir('/Users/xywu/OneDrive - Johns Hopkins/ra/HPC_climate/data')
os.chdir('C:/Users/xwu70/OneDrive - Johns Hopkins/ra/HPC_climate/data')

# load CDC data
fnl = pd.read_csv('ephtn/modular/cdc_climate_all_2010to2021.csv')
print(fnl.shape) # 37704
print(fnl.columns)
## check FIPS, check outdated first and updated second for replacement
# AL replacement
2270 in set(fnl.ctyfips) # F
2158 in set(fnl.ctyfips) # T
# AL split
2261 in set(fnl.ctyfips) # T
2063 in set(fnl.ctyfips) # F
2066 in set(fnl.ctyfips) # F
# South Dakota
46113 in set(fnl.ctyfips) # F
46102 in set(fnl.ctyfips) # T
# Virginia
51515 in set(fnl.ctyfips) # F
51019 in set(fnl.ctyfips) # T

# load processed EPA data
epa = pd.read_csv('other_source/epa_extracted_2010to2019.csv')
print(epa.shape) # 31420
print(epa.columns)
## check FIPS, check outdated first and updated second
# AL replacement
2270 in set(epa.ctyfips) # F
2158 in set(epa.ctyfips) # T
# AL split
2261 in set(epa.ctyfips) # T
2063 in set(epa.ctyfips) # F
2066 in set(epa.ctyfips) # F
# South Dakota
46113 in set(epa.ctyfips) # F
46102 in set(epa.ctyfips) # T
# Virginia
51515 in set(epa.ctyfips) # F
51019 in set(epa.ctyfips) # T

# merge
fnl = fnl.merge(epa[['stfips', 'ctyfips', 'year', 'area_sqkm', 'hurricane',
                     'tropical_storm', 'tornado', 'drought', 'landslide', 
                     'wildfire']], 
                how = 'outer', on = ['stfips', 'ctyfips', 'year'])
print(fnl.shape) # 37704
tmp_nan = fnl[fnl['year'] <= 2019]
tmp_nan = tmp_nan[tmp_nan.isnull().any(axis=1)]
print(set(tmp_nan['year'])) # 2017, 2018, 2019 for contiguous states
tmp_nan.info() # EPA tornado & landslide only largely unavailale in this subset

# output to shared folder
fnl.to_csv('processed_data/climate_all_2010to2021.csv', index = False)



"""
extract variables for analysis
"""

os.chdir('/Users/xywu/OneDrive - Johns Hopkins/ra/HPC_climate')
os.chdir('C:/Users/xwu70/OneDrive - Johns Hopkins/ra/HPC_climate')


# load data
fnl = pd.read_csv('data/processed_data/climate_all_2010to2021.csv')

## construct heat/prcp rank
# prcp
fnl['prcp_rank'] = np.where(fnl['prcp_abv98'] == 0, 1,
                            np.where(fnl['prcp_98to99'] > fnl['prcp_abv99'], 2,
                            np.where(fnl['prcp_abv98'].isnull(), np.nan, 3)))
# heat event
fnl['hte_rank'] = np.where(fnl['hte_abv98'] == 0, 1,
                           np.where(fnl['hte_98to99'] > fnl['hte_abv99'], 2, 
                           np.where(fnl['hte_abv98'].isnull(), np.nan, 3)))
# # heat day
# fnl['htd_rank'] = np.where(fnl['htd_abv98'] == 0, 1,
#                            np.where(fnl['htd_98to99'] > fnl['htd_abv99'], 2, 3))


# select
fnl = fnl[['stfips', 'stname', 'ctyfips', 'ctyname', 'year',
           'prcp_rank', 'prcp_abv95', 'hte_rank', 'hte_abv95',
           'usdm_pct_cum2_severe', '>=EF2', 
           'pm2.5_naqqs', 'hurricane', 'tropical_storm', 'tornado', 
           'drought', 'landslide', 'wildfire']]

# rename columns
print(fnl.columns)
fnl.rename(columns = {'usdm_pct_cum2_severe': 'drought_>=severe',
                      '>=EF2': 'tornado_>=EF2', 
                      'pm2.5_naqqs': 'pm2.5_over35'},
           inplace = True)
print(fnl.columns)

# output
fnl.to_csv('Climate-c2c-IRS/climate/climate_selected_2010to2021.csv', 
           index = False)



"""
FIPS code check
"""

os.chdir('/Users/xywu/OneDrive - Johns Hopkins/ra/HPC_climate')
os.chdir('C:/Users/xwu70/OneDrive - Johns Hopkins/ra/HPC_climate')


# fips
fips = dict()
for yr in range(2015, 2023):
    tdf = pd.read_excel('Climate-c2c-IRS/county_pop_data/US-fips/all-geocodes-v' + str(yr) + '.xlsx', header = 4)
    tdf.rename(columns = {'State Code (FIPS)': 'stfips', 'State FIPS Code': 'stfips', 
                          'County Code (FIPS)': 'ctyfips', 'County FIPS Code': 'ctyfips',
                          'County Subdivision Code (FIPS)': 'subfips', 'County Subdivision FIPS Code': 'subfips'}, inplace = True)
    tdf = tdf.loc[(tdf['stfips'] > 0) & (tdf['stfips'] <= 56) & 
                  (tdf['ctyfips'] != 0) & (tdf['subfips'] == 0)]
    tdf['scfips'] = tdf['stfips'] * 1000 + tdf['ctyfips']
    tdf.reset_index(drop = True, inplace = True)
    print('Year {}: {} counties'.format(yr, tdf.shape[0]))
    fips[str(yr)] = tdf

## check consistency
for yr in range(2015, 2022):
    print('In {}, not in {}'.format(yr, yr + 1))
    print([x for x in fips[str(yr)]['scfips'].tolist() 
           if x not in fips[str(yr + 1)]['scfips'].tolist()])
    print('In {}, not in {}'.format(yr + 1, yr))
    print([x for x in fips[str(yr + 1)]['scfips'].tolist() 
           if x not in fips[str(yr)]['scfips'].tolist()])


## CT crosswalk
ct = pd.read_excel('~/Downloads/ct_cou_to_cousub_crosswalk.xlsx')
ct = ct.iloc[:174, :]
print(ct.columns)
ct.rename(columns = {'STATEFP\n(INCITS38)': 'stfips',
                     'OLD_COUNTYFP\n(INCITS31)': 'ctyfips_old',
                     'OLD_COUNTY_NAMELSAD': 'ctyname_old',
                     'NEW_COUNTYFP\n(INCITS31)': 'ctyfips_new',
                     'NEW_COUNTY_NAMELSAD': 'ctyname_new'}, inplace = True)
# unique rows for old vs. new ctyfips
cu = ct[['stfips', 'ctyfips_old', 'ctyname_old', 'ctyfips_new', 'ctyname_new']].drop_duplicates(keep = 'first')
cu.to_excel('Climate-c2c-IRS/county_pop_data/CT_county_crosswalk.xlsx', index = False)

