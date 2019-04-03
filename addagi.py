import pandas as pd
import numpy as np
import taxcalc as tc
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('input', help='Name of the input file')
parser.add_argument('output', help='Name of the output file')

args = parser.parse_args()

# read in PUF from provided input
puf = pd.read_csv(args.input)
puf.drop(['FDED', 'E00100', 'E09600'], axis=1, inplace=True)
# basic data cleaning for tax-calc
upper_vars = {'DSI', 'EIC', 'MARS', 'MIDR', 'XTOT'}
puf.columns = [x.lower() if x not in upper_vars else x for x in puf.columns]
puf['RECID'] = puf.index + 1
# assume equal split of income between primary and secondary tax payer
puf['e00200p'] = np.where(puf['MARS'] == 1, puf['e00200'], puf['e00200'] * 0.5)
puf['e00200s'] = puf['e00200'] - puf['e00200p']
puf['e00900p'] = np.where(puf['MARS'] == 1, puf['e00900'], puf['e00900'] * 0.5)
puf['e00900s'] = puf['e00900'] - puf['e00900p']
puf['e02100p'] = np.where(puf['MARS'] == 1, puf['e02100'], puf['e02100'] * 0.5)
puf['e02100s'] = puf['e02100'] - puf['e02100p']

# run calculator with the input file
calc = tc.Calculator(policy=tc.Policy(),
                     records=tc.Records(puf))
calc.calc_all()
data = calc.dataframe(list(puf.columns) + ['c00100'])
# minor clean up to shrink file size
data = data.round(1)
int_vars = ['MARS', 'XTOT', 'MIDR', 'DSI', 'EIC', 'RECID']
data[int_vars] = data[int_vars].apply(pd.to_numeric)
data.to_csv(args.output, index=None)
