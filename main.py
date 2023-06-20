from flask import Flask, render_template
import os
import pandas as pd
from dhanhq import dhanhq

# Create DHANHQ object for sourcing data:
client_id = os.getenv('DHAN_CLIENT_ID')
access_token = os.getenv('DHAN_API_KEY')
dhan = dhanhq(client_id, access_token)

# cols in positions:
position_col = ['tradingSymbol', 'positionType', 'buyAvg', 'buyQty']

app = Flask(__name__)


@app.route('/')
def hello_world():
  positions = dhan.get_positions()['data']
  df = pd.DataFrame(positions)
  df = df[position_col]
  # return render_template('table.html',
  #                        tables=[df.to_html(classes='data')],
  #                        titles=df.columns.values)
  # return render_template('home.html',
  #                        nav_bar=render_template('navbar.html'),
  #                        positions=render_template(
  #                          'table.html',
  #                          tables=[df.to_html(classes='data')],
  #                          titles=df.columns.values))
  return render_template('navbar.html')


if __name__ == "__main__":
  app.run('0.0.0.0', debug=True)
