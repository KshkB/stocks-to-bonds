from numpy import nan
from datetime import datetime
from functions import etbListWithValueYield_AU
import matplotlib.pyplot as plt
from scipy.stats import linregress

def sketch_yields():

    bond_list = etbListWithValueYield_AU()
    x_data = []
    y_data = []
    for i, row in bond_list.iterrows():
        try:
            y = row['bond_yields']
            y = y.replace('%', '')
            y = float(y)
            y_data += [y]

            bond_code = row['ASX_code']
            x_data += [bond_code]
        except AttributeError:
            pass 

    # Yields plot
    plt.title('Current yield curve for Aussie eTBs')
    plt.xlabel('eTBs')
    plt.xticks(rotation=70)
    plt.ylabel('Yields (%)')

    # regression plot
    x_data_time = []
    for b_code in x_data:
        # time to maturity
        maturity = bond_list.loc[bond_list['ASX_code'] == b_code, 'maturity'].iloc[0]
        maturity = datetime.strptime(maturity, '%d-%b-%Y')
        time = (maturity - datetime.now()).days / 365.2522 # in years
        time = round(2 * time)//2 # to the nearest half integer

        x_data_time += [time]

    regr_line = linregress(x=x_data_time, y=y_data)
    slope = regr_line.slope
    intercept = regr_line.intercept

    regr_vals = [
        slope * x + intercept for x in x_data_time
    ]
    plt.plot(x_data, y_data)
    plt.plot(x_data_time, regr_vals, label=f'Regr. slope = {round(slope,4)}')

    plt.legend()
    plt.show()
    return
