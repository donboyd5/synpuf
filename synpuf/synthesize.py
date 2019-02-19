import pandas as pd
import synthimpute as si
# Also requires installing tzlocal
import rpy2.robjects as robjects
from rpy2.robjects import r, pandas2ri


# Columns to synthesize listed in https://github.com/donboyd5/synpuf/issues/4.
COLS = [
    'DSI',
    'E00200',
    'E00300',
    'E00400',
    'E00600',
    'E00650',
    'E00700',
    'E00800',
    'E00900',
    'E01100',
    'E01200',
    'E01400',
    'E01500',
    'E01700',
    'E02000',
    'E02100',
    'E02300',
    'E02400',
    'E03150',
    'E03210',
    'E03220',
    'E03230',
    'E03240',
    'E03270',
    'E03290',
    'E03300',
    'E03400',
    'E03500',
    'E07240',
    'E07260',
    'E07300',
    'E07400',
    'E07600',
    'E09700',
    'E09800',
    'E09900',
    'E11200',
    'E17500',
    'E18400',
    'E18500',
    'E19200',
    'E19800',
    'E20100',
    'E20400',
    'E24515',
    'E24518',
    'E26270',
    'E27200',
    'E32800',
    'E58990',
    'E62900',
    'E87521',
    'E87530',
    'EIC',
    'F2441',
    'F6251',
    'FDED',
    'MARS',
    'MIDR',
    'N24',
    'P08000',
    'P22250',
    'P23250',
    'S006',
    'XTOT']


CALCULATED_COLS = ['E00100', 'E09600']


# Consider adding E00100 and E09600.
SEED_COLS = ['MARS', 'XTOT', 'S006']
CLASSIFICATION_COLS = ['F6251', 'MIDR', 'FDED', 'DSI']
SEED_COLS = (SEED_COLS + CALCULATED_COLS +
             CLASSIFICATION_COLS)  # Until rf_synth handles classification.


AGG_RECIDS = [999996, 999997, 999998, 999999]


def load_puf(f='puf2011.csv', include_RECID=False):
    """Load raw PUF for synthesis.
    
    Args:
        f: Filepath and name. Defaults to 'puf2011.csv' in the current directory.
        include_RECID: Logical indicating whether to include the RECID field. Defaults
                       to False.
        
    Returns:
        DataFrame limited to relevant columns, no aggregate records, and no RECID (unless specified).
        Also subtracts features that should be nonnegative.
    """
    # Include RECID to exclude 4 aggregate records.
    input_cols = COLS + CALCULATED_COLS + ['RECID']
    puf = pd.read_csv(f, usecols=input_cols)
    # Calculate differences of variables that must be nonnegative for Tax-Calculator to run.
    # Per https://github.com/donboyd5/synpuf/issues/17, e00600 must be weakly greater than
    # e00650 and e01500 must be weakly greater than e01700.
    puf['e00600_minus_e00650'] = puf.E00600 - puf.E00650
    puf['e01500_minus_e01700'] = puf.E01500 - puf.E01700
    puf.drop(['E00600', 'E01500'], axis=1, inplace=True)
    puf = puf[~puf.RECID.isin(AGG_RECIDS)]
    if include_RECID:
        return puf
    return puf.drop('RECID', axis=1)


def add_subtracted_features(df):
    """Add back the subtracted features (to be used after synthesis).

    Args:
        df: DataFrame.
   
    Returns:
        Nothing. Adds features and drops old ones in place.
        Also drops calculated columns used for the synthesis process only.
    """
    df['E00600'] = df.E00650 + df.e00600_minus_e00650
    df['E01500'] = df.E01700 + df.e01500_minus_e01700
    df.drop(['e00600_minus_e00650', 'e01500_minus_e01700'] + CALCULATED_COLS,
            axis=1, inplace=True)

    
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
