#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Import required libraries
import pandas as pd
import numpy as np
import yfinance as yf
import math as m
from scipy.stats import linregress
from datetime import date, timedelta


# In[ ]:

#Interval of 180 days for extracting historical data
today_date = date.today()
start_date = date.today()-timedelta(days=180)

#Get trade days in the window using most active stock
all_trades = yf.Ticker('RELIANCE.NS').history(start=start_date, end=today_date)['Volume']
total_trade_days = len(all_trades)

#Momentum Calculated over 90 days
momo_calc_days = total_trade_days - 90

#ATR Calculated over 20 days
ATR_calc_days = total_trade_days - 20

#Define Capital available and Risk Factor which is average movement in a day
Capital = 100000.00
Risk_Factor = 0.002


# In[ ]:


#Import list of Stock from NSE. Consider Nifty 500. Link https://www1.nseindia.com/products/content/equities/indices/nifty_500.htm. Save names appending .NS to Symbol in NSE Stocks excel
tickers = pd.read_excel('/Users/ravibhaskar/Documents/Stocks on the Move/NSE Stocks.xlsx',header=None)[0].tolist()


# In[ ]:

#Define format of output file with required columns
df_Output = pd.DataFrame(columns=['Stock Name', 'Momentum Score', 'Average True Range', 'No. of Shares'])


# In[ ]:

#Function for calculating momentum (slope)
def Calculate_Momentum(close_prices):
    log_prices = np.log(close_prices)[momo_calc_days:]
    x = np.arange(len(log_prices))
    slope, _, rvalue, _, _ = linregress(x, log_prices)
    Annual_Slope = m.exp(slope)**250-1 #Annualization of slope
    Volatility = rvalue**2
    Mom_Score = Annual_Slope*Volatility
    return Mom_Score


# In[ ]:

# Function for calculating Average True Range
def Calculate_ATR(close_prices, high_prices, low_prices):
    
    close_string = close_prices.tolist()[ATR_calc_days-1:total_trade_days-1]
    high_string = high_prices.tolist()[ATR_calc_days:]
    low_string = low_prices.tolist()[ATR_calc_days:]
    
    df_ATR = pd.DataFrame({'High': high_string, 'Low': low_string, 'Prev Close': close_string})
    
    True_Range = 0
    
    for i in df_ATR.index:
        Curr_High = df_ATR['High'][i]
        Curr_Low = df_ATR['Low'][i]
        Prev_Close = df_ATR['Prev Close'][i]
        True_Range = True_Range + max(Curr_High - Curr_Low,abs(Curr_High - Prev_Close), abs(Prev_Close - Curr_Low))
        
    Avg_True_Range = True_Range/20
    return Avg_True_Range


# In[ ]:

#Function for Calculating 100 days Simple Moving Average 
def Calculate_Moving_Average(close_prices):
    windows = close_prices.rolling(100)
    Mov_Avg = windows.mean().tolist()
    return Mov_Avg[len(Mov_Avg)-1]


# In[ ]:

#Function for calculating Maximum day on day movement over last 90 days
def Calculate_Movement(close_prices):
    mom_series = close_prices[momo_calc_days:]
    movement = 0
    for x, y in zip(mom_series, mom_series[1:]):
        movement = max((abs(x - y) / x) * 100, movement)
    return movement


# In[ ]:

#Loop through ticker list and call respective functions
for ticker in tickers:
    trade_volume = yf.Ticker(ticker).history(start=start_date, end=today_date)['Volume']
    if trade_volume.values.any() == 0:         #Exclude stocks not traded in single during the period
        continue
    elif len(trade_volume) < total_trade_days:  #Exclude stocks not listed during entire period
        continue
    else:
        close_prices = yf.Ticker(ticker).history(start=start_date, end=today_date)['Close']
        high_prices = yf.Ticker(ticker).history(start=start_date, end=today_date)['High']
        low_prices = yf.Ticker(ticker).history(start=start_date, end=today_date)['Low']
        current_price = close_prices[total_trade_days-1]
        Momo_Score = Calculate_Momentum(close_prices)
        ATR_Score = Calculate_ATR(close_prices, high_prices, low_prices)
        Curr_Moving_Avg = Calculate_Moving_Average(close_prices)
        Max_Movement = Calculate_Movement(close_prices)
        No_of_Shares = round(Capital*Risk_Factor/ATR_Score,0)
        if Max_Movement > 15:      #Exclude stocks with day on day movement over 15% during the period
            continue
        elif current_price < Curr_Moving_Avg:       #Exclude stocks with Price below 100 day SMA
            continue
        else:
            df_Output = df_Output.append({'Stock Name': ticker,'Momentum Score': Momo_Score, 'Average True Range': ATR_Score, 'No. of Shares': No_of_Shares}, ignore_index = True)

# In[ ]:


df_Output = df_Output.sort_values(by='Momentum Score',ascending = False)
df_Output.to_excel("Output.xlsx",index=False)

