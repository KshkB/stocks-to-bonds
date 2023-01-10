from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime
from objects import Bond, Stock
from numpy import nan

def etbList_AU():
    url = 'https://www.australiangovernmentbonds.gov.au/bond-types/exchange-traded-treasury-bonds/list-etbs'
    r = requests.get(url, headers={'User-Agent': 'Custom'})
    soup = BeautifulSoup(r.text, 'lxml')
    bond_list = soup.find_all(
        'td'
    )
    cols = [
        'maturity',
        'coupon',
        'ASX_code',
        'payDates'
    ]
    df = pd.DataFrame(columns=cols)
    curr_stack = []
    for i, item in enumerate(bond_list):
        to_append = item.text
        to_append = to_append.replace('\n', '')
        curr_stack += [to_append]
        if i % 4 == 3:
            pd_row = pd.DataFrame([curr_stack], columns=cols)
            df = pd.concat([df, pd_row])
            curr_stack = []

    return df

def etbListWithValueYield_AU():

    bond_list = etbList_AU()
    values = []
    value_ylds = []
    yields = []
    roi = []
    for i, row in bond_list.iterrows():
        code = row['ASX_code']
        fv = 100
        coupon = row['coupon'].replace('%', '')
        coupon = float(coupon)/100
        coupon = coupon/2.0 # paid each half-year period

        maturity = row['maturity']
        maturity = datetime.strptime(maturity, '%d-%b-%Y')
        time = (maturity - datetime.now()).days / 365.2522
        time = round(2 * time)//2 # to the nearest half integer

        yf_bond_code = code + '.AX'
        bond_url = f'https://au.finance.yahoo.com/quote/{yf_bond_code}'
        bond_get = requests.get(bond_url, headers={'User-Agent': 'Custom'})
        bond_soup = BeautifulSoup(bond_get.text, 'lxml')
        try:
            bond_price = bond_soup.find_all( 
                'fin-streamer', {'class':'Fw(b) Fz(36px) Mb(-4px) D(ib)'}
            )[0].text
            bond_price = float(bond_price)

            bond = Bond(
                face=fv, 
                price=bond_price,
                coupon=coupon,
                time=time
            )  
            val = bond.value()

            val_yld = bond.value_yield()
            val_yld = round(val_yld * 100, 2)
            val_yld = str(val_yld) + '%'

            yld = bond.yld()
            yld = 2 * yld
            yld = round(100*yld, 2)
            yld = str(yld) + '%'

            roi_1000 = (1000 // bond_price) * val

            values += [val]
            value_ylds += [val_yld]
            yields += [yld]
            roi += [roi_1000]
        except IndexError:
            values += [nan]
            value_ylds += [nan]
            yields += [nan]
            roi += [nan]

    new_df_col = pd.DataFrame({
        'bond_value': values, 
        'bond_value_yield' : value_ylds, 
        'bond_yields': yields,
        'netReturnOn_AUD1000' : roi
        })
    new_df = bond_list.reset_index(drop=True).join(new_df_col.reset_index(drop=True), how='left')

    return new_df

def etbListWithValueYieldRunRate_AU():
    bond_list = etbListWithValueYield_AU()
    runrates = []
    for i, row in bond_list.iterrows():
        bond_code = row['ASX_code']

        # time to maturity
        maturity = bond_list.loc[bond_list['ASX_code'] == bond_code, 'maturity'].iloc[0]
        maturity = datetime.strptime(maturity, '%d-%b-%Y')
        time = (maturity - datetime.now()).days / 365.2522 # in years
        time = round(2 * time)//2 # to the nearest half integer

        value = row['bond_value']
        if time == 0:
            runrate = 0
            runrates += [runrate]
        else:
            runrate = 2 * value/time # doubled to annualise the rate
            runrates += [runrate] 
        
    new_df_col = pd.DataFrame({'runRate_annualised': runrates})
    new_df = bond_list.reset_index(drop=True).join(new_df_col.reset_index(drop=True), how='left')

    return new_df

def etbList_RROI(div_yld):
    "The RROI/B at dividend yield div_yld"
    bond_list = etbListWithValueYield_AU()
    rroi_list = []
    for i, row in bond_list.iterrows():
        bond_code = row['ASX_code']

        bond_value = row['bond_value_yield']
        try:
            bond_value = bond_value.replace('%', '')
            bond_value = float(bond_value)/100.0
        except AttributeError:
            bond_value = nan

        # time to maturity
        maturity = bond_list.loc[bond_list['ASX_code'] == bond_code, 'maturity'].iloc[0]
        maturity = datetime.strptime(maturity, '%d-%b-%Y')
        time = (maturity - datetime.now()).days / 365.2522 # in years
        time = round(2 * time)//2 # to the nearest half integer

        if time == 0:
            rroi = 0
            rroi = round(100 * rroi, 2)
            rroi_list += [str(rroi) + '%']
        if time == 1:
            rroi = bond_value - div_yld
            rroi = round(100 * rroi, 2)
            rroi_list += [str(rroi) + '%']
        if time >= 2:
            binom = (1/2)*time*(time-1)
            a = binom 
            b = time + binom * div_yld
            c = time * div_yld - bond_value

            rroi = -b + (b**2 - 4 * a * c)**(1/2)
            rroi = rroi/(2*a)

            rroi = round(100 * rroi, 2)
            rroi_list += [str(rroi) + '%']

    new_df_col = pd.DataFrame({f'RROI at {100 * div_yld}%': rroi_list})
    new_df = bond_list.reset_index(drop=True).join(new_df_col.reset_index(drop=True), how='left')

    return new_df

def etbList_RROIs(div_ylds):

    bond_list = etbListWithValueYield_AU()
    all_rrois = []
    for div_yld in div_ylds:
        rroi_list = []
        for i, row in bond_list.iterrows():
            bond_code = row['ASX_code']
            bond_value = row['bond_value_yield']
            try:
                bond_value = bond_value.replace('%', '')
                bond_value = float(bond_value)/100.0
            except AttributeError:
                bond_value = nan

            # time to maturity
            maturity = bond_list.loc[bond_list['ASX_code'] == bond_code, 'maturity'].iloc[0]
            maturity = datetime.strptime(maturity, '%d-%b-%Y')
            time = (maturity - datetime.now()).days / 365.2522 # in years
            time = round(2 * time)//2 # to the nearest half integer

            if time == 0:
                rroi = 0
                rroi = round(100 * rroi, 2)
                rroi_list += [str(rroi) + '%']
            if time == 1:
                rroi = bond_value - div_yld
                rroi = round(100 * rroi, 2)
                rroi_list += [str(rroi) + '%']                
            if time >= 2:
                binom = (1/2)*time*(time-1)
                a = binom 
                b = time + binom * div_yld
                c = time * div_yld - bond_value

                rroi = -b + (b**2 - 4 * a * c)**(1/2)
                rroi = rroi/(2*a)
                
                rroi = round(100 * rroi, 2)
                rroi_list += [str(rroi) + '%']

        all_rrois += [rroi_list]

    rroi_dict = {}
    for i, div_yld in enumerate(div_ylds):
        rroi_dict[f'RROI at {100 * div_yld}%'] = all_rrois[i]

    new_df_cols = pd.DataFrame(rroi_dict)
    new_df = bond_list.reset_index(drop=True).join(new_df_cols.reset_index(drop=True), how='left')
    return new_df

def etbAdj_PE_prelim(bond_code, stock_code):
    
    # Bond data
    bond_facevalue = 100 
    bond_list = etbList_AU()
    try:
        coupon = bond_list.loc[bond_list['ASX_code'] == bond_code, 'coupon'].iloc[0]
        coupon = coupon.replace('%', '')
        coupon = float(coupon)/100
        coupon = coupon/2.0

        maturity = bond_list.loc[bond_list['ASX_code'] == bond_code, 'maturity'].iloc[0]
        maturity = datetime.strptime(maturity, '%d-%b-%Y')
        time = (maturity - datetime.now()).days / 365.2522
        time = round(2 * time)//2 # to the nearest half integer

    except IndexError:
        print(
            f"{bond_code} not found. Try again."
        )
        return

    try:
        yf_bond_code = bond_code + '.AX'
        bond_url = f'https://au.finance.yahoo.com/quote/{yf_bond_code}'
        bond_get = requests.get(bond_url, headers={'User-Agent': 'Custom'})
        bond_soup = BeautifulSoup(bond_get.text, 'lxml')

        bond_price = bond_soup.find_all( 
            'fin-streamer', {'class':'Fw(b) Fz(36px) Mb(-4px) D(ib)'}
        )[0].text
        bond_price = float(bond_price) 
    except IndexError:
        # means bond code was not found on yfinance
        raise NotImplementedError(f"{bond_code} not found")

    bond = Bond(
        face=bond_facevalue, 
        price=bond_price, 
        coupon=coupon, 
        time=time
        )

    # stock data
    stock_url = f'https://au.finance.yahoo.com/quote/{stock_code}'
    stock_get = requests.get(stock_url, headers={'User-Agent': 'Custom'})
    stock_soup = BeautifulSoup(stock_get.text, 'lxml')
    stock_price = stock_soup.find_all(
        'fin-streamer', {'class': 'Fw(b) Fz(36px) Mb(-4px) D(ib)'}
    )[0].text
    stock_price = float(stock_price)

    stock_PE = stock_soup.find_all(
        'td', {'data-test':'PE_RATIO-value'}
    )[0].text
    try:
        stock_PE = float(stock_PE)
    except ValueError:
        stock_PE = nan

    earnings = stock_price/stock_PE

    try:
        div_yld = stock_soup.find_all(
            'td', {'data-test': 'DIVIDEND_AND_YIELD-value'}
        )[0].text
        try:
            div_yld = div_yld.split()
            div_yld = float(div_yld[0]) 
            div_yld = div_yld/100
        except ValueError:
            div_yld = 0.0
    except IndexError:
        div_yld = 0.0

    stock = Stock(
        bond.fv,
        bond.price,
        bond.coupon,
        bond.time,
        stock_price=stock_price,
        earnings=earnings,
        div_yield=div_yld
    )

    return stock

def etbAdj_PE(bond_code, stock_code):
    stock = etbAdj_PE_prelim(bond_code=bond_code, stock_code=stock_code)
    return stock.bond_time()

def etbListAdj_PE(stock_code):

    # dividend yield
    stock_url = f'https://au.finance.yahoo.com/quote/{stock_code}'
    stock_get = requests.get(stock_url, headers={'User-Agent': 'Custom'})
    stock_soup = BeautifulSoup(stock_get.text, 'lxml')
    try:
        div_yld = stock_soup.find_all(
            'td', {'data-test': 'DIVIDEND_AND_YIELD-value'}
        )[0].text
        try:
            div_yld = div_yld.split()
            div_yld = float(div_yld[0]) 
            div_yld = div_yld/100
        except ValueError:
            div_yld = 0.0
    except IndexError:
        div_yld = 0.0

    rrois = etbList_RROI(div_yld=div_yld)
    rrois = rrois[f'RROI at {100 * div_yld}%'].values

    # adjusted PE and excess
    bond_list = etbList_AU()    
    bond_codes = []
    adj_PEs = []
    excess_times = []
    for i, row in bond_list.iterrows():
        bond_code = row['ASX_code']
        bond_codes += [bond_code]
        try:
            adj_PE = etbAdj_PE(bond_code=bond_code, stock_code=stock_code)
            
            adj_PEs += [adj_PE['bond_adj_time']]
            excess_times += [adj_PE['excess']]
        except NotImplementedError:
            adj_PEs += [nan]
            excess_times += [nan]

    df = pd.DataFrame(
        {'ASX_code': bond_codes, 
        f'{stock_code} RROI/B at {100 * div_yld}%' : rrois, 
        f'{stock_code}_adjused PE': adj_PEs, 
        f'{stock_code} excess': excess_times}
    )
    return df
