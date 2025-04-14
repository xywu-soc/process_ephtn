#'county-to-county migration with IRS data 2011-2021
#'
#'networks for overlapping two consecutive years 1112-2021
#'undirected unweighted graph
#'
#'v2 edits based on v1:
#' 1.Split community detection and visualization
#' 2.Move visualization to vis_cluster_v2.R
#'
#'Xingyun Wu
#'
#'Initial: 7/15/2024
#'Latest: 7/15/2024

setwd('~/OneDrive - Johns Hopkins/ra/HPC_climate/Climate-c2c-IRS')
setwd('C:/Users/xwu70/OneDrive - Johns Hopkins/ra/HPC_climate/Climate-c2c-IRS')

rm(list = ls())
options(scipen = 999)

library(haven)
library(igraph)
library(dplyr)
library(tidyr)
library(tibble)
library(mclust)
library(grdpg)
library(visNetwork)
library(ggplot2)
library(RColorBrewer)
library(writexl)


########
# graph
########

elst <- read_dta('processed data/unzipped/e_out_all.dta') 
dim(elst)
length(unique(c(elst$y2fips, elst$y1fips))) # 3054
colnames(elst) # "y1fips"  "y2fips"  "fips"
# write.csv(elst[, c('y2fips', 'y1fips')], 'processed data/elst_all.csv', row.names = F)

# directed graph first, to account for the mutual relations
g <- graph_from_data_frame(d = elst, directed = T)
# turn into undirected, ignore loops
g <- as.undirected(g, mode = 'collapse')


# network description
# num vertices
vcount(g) # 3054
# num edges
ecount(g) # 62420
# density
edge_density(g) # 0.013
# eigenvector centrality
ec <- eigen_centrality(g, directed = F, scale = T)
ec$value # 206.8


##_____________________________
# get the real adjacency matrix
A <- as_adj(g)
A <- as.matrix(A)
head(diag(A))
summary(colSums(A))
#'Min. 1st Qu.  Median    Mean 3rd Qu.    Max.
#'1.00    7.00   12.00   40.88   30.00  922.00 
dim(A) # 3054 3054
head(colnames(A))

# A is undirected, unweighted binary, hollow
A <- 1*(A>=1)
diag(A) <- 0
sum(A) # 124840
# PLOT USING BASE FUNCTION INSTEAD OF GGSAVE, AS GGSAVE IS FOR GGPLOT ONLY --REMOVING ORIGINAL CODE # ggsave('results/hist_1.png')
png('results/hist_degree_raw.png')
hist(rowSums(A), breaks = 100)
dev.off()


############
# ASE + GMM 
############
# spectral embedding function
set.seed(123)
dmax <- 10

# use 'g' instead of A here, as my latest version of R specify A's type to be both 'matrix' and 'array', causing errors
embed <- SpectralEmbedding(g, dmax, work = 100)
s <- embed$D
dimselect(s) 
# $value
#  206.83706  52.92072  41.28708
# $elbow
#  1 4 6

dhat <- dimselect(s)$elbow[1:2]+1
dhat # 2 5

Xhat <- embed$X[,1:dhat[1]] %*% sqrt(diag(s[1:dhat[1]], nrow = dhat[1], ncol = dhat[1]))
Ipq <- getIpq(A, dhat[1])
Ipq
#'     [,1] [,2]
#'[1,]    1    0
#'[2,]    0    1

# GMM cluster Xhat
kmax <- 20
set.seed(123)
model <- Mclust(Xhat, G = 1:kmax)

# USE DPLYR FUNCTION TO LOOK AT BLOCK MEMBERSHIP DISTRIBUTION
block <- as.data.frame(model$classification)
colnames(block)
colnames(block) <- 'block'
block$fips <- as.numeric(row.names(A))
sumblk <- as.data.frame(
  block %>% group_by(block) %>% summarise(n = n()))
View(sumblk)

# grdpg without covariates - get screeplot
# set.seed(123)
# ptm <- proc.time()
# results <- GRDPGwithoutCovariates(g, G = 1, work = 200)
# print(proc.time()-ptm)  # 7 seconds
# results$Ipq # check dhat [1,1]
# ggsave('results/scree_all.png')

# screeplot
cols <- ncol(A)
temp1 <- eigs_sym(matrix(as.numeric(A), ncol = cols), dmax, 'LA')
s1 <- temp1$values
temp2 <- eigs_sym(matrix(as.numeric(A), ncol = cols), dmax, 'SA')
s2 <- temp2$values
tempdat <- data.frame(raw = c(s1,s2)) %>%
  mutate(sign = ifelse(raw > 0, 'positive', 'negative'), s = abs(raw)) %>%
  arrange(desc(s))
# pp1 <- scree(tempdat$raw[1:dmax], 'Screeplot (without Covariates)')
# pp1
# ggsave('results/scree_grdpg.png', width = 6, height = 6)
pcnt <- 0
ncnt <- 0
for(i in 1:dim(tempdat)[1]){
  if(tempdat[i, 'raw'] > 0){
    pcnt <- pcnt + 1
    tempdat[i, 'rank'] <- pcnt
  }
  else if(tempdat[i, 'raw'] < 0){
    ncnt <- ncnt + 1
    tempdat[i, 'rank'] <- ncnt
  }
}
ggplot(data = tempdat, aes(x = rank, y = s, color = sign)) +
  geom_line(linetype='dotted') +
  geom_point(aes(shape = sign), size = 2) +
  scale_x_continuous(breaks = 1:max(tempdat$rank)) +
  labs(x = 'Rank in Magnitude', y = 'Eigenvalue in Magnitude') +
  ggtitle('Screeplot')
ggsave('results/scree_manual.png', width = 6, height = 6)


## BIC
#model$BIC
BICs <- data.frame(K = 1:kmax, model$BIC[1:kmax,])

# look at plot VVV only
vvv <- as.data.frame(BICs[1:kmax, 15])
colnames(vvv) <- 'VVV'
vvv <- na.omit(vvv)
vvv$p <- vvv$VVV / max(vvv[, 'VVV'])
vvv$id <- as.numeric(rownames(vvv))
g1 <- ggplot(data=vvv, aes(x=id, y=p)) +
  geom_point(color='dark blue') +
  geom_line(color='dark blue') +
  geom_hline(yintercept=1, color='red') +
  labs(x='K', y='Proportion to the Highest Value') +
  scale_shape_manual(values=1:nrow(vvv)) +
  scale_x_continuous(breaks=seq(1,kmax,1)) +
  scale_y_continuous(breaks=seq(0, 1, 0.05))
g1 # choose k = 5, 7, or 13
ggsave('results/vvv_1.png', width = 6, height = 6)

set.seed(123)
model <- list()
model$k5 <- Mclust(Xhat, G = 5)
model$k7 <- Mclust(Xhat, G = 7)
model$k8 <- Mclust(Xhat, G = 8)
model$k13 <- Mclust(Xhat, G = 13)
# output models
save(Xhat, model, A, g, elst, file = 'results/grdpg_eout_all.rda')

# load models
load('results/grdpg_eout_all.rda')

# load geo info
geodf <- read.csv('../data/processed_data/2019_Gaz_counties_national_converted.csv')

# network statistics
dc_raw <- degree(g, mode = 'all', normalized = F)
dc_norm <- degree(g, mode = 'all', normalized = T)
ec <- eigen_centrality(g, directed = F, scale = T)$vector
eigen_centrality(g, directed = F, scale = T)$value # 206.8371

# base vertex-df
vdf <- as.data.frame(as.numeric(rownames(A)))
colnames(vdf) <- 'id'
# merge with geo loc
colnames(geodf)
vdf <- left_join(x = vdf, y = geodf[, c('stabbr', 'id', 'ctyname', 
                                        'latitude', 'longitude')])
# merge with network stats
vdf$dc_raw <- dc_raw
vdf$dc_norm <- dc_norm
vdf$ec <- ec
# merge with latent positions
vdf <- cbind(vdf, Xhat)
colnames(vdf)
colnames(vdf)[9:10] <- paste('dim', 1:2, sep = '')
colnames(vdf)


#========
# k = 13
#========

# extract block
block13 <- as.data.frame(model$k13$classification)
colnames(block13) <- 'block'
table(block13)
#'  1   2   3   4   5   6   7   8   9  10  11  12  13 
#'203 261 220 346 248 667 100 233  89  16 494 131  46 

# compile info
vdf13 <- cbind(vdf, as.data.frame(model$k13$data))
vdf13$block <- as.factor(model$k13$classification)
# prob
pr <- model$k13$z
dim(pr)
colnames(pr)
colnames(pr) <- paste('prob', 1:dim(pr)[2], sep = '')
vdf13 <- cbind(vdf13, pr)

# colors
num_color <- 13
mycolors <- c(colorRampPalette(brewer.pal(12, 'Paired'))(12), '#FF00FF')

# plot latent positions
g13 <- ggplot(data = vdf13, aes(x = V1, y = V2, color = block)) +
  geom_point() +
  ggtitle('Latent Positions of Counties', subtitle = 'K = 13') +
  labs(x = 'Dimension 1', y = 'Dimension 2') +
  scale_color_manual(values = mycolors) +
  theme_bw()
g13
ggsave('results/latentpos_out_k13.png', width = 6, height = 6)


#=======
# k = 8
#=======

# extract block
block8 <- as.data.frame(model$k8$classification)
colnames(block8) <- 'block'
table(block8)
#'  1   2   3   4   5   6   7   8
#'363 456 360 441 834 189 266 145

# compile info
vdf8 <- cbind(vdf, as.data.frame(model$k8$data))
vdf8$block <- as.factor(model$k8$classification)
# prob
pr <- model$k8$z
dim(pr)
colnames(pr)
colnames(pr) <- paste('prob', 1:dim(pr)[2], sep = '')
vdf8 <- cbind(vdf8, pr)

# plot latent positions
g8 <- ggplot(data = vdf8, aes(x = V1, y = V2, color = block)) +
  geom_point() +
  ggtitle('Latent Positions of Counties', subtitle = 'K = 8') +
  labs(x = 'Dimension 1', y = 'Dimension 2') +
  scale_color_manual(values = mycolors) +
  theme_bw()
g8
ggsave('results/latentpos_out_k8.png', width = 6, height = 6)


#=======
# k = 7
#=======

# extract block
block7 <- as.data.frame(model$k7$classification)
colnames(block7) <- 'block'
table(block7)
#'  1   2   3   4   5   6   7 
#'222 751 687 317 561 119 397 

# compile info
vdf7 <- cbind(vdf, as.data.frame(model$k7$data))
vdf7$block <- as.factor(model$k7$classification)
# prob
pr <- model$k7$z
dim(pr)
colnames(pr)
colnames(pr) <- paste('prob', 1:dim(pr)[2], sep = '')
vdf7 <- cbind(vdf7, pr)

# plot latent positions
g7 <- ggplot(data = vdf7, aes(x = V1, y = V2, color = block)) +
  geom_point() +
  ggtitle('Latent Positions of Counties', subtitle = 'K = 7') +
  labs(x = 'Dimension 1', y = 'Dimension 2') +
  scale_color_manual(values = mycolors) +
  theme_bw()
g7
ggsave('results/latentpos_out_k7.png', width = 6, height = 6)


#=======
# k = 5
#=======

# extract block
block5 <- as.data.frame(model$k5$classification)
colnames(block5) <- 'block'
table(block5)
#'  1    2    3    4    5
#'389  613 1051  567  434 

# compile info
vdf5 <- cbind(vdf, as.data.frame(model$k5$data))
vdf5$block <- as.factor(model$k5$classification)
# prob
pr <- model$k5$z
dim(pr)
colnames(pr)
colnames(pr) <- paste('prob', 1:dim(pr)[2], sep = '')
vdf5 <- cbind(vdf5, pr)

# plot latent positions
g5 <- ggplot(data = vdf5, aes(x = V1, y = V2, color = block)) +
  geom_point() +
  ggtitle('Latent Positions of Counties', subtitle = 'K = 5') +
  labs(x = 'Dimension 1', y = 'Dimension 2') +
  scale_color_manual(values = mycolors) +
  theme_bw()
g5
ggsave('results/latentpos_out_k5.png', width = 6, height = 6)


#==================
# output for Gephi
#==================

colnames(vdf)
# merge-in block from k = 5
vdf <- left_join(x = vdf, y = vdf5[, c('id', 'block')], by = 'id')
colnames(vdf)[dim(vdf)[2]] <- 'block5'
# merge-in block from k = 7
vdf <- left_join(x = vdf, y = vdf7[, c('id', 'block')], by = 'id')
colnames(vdf)[dim(vdf)[2]] <- 'block7'
# merge-in block from k = 8
vdf <- left_join(x = vdf, y = vdf8[, c('id', 'block')], by = 'id')
colnames(vdf)[dim(vdf)[2]] <- 'block8'
# merge-in block from k = 13
vdf <- left_join(x = vdf, y = vdf13[, c('id', 'block')], by = 'id')
colnames(vdf)[dim(vdf)[2]] <- 'block13'

# output
write.csv(vdf, 'results/vtx_out_all.csv', row.names = F)


# ## degree distribution by block
# View(vdf %>% group_by(block) %>% 
#        summarise(n = n(), prop = round(n / dim(vdf)[1], 3)))
# View(df %>% group_by(block) %>%
#        summarise(dc_raw_min = min(dc_raw),
#                  dc_raw_mid = median(dc_raw),
#                  dc_raw_max = max(dc_raw),
#                  dc_norm_min = round(min(dc_norm), 5),
#                  dc_norm_mid = round(median(dc_norm), 5),
#                  dc_norm_max = round(max(dc_norm), 5)))
# df <- as.data.frame(df)
# ggplot(data = df, aes(x = dc_raw)) +
#   geom_histogram(position = 'identity', color="black", fill="white") +
#   facet_grid(~ block)
# 
# # eigenvector centrality
# ggplot(data = df, aes(x = ec)) +
#   geom_histogram(position = 'identity', color="black", fill="white") +
#   theme(axis.text.x = element_text(angle = 45, vjust = 0.5, hjust = 0.5)) +
#   facet_grid(~ block)



#################
# edge-level vis
#################

# use undirected edges
edf <- as.data.frame(as_edgelist(g, names = T))
colnames(edf)
colnames(edf) <- c('y2fips', 'y1fips')
# convert into numeric
edf$y2fips <- as.numeric(edf$y2fips)
edf$y1fips <- as.numeric(edf$y1fips)

# merge-in blocks for y2
edf <- left_join(x = edf, y = vdf[, c('id', paste('block', c(5, 7, 8, 13), sep = ''))],
                 by = c('y2fips' = 'id'))
colnames(edf)
colnames(edf)[3:6] <- paste('y2', colnames(edf)[3:6], sep = '_')
# merge-in blocks for y1
edf <- left_join(x = edf, y = vdf[, c('id', paste('block', c(5, 7, 8, 13), sep = ''))],
                 by = c('y1fips' = 'id'))
colnames(edf)
colnames(edf)[7:10] <- paste('y1', colnames(edf)[7:10], sep = '_')
# add y2fips = source and y1fips = target for Gephi
edf$Source <- edf$y2fips
edf$Target <- edf$y1fips
# output
write.csv(edf, file = 'results/elst_out_all.csv', row.names = F)


###############
# order blocks
###############

# load data
vdf <- read.csv('results/vtx_out_all.csv')
edf <- read.csv('results/elst_out_all.csv')
vcov <- read_dta('processed data/unzipped/v_all_h.dta')

# merge vdf with out-migration rates
colnames(vcov)[1:15]
# proceed with index_k in [1, 10]
vcov <- vcov[which(vcov$index_k %in% 1:10),]
summary(vcov[, c('otn2', 'epop')])
# calculate annual rates
vcov$otn2_rate <- vcov$otn2 / vcov$epop
summary(vcov$otn2_rate)
#'Min. 1st Qu.  Median    Mean 3rd Qu.    Max.    NA's 
#'0.0000  0.1590  0.1925  0.2038  0.2327 11.8466       2 
print(vcov$otn2_rate[which(vcov$otn2_rate > 1)])
vcov$otn2_rate <- ifelse(vcov$otn2_rate > 1, 1, vcov$otn2_rate)
# reduce to mean across year
vmig <- as.data.frame(
  vcov %>% group_by(fips) %>%
    summarise(otn2_rate = mean(otn2_rate, na.rm = T))
)
colnames(vmig)
hist(vmig$otn2_rate, breaks = 100)
# output plot
png('results/hist_otn2rate.png')
hist(vmig$otn2_rate, breaks = 100)
dev.off()
# summary
summary(vmig$otn2_rate)
#'  Min. 1st Qu.  Median    Mean 3rd Qu.    Max. 
#'0.0000  0.1660  0.1938  0.2033  0.2249  0.9817

# merge into vdf
dim(vdf) # 3054
colnames(vdf)
dim(vmig) # 3141
colnames(vmig)
vdf <- left_join(x = vdf, y = vmig, by = c('id' = 'fips'))

# mean out-migration by block
vdf %>% group_by(block13) %>% 
  summarise(otn2_rate = mean(otn2_rate)) %>%
  arrange(desc(otn2_rate))
vdf %>% group_by(block8) %>% 
  summarise(otn2_rate = mean(otn2_rate))%>%
  arrange(desc(otn2_rate))
vdf %>% group_by(block7) %>% 
  summarise(otn2_rate = mean(otn2_rate)) %>%
  arrange(desc(otn2_rate))
vdf %>% group_by(block5) %>% 
  summarise(otn2_rate = mean(otn2_rate)) %>%
  arrange(desc(otn2_rate))

# merge block into vcov instead
colnames(vcov)[1:15]
colnames(vdf)
vcov <- left_join(x = vcov, y = vdf[, c('id', 'block5', 'block7', 
                                        'block8', 'block13')],
                  by = c('fips' = 'id'))
# mean out-migration by block
b13 <- as.data.frame(
  vcov[which(vcov$fips %in% vdf$id),] %>% group_by(block13) %>%
    summarise(otn2_rate = mean(otn2_rate, na.rm = T)) %>%
    arrange(desc(otn2_rate)) %>%
    add_column(block13_reordered = 1:13)
)
b8 <- as.data.frame(
  vcov[which(vcov$fips %in% vdf$id),] %>% group_by(block8) %>%
    summarise(otn2_rate = mean(otn2_rate, na.rm = T)) %>%
    arrange(desc(otn2_rate)) %>%
    add_column(block8_reordered = 1:8)
)
b7 <- as.data.frame(
  vcov[which(vcov$fips %in% vdf$id),] %>% group_by(block7) %>%
    summarise(otn2_rate = mean(otn2_rate, na.rm = T)) %>%
    arrange(desc(otn2_rate)) %>%
    add_column(block7_reordered = 1:7)
)
b5 <- as.data.frame(
  vcov[which(vcov$fips %in% vdf$id),] %>% group_by(block5) %>%
    summarise(otn2_rate = mean(otn2_rate, na.rm = T)) %>%
    arrange(desc(otn2_rate)) %>%
    add_column(block5_reordered = 1:5)
)

# merge ordered block into vdf
vdf <- left_join(x = vdf, y = b13[, c('block13', 'block13_reordered')], 
                 by = 'block13')
vdf <- left_join(x = vdf, y = b8[, c('block8', 'block8_reordered')], 
                 by = 'block8')
vdf <- left_join(x = vdf, y = b7[, c('block7', 'block7_reordered')], 
                 by = 'block7')
vdf <- left_join(x = vdf, y = b5[, c('block5', 'block5_reordered')], 
                 by = 'block5')

# merge ordered block into edf
colnames(edf)
# for y2
edf <- left_join(x = edf, y = vdf[, c('id', 'block13_reordered', 'block8_reordered',
                                      'block7_reordered', 'block5_reordered')],
                 by = c('y2fips' = 'id'))
colnames(edf)
colnames(edf)[13:16] <- paste('y2', colnames(edf)[13:16], sep = '')
# for y1
colnames(edf)
edf <- left_join(x = edf, y = vdf[, c('id', 'block13_reordered', 'block8_reordered',
                                      'block7_reordered', 'block5_reordered')],
                 by = c('y1fips' = 'id'))
colnames(edf)
colnames(edf)[17:20] <- paste('y1', colnames(edf)[17:20], sep = '')
colnames(edf)

# output reordered blocks
save(vdf, edf, file = 'results/block_reordered_by_otn2rate.rda')

# load saved reordered blocks
load('results/block_reordered_by_otn2rate.rda')


# summarize vertex characteristics by reordered block
t0 <- as.data.frame(
  vdf %>% group_by(block13_reordered) %>%
    summarise(n = n(), p = round(n / dim(vdf)[1], 3),
              mean_dc = round(mean(dc_norm), 5),
              mid_dc = round(median(dc_norm), 5),
              mean_ec = round(mean(ec), 5),
              mid_ec = round(median(ec), 5),
              mean_otn2_rate = round(mean(otn2_rate), 3),
              mid_otn2rate = round(median(otn2_rate), 3))
)
t1 <- as.data.frame(
  vdf %>% group_by(block8_reordered) %>%
    summarise(n = n(), p = round(n / dim(vdf)[1], 3),
              mean_dc = round(mean(dc_norm), 5),
              mid_dc = round(median(dc_norm), 5),
              mean_ec = round(mean(ec), 5),
              mid_ec = round(median(ec), 5),
              mean_otn2_rate = round(mean(otn2_rate), 3),
              mid_otn2rate = round(median(otn2_rate), 3))
)
t2 <- as.data.frame(
  vdf %>% group_by(block7_reordered) %>%
    summarise(n = n(), p = round(n / dim(vdf)[1], 3),
              mean_dc = round(mean(dc_norm), 5),
              mid_dc = round(median(dc_norm), 5),
              mean_ec = round(mean(ec), 5),
              mid_ec = round(median(ec), 5),
              mean_otn2_rate = round(mean(otn2_rate), 3),
              mid_otn2rate = round(median(otn2_rate), 3))
)
t3 <- as.data.frame(
  vdf %>% group_by(block5_reordered) %>%
    summarise(n = n(), p = round(n / dim(vdf)[1], 3),
              mean_dc = round(mean(dc_norm), 5),
              mid_dc = round(median(dc_norm), 5),
              mean_ec = round(mean(ec), 5),
              mid_ec = round(median(ec), 5),
              mean_otn2rate = round(mean(otn2_rate), 3),
              mid_otn2rate = round(median(otn2_rate), 3))
)
# output to excel
write_xlsx(list('k13' = t0, 'k8' = t1, 'k7' = t2, 'k5' = t3),
           'results/block_vtxchar_all.xlsx')


# intersection among blocks
View(vdf %>% group_by(block5_reordered, block8_reordered,
                      block7_reordered, block13_reordered) %>%
       summarise(n = n()))

# top counties in blocks
for(k in c(13, 8, 7, 5)){
  cat('K =', k, '\n')
  for(i in 1:k){
    cat('  Block', i, ':\n')
    cat('    Top 6 by ont2_rate:\n')
    print(head(
      vdf[which(vdf[[paste('block', k, '_reordered', sep = '')]] == i),
          c('id', 'stabbr', 'ctyname', 'dc_norm', 'ec', 'otn2_rate')] %>%
        arrange(desc(otn2_rate))))
    cat('    Top 6 by normalized degree centrality:\n')
    print(head(
      vdf[which(vdf[[paste('block', k, '_reordered', sep = '')]] == i),
          c('id', 'stabbr', 'ctyname', 'dc_norm', 'ec', 'otn2_rate')] %>%
        arrange(desc(dc_norm))))
    cat('    Top 6 by normalized eigenvector centrality:\n')
    print(head(
      vdf[which(vdf[[paste('block', k, '_reordered', sep = '')]] == i),
          c('id', 'stabbr', 'ctyname', 'dc_norm', 'ec', 'otn2_rate')] %>%
        arrange(desc(ec))))
    cat('\n')
  }
  cat('\n\n')
}

# selected metropolitan
View(vdf[which(vdf$id %in% c(36061, 36047, 36005, 36085, 36081)),])
View(vdf[which(vdf$id %in% c(6037, 6059, 6065, 6071, 6111)),])
View(vdf[which(vdf$stabbr == 'FL'),])



######
# viz
######

#=====================
# net repres of block
#=====================

## auxiliary function for block relations
get_blocknet <- function(vdt, edt, k, seed = 123, output = F){
  # target col
  tcol <- paste('block', k, '_reordered', sep = '')
  print(tcol)
  
  # nodes
  print('Summarize vertex characteristics to block...')
  bdf_node <- as.data.frame(
    vdt %>% group_by(.data[[tcol]]) %>%
      summarise(size = n(), prop = round(size / dim(vdt)[1], 3),
                dc = median(dc_norm),
                ec = median(ec))
  )
  dim(bdf_node)
  colnames(bdf_node)
  colnames(bdf_node) <- c('id', 'size', 'prop', 'dc', 'ec')
  bdf_node$label <- paste('Block', bdf_node$id)
  bdf_node <- bdf_node[, c('id', 'label', 'prop')]
  bdf_node$shape <- 'dot'
  colnames(bdf_node)[3] <- 'size'
  bdf_node$size <- bdf_node$size * 300
  
  # edges
  print('Summarize edge characteristics to block...')
  cat('layer1...\n')
  bdf_tmp <- as.data.frame(
    edt %>% group_by(.data[[paste('y1', tcol, sep = '')]], 
                     .data[[paste('y2', tcol, sep = '')]]) %>%
      summarise(size = n(), 
                prop = round(size / dim(edt)[1], 3))
  )
  colnames(bdf_tmp) <- c('from', 'to', 'size', 'prop')
  bdf_tmp$from <- as.numeric(bdf_tmp$from)
  bdf_tmp$to <- as.numeric(bdf_tmp$to)
  # initiate final edge df
  cat('layer2...\n')
  bdf_edge <- crossing(1:k, 1:k)
  bdf_edge[, 3:4] <- 0
  colnames(bdf_edge) <- c('from', 'to', 'size', 'prop')
  bdf_edge <- bdf_edge[which(bdf_edge$from <= bdf_edge$to),]
  for(i in 1:dim(bdf_tmp)[1]){
    tmpi <- min(bdf_tmp[i, c('from', 'to')])
    tmpj <- max(bdf_tmp[i, c('from', 'to')])
    trow <- which(bdf_edge$from == tmpi & bdf_edge$to == tmpj)
    bdf_edge[trow, 'size'] <- bdf_edge[trow, 'size'] + bdf_tmp[i, 'size']
  }
  bdf_edge$prop <- bdf_edge$size / dim(edt)[1]
  colnames(bdf_edge)[4] <- 'value'
  
  # plot block network
  print('Get network representation...')
  p <- visNetwork(bdf_node, bdf_edge, physics = T, idToLabel = T, 
                  width = '100%', height = '1000px') %>%
    visNodes(font = '20px arial red bold') %>% # scaling = list(label = list(enabled = T))
    visEdges(smooth = T) %>%
    visLayout(randomSeed = seed) %>%
    visPhysics(solver = "forceAtlas2Based", stabilization = F,# , stabilization = list(iterations = 20)
               forceAtlas2Based = list(gravitationalConstant = -100)) %>%
    visOptions(highlightNearest = TRUE)
  
  print(p)
  if(output){
    p %>% visSave(file = paste('results/network_out_k', k, 'ordered.html', sep = ''), 
                  background = 'white')
  }
  
  rv <- list()
  rv$nodes <- bdf_node
  rv$edges <- bdf_edge
  rv$plot <- p
  return(rv)
}

# block = 7
t0 <- get_blocknet(vdf, edf, k = 7, output = T)
# block = 13
t0 <- get_blocknet(vdf, edf, k = 13, output = T)
# block = 5
t0 <- get_blocknet(vdf, edf, k = 5, output = T)
# block = 8
t0 <- get_blocknet(vdf, edf, k = 8, output = T)


#==========================
# latent position by block
#==========================

## auxiliary function to plot latent positions
get_latpos <- function(vdt, k, output = F){
  # target col
  tcol <- paste('block', k, '_reordered', sep = '')
  print(tcol)
  vdt[[tcol]] <- factor(vdt[[tcol]], levels = 1:k)
  
  if(k == 13){
    mycolors <- c(colorRampPalette(brewer.pal(12, 'Paired'))(12), 
                  '#FF00FF')
  }
  else{
    mycolors <- colorRampPalette(brewer.pal(k, 'Paired'))(k)
  }
  
  # plot latent positions
  p <- ggplot(data = vdt, aes(x = dim1, y = dim2, color = .data[[tcol]])) +
    geom_point(alpha = 0.7) +
    ggtitle('Latent Positions of Counties', subtitle = paste('K =', k)) +
    labs(x = 'Dimension 1', y = 'Dimension 2') +
    scale_color_manual(values = mycolors) #+
    # theme_bw()
  
  print(p)
  if(output){
    ggsave(paste('results/net_all_k', k, 'reordered.png', sep = ''), 
           width = 6, height = 6)
  }
  
  # output
  rv <- list()
  rv$plot <- p
  rv$colors <- mycolors
  return(rv)
}


# block 7
t1 <- get_latpos(vdf, k = 7, output = T)
# block 13
t1 <- get_latpos(vdf, k = 13, output = T)
# block 5
t1 <- get_latpos(vdf, k = 5, output = T)
# block 8
t1 <- get_latpos(vdf, k = 8, output = T)



