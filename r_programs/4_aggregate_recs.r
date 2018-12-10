



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
synvars.vals <- c(
  "e00200", "e00300", "e00400", "e00600", "e00650", "e00700", "e00800", "e00900", 
  "e01100", "e01200", "e01400", "e01500", "e01700", 
  "e02000", "e02100", "e02300", "e02400", 
  "e03150", "e03210", "e03220", "e03230", "e03240", "e03270", "e03290", "e03300", "e03400", "e03500", 
  "e07240", "e07260", "e07300", "e07400", "e07600", 
  "e09700", "e09800", "e09900", 
  "e11200", "e17500", "e18400", "e18500", "e19200", "e19800", 
  "e20100", "e20400", "e24515", "e24518", "e26270", "e27200", 
  "e32800", "e58990", "e62900", "e87521", "e87530", 
  "p08000", "p22250", "p23250", "p86421")


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

# get pufnames
pufnames <- read_excel("./data/BoydPUFNotes(2).xlsx", sheet="puf2011_variables", range=cell_limits(c(2, 1), c(NA, 4)))
pufnames
pufnames <- pufnames %>%
  filter(!is.na(vname)) %>%
  mutate(vname=str_to_lower(vname))
pufnames

write_csv(pufnames,"./data/pufvars.csv")

setdiff(names(puf), pufnames$vname)
identical(names(puf) %>% sort, pufnames$vname %>% sort)



#****************************************************************************************************
#                About the aggregate records ####
#****************************************************************************************************
# From the PUF general description booklet
# ... returns that contain one or more amount fields with deemed extremely large values(1)
# have been excluded from the microdata sample and are aggregated into one of four records(2),
# identified by 
#   RECID=999996 for returns reporting negative Adjusted Gross Income (AGI),
#   RECID=999997 for returns reporting positive AGI between $0 and $10,000,000,
#   RECID=999998 for returns reporting positive AGI between $10,000,001 and $100,000,000,
#   RECID=999999 for returns reporting positive AGI of $100,000,001 or more.
# 
# 1 Values are considered extremely large if they are, generally,
#     within the highest 30 amounts reported for any income amount value or
#     within the lowest 30 amounts reported for any negative income.

# 2 A total of 1,155 returns were aggregated, representing 1,300 returns in the population.

# The rules for identifying extremely large values are not applied to amount fields that are statutorily capped, 
# subject to income limits, or calculated from other fields that are subject to these rules.
# Information regarding these aggregate returns can be found in the accompanying tabulation entitled
# “Weighted Counts and Sum of Amounts for Returns Used to Populate Aggregate Records”.

# Q: Could we use the info in the table on aggregate records to create false records with more info than this?


# important veriables
# e05800 Income tax before credits
# s006 weight


#****************************************************************************************************
#                Analyze ####
#****************************************************************************************************
naz <- function(vec) {return(ifelse(is.na(vec), 0, vec))} # convert NA to zero

summary(puf)
glimpse(puf)
names(puf)
aggrecs <- 999996:999999


shares_base <- puf %>%
  mutate(aggrec=ifelse(recid %in% aggrecs, "aggrec", "other"),
         rectype=case_when(recid==999996 ~ "aggrec.negagi",
                           recid %in% 999997:999999 ~ "aggrec.posagi",
                           !recid %in% aggrecs & (e00100 < 0) ~ "other.negagi",
                           !recid %in% aggrecs & (e00100 >= 0) ~ "other.posagi",
                           TRUE ~ "other"),
         negpos=ifelse(str_detect(rectype, "neg"), "negagi", "posagi")) %>%
  mutate(wt=s006 /  100) %>%
  select(recid, aggrec, rectype, negpos, wt, one_of(synvars.vals), e00100, e09600, e06500) %>%
  gather(vname, value, -recid, -aggrec, -rectype, -negpos, -wt) %>%
  left_join(pufnames %>% select(vname, vdesc, category))

glimpse(shares_base)
names(shares_base)

count(shares_base, aggrec, negpos, rectype)

# weighted means for top variables
# get sort order
sortvars <- shares_base %>%
  group_by(vname) %>%
  summarise(sortvalue=sum(value * wt) / 1e6) %>%
  arrange(-sortvalue) %>%
  mutate(order=row_number())

wmeans <- shares_base %>%
  group_by(rectype, vname, vdesc) %>%
  summarise(value=sum(value * wt) / sum(wt)) %>%
  spread(rectype, value) %>%
  left_join(sortvars %>% select(vname, order)) %>%
  ungroup %>%
  arrange(order)

wmeans %>%
  select(-order) %>%
  filter(row_number()<= 25) %>%
  kable(digits=c(0, 0, 0, 0, 0, 0), format.args=list(big.mark = ','))



# vary filter and sort in block below
shares_base %>%
  filter(negpos=="negagi") %>%
  group_by(vname, vdesc, aggrec) %>%
  summarise(valm=sum(value * wt) / 1e6) %>%
  spread(aggrec, valm) %>%
  mutate(filetot=naz(aggrec) + naz(other),
         aggpct=aggrec / (aggrec + other) * 100) %>% 
  arrange(-abs(filetot)) %>%
  ungroup %>%
  filter(row_number()<= 25) %>%
  kable(digits=c(0, 0, 1, 1, 1, 1), format.args=list(big.mark = ','))


# what share of tax is paid by the > $250k records that are not aggregate?
puf %>%
  mutate(rectype=case_when(recid %in% aggrecs ~ "aggrec",
                           !recid %in% aggrecs & (e00100 > 250e3) ~ "agi>250k",
                           TRUE ~ "agi<=250k"),
         wt=s006 /  100) %>%
  group_by(rectype) %>%
  summarise(taxsum=sum(e06500 * wt) / 1e9)


