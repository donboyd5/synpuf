import pandas as pd
import synthimpute as si
# Also requires installing tzlocal
import rpy2.robjects as robjects
from rpy2.robjects import r, pandas2ri


# Columns to synthesize listed in https://github.com/donboyd5/synpuf/issues/4.
COLS = [
    'dsi',
    'e00200',
    'e00300',
    'e00400',
    'e00600',
    'e00650',
    'e00700',
    'e00800',
    'e00900',
    'e01100',
    'e01200',
    'e01400',
    'e01500',
    'e01700',
    'e02000',
    'e02100',
    'e02300',
    'e02400',
    'e03150',
    'e03210',
    'e03220',
    'e03230',
    'e03240',
    'e03270',
    'e03290',
    'e03300',
    'e03400',
    'e03500',
    'e07240',
    'e07260',
    'e07300',
    'e07400',
    'e07600',
    'e09700',
    'e09800',
    'e09900',
    'e11200',
    'e17500',
    'e18400',
    'e18500',
    'e19200',
    'e19800',
    'e20100',
    'e20400',
    'e24515',
    'e24518',
    'e26270',
    'e27200',
    'e32800',
    'e58990',
    'e62900',
    'e87521',
    'e87530',
    'eic',
    'f2441',
    'f6251',
    'fded',
    'mars',
    'midr',
    'n24',
    'p08000',
    'p22250',
    'p23250',
    's006',
    'xtot']


SEED_COLS = ['MARS', 'E00100', 'E09600', 'XTOT', 'S006']
CLASSIFICATION_COLS = ['F6251', 'MIDR', 'FDED', 'DSI']
SEED_COLS += CLASSIFICATION_COLS  # Until rf_synth handles classification.


AGG_RECIDS = [999996, 999997, 999998, 999999]


def load_puf(f='puf2011.csv'):
    """Load raw PUF for synthesis.
    
    Args:
        f: Filepath and name. Defaults to 'puf2011.csv' in the current directory.
        
    Returns:
        DataFrame limited to relevant columns, no aggregate records, and no RECID.
        Also subtracts features that should be nonnegative.
    """
    # Include RECID to exclude 4 aggregate records.
    input_cols = [x.upper() for x in COLS] + ['RECID']
    raw = pd.read_csv('puf2011.csv', usecols=input_cols)
    # Calculate differences of variables that must be nonnegative for Tax-Calculator to run.
    # Per https://github.com/donboyd5/synpuf/issues/17, e00600 must be weakly greater than
    # e00650 and e01500 must be weakly greater than e01700.
    raw['e00600_minus_e00650'] = raw.E00600 - raw.E00650
    raw['e01500_minus_e01700'] = raw.E01500 - raw.E01700
    raw.drop(['E00600', 'E01500'], axis=1, inplace=True)
    return raw[~raw.RECID.isin(AGG_RECIDS)].drop('RECID', axis=1)


def add_subtracted_features(df):
    """Add back the subtracted features (to be used after synthesis).

    Args:
        df: DataFrame.
   
    Returns:
        Nothing. Adds features and drops old ones in place.
    """
    df['E00600'] = df.E00650 + df.e00600_minus_e00650
    df['E01500'] = df.E01700 + df.e01500_minus_e01700
    df.drop(['e00600_minus_e00650', 'e01500_minus_e01700'], axis=1, inplace=True)

    
def synthesize_puf_rf(puf=None, random_state=0, seed_cols=SEED_COLS, trees=20):
    """Synthesize PUF via random forests.
    
    Args:
        puf: PUF file produced from load_puf(). If not provided, will load via load_puf().
        random_state: random_state passed to synthimpute rf_synth. Defaults to 0.
        seed_cols: seed_cols passed to synthimpute rf_synth. Defaults to
                   ['MARS', 'E00100', 'E09600', 'XTOT', 'S006', 'F6251', 'MIDR', 'FDED', 'DSI'].
        trees: trees passed to synthimpute rf_synth. Defaults to 20.
 
    Returns:
        PUF synthesis produced via random forests.
    """
    if puf is None:
        puf = load_puf()
    result = si.rf_synth(puf, random_state=random_state, seed_cols=seed_cols, trees=trees)
    add_subtracted_features(result)
    return result.round()


def synthesize_puf_synthpop(puf=None):
    """Synthesize PUF via synthpop R package (CART).
    
    Args:
        puf: PUF file produced from load_puf(). If not provided, will load via load_puf().
 
    Returns:
        PUF synthesis produced via CART.
    """
    if puf is None:
        puf = load_puf()
    pandas2ri.activate()
    robjects.r('library(synthpop)')
    robjects.globalenv['puf'] = puf
    result = robjects.r('syn(puf)$syn')
    add_subtracted_features(result)
    return result.round()
