# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 14:26:50 2024

Merge migration-social vulnerability-resilience-climate data
    Vertex level
    Dyad level
    
Descriptive analysis with merged data

Modified based on analyze_migration_v1.py
    1.Refined measurement of resilience and climate
    2.Univariate distribution of compound climate risks and resilience
    3.Bivariate distribution between climate risks & newly constructed resilience

Initial: 3/29/2024
Latest: 4/3/2024

@author: Xingyun Wu, Johns Hopkins University, xywu@jhu.edu
"""


import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
os.chdir('/Users/xywu/OneDrive - Johns Hopkins/ra/HPC_climate/script/')
os.chdir('C:/Users/xwu70/OneDrive - Johns Hopkins/ra/HPC_climate/script/')
from analyze_migration_utils import * # import my written functions


os.chdir('/Users/xywu/OneDrive - Johns Hopkins/ra/HPC_climate/')
os.chdir('C:/Users/xwu70/OneDrive - Johns Hopkins/ra/HPC_climate/')


"""
vertex-level
"""

'''
merge
'''

# migration
mgdf = pd.read_csv('irs_migration/data/node_migration_long.csv')
list(mgdf.columns)
mgdf.rename(columns = {'fips': 'ctyfips', 'index_k': 'time'}, inplace = True)
mgdf['year'] = mgdf['time'] + 2009

# social vulnerability
svdf = pd.read_csv('Climate-c2c-IRS/pop_vul/county-year-indicator/svi_pc2.csv')
list(svdf.columns)
svdf.rename(columns = {'GEOID': 'ctyfips', 'index.TC1': 'svi1', 
                       'index.TC2': 'svi2'}, inplace = True)
svdf = svdf[['ctyfips', 'year', 'svi1', 'svi2']]

# resilience
rsl = []
for yr in [2010, 2015, 2020]:
    tmp = pd.read_csv('Climate-c2c-IRS/BRIC_score/bric{}.csv'.format(yr))
    tmp.rename(columns = {'GEOID': 'ctyfips', 'TOT RESIL{}'.format(yr): 
                          'rsl{}'.format(yr)}, inplace = True)
    tmp = tmp.loc[(tmp['State Code (FIPS)'] <= 56) & 
                  (tmp['State Code (FIPS)'] != 2) &
                  (tmp['State Code (FIPS)'] != 15), :].copy(deep = True)
    tmp.reset_index(drop = True, inplace = True)
    tmp = tmp[['ctyfips', 'rsl{}'.format(yr)]]
    rsl.append(tmp)
rsdf = rsl[0].merge(rsl[1], how = 'outer', on = 'ctyfips')
rsdf = rsdf.merge(rsl[2], how = 'outer', on = 'ctyfips')
# get difference
rsdf['diff1'] = rsdf['rsl2015'] - rsdf['rsl2010']
rsdf['diff2'] = rsdf['rsl2020'] - rsdf['rsl2015']
# distribution of original variable and differences
rsdf[['rsl2010', 'rsl2015', 'rsl2020', 'diff1', 'diff2']].describe()
rsdf[['rsl2010', 'rsl2015', 'rsl2020', 'diff1', 'diff2']].skew()
rsdf[['rsl2010', 'rsl2015', 'rsl2020', 'diff1', 'diff2']].kurt()

# check % of >= 0
rsdf[rsdf['diff1'] >= 0].shape[0] / rsdf.shape[0] # 4.18%
rsdf[rsdf['diff2'] >= 0].shape[0] / rsdf.shape[0] # 3.83%
rsdf[(rsdf['diff1'] >= 0) | (rsdf['diff2'] >= 0)].shape[0] / rsdf.shape[0] # 7.66%
rsdf[(rsdf['diff1'] < rsdf['diff2'])].shape[0] / rsdf.shape[0] # 88.9%
# check overall distribution
plt.hist(rsdf['diff1'], bins = 200, alpha = 0.8, label = '2015-2010')
plt.hist(rsdf['diff2'], bins = 200, alpha = 0.8, label = '2020-2015')
plt.legend()
plt.show()
# alternative: 75th percentile as cut-off point
rsdf['rslcat1'] = np.where(rsdf['diff1'] > np.nanpercentile(rsdf['diff1'], 75), 1, 0)
rsdf['rslcat2'] = np.where(rsdf['diff2'] > np.nanpercentile(rsdf['diff2'], 75), 1, 0)


# climate
cldf = pd.read_csv('ephtn/modular/precipitation_heat_2011to2021_extended.csv')
list(cldf.columns)
cldf = cldf[['stfips', 'stname', 'ctyfips', 'ctyname', 'year', 
             'prcp_rank', 'hte_rank', 'htd_rank']]
# compound climate risks of heat & precipitation
set(cldf['prcp_rank'])
for i in range(cldf.shape[0]):
    tmp = cldf.loc[i, ['prcp_rank', 'hte_rank']].tolist()
    # low risk
    if tmp == [1, 1] or tmp == [2, 1] or tmp == [1, 2]:
        tval = 1
    # medium risk
    elif tmp == [3, 1] or tmp == [2, 2] or tmp == [1, 3]:
        tval = 2
    elif tmp[0] == 3 & tmp[1] == 3:
        tval = 4
    # high on one
    else:
        tval = 3
    # add to df
    cldf.loc[i, 'crisk'] = tval
# turn categorical variables into integer
cldf['crisk'] = cldf['crisk'].astype(int)
# inspect distribution
cldf.groupby(['year', 'crisk']).size()
clsum = pd.DataFrame(cldf.groupby(['year', 'crisk']).size())
clsum.reset_index(drop = False, inplace = True)
clsum.rename(columns = {0: 'count'}, inplace = True)
sns.catplot(data = clsum, kind = 'bar', x = 'year', y = 'count', hue = 'crisk',
            height = 8, aspect = 15/8)

# county-level risk exposure in [2011, 2014]
clsum = pd.DataFrame(cldf.loc[(cldf['year'] >= 2011) & (cldf['year'] <= 2014)].
                     groupby(['stfips', 'stname', 'ctyfips', 'ctyname', 'crisk']).
                     size().unstack(fill_value=0).stack())
clsum.reset_index(drop = False, inplace = True)
clsum.rename(columns = {0: 'num_expsr'}, inplace = True)
# alternative: collapsing 3 & 4
cldf['crisk_clps'] = cldf['crisk'].copy(deep = True)
cldf.loc[cldf['crisk_clps'] == 4, 'crisk_clps'] = 3
set(cldf['crisk'] == cldf['crisk_clps']) # not influencing original
clsum = pd.DataFrame(cldf.loc[(cldf['year'] >= 2011) & (cldf['year'] <= 2014)].
                     groupby(['stfips', 'stname', 'ctyfips', 'ctyname', 'crisk_clps']).
                     size().unstack(fill_value=0).stack())
clsum.reset_index(drop = False, inplace = True)
clsum.rename(columns = {0: 'num_expsr'}, inplace = True)
# count by number of exposure to high compound risks
clsum.groupby(['crisk_clps', 'num_expsr']).size()
hrsk = clsum[clsum['crisk_clps'] == 3].copy(deep = True)
hrsk.reset_index(drop = True, inplace = True)
# merge resilience into the counts
hrsk = hrsk.merge(rsdf, on = 'ctyfips', how = 'left')
hrsk[['num_expsr', 'rsl2010', 'rsl2015', 'rsl2020', 'diff1', 'diff2']].groupby('num_expsr').mean()
hrsk[['num_expsr', 'rsl2010', 'rsl2015', 'rsl2020', 'diff1', 'diff2']].groupby('num_expsr').median()
sns.histplot(data = hrsk, x = 'diff1', hue = 'num_expsr', stat = 'density')
sns.catplot(
    data=hrsk, x="num_expsr", y="diff1",
    kind="violin", bw_adjust=1, split= False,
)



## merge
# climate + migration
cldf.shape
mgdf.shape
ndf = cldf.merge(mgdf, how = 'left', on = ['ctyfips', 'year'])
ndf.shape
# + resilience (option 1, two time points)
ndf = ndf.merge(rsdf, how = 'left', on = ['ctyfips', 'year'])
# + resilience (option 2, time-invariant)
ndf = ndf.merge(rsdf, how = 'left', on = 'ctyfips')
# + social vulnerability
ndf = ndf.merge(svdf, how = 'left', on = ['ctyfips', 'year'])


## output
# slice to the targeted year range
ndf.shape
ndf = ndf[ndf['year'].isin(range(2011, 2020))]
ndf.reset_index(drop = True, inplace = True)
ndf.shape
set(ndf['year'])
# summarize county counts by year
ndf.groupby('year').size()
# save
list(ndf.columns)
ndf.to_csv('Climate-c2c-IRS/node_allvar_long.csv', index = False)
ndf.to_csv('Climate-c2c-IRS/node_allvar_long_opt2.csv', index = False)


'''
constructed variables
'''

# load data opt 1: two-time-point RSL scores
ndf = pd.read_csv('Climate-c2c-IRS/node_allvar_long.csv')
list(ndf.columns)
# load data opt 2: time-invariant categorical RSL
ndf = pd.read_csv('Climate-c2c-IRS/node_allvar_long_opt2.csv')
list(ndf.columns)

# ## construct climate risk rank: compound measure for climate
# set(ndf['prcp_rank'])
# for i in range(ndf.shape[0]):
#     tmp = ndf.loc[i, ['prcp_rank', 'hte_rank']].tolist()
#     # low risk
#     if tmp == [1, 1] or tmp == [2, 1] or tmp == [1, 2]:
#         tval = 1
#     # medium risk
#     elif tmp == [3, 1] or tmp == [2, 2] or tmp == [1, 3]:
#         tval = 2
#     elif tmp[0] == 3 & tmp[1] == 3:
#         tval = 4
#     # high on one
#     else:
#         tval = 3
#     # add to df
#     ndf.loc[i, 'crisk'] = tval
# # inspect distribution
# ndf.groupby('crisk').size()
# # turn categorical variables
# ndf['crisk'] = ndf['crisk'].astype(int)


# categorize SVI1
v1 = np.nanpercentile(ndf['svi1'], q = 30)
v2 = np.nanpercentile(ndf['svi1'], q = 70)
for i in range(ndf.shape[0]):
    if ndf.loc[i, 'svi1'] < v1:
        tval = 1
    elif ndf.loc[i, 'svi1'] > v2:
        tval = 3
    else:
        tval = 2
    ndf.loc[i, 'svicat'] = tval
ndf['svicat'] = ndf['svicat'].astype(int)

# # categorize RSL, opt 1
# v1 = np.nanpercentile(ndf['rsl'], q = 30)
# v2 = np.nanpercentile(ndf['rsl'], q = 70)
# for i in range(ndf.shape[0]):
#     if ndf.loc[i, 'rsl'] < v1:
#         tval = 1
#     elif ndf.loc[i, 'rsl'] > v2:
#         tval = 3
#     else:
#         tval = 2
#     ndf.loc[i, 'rslcat'] = tval
# ndf['rslcat'] = ndf['rslcat'].astype(int)
# # construct SVI1 * RSL
# for i in range(ndf.shape[0]):
#     tmp = ndf.loc[i, ['svicat', 'rslcat']].tolist()
#     if tmp == [1, 1]:
#         tval = 1
#     elif tmp == [2, 2]:
#         tval = 2
#     elif tmp == [3, 3]:
#         tval = 3
#     elif tmp == [2, 1] or tmp == [3, 1] or tmp == [3, 2]:
#         tval = 4
#     else:
#         tval = 5
#     ndf.loc[i, 'svirsl'] = tval
# ndf['svirsl'] = ndf['svirsl'].astype(int)
# # inspect counts
# ndf.groupby('svirsl').size()

# construct SVI1 * RSL
for i in range(ndf.shape[0]):
    tmp = ndf.loc[i, ['svicat', 'rslcat']].tolist()
    if tmp == [1, 1]:
        tval = 1
    elif tmp == [1, 2]:
        tval = 2
    elif tmp == [2, 1]:
        tval = 3
    elif tmp == [2, 2]:
        tval = 4
    elif tmp == [3, 1]:
        tval = 5
    else:
        tval = 6
    ndf.loc[i, 'svirsl'] = tval
ndf['svirsl'] = ndf['svirsl'].astype(int)
# inspect counts
ndf.groupby('svirsl').size()



'''
descriptive tables
'''

# longitudinal trends
lsum = []
for var in ['irn1', 'rsl', 'svi1', 'svi2', 'crisk']:
    tmp = get_summary(ndf, col = var, precision = 1, group_by = 'year')
    tmp['variable'] = var
    lsum.append(tmp)
lsum = pd.concat(lsum, axis = 0, ignore_index = True)
# output
lsum.to_csv('Climate-c2c-IRS/summary/summary_vertex_vars.csv', index = False)

ndf.groupby('svicat').size()
ndf.groupby('rslcat').size()
ndf.groupby(['prcp_rank', 'hte_rank', 'crisk']).size()



'''
basic plots
'''

sns.lineplot(lsum[lsum['variable'] == 'crisk'], x = 'year', y = 'median')

sns.histplot(ndf, x = 'irn1', hue = 'crisk')
sns.histplot(ndf, x = 'orn1', hue = 'crisk')
sns.histplot(ndf, x = 'svi1', hue = 'crisk')
sns.histplot(ndf, x = 'svi2', hue = 'crisk')
sns.histplot(ndf, x = 'rsl', hue = 'crisk')

sns.countplot(ndf, x = 'year', hue = 'crisk')

sns.kdeplot(ndf, x = 'svi1', bw_adjust = 2, hue = 'crisk')
sns.kdeplot(ndf, x = 'rsl', bw_adjust = 2, hue = 'crisk')

sns.scatterplot(ndf, x = 'svi1', y = 'svi2', hue = 'crisk')
sns.scatterplot(ndf, x = 'svi1', y = 'rsl', hue = 'crisk')

jp1 = sns.jointplot(data = ndf, hue = 'crisk', #kind = 'kde', 
                    x = 'svi1', y = 'svi2')
jp2 = sns.jointplot(data = ndf, #hue = 'crisk', #kind = 'kde', 
                    x = 'svi1', y = 'rsl')

sns.countplot(ndf, x = 'svirsl')


'''
heatmap
'''

# summary table
sumi = get_summary(ndf, col = 'irn1', precision = 3, 
                   group_by = ['svirsl', 'crisk'])

# # streamline categories of svi-rsl: opt1
# yticklabels = ['Low-low', 'Medium-medium', 'high-high', 
#                'Vulnerability > Resilience', 'Vulnerability < Resilience']
# row_order_value = [1, 5, 2, 4, 3]
# for i in range(ndf.shape[0]):
#     if ndf.loc[i, 'svirsl'] == 5:
#         ndf.loc[i, 'recat'] = 2
#     elif ndf.loc[i, 'svirsl'] == 2:
#         ndf.loc[i, 'recat'] = 3
#     elif ndf.loc[i, 'svirsl'] == 3:
#         ndf.loc[i, 'recat'] = 5
#     else:
#         ndf.loc[i, 'recat'] = ndf.loc[i, 'svirsl']
# ndf['recat'] = ndf['recat'].astype(int)
# yticklabels = [yticklabels[0], yticklabels[4], yticklabels[1], yticklabels[3], yticklabels[2]]
# yticklabels


# ndf.groupby('recat').size()
# ndf.groupby('crisk').size()
# ndf.groupby(['svirsl', 'crisk', 'recat']).size()
ndf.groupby(['svirsl', 'crisk']).size()

# tval = 'recat'

tval = 'svirsl'
yticklabels = ['Low-low', 'Low-high', 'Mid-low', 'Mid-high', 'High-low', 'High-high']


# matrix of inflow rate
mtxi = np.zeros([len(set(ndf[tval])), len(set(ndf['crisk']))])
for i in range(mtxi.shape[0]):
    for j in range(mtxi.shape[1]):
        tmp = ndf.loc[(ndf[tval] == i + 1) & #(ndf['year'] == 2014) & 
                      (ndf['crisk'] == j + 1), 'irn1']
        mtxi[i][j] = np.nanpercentile(tmp, q = 50)
        
# matrix of outflow rate
mtxo = np.zeros([len(set(ndf[tval])), len(set(ndf['crisk']))])
for i in range(mtxo.shape[0]):
    for j in range(mtxo.shape[1]):
        tmp = ndf.loc[(ndf[tval] == i + 1) & # (ndf['year'] == 2014) & 
                      (ndf['crisk'] == j + 1), 'orn1']
        mtxo[i][j] = np.nanpercentile(tmp, q = 50)
        
# matrix of county-year proportion
mtxp = np.zeros([len(set(ndf[tval])), len(set(ndf['crisk']))])
for i in range(mtxo.shape[0]):
    for j in range(mtxo.shape[1]):
        tmp = ndf.loc[(ndf[tval] == i + 1) & # (ndf['year'] == 2014) & 
                      (ndf['crisk'] == j + 1), :].shape[0]
        tmp = round(tmp / ndf.shape[0], 3) * 100
        mtxp[i][j] = tmp


# set parameters of heatmap
vmin, vmax = math.floor(min([mtxi.min(), mtxo.min()])), math.ceil(max([mtxi.max(), mtxo.max()]))
xticklabels = ['Low', 'Limited', 'Moderate', 'High']


# inflow rate heatmap
hmi = sns.heatmap(mtxi, annot = True, fmt = ".1f", cmap = 'coolwarm', 
                  vmin = vmin, vmax = vmax,
                  xticklabels = xticklabels, yticklabels = yticklabels)
hmi.set(xlabel = 'Climate Risk', ylabel = 'Social Vulnerability-Resilience Index', 
        title = 'Migration Inflow Rates')
hmi.set_xticklabels(hmi.get_xticklabels(), rotation = 0)
hmi.set_yticklabels(hmi.get_yticklabels(), rotation = 0)
# output
hmi.figure.tight_layout()
hmi.figure.savefig('Climate-c2c-IRS/summary/heatmap_4field_inflow.png')

# outflor rate heatmap
hmo = sns.heatmap(mtxo, annot = True, fmt = ".1f", cmap = 'coolwarm', 
                  vmin = vmin, vmax = vmax,
                  xticklabels = xticklabels, yticklabels = yticklabels)
hmo.set(xlabel = 'Climate Risk', ylabel = 'Social Vulnerability-Resilience Index', 
        title = 'Migration Outflow Rates')
hmo.set_xticklabels(hmo.get_xticklabels(), rotation = 0)
hmo.set_yticklabels(hmo.get_yticklabels(), rotation = 0)
# output
hmo.figure.tight_layout()
hmo.figure.savefig('Climate-c2c-IRS/summary/heatmap_4field_outflow.png')

# county-year proportion
hmp = sns.heatmap(mtxp, annot = True, fmt = ".1f", cmap = 'coolwarm', 
                  xticklabels = xticklabels, yticklabels = yticklabels)
hmp.set(xlabel = 'Climate Risk', ylabel = 'Social Vulnerability-Resilience Index', 
        title = 'Percentage of County-Year')
hmp.set_xticklabels(hmp.get_xticklabels(), rotation = 0)
hmp.set_yticklabels(hmp.get_yticklabels(), rotation = 0)
# output
hmp.figure.savefig('Climate-c2c-IRS/summary/heatmap_4field_size.png')



"""
dyad-level
"""




"""
example county
"""

# load data
ndf = pd.read_csv('Climate-c2c-IRS/node_allvar_long_opt2.csv')
edf = pd.read_csv('Climate-c2c-IRS/dyad_migration_climate_socvul.csv')

# inspect paired Texas county
edf.columns
edf['stfips_i'] = edf['ctyfips_i'] // 1000
edf['stfips_j'] = edf['ctyfips_j'] // 1000
set(edf['stfips_i'])
# inspect connections with Texas counties
t0 = edf.loc[(edf['stfips_i'] == 48) | (edf['stfips_j'] == 48), :]
# 48121, 22061, connected in 2011

ndf.columns
# 48121
ndf.loc[ndf['ctyfips'] == 48121]
ndf.loc[(ndf['ctyfips'] == 48121) & (ndf['year'] == 2011)]
ndf.iloc[22941, :]

# 22061
ndf.loc[ndf['ctyfips'] == 22061]
ndf.loc[(ndf['ctyfips'] == 22061) & (ndf['year'] == 2011)]
ndf.iloc[9981, :]

ndf.iloc[[9981, 22941], :].transpose()


