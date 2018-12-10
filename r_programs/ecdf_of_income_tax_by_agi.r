


#****************************************************************************************************
#                Libraries ####
#****************************************************************************************************
library("magrittr")
library("plyr") # needed for ldply; must be loaded BEFORE dplyr
library("tidyverse")
options(tibble.print_max = 60, tibble.print_min = 60) # if more than 60 rows, print 60 - enough for states
# ggplot2 tibble tidyr readr purrr dplyr stringr forcats
library("readxl")
library("knitr")
library("scales")


#****************************************************************************************************
#                Globals ####
#****************************************************************************************************


#****************************************************************************************************
#                Get data ####
#****************************************************************************************************
# D:\Dropbox\OSPC - Shared\IRS_pubuse_2011
pufdir <- "D:/Dropbox/OSPC - Shared/IRS_pubuse_2011/"
puf.fn <- "puf2011.csv"

puf <- read_csv(paste0(pufdir, puf.fn), 
                col_types = cols(.default= col_double()), 
                n_max=-1)
names(puf) <- str_to_lower(names(puf))


pufnames <- read_csv("./data/pufvars.csv")
pufnames


#****************************************************************************************************
#                Create cdf of weighted income tax liability ####
#****************************************************************************************************
df <- puf %>%
  filter(!recid %in% 999996:999999) %>%
  mutate(wt=s006 / 100) %>%
  select(recid, wt, e06500, e00100) %>%
  arrange(e00100) %>%
  mutate(cum.pct=cumsum(wt * e06500) / sum(wt * e06500))

# compute line segments

capt <- "- x-axis (AGI) is log10 scale\n- For display purposes x-axis is truncated at left to only show AGI >= $10,000"
gtitle <- "Cumulative distribution of weighted total income tax (e06500) vs. Adjusted gross income in 2011 PUF"
gsub <- "Aggregate records excluded before calculating distribution"

sq10 <- c(0, 10e3, 25e3, 50e3, 100e3, 250e3, 500e3, 750e3, 1e6, 1.5e6, 2e6, 3e6, 4e6, 5e6, 10e6, 25e6, 50e6, 100e6)
xlabs <- scales::comma(sq10 / 1e3)
xscale.l10 <- scale_x_log10(name="AGI in $ thousands", breaks=sq10, labels=xlabs)

# geom_segment(aes(x = x1, y = y1, xend = x2, yend = y2, colour = "segment"), data = df)

sz <- 1
df %>%
  filter(e00100 > 10e3) %>%
  ggplot(aes(e00100, cum.pct)) + 
  geom_line(size=1.5, colour="blue") +
  geom_vline(xintercept=250e3, linetype="dashed", colour="red", size=sz) +
  geom_hline(yintercept=.56, linetype="dashed", colour="red", size=sz) +
  geom_vline(xintercept=1e6, linetype="dashed", colour="grey", size=sz) +
  geom_hline(yintercept=.8, linetype="dashed", colour="grey", size=sz) +
  geom_vline(xintercept=3.2e6, linetype="dashed", colour="green", size=sz) +
  geom_hline(yintercept=.9, linetype="dashed", colour="green", size=sz) +
  theme_bw() +
  ggtitle(gtitle, subtitle=gsub) +
  labs(caption=capt) +
  scale_y_continuous(name="Cumulative proportion of the sum of weighted total income tax (e06500)", breaks=c(seq(0, .9, .05), seq(.92, 1, .02))) +
  xscale.l10 +
  theme(axis.text.x=element_text(angle=45, size=10, hjust=1, colour="black")) +
  theme(plot.caption = element_text(hjust=0, size=rel(.8)))

# scale_x_continuous(name="Adjusted gross income", limits=c(0, NA), breaks=c(0, 50e3, 100e3, 250e3, 500e3, 750e3, 1e6)) +



