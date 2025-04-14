#'Inspect overall distributions of climate risks (compounds & natural disasters)
#'ASA 2024, Climate risks & place resilience
#'
#'V3: modified based on inspect_climate_v2.R
#'Changes:
#'  1.reconstruct hot-dry and cold-wet
#'  2.reconstruct natural disaster
#'
#'V4: modified based on inspect_climate_v3.R
#'Changes:
#'  1.remove redundant code for non-output tested binaries
#'  2.remove the part checking distributions after construct because that was
#'    aligned with the removed binaries
#'
#'Xingyun Wu
#'
#'Initial: 8/16/2024
#'Intermediate 1: 8/19/2024
#'Intermediate 2: 8/23/2024
#'Latest: 8/29/2024

library(dplyr)
library(tidyr)
library(haven)
library(ggplot2)

options(scipen = 999)

setwd('~/OneDrive - Johns Hopkins/ra/HPC_climate')
setwd('C:/Users/xwu70/OneDrive - Johns Hopkins/ra/HPC_climate')


###########
# raw data
###########

#=======================
# monthly precipitation
#=======================

prcp <- read.csv('Climate-c2c-IRS/climate/raw/cdc_precipitation/precipitation_measure577_1990to2022.csv')
colnames(prcp)

# check availability
sprcp <- prcp %>% group_by(geoId, parentTemporalId) %>% summarise(n = n()) %>% 
  pivot_wider(names_from = parentTemporalId, values_from = n)
# available counties
dim(sprcp)
2 %in% sprcp$geoId
15 %in% sprcp$geoId
# number of available months by year
summary(sprcp[, 2:dim(sprcp)[2]])
NA %in% sprcp
min(sprcp[, 2:dim(sprcp)[2]])

class(prcp$temporal)
class(prcp$temporalId)


load('Climate-c2c-IRS/climate/raw/cdc_heat/daily/county1001.rda')


#################
# processed data
#################

# load my processed full climate data
clmt <- read.csv('data/processed_data/climate_all_2010to2021.csv')
length(unique(clmt$ctyfips))
clmt <- clmt[which(!(clmt$ctyfips %/% 1000 %in% c(2, 15))),]
# load Lingxin's harmonized & compiled data
vdt <- read_dta('Climate-c2c-IRS/IC2S2 analysis/v_all_r.dta')
colnames(vdt)
length(unique(vdt$fips)) # 3141
vdt <- vdt[which(!(vdt$fips %/% 1000 %in% c(2, 15))),]

# check fips
setdiff(unique(clmt$ctyfips), unique(vdt$fips))
setdiff(unique(vdt$fips), unique(clmt$ctyfips))

#'time range should be [2011, 2020] to allow for pre- and post-year inspect of
#'place resilience


###########################
# reconstruct CDC compound
###########################

colnames(clmt)
summary(clmt$hte_abv99)
summary(clmt$prcp_abv90)


#=========
# hot-dry
#=========

## new thought: use drought for dry-condition to replace precipitation
clmt$hd_hte99d5_drt2 <- ifelse(clmt$hte_abv99 > 5 & clmt$usdm_pct_cum2_severe > 5, 1, 0)
t(clmt %>% group_by(year) %>% summarise(n = length(which(hd_hte99d5_drt2 > 0))))
#'year 2010 2011 2012 2013 2014 2015 2016 2017 2018  2019  2020  2021
#'n     233  651  170   16    0   75    3    2   19    17   107   139
length(clmt[which(clmt$hd_hte99d5_drt2 > 0), 'ctyfips']) # 1432 county-year
length(unique(clmt[which(clmt$hd_hte99d5_drt2 > 0), 'ctyfips'])) # 1177 unique counties

clmt$hd_hte99d7_drt2 <- ifelse(clmt$hte_abv99 > 7 & clmt$usdm_pct_cum2_severe > 5, 1, 0)
t(clmt %>% group_by(year) %>% summarise(n = length(which(hd_hte99d7_drt2 > 0))))
#'year 2010 2011 2012 2013 2014 2015 2016 2017 2018  2019  2020  2021
#'n     122  398   60    8    0   21    0    1    0    10    34    52
length(clmt[which(clmt$hd_hte99d7_drt2 > 0), 'ctyfips']) # 706 county-year
length(unique(clmt[which(clmt$hd_hte99d7_drt2 > 0), 'ctyfips'])) # 644 unique counties

clmt$hd_hte99d5_drt3 <- ifelse(clmt$hte_abv99 > 5 & clmt$usdm_pct_cum3_extreme > 5, 1, 0)
t(clmt %>% group_by(year) %>% summarise(n = length(which(hd_hte99d5_drt3 > 0))))
#'year 2010 2011 2012 2013 2014 2015 2016 2017 2018  2019  2020  2021
#'n      53  414  136    3    0   35    0    2   18     3    62   121
length(clmt[which(clmt$hd_hte99d5_drt3 > 0), 'ctyfips']) # 847 county-year
length(unique(clmt[which(clmt$hd_hte99d5_drt3 > 0), 'ctyfips'])) # 766 unique counties

clmt$hd_hte99d7_drt3 <- ifelse(clmt$hte_abv99 > 7 & clmt$usdm_pct_cum3_extreme > 5, 1, 0)
t(clmt %>% group_by(year) %>% summarise(n = length(which(hd_hte99d7_drt3 > 0))))
#'year 2010 2011 2012 2013 2014 2015 2016 2017 2018  2019  2020  2021
#'n      32  265   58    0    0    8    0    1    0     1    23    47
length(clmt[which(clmt$hd_hte99d7_drt3 > 0), 'ctyfips']) # 435 county-year
length(unique(clmt[which(clmt$hd_hte99d7_drt3 > 0), 'ctyfips'])) # 418 unique counties


#====
# ND
#====

epa <- clmt[which(clmt$year %in% 2010:2019), 
            c('ctyfips', 'year', 'hurricane', 'tropical_storm', 
              'tornado', 'drought', 'landslide', 'wildfire')]
summary(epa[, 3:dim(epa)[2]]) # tornado & landslide not available 2019


epa %>% group_by(year) %>% summarise(n_cty = n())
colnames(epa)


# annual cumulative
epa$nd_cum <- rowSums(epa[, 3:dim(epa)[2]], na.rm = T)

# count of ND exposed
for(i in 1:dim(epa)[1]){
  epa[i, 'nd_cnt'] <- length(which(epa[i, c('hurricane', 'tropical_storm', 'tornado', 
                                            'drought', 'landslide', 'wildfire')] > 0))
}
# inspect
summary(epa$nd_cnt)
#'   Min. 1st Qu.  Median    Mean 3rd Qu.    Max. 
#'0.0000  0.0000  1.0000  0.7516  1.0000  5.0000 
epa %>% group_by(year, nd_cnt) %>% summarise(n = n()) %>%
  pivot_wider(names_from = nd_cnt, values_from = n)
#'   year   `0`   `1`   `2`   `3`   `4`   `5`
#'  2010  1571  1218   310     9    NA    NA
#'  2011  1024  1402   614    62     6    NA
#'  2012   641  1677   689    88    13    NA
#'  2013  1116  1497   473    21     1    NA
#'  2014  1722  1105   276     5    NA    NA
#'  2015  1738   928   416    25     1    NA
#'  2016  1351  1123   506   109    19    NA
#'  2017  1346  1077   447   201    36     1
#'  2018  1252  1154   560   122    20    NA
#'  2019  1972   995   136     5    NA    NA

# top ND
colnames(epa)
nd_item <- c('hurricane', 'tropical_storm', 'tornado', 'drought', 
             'landslide', 'wildfire')
for(i in 1:dim(epa)[1]){
  if(max(epa[i, nd_item], na.rm = T) > 0){
    epa[i, 'nd_top'] <- nd_item[which.max(epa[i, nd_item])]
    epa[i, 'nd_max'] <- epa[i, nd_item[which.max(epa[i, nd_item])]]
  }
  else{
    epa[i, 'nd_top'] <- 'none'
    epa[i, 'nd_max'] <- 0
  }
}
# inspect
epa %>% group_by(year, nd_top) %>% summarise(n = n()) %>%
  pivot_wider(names_from = nd_top, values_from = n)
#'year drought hurricane landslide  none tornado tropical_storm wildfire
#'2010     870        10         3  1571     372             79      203
#'2011    1229       160         1  1024     382            102      210
#'2012    2024        85         2   641      79            167      110
#'2013    1534        NA        NA  1116     239            152       67
#'2014     783       126         3  1722     342              8      124
#'2015     862        NA        NA  1738     318             86      104
#'2016    1128       216        NA  1351     215             24      174
#'2017     793       170        NA  1346     358            225      216
#'2018    1000       259         2  1252     235            211      149
#'2019     870       180        NA  1972      NA             86       NA


# hurricane
epa %>% group_by(year) %>% 
  summarise(n = length(which(hurricane >= 30))) %>%
  pivot_wider(names_from = year, values_from = n)
#'  `2010` `2011` `2012` `2013` `2014` `2015` `2016` `2017` `2018` `2019`
#'      6    157     77      0    103      0    216    172    272    166

# tropical storm
epa %>% group_by(year) %>% 
  summarise(n = length(which(tropical_storm >= 30))) %>%
  pivot_wider(names_from = year, values_from = n)
#'  `2010` `2011` `2012` `2013` `2014` `2015` `2016` `2017` `2018` `2019`
#'     69    132    187    137      4     73    195    309    354     99

# tornado ==> not good
epa %>% group_by(year) %>% 
  summarise(n = length(which(tornado >= 5))) %>%
  pivot_wider(names_from = year, values_from = n)
#'  `2010` `2011` `2012` `2013` `2014` `2015` `2016` `2017` `2018` `2019`
#'      4     13      3      1      0      0      0      3      1      0

# drought
epa %>% group_by(year) %>% 
  summarise(n = length(which(drought >= 30))) %>%
  pivot_wider(names_from = year, values_from = n)
#'  `2010` `2011` `2012` `2013` `2014` `2015` `2016` `2017` `2018` `2019`
#'     46    747   1190    798    395    295    187     68    284     27
epa %>% group_by(year) %>% 
  summarise(n = length(which(drought >= 80))) %>%
  pivot_wider(names_from = year, values_from = n)
#'  `2010` `2011` `2012` `2013` `2014` `2015` `2016` `2017` `2018` `2019`
#'      0    222    175    155    175     79     34      0     47      0
epa %>% group_by(year) %>% 
  summarise(n = length(which(drought >= 90))) %>%
  pivot_wider(names_from = year, values_from = n)
#'  `2010` `2011` `2012` `2013` `2014` `2015` `2016` `2017` `2018` `2019`
#'     0    135    117    116    132     74     27      0     34      0

# landslide
epa %>% group_by(year) %>% 
  summarise(n = length(which(landslide > 0))) %>%
  pivot_wider(names_from = year, values_from = n)
#'  `2010` `2011` `2012` `2013` `2014` `2015` `2016` `2017` `2018` `2019`
#'      3      1      2      2      4      2      2      4     10      0

# wildfire
epa %>% group_by(year) %>% 
  summarise(n = length(which(wildfire > 0))) %>%
  pivot_wider(names_from = year, values_from = n)
#'  `2010` `2011` `2012` `2013` `2014` `2015` `2016` `2017` `2018` `2019`
#'    310    383    395    268    295    314    418    390    377      0
epa %>% group_by(year) %>% 
  summarise(n = length(which(wildfire > 5))) %>%
  pivot_wider(names_from = year, values_from = n)
#'  `2010` `2011` `2012` `2013` `2014` `2015` `2016` `2017` `2018` `2019`
#'      3     28     22      7      5     10      7     24     15      0


#=========
# HD + ND
#=========

## merge
setequal(unique(vdt$fips), unique(clmt$ctyfips))
clmt_out <- vdt[, c('fips', 'year')] %>%
  left_join(clmt[, c('ctyfips', 'year', 'hd_hte99d5_drt2', 'hd_hte99d7_drt2',
                     'hd_hte99d5_drt3', 'hd_hte99d7_drt3')],
            by = c('fips' = 'ctyfips', 'year' = 'year')) %>%
  left_join(epa[, c('ctyfips', 'year', 'nd_cum', 'nd_cnt', 'nd_top', 'nd_max')],
            by = c('fips' = 'ctyfips', 'year' = 'year'))
# output
write.csv(clmt_out, file = 'data/processed_data/cliamte_hd_nd.csv', row.names = F)

## merge previously organized data with constructed binaries
clmt <- read.csv('data/processed_data/climate_all_2010to2021.csv')
head(colnames(clmt))
head(colnames(clmt_out))
clmt <- clmt %>% 
  left_join(clmt_out, by = c('ctyfips' = 'fips', 'year' = 'year'))
tail(colnames(clmt), n = 10)
# streamline column name for FIPS
head(colnames(clmt))
colnames(clmt)[4] <- 'fips'
head(colnames(clmt))
# output to shared folder
write.csv(clmt, row.names = F,
          file = 'Climate-c2c-IRS/climate/climate_all_2010to2021_withHDND.csv')

