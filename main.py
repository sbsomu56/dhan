from flask import Flask, render_template
import os
import pandas as pd
from dhanhq import dhanhq

# Create DHANHQ object for sourcing data:
client_id = os.getenv('DHAN_CLIENT_ID')
access_token = os.getenv('DHAN_API_KEY')
dhan = dhanhq(client_id, access_token)


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
  df = dhan.intraday_daily_minute_charts(security_id=security_id,
                                         exchange_segment='NSE_FNO',
                                         instrument_type='OPTIDX')

  df = pd.DataFrame(df['data'])
  df['start_Time'] = df['start_Time'].map(
    lambda x: dhan.convert_to_date_time(x))
  return df.iloc[-1]['close']


#================#
#   PARAMETERS   #
#================#
# cols in positions:
position_col = [
  'tradingSymbol', 'securityId', 'positionType', 'buyAvg', 'buyQty'
]

app = Flask(__name__)


@app.route('/')
def home():
  return render_template('home.html')


@app.route('/positions')
def positions():
  positions = dhan.get_positions()['data']
  df = pd.DataFrame(positions)
  df = df[df['securityId'] != '10176']
  df = df[position_col]
  df['LTP'] = df['securityId'].map(lambda x: get_ltp(x))
  df['PnL'] = (df['LTP'] - df['buyAvg']) * df['buyQty']

  return render_template('positions.html',
                         tables=[df.to_html(classes='data')],
                         titles=df.columns.values)


if __name__ == "__main__":
  app.run('0.0.0.0', debug=True)
