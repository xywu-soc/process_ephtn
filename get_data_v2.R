#'Download data CDC EPHTrack platform
#'
#'Modified based on NLDAS > Jan 26 code for getting data > scfolder.Rmd 
#'  from Yuanhao Liu created on 1/26/2024
#'  > 8/21/2024 check for more granular heat information
#'
#'v2: remove personal token detail
#'
#'Xingyun Wu
#'
#'Initial: 8/21/2024
#'Latest: 8/21/2024

# devtools::install_github('CDCgov/EPHTrackR')
# install.packages('~/Download/EPHTracking-3.24.1.1')
library(EPHTrackR)
library(dplyr)
library(tidyr)
library(stringr)


# load token
readRenviron("~/.Renviron")
# view token
Sys.getenv("TRACKING_API_TOKEN")


# working directory
setwd('C:/Users/xwu70/OneDrive - Johns Hopkins/ra/HPC_climate/data/ephtn')
setwd('~/OneDrive - Johns Hopkins/ra/HPC_climate/data/ephtn')


##########
# inspect
##########

# available measures
msr <- list_measures()
View(msr)
# fields covered
colnames(msr)
flds <- msr %>% 
  group_by(contentAreaId, contentAreaName) %>% summarise(n = n())
View(flds)

# # precipitation & drought
# View(msr[which(msr$contentAreaId %in% c(25, 36)),])
# 
# # social vulnerability
# View(msr[which(msr$contentAreaId == 13),])

# list indicators of content area
list_indicators(content_area = 'Precipitation & Flooding')
list_indicators(content_area = 'Heat & Heat-related Illness (HRI)')

# get time unit of measures, selected field
smsr <- msr[which(msr$contentAreaId %in% c(25, 36, 11, 39, 35)),]
smsr$varname <- tolower(smsr$measureName)
smsr['unit'] <- ifelse(str_detect(smsr$varname, 'annual | year | number of weeks | percent of weeks'), 'annual',
                  ifelse(str_detect(smsr$varname, 'month'), 'monthly',
                  ifelse(str_detect(smsr$varname, 'weekly'), 'weekly',
                  ifelse(str_detect(smsr$varname, 'daily'), 'daily', 'other'))))
smsr$unit <- factor(smsr$unit, levels = c('annual', 'monthly', 'weekly', 'daily', 'other'))
smsr$varname <- NULL
# summary by field and time unit
smsr %>% group_by(contentAreaName, unit) %>% summarise(n = n())
# # see for drought
# View(smsr[which(smsr$contentAreaName == 'Drought'),])
# output
write.csv(smsr, file = 'summary/selected_data_with_unit.csv', row.names = F)


###########
# download
###########

# weekly US Drought Monitor (USDM): 1148
View(list_GeographicItems(measure = 1148, geo_type = 'County')[[1]])
list_GeographyTypes(measure = 1148)
View(list_TemporalItems(measure = 1148, geo_type = 'County')[[1]])
# only available since 2021


#=========
# tornado
#=========

View(list_TemporalItems(measure = 1294, geo_type = 'County')[[1]])
View(list_GeographicItems(measure = 1294, geo_type = 'county')[[1]])
View(list_StratificationTypes(measure = 1294, geo_type = 'County')[[1]])
View(list_StratificationLevels(measure = 1294, geo_type = 'County')[[1]])

# query
tnd <- get_data(measure = 1294, geo_type = 'County',
                temporalItems = 2000:2021, token = ephtn_token)
length(tnd)
# object 1
colnames(tnd[[1]])
write.csv(tnd[[1]], row.names = F,
          file = 'tornado/raw/numtnd_cat_2000to2021.csv')
# object 2
colnames(tnd[[2]])
write.csv(tnd[[2]], row.names = F,
          file = 'tornado/raw/numtnd_cum_2000to2021.csv')



#===============
# precipitation
#===============

View(msr[which(msr$contentAreaName == 'Precipitation & Flooding'),])
tmp <- list_TemporalItems(measure = 577)[[1]]
View(tmp %>% group_by(parentTemporalId) %>% summarise(n = n()))
list_GeographicItems(measure = 577)

prcp <- get_data(measure = 577, geo_type = 'County', temporalItems = 1990:2022,
                 simplified_output = T, token = ephtn_token)
length(prcp[[1]])
names(prcp[[1]])
prcp <- prcp[[1]]
# output
write.csv(prcp, file = 'precipitation_measure577_1990to2022.csv', row.names = F)

# check availability
unique(prcp$measureName)
head(prcp$dataValue)
psum <- as.data.frame(
  prcp %>% group_by(geoId, parentTemporalId) %>%
    summarise(n = n()) %>%
    pivot_wider(names_from = parentTemporalId, values_from = n))
unique(psum[, 2:dim(psum)[2]])


# # annual precipitation
# apct <- get_data(measure = 576, geo_type = 'County', temporalItems = 2000:2022,
#                  simplified_output = F, token = ephtn_token)
# length(apct) # 2
# # absolute threshold
# colnames(apct[[1]])
# write.csv(apct[[1]][, c('geo', 'geoId', 'parentGeo', 'parentGeoId', 
#                         'dataValue', 'calculationType',
#                         'Absolute Threshold', 'temporalId')], 
#           file = 'raw/item576_annual_precipitation_absolute.csv', row.names = F)
# # relative threshold
# colnames(apct[[2]])
# write.csv(apct[[2]][, c('geo', 'geoId', 'parentGeo', 'parentGeoId', 
#                         'dataValue', 'calculationType',
#                         'Relative Threshold', 'temporalId')], 
#           file = 'raw/item576_annual_precipitation_relative.csv', row.names = F)
# 
# 
# # monthly precipitation
# View(list_GeographicItems(measure = 577, geo_type = 'County')[[1]])
# View(list_TemporalItems(measure = 577, geo_type = 'County')[[1]])
# list_StratificationTypes(measure = 577, geo_type = 'County')
# mpct <- get_data(measure = 577, geo_type = 'County', temporalItems = 2000:2022,
#                  simplified_output = F, token = ephtn_token)
# length(mpct) # 1
# mpct <- as.data.frame(mpct[[1]])
# save(mpct, file = 'raw/item577_monthly_precipitation.rda')
# # select columns and save to csv
# colnames(mpct)
# mpct <- mpct[, c('geo', 'geoId', 'parentGeo', 'parentGeoId', 'dataValue',
#                  'calculationType', 'temporalId', 'parentTemporalId')]
# write.csv(mpct, file = 'raw/item577_monthly_precipitation.csv', row.names = F)


#======
# heat
#======

#--------
# annual
#--------

# check other measures
View(list_TemporalItems(measure = 1024, geo_type = 'County')[[1]])
View(list_TemporalItems(measure = 1023, geo_type = 'County')[[1]])
View(list_TemporalItems(measure = 357, geo_type = 'County')[[1]])
View(list_TemporalItems(measure = 358, geo_type = 'County')[[1]])
View(list_TemporalItems(measure = 423, geo_type = 'County')[[1]])
View(list_TemporalItems(measure = 425, geo_type = 'County')[[1]])

# annual number of extreme heat days
heatDay <- get_data(measure = 423, geo_type = 'County', 
                    temporalItems = 2000:2022, 
                    simplified_output = F, token = ephtn_token)
length(heatDay)
View(heatDay[[1]]) # relative threshold?
unique(heatDay[[1]]$measureName)
View(heatDay[[2]]) # absolute threshold?

# annual number of extreme heat events
heatEvt <- get_data(measure = 425, geo_type = 'County',
                    temporalItems = 2000:2022,
                    simplified_output = F, token = ephtn_token)
length(heatEvt)

## save downloaded annual heat data
save(heatDay, heatEvt, file = 'raw/item423_425_heat_day_and_event.rda')
# heat days
colnames(heatDay[[1]])
write.csv(heatDay[[1]][, c('geo', 'geoId', 'parentGeo', 'parentGeoId', 
                           'dataValue', 'calculationType', 'Heat Metric',
                           'Relative Threshold', 'temporalId')],
          file = 'raw/item423_annual_heat_day_relative.csv', row.names = F)
colnames(heatDay[[2]])
write.csv(heatDay[[2]][, c('geo', 'geoId', 'parentGeo', 'parentGeoId', 
                           'dataValue', 'calculationType', 'Heat Metric',
                           'Absolute Threshold', 'temporalId')],
          file = 'raw/item423_annual_heat_day_absolute.csv', row.names = F)
# heat events
colnames(heatEvt[[1]])
write.csv(heatEvt[[1]][, c('geo', 'geoId', 'parentGeo', 'parentGeoId', 
                           'dataValue', 'Minimum Duration Days', 'calculationType', 
                           'Heat Metric', 'Relative Threshold', 'temporalId')],
          file = 'raw/item425_annual_heat_event_relative.csv', row.names = F)
colnames(heatEvt[[2]])
write.csv(heatEvt[[2]][, c('geo', 'geoId', 'parentGeo', 'parentGeoId', 
                           'dataValue', 'Minimum Duration Days', 'calculationType', 
                           'Heat Metric', 'Absolute Threshold', 'temporalId')],
          file = 'raw/item425_annual_heat_event_absolute.csv', row.names = F)

#-------
# month
#-------

View(msr[which(msr$indicatorId == 173),])

# weekly avg. max. temperature
View(list_TemporalItems(measure = 1025, geo_type = 'County')[[1]])

# only available since 2018, download 2018 for trial
heatTemp <- get_data(measure = 1025, geo_type = 'County', 
                     #temporalItems = 2018:2022,
                     simplified_output = T, token = ephtn_token)
length(heatTemp)
heatTemp <- heatTemp[[1]]
colnames(heatTemp)
head(heatTemp$temporalId)
head(heatTemp$parentTemporalId)
heatTemp %>% group_by(parentTemporalId) %>% summarise(n = n()) # only 2018 to 2014
# save(heatTemp, file = 'raw/item1025_weekly_heatTemperature.rda', row.names = F)



#-------
# daily
#-------

## measure 1236: 2022+ only
list_GeographicTypes(measure = 1236)
tmp <- list_TemporalItems(measure = 1236)[[1]]
tmp %>% group_by(parentTemporalId) %>% summarise(n = n())


## meadsure 358
# daily heat index from May to Sept
list_GeographicTypes(measure = 358)
View(list_GeographicItems(measure = 358)[[1]])
tmp <- list_TemporalItems(measure = 358)[[1]]
# test with county 1001
t0 <- get_data(measure = 358, geo_type = 'County', 
               temporalItems = 2000:2020,
               geoItems = 1001,
               simplified_output = T, token = ephtn_token)
t0 <- t0[[1]]
t0 %>% group_by(parentTemporalId) %>% summarise(n = n())
# test with county 6001
t1 <- get_data(measure = 358, geo_type = 'County', 
               temporalItems = 2000:2020,
               geoItems = 6001,
               simplified_output = T, token = ephtn_token)
t1 <- t1[[1]]
t1 %>% group_by(parentTemporalId) %>% summarise(n = n())
unique(t1$measureName)
head(t1$dataValue)


# download by county, as holistic attempt doesn't go through
# sink(file = 'log_get_dailyHeatIndex.txt')
heat_geo <- list_GeographicItems(measure = 358)[[1]]
colnames(heat_geo)
dim(heat_geo)
dwd <- c() # downloaded counties
which(heat_geo$childGeographicId == 37055)
for(i in 1:dim(heat_geo)[1]){
  j <- heat_geo[i, 'childGeographicId']
  print(j)
  Sys.sleep(sample(x = sample(5:20), size = 1))
  tryCatch({
    tmp <- get_data(measure = 358, geo_type = 'County', 
                    temporalItems = 1990:2021,
                    geoItems = j,
                    simplified_output = T, token = ephtn_token)
    tmp <- tmp[[1]]
    save(tmp, file = paste('heat/raw_daily/county', j, '.rda', sep = ''))
    dwd <- c(dwd, j)
  },
  error=function(e){
    print('error')
    }
  )
  tmp <- NULL
}
# sink()

# check for completeness
length(dwd)
# difference between downloaded and full county list
setdiff(heat_geo$childGeographicId, dwd) # 4017 17113 26123
for(j in c(4017, 17113, 26123)){
  tmp <- get_data(measure = 358, geo_type = 'County', 
                  temporalItems = 1990:2021,
                  geoItems = j,
                  simplified_output = T, token = ephtn_token)
  tmp <- tmp[[1]]
  save(tmp, file = paste('heat/raw_daily/county', j, '.rda', sep = ''))
}
# check downloaded list
dtdir <- c('heat/raw_daily/')
all_file <- list.files(path = dtdir, 
                       pattern = NULL, all.files = F, full.names = T)
head(all_file)
tmp <- c()
for(i in 1:length(all_file)){
  tmp <- c(tmp, str_extract(all_file[i], '[[:digit:]]+'))
}
tmp <- as.numeric(tmp)
setdiff(tmp, heat_geo$childGeographicId)
setdiff(heat_geo$childGeographicId, tmp)


# download missed counties in the prior round
for(j in c(5027, 5047, 5049, 48169)){
  print(j)
  Sys.sleep(sample(x = sample(5:20), size = 1))
  tmp <- get_data(measure = 358, geo_type = 'County', 
                  temporalItems = 2000:2020,
                  geoItems = j,
                  simplified_output = F, token = ephtn_token)
  tmp <- tmp[[1]]
  save(tmp, file = paste('raw/daily_heatIndex/county', j, '.rda', sep = ''))
}

# check year-day availability for each county
dtdir <- c('G:/.shortcut-targets-by-id/1gAsxIHTrYObf_jRW36X25nHFdFqkAn-K/SC folder/CDC_EPHTN/raw/daily_heatIndex')
all_file <- list.files(path = dtdir, 
                       pattern = NULL, all.files = F, full.names = T)
head(all_file)
sdf <- as.data.frame(matrix(NA, nrow = 1, ncol = 3))
colnames(sdf) <- c('parentTemporalId', 'n', 'fips')
i <- 0
for(filename in all_file){
  i <- i + 1
  print(i)
  if(grepl('.rda', filename, fixed = T)){
    load(filename)
    tsum <- as.data.frame(
      tmp %>% group_by(parentTemporalId) %>% 
        summarise(n = n(), fips = as.numeric(unique(geoId))))
    # attach to output
    sdf <- rbind(sdf, tsum)
  }
}
View(sdf)
sdf <- sdf[2:dim(sdf)[1],]

swdf <- sdf %>% pivot_wider(names_from = parentTemporalId, values_from = n) %>%
  arrange(-desc(fips))



# #=============
# # food access
# #=============

View(list_TemporalItems(measure = 1041)[[1]])
View(list_GeographicItems(measure = 1041)[[1]])
unique(list_GeographicItems(measure = 1041)[[1]]$geo_type)


#=========
# drought
#=========

View(msr[which(msr$indicatorId == 175),])


# 1139: Total Number of Weeks a County Was in Drought by Year (SPEI)
unique(list_GeographicItems(measure = 1139)[[1]]$geo_type)
View(list_StratificationLevels(measure = 1139, geo_type = 'county')[[1]])
View(list_TemporalItems(measure = 1139, geo_type = 'County')[[1]])
spei1 <- get_data(measure = 1139, geo_type = 'County',
                  temporalItems = 2000:2021, token = ephtn_token)
length(spei1)
# object 1
View(spei1[[1]])
colnames(spei1[[1]])
write.csv(spei1[[1]], row.names = F,
          file = 'drought/raw/spei_numweek_cat_2000to2021.csv')
# object2
colnames(spei1[[2]])
write.csv(spei1[[2]], row.names = F,
          file = 'drought/raw/spei_numweek_cum_2000to2021.csv')


# 1140: Maximum Number of Consecutive Weeks a County Was in Drought by Year (SPEI)
View(list_TemporalItems(measure = 1140, geo_type = 'County')[[1]])
spei2 <- get_data(measure = 1140, geo_type = 'County',
                temporalItems = 2000:2021, token = ephtn_token)
length(spei2)
# object 1
colnames(spei2[[1]])
write.csv(spei2[[1]], row.names = F,
          file = 'drought/raw/spei_nummax_cat_2000to2021.csv')
# object 2
colnames(spei2[[2]])
write.csv(spei2[[2]], row.names = F,
          file = 'drought/raw/spei_nummax_cum_2000to2021.csv')


# 1141: Percent of Weeks a County Was in Drought by Year (SPEI)
View(list_TemporalItems(measure = 1141, geo_type = 'County')[[1]])
spei3 <- get_data(measure = 1141, geo_type = 'County',
                temporalItems = 2000:2021, token = ephtn_token)
length(spei3)
# object 1
colnames(spei3[[1]])
write.csv(spei3[[1]], row.names = F,
          file = 'drought/raw/spei_pctweek_cat_2000to2021.csv')
# object 2
colnames(spei3[[2]])
write.csv(spei3[[2]], row.names = F,
          file = 'drought/raw/spei_pctweek_cum_2000to2021.csv')


## USDM
# 1145: Total Number of Weeks a County Was in Drought by Year (USDM)
# 1146: Maximum Number of Consecutive Weeks a County Was in Drought by Year (USDM)
# 1147: Percent of Weeks a County Was in Drought by Year (USDM)

# 1145
View(list_TemporalItems(measure = 1145, geo_type = 'County')[[1]])
usdm1 <- get_data(measure = 1145, geo_type = 'County',
                  temporalItems = 2000:2021, token = ephtn_token)
length(usdm1)
# object 1
colnames(usdm1[[1]])
write.csv(usdm1[[1]], row.names = F, 
          file = 'drought/raw/usdm_numweek_cat_2000to2021.csv')
# object 2
colnames(usdm1[[2]])
write.csv(usdm1[[2]], file = 'drought/raw/usdm_cum_2000to2021.csv', row.names = F)

# 1146
View(list_TemporalItems(measure = 1146, geo_type = 'County')[[1]])
usdm2 <- get_data(measure = 1146, geo_type = 'County',
                  temporalItems = 2000:2021, token = ephtn_token)
length(usdm2)
# object 1
colnames(usdm2[[1]])
write.csv(usdm2[[1]], row.names = F,
          file = 'drought/raw/usdm_nummax_cat_2000to2021.csv')
# object 2
colnames(usdm2[[2]])
write.csv(usdm2[[2]], row.names = F,
          file = 'drought/raw/usdm_nummax_cum_2000to2021.csv')

# 1147
View(list_TemporalItems(measure = 1147, geo_type = 'County')[[1]])
usdm3 <- get_data(measure = 1147, geo_type = 'County',
                  temporalItems = 2000:2021, token = ephtn_token)
length(usdm3)
# object 1
colnames(usdm3[[1]])
write.csv(usdm3[[1]], row.names = F,
          file = 'drought/raw/usdm_pctweek_cat_2000to2021.csv')
# object 2
colnames(usdm3[[2]])
write.csv(usdm3[[2]], row.names = F,
          file = 'drought/raw/usdm_pctweek_cum_2000to2021.csv')



#============
# resilience
#============

bric_soc <- get_data(measure = 1433, 
                simplified_output = F, token = ephtn_token)


#=============
# air quality
#=============

View(msr[which(msr$contentAreaId == 11),])
unique(msr[which(msr$contentAreaId == 11), 'measureName'])

# current & historical air quality: PM2.5, EPA
View(list_TemporalItems(measure = 296)[[1]])
pm2.5 <- get_data(measure = 296, geo_type = 'County', temporalItems = 2001:2020)
length(pm2.5)
pm2.5 <- pm2.5[[1]]
colnames(pm2.5)
length(unique(pm2.5$temporalId)) # 20
length(unique(pm2.5$geoId)) # 3143
# output
write.csv(pm2.5, file = 'air/raw/item296_annual_pm2.5_epa.csv', row.names = F)


# national ambient: PM2.5, NAQQS
View(list_TemporalItems(measure = 294)[[1]])
pm2.5 <- get_data(measure = 294, geo_type = 'County', temporalItems = 2001:2020)
length(pm2.5)
pm2.5 <- pm2.5[[1]]
colnames(pm2.5)
length(unique(pm2.5$temporalId)) # 20
length(unique(pm2.5$geoId)) # 3143
# output
write.csv(pm2.5, file = 'air/raw/item294_annual_pm2.5_naqqs.csv', row.names = F)


# national ambient: Ozone, NAQQS
View(list_TemporalItems(measure = 292)[[1]])
o3 <- get_data(measure = 292, geo_type = 'County', temporalItems = 2001:2020)
length(o3)
o3 <- o3[[1]]
colnames(o3)
length(unique(o3$temporalId)) # 20
length(unique(o3$geoId)) # 3115
# output
write.csv(o3, file = 'air/raw/item292_annual_o3_naqqs.csv', row.names = F)


# current & historical air quality: Ozone, EPA
tmp <- list_TemporalItems(measure = 1354)[[1]]
unique(tmp$parentTemporalId) # only available for 2023 & 2024

