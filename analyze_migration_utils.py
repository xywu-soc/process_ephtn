#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 24 16:23:28 2024

@author: xywu
"""

import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
# from matplotlib.ticker import FuncFormatter
import matplotlib.colors as mcolors
import plotly.express as px
import plotly.io as pio
import itertools



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
    rv['prop'] = round(rv['count'] / df.shape[0], precision)
    
    # round if needed
    for col in ['mean', 'std']:
        rv[col] = round(rv[col], precision).apply(lambda x: format(float(x), ".{}f".format(precision)))
    
    # output
    rv.reset_index(drop = False, inplace = True)
    return rv



def get_dyad_lineplot(df, varlist, statlist, timevar, plt_title, ylim = None):
    '''
    '''
    slst = []
    if ylim == None:
        ylim = [0, 3]
    if ylim[1] - ylim[0] <= 1:
        ytick = 0.1
    else:
        ytick = 0.5
    
    # plot
    fig, axs = plt.subplots(1, len(varlist), figsize=(10 * len(varlist), 10))
    fig.suptitle('Dyad-Level Measure: {}'.format(plt_title), fontsize = 20)
    cnt = 0
    for var in varlist:
        slst.append(get_summary(df, col = var, precision = 3, group_by = timevar))
        for tmp_stat in ['median', 'mean']:
            axs[cnt].plot(slst[cnt].loc[:, timevar], 
                          slst[cnt].loc[:, tmp_stat].astype(float), 
                          label = 'Stats = ' + tmp_stat)
            axs[cnt].set_xticks(np.arange(2, 10, 1))
            axs[cnt].set_yticks(np.arange(ylim[0], ylim[1], ytick))
            axs[cnt].set_ylim(ylim[0], ylim[1])
        axs[cnt].set_title(['Household', 'Individual', 'AGI'][cnt])
        cnt += 1
    handles, labels = axs[-1].get_legend_handles_labels()
    fig.legend(handles, labels, loc = 'center left', bbox_to_anchor=(1, 0.5))

    # summary table
    for i in range(len(slst)):
        slst[i]['measure'] = varlist[i]
    sdf = pd.concat(slst, axis = 0, ignore_index = True)
        
    return fig, sdf


    
def get_bivar_lineplot(df, varlist, timevar, netvar, stats, plt_title, 
                       ylim = None, ylab = None):
    '''
    
    '''
    
    slst = []
    if ylim == None:
        ylim = [0, 3]
    if ylim[1] - ylim[0] <= 1:
        ytick = 0.1
    else:
        ytick = 0.5
    
    # plot
    fig, axs = plt.subplots(1, len(varlist), figsize=(10 * len(varlist), 10))
    fig.suptitle('Dyad-Level Measure: {}'.format(plt_title), fontsize = 20)
    cnt = 0
    for var in varlist:
        slst.append(get_summary(df, col = netvar, precision = 3, group_by = [timevar, var]))
        for cat in list(set(slst[cnt][var])):
            axs[cnt].plot(slst[cnt].loc[slst[cnt][var] == cat, timevar], 
                          slst[cnt].loc[slst[cnt][var] == cat, stats].astype(float), 
                          label = 'Climate rank diff = ' + str(cat))
            axs[cnt].set_xticks(np.arange(2, 10, 1))
            axs[cnt].set_yticks(np.arange(ylim[0], ylim[1], ytick))
            axs[cnt].set_ylim(ylim[0], ylim[1])
            axs[cnt].set_ylabel(ylab)
        axs[cnt].set_title(['Precipitation Rank', 'Heat Event Rank'][cnt])
        cnt += 1
    handles, labels = axs[-1].get_legend_handles_labels()
    fig.legend(handles, labels, loc = 'center left', bbox_to_anchor=(1, 0.5))

    # # summary table
    # for i in range(len(slst)):
    #     slst[i]['measure'] = varlist[i]
    # sdf = pd.concat(slst, axis = 0, ignore_index = True)
        
    return fig, slst
    
    

def get_trivar_lineplot(df, varlist, timevar, netvar, stats, plt_title, 
                       ylim = None, ylab = None):
    '''
    
    '''
    
    slst = []
    if ylim == None:
        ylim = [0, 3]
    if ylim[1] - ylim[0] <= 1:
        ytick = 0.1
    else:
        ytick = 0.5
    
    # plot
    fig, axs = plt.subplots(2, len(varlist), figsize=(10 * len(varlist), 10))
    fig.suptitle('Dyad-Level Measure: {}'.format(plt_title), fontsize = 20)
    cnt = 0
    for var in varlist:
        slst.append(get_summary(df, col = netvar, precision = 3, group_by = [timevar, var]))
        for cat in list(set(slst[cnt][var])):
            axs[cnt].plot(slst[cnt].loc[slst[cnt][var] == cat, timevar], 
                          slst[cnt].loc[slst[cnt][var] == cat, stats].astype(float), 
                          label = 'Climate rank diff = ' + str(cat))
            axs[cnt].set_xticks(np.arange(2, 10, 1))
            axs[cnt].set_yticks(np.arange(ylim[0], ylim[1], ytick))
            axs[cnt].set_ylim(ylim[0], ylim[1])
            axs[cnt].set_ylabel(ylab)
        axs[cnt].set_title(['Precipitation Rank', 'Heat Event Rank'][cnt])
        cnt += 1
    handles, labels = axs[-1].get_legend_handles_labels()
    fig.legend(handles, labels, loc = 'center left', bbox_to_anchor=(1, 0.5))

    # # summary table
    # for i in range(len(slst)):
    #     slst[i]['measure'] = varlist[i]
    # sdf = pd.concat(slst, axis = 0, ignore_index = True)
        
    return fig, slst


def get_3d_scatter(df, migration, climate, socvul, plt_title):
    '''
    Input:
        df: data frame for dyad with covariates
        migration: str for variable name of migration
        climate: str for variable name of climate
        socvul: str for variable name of social vulnerability
    '''
    
    fig = px.scatter_3d(df, title = plt_title, color = climate,
                        x = climate, 
                        y = socvul, 
                        z = migration)
    # Save the plot as an interactive HTML file
    pio.write_html(fig, file = '{}.html'.format(plt_title))
    
    return(fig)

