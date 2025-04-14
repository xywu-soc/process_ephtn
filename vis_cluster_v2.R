#'county-to-county migration with IRS data 2011-2021: visualization
#'
#'Moved from get_cluster_v1.R. get_cluster_v2.R no longer contains visualization.
#'
#'Further edits:
#' 1.Use Lingxin's block output instead of mine, and merge with vertex-level covariates
#' 2.Construct county-and-period-level climate summaries, and summarize by block
#'
#'Xingyun Wu
#'
#'Initial: 7/15/2024
#'Latest: 7/15/2024

library(haven)
library(dplyr)
library(tidyr)
library(visNetwork)
library(ggplot2)
library(RColorBrewer)

options(scipen = 999)

setwd('~/OneDrive - Johns Hopkins/ra/HPC_climate/Climate-c2c-IRS')
setwd('C:/Users/xwu70/OneDrive - Johns Hopkins/ra/HPC_climate/Climate-c2c-IRS')


########
# block
########

block <- read_dta('IC2S2 analysis/e_out_all.dta')
length(unique(block$y1fips))
length(unique(block$y2fips))

t0 <- block[, c('y1fips','y1rblock5')]
colnames(t0) <- c('fips', 'rblock5')
t1 <- block[, c('y2fips', 'y2rblock5')]
colnames(t1) <- c('fips', 'rblock5')
blk <- rbind(t0, t1)
blk <- blk[!duplicated(blk),]
blk <- blk %>% arrange(-desc(fips))

block <- read_dta('IC2S2 analysis/rblock_all.dta')
block <- block %>% arrange(-desc(fips))

setequal(blk$rblock5, block$rblock5)

# merge-in previously processed vertex data
load('results/block_reordered_by_otn2rate.rda')
# double-check whether Linxin's block is the same as in vdf
setequal(vdf$block5_reordered, block$rblock5)
# output for Gephi
write.csv(vdf, 'results/vdf_compiled.csv', row.names = F)
# load directed edge list
elst <- read_dta('processed data/unzipped/e_out_all.dta')
edir <- as.data.frame(elst %>% group_by(y2fips, y1fips) %>% 
                        summarise(n = n()))
colnames(edir)
colnames(edir) <- c('Source', 'Target', 'nyear')
edir <- left_join(x = edir, y = vdf[, c('id', 'block5_reordered')],
                  by = c('Source' = 'id'))
colnames(edir)[dim(edir)[2]] <- 'source_rblock5'
edir <- left_join(x = edir, y = vdf[, c('id', 'block5_reordered')],
                  by = c('Target' = 'id'))
colnames(edir)[dim(edir)[2]] <- 'target_rblock5'
write.csv(edir, file = 'results/edf_directed.csv', row.names = F)
edf %>% group_by(y2block5_reordered) %>% summarise(n = n(), p = n / dim(edf)[1])



#########
# climate
##########

cmt <- read.csv('../data/processed_data/climate_all_2010to2021.csv')

# double-check EPA data availability
colnames(cmt)
cmt %>% group_by(year) %>% summarise(n = length(which(!is.na(hurricane))))
cmt %>% group_by(year) %>% summarise(n = length(which(!is.na(tropical_storm))))
cmt %>% group_by(year) %>% summarise(n = length(which(!is.na(tornado)))) #
cmt %>% group_by(year) %>% summarise(n = length(which(!is.na(drought))))
cmt %>% group_by(year) %>% summarise(n = length(which(!is.na(landslide))))
cmt %>% group_by(year) %>% summarise(n = length(which(!is.na(wildfire)))) #

## annual averages output to Stata
anncmt <- cmt %>% group_by(stfips, stname, stabbr, ctyfips, ctyname, year) %>%
  summarise(mean_hazard_area = mean(c(hurricane, tropical_storm, tornado,
                               drought, landslide, wildfire), na.rm = T)) %>%
  mutate_if(is.numeric, coalesce, -1)
# inspect
summary(anncmt$mean_hazard_area)
# output
colnames(anncmt)
write_dta(anncmt, path = 'processed data/annual_hazard_area.dta')

## annual averages to proceed
anncmt <- cmt %>% group_by(stfips, stname, stabbr, ctyfips, ctyname, year) %>%
  summarise(mean_hazard_area = mean(c(hurricane, tropical_storm, tornado,
                                      drought, landslide, wildfire), na.rm = T),
            sd_hazard_area = sd(c(hurricane, tropical_storm, tornado,
                                  drought, landslide, wildfire), na.rm = T)) %>%
  mutate_if(is.numeric, coalesce, NA)
# inspect
summary(anncmt$mean_hazard_area)
# output
colnames(anncmt)


##############
# merge & sum
##############

# Lingxin's harmonized vertex variables
vtx <- read_dta('IC2S2 analysis/v_all_r.dta')
colnames(vtx)

dt <- left_join(x = vtx[which(vtx$fips %in% block$fips),], 
                y = block, by = 'fips')
colnames(dt)
length(unique(dt$fips))

unique(dt$rblock5)
dt$rblock5 <- factor(dt$rblock5, levels = c(1:5))

# scatter plot with line
ggplot(data = dt, aes(x = year, y = nd)) +
  geom_point() +
  geom_smooth(color = 'red') +
  scale_x_continuous(breaks = 0:10) +
  facet_grid(~ rblock5) +
ggsave('results/nd_smoothed_trend_by_block.png', width = 10, height = 6)


bsum <- dt[which(!is.na(dt$nd)),] %>% 
  group_by(fips, rblock5) %>%
  summarise(sum_nd = sum(nd)) %>%
  group_by(rblock5) %>%
  summarise(mean_nd = mean(sum_nd), sd_nd = sd(sum_nd))
ggplot(data = bsum, aes(x = rblock5)) +
  geom_bar(aes(y = mean_nd, color = rblock5, fill = rblock5), 
           stat = 'identity') +
  geom_point(aes(y = sd_nd, group = 1)) +
  geom_line(aes(y = sd_nd, group = 1)) +
  # scale_y_continuous(sec.axis = sec_axis(~. - 0.0000001, name = 'SD')) +
  # geom_text(aes(label = round(mean_nd, 1), y = mean_nd), 
  #           position=position_dodge(width = 0.9), vjust = -1.1) +
  ylim(c(0, 50)) +
  xlab('Block') +
  ylab('Mean') +
  scale_color_manual(name = 'Block',
                    labels = as.character(1:5),
                    values = c('1' = 'lightskyblue', 
                               '2' = 'dodgerblue3',
                               '3' = 'lightgreen',
                               '4' = 'red3',
                               '5' = '#FF00FF')) +
  scale_fill_manual(name = 'Block',
                    labels = as.character(1:5),
                    values = c('1' = 'lightskyblue', 
                               '2' = 'dodgerblue3',
                               '3' = 'lightgreen',
                               '4' = 'red3',
                               '5' = '#FF00FF')) +
  ggtitle('Cumulative percent of county area with natural disaster',
          # subtitle = 'Line for standard deviation on the same scale'
          ) +
  theme_bw() +
  theme(legend.position = 'bottom')
ggsave('results/nd_cumulative_rblock5.png', width = 6, height = 6)


## reduce to county averages
prdcmt <- anncmt %>% group_by(stfips, stname, stabbr, ctyfips, ctyname) %>%
  summarise(hzdarea_mean = mean(mean_hazard_area, na.rm = T),
            hzdarea_sd = sd(mean_hazard_area, na.rm = T))
dt2 <- right_join(x = prdcmt, y = block, by = c('ctyfips' = 'fips')) %>%
  group_by(rblock5) %>%
  summarise(n = n(), mean = mean(hzdarea_mean), sd = sd(hzdarea_mean),
            min = min(hzdarea_mean), 
            q25 = quantile(hzdarea_mean, probs = 0.25),
            mid = median(hzdarea_mean), 
            q75 = quantile(hzdarea_mean, probs = 0.75),
            max = max(hzdarea_mean))


library(ggridges)
library(viridis)
library(hrbrthemes)
# plot
dt$rblock5 <- as.character(dt$rblock5)
blk_names <- list('1' = 'Block 1',
                  '2' = 'Block 2',
                  '3' = 'Block 3',
                  '4' = 'Block 4',
                  '5' = 'Block 5')
ggplot(dt[which(!is.na(dt$nd)),], 
       aes(x = nd, y = as.factor(year), fill = as.factor(year))) +
  geom_density_ridges() +
  xlim(0, NA) +
  theme_ridges() + 
  theme(legend.position = "none") +
  xlab('% area with ND') +
  ylab('year') +
  ggtitle('Ridgeline plot by year and rblock5',
          subtitle = 'Density distributions of ND') +
  facet_grid(~ rblock5,
             labeller = blk_names) +
  theme_bw()
ggsave('results/nd_ridgeline_trend_by_block.png', width = 15, height = 8)

# ##
# # get grand mean by year
# yrsum <- vtx %>% group_by(year) %>% summarise(grand_mean = mean(nd))
# # get grand-mean centered
# for(i in 1:dim(dt)[1]){
#   dt[i, 'nd_centered'] <- 
# }

# inspect annual means/median/max by block
dt[which(!is.na(dt$nd)),] %>% group_by(rblock5) %>%
  summarise(mean_nd = mean(nd), sd_nd = sd(nd))
dt[which(!is.na(dt$nd)),] %>% group_by(rblock5, year) %>%
  summarise(mean_nd = mean(nd)) %>%
  pivot_wider(names_from = year, values_from = mean_nd)
dt[which(!is.na(dt$nd)),] %>% group_by(rblock5, year) %>%
  summarise(mid_nd = median(nd)) %>%
  pivot_wider(names_from = year, values_from = mid_nd)
dt[which(!is.na(dt$nd)),] %>% group_by(rblock5, year) %>%
  summarise(q75_nd = quantile(nd, probs = 0.75)) %>%
  pivot_wider(names_from = year, values_from = q75_nd)
dt[which(!is.na(dt$nd)),] %>% group_by(rblock5, year) %>%
  summarise(max_nd = max(nd)) %>%
  pivot_wider(names_from = year, values_from = max_nd)
# get long-df for plots
annsum <- dt[which(!is.na(dt$nd)),] %>% group_by(rblock5, year) %>%
  summarise(mean_nd = mean(nd), mid_nd = median(nd),
            q75_nd = quantile(nd, probs = 0.75),
            q90_nd = quantile(nd, probs = 0.90),
            q95_nd = quantile(nd, probs = 0.95), 
            max_nd = max(nd))
# plot mean
ggplot(data = annsum, aes(x = year, y = mean_nd, color = rblock5)) +
  geom_point() +
  geom_line() +
  # geom_smooth(se = F) +
  scale_x_continuous(breaks = 2010:2020) +
  xlab('Year') +
  ylab('Mean') +
  ggtitle('Percent of county area affected by natural disaster') +
  theme_bw() +
  theme(legend.position = 'bottom')
# plot median
ggplot(data = annsum, aes(x = year, y = mid_nd, color = rblock5)) +
  geom_point() +
  geom_line() +
  scale_x_continuous(breaks = 2010:2020) +
  xlab('Year') +
  ylab('Median') +
  ggtitle('Percent of county area affected by natural disaster') +
  theme_bw() +
  theme(legend.position = 'bottom')
# plot 3rd quartile
ggplot(data = annsum, aes(x = year, y = q75_nd, color = rblock5)) +
  geom_smooth(span = 1.5, se = F) +
  scale_x_continuous(breaks = 2010:2020) +
  xlab('Year') +
  ylab('75th Percentile') +
  ggtitle('Percent of county area affected by natural disaster') +
  theme_bw() +
  theme(legend.position = 'bottom')
ggsave('results/nd_annual_75pct_rblock5.png', width = 6, height = 6)
# plot 90th quartile
ggplot(data = annsum, aes(x = year, y = q90_nd, color = rblock5)) +
  geom_smooth(span = 1.5, se = F) +
  scale_x_continuous(breaks = 2010:2020) +
  xlab('Year') +
  ylab('90th Percentile') +
  ggtitle('Percent of county area affected by natural disaster') +
  theme_bw() +
  theme(legend.position = 'bottom')
ggsave('results/nd_annual_90pct_rblock5.png', width = 6, height = 6)
# plot 95th quartile
ggplot(data = annsum, aes(x = year, y = q95_nd, color = rblock5)) +
  geom_smooth(span = 1.5, se = F) +
  scale_x_continuous(breaks = 2010:2020) +
  scale_color_manual(name = 'Block',
                     labels = as.character(1:5),
                     values = c('1' = 'lightskyblue', 
                                '2' = 'dodgerblue3',
                                '3' = 'lightgreen',
                                '4' = 'red3',
                                '5' = '#FF00FF'))+
  xlab('Year') +
  ylab('95th Percentile') +
  ggtitle('Percent of county area affected by natural disaster') +
  theme_bw() +
  theme(legend.position = 'bottom')
ggsave('results/nd_annual_95pct_rblock5_span075.png', width = 6, height = 6)
ggplot(data = annsum, aes(x = year, y = q95_nd, color = rblock5)) +
  geom_point() +
  geom_line() +
  scale_x_continuous(breaks = 2010:2020) +
  xlab('Year') +
  ylab('95th Percentile') +
  ggtitle('Percent of county area affected by natural disaster') +
  theme_bw() +
  theme(legend.position = 'bottom')
# plot max
ggplot(data = annsum, aes(x = year, y = max_nd, color = rblock5)) +
  geom_point() +
  geom_line() +
  scale_x_continuous(breaks = 2010:2020) +
  xlab('Year') +
  ylab('Maximum') +
  ggtitle('Percent of county area affected by natural disaster') +
  theme_bw() +
  theme(legend.position = 'bottom')


# cold & wet, hot & dry
unique(dt$cold_wet)
unique(dt$hot_dry)
crsum <- dt[which(!is.na(dt$nd)),] %>% group_by(rblock5, year) %>%
  summarise(n_cold_wet = sum(cold_wet), p_cold_wet = n_cold_wet / n(),
            n_hot_dry = sum(hot_dry), p_hot_dry = n_hot_dry / n())
crsum[, c('rblock5', 'year', 'p_cold_wet')] %>% 
  pivot_wider(names_from = year, values_from = p_cold_wet)
## cold & wet
ggplot(data = crsum, aes(x = year, y = p_cold_wet * 100, color = rblock5)) +
  geom_point() +
  geom_line() +
  scale_x_continuous(breaks = 2010:2020) +
  ylab('% of counties') +
  ggtitle('Cold & Wet') +
  theme(legend.position = 'bottom')
ggplot(data = crsum, aes(x = year, y = p_cold_wet * 100, color = rblock5)) +
  geom_smooth(span = 1.5, se = F) +
  scale_x_continuous(breaks = 2010:2020) +
  scale_color_manual(name = 'Block',
                    labels = as.character(1:5),
                    values = c('1' = 'lightskyblue', 
                               '2' = 'dodgerblue3',
                               '3' = 'lightgreen',
                               '4' = 'red3',
                               '5' = '#FF00FF')) +
  ylab('% of counties') +
  ggtitle('Cold & Wet') +
  theme_bw() +
  theme(legend.position = 'bottom')
ggsave('results/coldwet_rblock5.png', width = 6, height = 6)
## hot & dry
ggplot(data = crsum, aes(x = year, y = p_hot_dry * 100, color = rblock5)) +
  geom_point() +
  geom_line() +
  scale_x_continuous(breaks = 2010:2020) +
  ylab('% of counties') +
  ggtitle('Hot & Dry') +
  theme(legend.position = 'bottom')
ggplot(data = crsum, aes(x = year, y = p_hot_dry * 100, color = rblock5)) +
  geom_smooth(span = 1.5, se = F) +
  scale_x_continuous(breaks = 2010:2020) +
  scale_color_manual(name = 'Block',
                    labels = as.character(1:5),
                    values = c('1' = 'lightskyblue', 
                               '2' = 'dodgerblue3',
                               '3' = 'lightgreen',
                               '4' = 'red3',
                               '5' = '#FF00FF')) +
  ylab('% of counties') +
  ggtitle('Hot & Dry') +
  theme_bw() +
  theme(legend.position = 'bottom')
ggsave('results/hotdry_rblock5.png', width = 6, height = 6)

## cumulative hot-dry conditions
crsum2 <- dt[which(!is.na(dt$nd)),] %>% 
  group_by(rblock5, fips) %>%
  summarise(n_cold_wet = sum(cold_wet), 
            p_cold_wet = n_cold_wet / n() * 100,
            n_hot_dry = sum(hot_dry), 
            p_hot_dry = n_hot_dry / n() * 100) %>%
  arrange(-desc(fips))
# mean
crsum3 <- crsum2 %>% group_by(rblock5) %>%
  summarise(n = n(), 
            mean_hd = mean(p_hot_dry), sd_hd = sd(p_hot_dry),
            mean_cw = mean(p_cold_wet), sd_cw = sd(p_cold_wet))
ggplot(data = crsum3, aes(x = rblock5, color = rblock5, fill = rblock5)) +
  geom_bar(aes(y = mean_hd), stat = 'identity') +
  geom_point(aes(y = sd_hd * 1/2, group = 1), color = 'black')+
  geom_line(aes(y = sd_hd * 1/2, group = 1), color = 'black')+
  scale_y_continuous(sec.axis = sec_axis(~./(1/2), name = 'SD'))+
  scale_x_discrete(breaks = 1:5) +
  scale_color_manual(name = 'Block',
                     labels = as.character(1:5),
                     values = c('1' = 'lightskyblue', 
                                '2' = 'dodgerblue3',
                                '3' = 'lightgreen',
                                '4' = 'red3',
                                '5' = '#FF00FF')) +
  scale_fill_manual(name = 'Block',
                     labels = as.character(1:5),
                     values = c('1' = 'lightskyblue', 
                                '2' = 'dodgerblue3',
                                '3' = 'lightgreen',
                                '4' = 'red3',
                                '5' = '#FF00FF')) +
  xlab('Block') +
  ylab('Mean') +
  ggtitle("County's percent of years with hot-dry compound") +
  theme_bw() +
  theme(legend.position = 'bottom')
ggsave('results/hotdry_mean_rblock5.png', width = 6, height = 6)
# cumulative
crsum4 <- crsum2 %>% group_by(rblock5) %>%
  summarise(n = n(), 
            sum_hd = sum(p_hot_dry), sum_cw = sum(p_cold_wet))
ggplot(data = crsum4, aes(x = rblock5, y = sum_hd, 
                          color = rblock5, fill = rblock5)) +
  geom_bar(stat = 'identity') +
  scale_x_discrete(breaks = 1:5) +
  scale_color_manual(name = 'Block',
                     labels = as.character(1:5),
                     values = c('1' = 'lightskyblue', 
                                '2' = 'dodgerblue3',
                                '3' = 'lightgreen',
                                '4' = 'red3',
                                '5' = '#FF00FF')) +
  scale_fill_manual(name = 'Block',
                    labels = as.character(1:5),
                    values = c('1' = 'lightskyblue', 
                               '2' = 'dodgerblue3',
                               '3' = 'lightgreen',
                               '4' = 'red3',
                               '5' = '#FF00FF')) +
  xlab('Block') +
  ylab('Sum') +
  ggtitle('Percent of years with hot-dry compound') +
  theme_bw() +
  theme(legend.position = 'bottom')

## load edge covaraites from Lingxin
eall <- read_dta('IC2S2 analysis/e_out_all.dta')
dim(eall)
colnames(eall)
summary(eall$e_y)
summary(eall$e_p)
summary(eall$e_u)
# d_climate of edges
dsum <- eall %>% group_by(y2rblock5, index_k) %>%
  summarise(mean_d = mean(d_climate), sd_d = sd(d_climate))
dsum$y2rblock5 <- factor(dsum$y2rblock5, levels = 1:5)
View(eall %>% group_by(y2rblock5) %>%
       summarise(mean_d = mean(d_climate), sd_d = sd(d_climate)))
ggplot(data = dsum, aes(x = index_k, y = mean_d, color = y2rblock5)) +
  # geom_point() +
  # geom_line() +
  geom_smooth(span = 1, se = F) +
  scale_x_continuous(breaks = 1:10) +
  scale_color_manual(name = 'Block',
                     labels = as.character(1:5),
                     values = c('1' = 'lightskyblue', 
                                '2' = 'dodgerblue3',
                                '3' = 'lightgreen',
                                '4' = 'red3',
                                '5' = '#FF00FF')) +
  ylab('Mean') +
  ggtitle('Climate dissimilarity of dyads') +
  theme_bw() +
  theme(legend.position = 'bottom')
ggsave('results/dclimate_rblock5.png', width = 6, height = 6)
# bivariate
eall$y2rblock5 <- factor(eall$y2rblock5, levels = 1:5)
ggplot(data = eall, aes(x = d_climate, y = e_y, group = y2rblock5, color = y2rblock5)) +
  geom_smooth(formula = y ~ x, span = 1, se = F) +
  scale_color_manual(name = 'Block',
                     labels = as.character(1:5),
                     values = c('1' = 'lightskyblue',
                                '2' = 'dodgerblue3',
                                '3' = 'lightgreen',
                                '4' = 'red3',
                                '5' = '#FF00FF')) +
  xlab('Climate dissimilarity') +
  ylab('e_y') +
  ggtitle('Dyadic bivariate relationship', 
          subtitle = 'e_y ~ climate dissimilarity') +
  theme_bw() +
  theme(legend.position = 'bottom')
ggsave('results/ey_dclimate_rblock5.png', width = 6, height = 6)



######
# vis
######




