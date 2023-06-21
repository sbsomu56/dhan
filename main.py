from flask import Flask, render_template
import os
import pandas as pd
from dhanhq import dhanhq
# import talib

# Create DHANHQ object for sourcing data:
client_id = os.getenv('DHAN_CLIENT_ID')
access_token = os.getenv('DHAN_API_KEY')
dhan = dhanhq(client_id, access_token)

# load api-script-master
script_master = pd.read_csv('data/api-scrip-master.csv')


# FUNCTIONS:
# 01. get_ltp
def get_ltp(security_id):
  """
    Function to retrieve LTP given a security_id

    Parameters:
    -----------
    security_id: string, default=None
        security_id based on api-scrip-master.csv file
    """
  try:
    df1 = script_master[script_master['SEM_SMST_SECURITY_ID'] == int(
      security_id)]
    instrument_type = df1['SEM_INSTRUMENT_NAME'].iloc[0]

    if instrument_type != "EQUITY":
      exchange_segment = 'NSE_FNO'
    else:
      exchange_segment = 'NSE_EQ'

    df = dhan.intraday_daily_minute_charts(security_id=security_id,
                                           exchange_segment=exchange_segment,
                                           instrument_type=instrument_type)
    df = pd.DataFrame(df['data'])
    df['start_Time'] = df['start_Time'].map(
      lambda x: dhan.convert_to_date_time(x))
    return df.iloc[-1]['close']
  except:
    return 0


# 02. ConvertDailyToWeekly
def ConvertDailyToWeekly(df):
  df = pd.DataFrame(df)
  df['start_Time'] = df['start_Time'].apply(
    lambda x: dhan.convert_to_date_time(x))
  df['Date'] = pd.to_datetime(df['start_Time'])
  df['Week_Number'] = df['Date'].dt.isocalendar().week
  df['Year'] = df['Date'].dt.isocalendar().year
  df = df.groupby(['Year', 'Week_Number']).agg({
    'Date': 'min',
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
  })
  df['ema'] = talib.EMA(df['close'], timeperiod=5)
  df = df.set_index('Date')
  return df


#================#
#   PARAMETERS   #
#================#
# cols in positions:
position_col = [
  'tradingSymbol', 'securityId', 'positionType', 'buyAvg', 'buyQty', 'LTP',
  'PnL'
]

app = Flask(__name__)


@app.route('/')
def home():
  return render_template('home.html')


@app.route('/positions')
def positions():
  positions = dhan.get_positions()['data']
  df = pd.DataFrame(positions)

  df['LTP'] = df['securityId'].map(lambda x: get_ltp(x))

  # df['PnL'] = (df['LTP'] - df['buyAvg']) * df['buyQty']

  idx_long = df['positionType'] == 'LONG'
  df.loc[idx_long,
         'PnL'] = (df.loc[idx_long, 'LTP'] * df.loc[idx_long, 'buyQty'] -
                   df.loc[idx_long, 'dayBuyValue'])

  idx_short = df['positionType'] == 'SHORT'
  df.loc[idx_short,
         'PnL'] = (-df.loc[idx_short, 'LTP'] * df.loc[idx_short, 'sellQty'] +
                   df.loc[idx_short, 'sellAvg'])

  idx_closed = df['positionType'] == 'CLOSED'
  df.loc[idx_closed, 'PnL'] = (-df.loc[idx_closed, 'dayBuyValue'] +
                               df.loc[idx_closed, 'daySellValue'])

  df = df[position_col]
  return render_template('positions.html',
                         tables=[df.to_html(classes='data')],
                         titles=df.columns.values)


@app.route('/screener-15-ema')
def screener_15_ema():
  return render_template('screener_15_ema.html')


if __name__ == "__main__":
  app.run('0.0.0.0', debug=True)
