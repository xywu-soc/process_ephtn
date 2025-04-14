#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 21 17:17:21 2024



@author: Xingyun Wu, Johns Hopkins University
"""


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# from matplotlib.ticker import FuncFormatter
import matplotlib.colors as mcolors
import itertools



"""
functions to process data
"""


def get_summary(df, col = 'dataValue', precision = 0, group_by = None):
    '''
    auxiliary function to get summary statistics
    
    input: 
        df: long-form data in pandas dataframe, 
            targetted variable named 'dataValue'
        col: string for targetted variable name
        precision: integer for number of digits to display
        group_by: string for targetted group_by variable
        
    output: 
        rv: pandas dataframe of summary statistics
    '''
    # groupby criteria
    if col == 'dataValue':
        item_groupby = ['temporalId', 'threshold']
    elif group_by != None:
        item_groupby = group_by
    else:
        item_groupby = 'year'
    
    # get summary stats
    rv = pd.DataFrame(df.groupby(item_groupby).agg(
        count = (col, np.size),
        skew = (col, 'skew'),
        # kurt = (col, lambda x: pd.DataFrame.kurt(x)),
        mean = (col, 'mean'),
        std = (col, 'std'),
        vmin = (col, 'min'),
        pct25 = (col, lambda x: np.nanpercentile(x, q = 25)),
        median = (col, lambda x: np.nanpercentile(x, q = 50)),
        pct75 = (col, lambda x: np.nanpercentile(x, q = 75)),
        vmax = (col, 'max')
    ))
    
    # round if needed
    for col in ['mean', 'std']:
        rv[col] = round(rv[col], precision).apply(lambda x: format(float(x), ".{}f".format(precision)))
    
    # output
    rv.reset_index(drop = False, inplace = True)
    return rv



def reshape_variable(df, variable):
    '''
    Reshape long-form data into wide-form on selected variable
    
    Input:
        df: data frame of climate data, long-form
        variable: string to indicate variable name to reshape
    
    Output:
        rv: data frame of climate data, wide-form fo selected variable
    '''
    # reshape targetted variable
    rvdf = pd.DataFrame(df.pivot(index = ['stfips', 'stname', 'ctyfips', 'ctyname'], 
                                 columns = 'year', values = variable))
    for col in list(rvdf.columns):
        rvdf.rename(columns = {col: variable + '_' + str(col)}, inplace = True)
    rvdf.reset_index(drop = False, inplace = True)
    
    # summarize trend
    rvsum = get_summary(df, col = variable, precision = 0, group_by = 'ctyfips')
    
    # output
    print('Dimension of processed df: {}, {}'.format(rvdf.shape[0], rvdf.shape[1]))
    return rvdf, rvsum



def reshape_varlist(df, varlist):
    '''
    Wrapper function to implement reshape_variable() on a list of variables
    
    Input:
        df: data frame for climate data
        varlist: a list of strings for selected variables
    '''
    l_df = []
    l_sum = []
    for tvar in varlist:
        tdf, tsum = reshape_variable(df, tvar)
        l_df.append(tdf)
        tsum.columns = list(tsum.columns)[:2] + [tvar + '_' + x for x in list(tsum.columns)[2:]]
        tsum.drop(labels = 'count', axis = 1)
        l_sum.append(tsum)
    
    # compile
    rvdf = l_df[0]
    rvsum = l_sum[0]
    for i in range(2, len(l_df)):
        rvdf = rvdf.merge(l_df[i], how = 'outer', on = ['stfips', 'stname', 'ctyfips', 'ctyname'])
        rvsum = rvsum.merge(l_sum[i], how = 'outer', on = ['ctyfips', 'count'])
    
    return rvdf, rvsum



def get_dyad(df, year, variable):
    '''
    Input:
        df: data frame for climate or social vulnerability meaasures
        year: integer for the year to process
        variable: string for selected variable
    
    Output:
        rv: data frame with 4 columns: ctyfips_i, ctyfips_j, variable, year
    '''
    
    # get combinations
    tdf = df[df['year'] == year]
    rv = list(itertools.permutations(tdf[['ctyfips', variable]].values.tolist(), 2))
    rv = [x[0] + x[1] for x in rv]
    
    # convert to data frame
    rv = pd.DataFrame(rv, columns = ['ctyfips_i', variable + '_i', 
                                     'ctyfips_j', variable + '_j'])
    # obtain differences
    rv[variable + '_diff'] = rv[variable + '_i'] - rv[variable + '_j']
    rv.rename(columns = {variable + '_diff': variable}, inplace = True)
    # keep necessary columns
    rv = rv[['ctyfips_i', 'ctyfips_j', variable]]
    # add year
    rv['year'] = year
    
    # output
    return rv



"""
functions to plot
"""


def get_histogram(df, time_range, variable, xmax = 100, ymax = 800, nbin = 50, size = 5):
    '''
    auxiliary function to plot histogram by year
    
    input: pandas data frame
    output: plot object
    '''
    # set up figure
    fig, axs = plt.subplots(len(time_range), 4, figsize=(20, size * len(time_range)))
    fig.suptitle(variable, fontsize = 20)
    fig.text(0.5, 0.04, 'Count', ha = 'center', size = 16)
    fig.text(0.04, 0.5, 'Number of Counties', va = 'center', rotation='vertical', size = 16)
    # add subplot
    for i in range(len(time_range)):
        for j in range(4):
            k = [90, 95, 98, 99][j]
            axs[i, j].hist(df.loc[(df['temporalId'] == time_range[i]) &
                                  (df['threshold'] == k),
                                  'dataValue'],
                           bins = 50)
            axs[i, j].set_title('Year {}: {}th percentile'.format(time_range[i], k))
            axs[i, j].set_xticks(np.arange(0, 100, 10))
            axs[i, j].set_xlim(0, xmax)
            axs[i, j].set_yticks(np.arange(0, 1000, 200))
            axs[i, j].set_ylim(0, ymax)
    
    return fig



def get_national_lineplot(df, time_var, varlist, plt_title = 'Unknown'):
    '''
    auxiliary function for line plot
    '''
    # set up figure
    fig, axs = plt.subplots(nrows = 2, ncols = 2, figsize = (10 * 2, 5 * 2))
    fig.suptitle(plt_title, fontsize = 20)
    
    # iterate
    i = 0
    j = 0
    tmp_lst = sorted(set(df['pct']))
    for tmp_pct in tmp_lst:
        tdf = df[df['pct'] == tmp_pct]
        # add line
        for tmp_var in varlist:
            tmp_x = tdf[time_var]
            tmp_y = tdf[tmp_var].astype(float)
            axs[i, j].plot(tmp_x, tmp_y, label = tmp_var)
            axs[i, j].set_title(tmp_pct)
            axs[i, j].set_xticks(np.arange(2011, 2022, 1))
        # update plot tick
        if j == 0:
            j += 1
        else:
            i += 1
            j = 0

    # add legend
    handles, labels = axs[1, 1].get_legend_handles_labels()
    fig.legend(handles, labels, loc = 'center left', bbox_to_anchor=(1, 0.5))
    
    # output
    plt.show()
    return fig



def get_county_lineplot(df, varlist, plt_title = 'Unknown', var_title = 'Unknown'):
    '''
    auxiliary function for line plot
    '''
    # set up figure
    fig, axs = plt.subplots(1, figsize = (10, 15))
    fig.suptitle(plt_title, fontsize = 20)
    axs.set_title('{}: {}'.format(plt_title, var_title),
                 fontdict={'fontsize': '42', 'fontweight' : '1'})
    
    # iterate
    tmp_x = range(2011, 2022)
    for i in range(df.shape[0]):
        # tstate = df.loc[i, 'stname']
        # add line
        tmp_y = df.loc[i, varlist] #.astype(float)
        axs.plot(tmp_x, tmp_y)
        axs.set_xticks(np.arange(2011, 2022, 1))

    # add legend
    handles, labels = axs.get_legend_handles_labels()
    fig.legend(handles, labels, loc = 'center left', bbox_to_anchor=(1, 0.5))
    
    # output
    plt.show()
    return fig



# # auxiliary function for colors
# def makeColorColumn(df, variable, vmin, vmax, color_scheme):
#     '''
#     auxiliary function to map colors according to value for get_map()
#     Input:
#         df: data frame with variable to plot
#         variable: string to identify targetted variable
#         color_scheme: string for the name of color scheme
#     '''
#     # define range of values for color mapper
#     norm = mcolors.Normalize(vmin = vmin, vmax = vmax, clip = True)
#     # define color-mapping function
#     mapper = plt.cm.ScalarMappable(norm = norm, 
#                                    cmap = plt.colormaps[color_scheme]) # cmap=plt.cm.BuPu
#     # map colors according to variable value
#     df['value_determined_color'] = df[variable].apply(lambda x: mcolors.to_hex(mapper.to_rgba(x)))
#     # output
#     return df


# auxiliary function to draw map of specified year and climate indicator
def get_map(geodf, cmtdf, variable, year, color_scheme = 'BuPu', 
            plt_title = None, vmin = None, vmax = None):
    '''
    Input:
        geodf: data frame for geographic info for the map
        cmtdf: data frame for climate data, long-form of county-year
        variable: climate variable to draw
        year: int for the year to inspect
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
    geodf = geodf.merge(cmtdf.loc[cmtdf['year'] == year, ['ctyfips', variable]], 
                        left_on = 'geoId', right_on = 'ctyfips', how = 'left')
    cnt_post = geodf.shape[0]
    # stop if number of counties unmatched
    if cnt_pre != cnt_post:
        print('unmatched number of counties between map and climate data: {} before merge, {} after merge'.format(cnt_pre, cnt_post))
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
    hfont = {'fontname':'Helvetica'}

    # add a title and annotation
    if plt_title == None:
        plt_title = 'Non-specified'
    ax.set_title('{}: {}, {}'.format(plt_title, variable, str(year)), **hfont, 
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
    ax.annotate("Data: CDC EPHTN", xy=(0.22, .085), xycoords='figure fraction', fontsize=14, color='#555555')

    # create map: add color by county as specified in visframe
    for row in visframe.itertuples():
        # if row.state not in ['AK','HI']:
        vf = visframe[visframe.geoId == row.geoId]
        c = geodf[geodf.geoId == row.geoId][0:1].value_determined_color.item()
        vf.plot(color = c, linewidth = 0.8, ax = ax, edgecolor = '0.8')

    # output
    fig.savefig('summary/map_{}_{}_{}.png'.format(plt_title, variable, year),
                dpi = 400, bbox_inches = "tight")
    return fig


