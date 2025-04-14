#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 24 10:52:41 2024

Post-estimation analysis of block assignemnt after GRDPG


@author: Xingyun Wu, Johns Hopkins University

Initial: 6/24/2024
Latest: 6/24/2024
"""

import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# work directory
os.chdir('/Users/xywu/OneDrive - Johns Hopkins/ra/HPC_climate')
os.chdir('C:/Users/xwu70/OneDrive - Johns Hopkins/ra/HPC_climate')

# load data
egdf = pd.read_stata('Climate-c2c-IRS/processed data/unzipped/e_out_all.dta')
vtxdf = pd.read_stata('Climate-c2c-IRS/processed data/unzipped/v_all_h.dta')
block = pd.read_csv('Climate-c2c-IRS/results/block_1.csv')


"""
viz with map
"""

# auxiliary function to draw map of specified year and climate indicator
def get_map(geodf, blkdf, variable, color_scheme = 'Set1', 
            plt_title = None, vmin = None, vmax = None):
    '''
    Input:
        geodf: data frame for geographic info for the map
        blkdf: data frame for climate data, long-form of county-year
        variable: climate variable to draw
        plt_title: string to display as the title of map
    
    Output:
        fig: a matplotlib object as the map
    '''
    ## Step 1: data processing
    
    # standardize column names
    geodf.rename(columns = {'STATEFP': 'stfips', 'COUNTYFP': 'ctyfips', \
                            'GEOID': 'geoId'}, inplace = True)
    geodf['geoId'] = geodf['geoId'].astype('int')

    # select US continent states + DC
    geodf['stfips'] = geodf['stfips'].astype(int)
    geodf = geodf[geodf['stfips'] < 60]
    # exclude Alaska
    geodf = geodf[geodf['stfips'] != 2]
    # exclude Hawaii
    geodf = geodf[geodf['stfips'] != 15]

    # merge climate indicator of specified year
    cnt_pre = geodf.shape[0]
    geodf = geodf.merge(blkdf, how = 'left',
                        left_on = 'geoId', right_on = 'fips')
    geodf['block'] = geodf['block'].astype('Int64')
    cnt_post = geodf.shape[0]
    # stop if number of counties unmatched
    if cnt_pre != cnt_post:
        print('unmatched number of counties between map and block data: {} before merge, {} after merge'.format(cnt_pre, cnt_post))
        return
    
    # get customized color
    if vmin == None or vmax == None:
        vmin, vmax = geodf[variable].min(), geodf[variable].max()
    # # geodf = makeColorColumn(geodf, variable, vmin, vmax, color_scheme = color_scheme)
    # define range of values for color mapper
    norm = mcolors.Normalize(vmin = vmin, vmax = vmax, clip = True)
    # define color-mapping function
    mapper = plt.cm.ScalarMappable(norm = norm, 
                                   cmap = plt.colormaps[color_scheme]) # cmap=plt.cm.BuPu
    # map colors according to variable value
    geodf['value_determined_color'] = geodf[variable].apply(lambda x: mcolors.to_hex(mapper.to_rgba(x)))

    # create "visframe" as a re-projected gdf using EPSG 2163 for CONUS
    # clrmap = color_scheme
    visframe = geodf.to_crs('epsg:2163')
    
    
    ## Step 2: plot
    
    # initiate figure and axes
    fig, ax = plt.subplots(1, figsize=(18, 14))
    # remove the axis box around the vis
    ax.axis('off')

    # set the font for the visualization to Helvetica
    hfont = {'fontname': 'Arial'} # 'Helvetica'

    # add a title and annotation
    if plt_title == None:
        plt_title = 'Non-specified'
    ax.set_title('{}: {}'.format(plt_title, variable), **hfont, 
                 fontdict={'fontsize': '42', 'fontweight' : '1'})

    # Create colorbar legend
    fig = ax.get_figure()
    # add colorbar axes to the figure
    # This will take some iterating to get it where you want it [l,b,w,h] right
    # l:left, b:bottom, w:width, h:height; in normalized unit (0-1)
    cbax = fig.add_axes([0.89, 0.21, 0.03, 0.31])
    # set legend title
    cbax.set_title('Precipitation', **hfont, fontdict={'fontsize': '15', 'fontweight' : '0'})
    # add color scale
    sm = plt.cm.ScalarMappable(cmap = color_scheme, \
                     norm = plt.Normalize(vmin = vmin, vmax = vmax))
    # reformat tick labels on legend
    sm._A = []
    # comma_fmt = FuncFormatter(lambda x, p: format(x/100, '.0%'))
    fig.colorbar(sm, cax=cbax) #, format=comma_fmt)
    cbax.tick_params(labelsize = 16)
    # annotate the data source, date of access, and hyperlink
    ax.annotate("Data: IRS", xy=(0.22, .085), xycoords='figure fraction', fontsize=14, color='#555555')

    # create map: add color by county as specified in visframe
    for row in visframe.itertuples():
        # if row.state not in ['AK','HI']:
        vf = visframe[visframe.geoId == row.geoId]
        c = geodf[geodf.geoId == row.geoId][0:1].value_determined_color.item()
        vf.plot(color = c, linewidth = 0.8, ax = ax, edgecolor = '0.8')

    # output
    fig.savefig('Climate-c2c-IRS/results/map_{}_{}.png'.format(plt_title, variable),
                dpi = 400, bbox_inches = "tight")
    return fig


# load map
gdf = gpd.read_file('data/cb_2018_us_county_500k')
gdf.columns

# check for FIPS differences
lcty = sorted(list(set(vtxdf.loc[(vtxdf['fips'] // 1000 != 2) & 
                                 (vtxdf['fips'] // 1000 != 15), 'fips'])))
gcty = list(gdf['GEOID'].astype('int'))
gcty = [x for x in gcty if x // 1000 < 60 and x // 1000 not in [2, 15]]
[x for x in gcty if x not in lcty]
[x for x in lcty if x not in gcty]


# plot precipitation
tmin, tmax = block['block'].min(), block['block'].max()
plt.colormaps['Set1']


# draw map: all counties
bmap = get_map(gdf, block, 'block', plt_title = 'counties',
               vmin = tmin, vmax = tmax)

# block 4: contain NYC, LA
bmap = get_map(gdf, block[block['block'] == 4], 'block', plt_title = 'block4',
               vmin = tmin, vmax = tmax)



"""
summary stats
"""

# check vertex availability
vtxdf.shape
# fill missing in rural-urban continnium
set(vtxdf.loc[vtxdf['rucc'].notnull(), 'rucc'])
vtxdf['rucc'].fillna(0, inplace = True)
vtxdf['rucc'] = vtxdf['rucc'].astype('int')

# specify block as int
block['block'] = block['block'].astype(int)

# merge network1 block with index0 covariates
vtx0 = vtxdf.loc[(vtxdf.index_k == 0) & (vtxdf['fips'] // 1000 != 2) &
                 (vtxdf['fips'] // 1000 != 15), :].merge(block[['fips', 'block']], 
                                                         how = 'outer', on = 'fips')
# check dimension
vtx0.shape
print(list(vtx0.columns))
# crosstab: block * rucc
vtx0['block'].fillna(-1, inplace = True)
vtx0['block'] = vtx0['block'].astype(int)
t0 = pd.crosstab(vtx0['block'], vtx0['rucc'])

# merge network1 block with index1 covariates
vtx1 = vtxdf.loc[(vtxdf.index_k == 1) & (vtxdf['fips'] // 1000 != 2) &
                 (vtxdf['fips'] // 1000 != 15), :].merge(block[['fips', 'block']], 
                                                         how = 'outer', on = 'fips')
vtx1.shape
vtx0.equals(vtx1) # False

# define variables to inspect
vtx0['prcp_prop_abv95'] = vtx0['prcp_abv95'] / 365
vtx0['hte_prop_abv95'] = vtx0['hte_abv95'] / 365
vtx0['drt_severe'] = vtx0['drought_severe'] / 100
d_var = dict()
d_var['clmt'] = ['prcp_prop_abv95', 'hte_prop_abv95', 'drt_severe']
d_var['age'] = ['age_under5', 'age5_9', 'age10_14', 'age15_19', 'age20_24', 
                'age24_29', 'age30_34', 'age35_39', 'age40_44', 'age45_49', 
                'age50_54', 'age55_59', 'age60_64', 'age65_69', 'age70_74',
                'age75_79', 'age80_84', 'age85_above']
d_var['edu'] = ['edu1', 'edu2', 'edu3', 'edu4']
d_var['inc'] = ['hhinc_pct1', 'hhinc_pct2', 'hhinc_pct3', 'hhinc_pct4', 
                'hhinc_pct5', 'hhinc_pct6', 'hhinc_pct7', 'hhinc_pct8', 
                'hhinc_pct9' ,'hhinc_pct10', 'hhinc_pct11', 'hhinc_pct12', 
                'hhinc_pct13', 'hhinc_pct14', 'hhinc_pct15']
d_var['crwd'] = ['occupant1', 'occupant2', 'occupant3', 'occupant4', 'occupant5']

# obtain summary
t1 = vtx0[['block'] + d_var['age']].groupby('block').describe().T
t2 = vtx0[['block'] + d_var['edu']].groupby('block').describe().T
t3 = vtx0[['block'] + d_var['inc']].groupby('block').describe().T
t4 = vtx0[['block'] + d_var['crwd']].groupby('block').describe().T
t5 = vtx0[['block'] + d_var['clmt']].groupby('block').describe().T
# # write index0 distributions
# with pd.ExcelWriter('results/net1block_vertex0_summary.xlsx', 
#                     engine='xlsxwriter') as writer:
#     t0.to_excel(writer, sheet_name = 'rucc')
#     t1.to_excel(writer, sheet_name = 'age')
#     t2.to_excel(writer, sheet_name = 'edu')
#     t3.to_excel(writer, sheet_name = 'inc') 
#     t4.to_excel(writer, sheet_name = 'crwd') 
#     t5.to_excel(writer, sheet_name = 'clmt')       


"""
viz with network
"""

import networkx as nx
from pyvis.network import Network

G = nx.from_pandas_edgelist(
    egdf.iloc[:, :2],
    source = 'y2fips',
    target = 'y1fips',
    create_using = nx.Graph
)

# initiate
nt = Network('500px', '500px', notebook = False)
nt.from_nx(G)
nt.show('results/nx.html', notebook = False)

# load full geo loc df
gpos = pd.read_table('data/other_source/2019_Gaz_counties_national.txt', 
                     sep = '\t', engine = 'python')
list(gpos.columns)
gpos.columns = ['stabbr', 'id', 'ANSICODE', 'ctyname', 'ALAND', 'AWATER', 
                'ALAND_SQMI', 'AWATER_SQMI', 'latitude', 'longitude']
list(gpos.columns)
# slice
[x for x in gpos.id if x not in list(set(vtxdf.fips))]
egdf.columns
lcty2 = sorted(list(set(egdf.y2fips).union(egdf.y1fips)))
len(lcty2) # 3054 counties
gpos[gpos['id'].isin(lcty2)].shape # 3054 counties
gpos = gpos[gpos['id'].isin(lcty2)]
# output
gpos.to_csv('data/processed_data/2019_Gaz_counties_national_converted.csv', index = False)
