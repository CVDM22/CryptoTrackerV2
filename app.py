# ./app.py
import os
from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pusher
import requests, json, atexit, time, plotly, plotly.graph_objs as go

# create flask app
app = Flask(__name__)


pusher_CT = pusher.Pusher(
    app_id=os.environ.get("CT_APP_ID"),
    key=os.environ.get("CT_APP_KEY"),
    secret=os.environ.get("CT_APP_SECRET"),
    cluster='eu',
    ssl=True
)


# define variables for data retrieval
times = []
currencies = ["BTC","ETH"]
prices = {"BTC": [], "ETH": []}


@app.route("/")
def index():
    return render_template("index.html")


def retrieve_data():
    # create dictionary for saving current prices
    current_prices = {}
    for currency in currencies:
        current_prices[currency] = []
    # append new time to list of times
    times.append(time.strftime('%H:%M:%S'))

    # make request to API and get response as object
    api_url = "https://min-api.cryptocompare.com/data/pricemulti?fsyms=BTC,ETH&tsyms=EUR".format(",".join(currencies))
    response = json.loads(requests.get(api_url).content)

    # append new price to list of prices for graphs 
    # and set current price for bar chart
    for currency in currencies:
        price = response[currency]['EUR']
        current_prices[currency] = price
        print(current_prices)
        prices[currency].append(price)
        #print(prices["BTC"])

    # create an array of traces for graph data
    graph_data = [go.Scatter(
        x=times, 
        y=prices["BTC"],
        name="{} Prices BTC",
        )]

    graph_data2 = [go.Scatter(
        x=times, 
        y=prices["ETH"],
        name="{} Prices ETH",
        )]

    # create an array of traces for bar chart data
    bar_chart_data = [go.Bar(
        x=currencies,
        y=list(current_prices.values())
        )]

    data = {
        'graph': json.dumps(list(graph_data), cls=plotly.utils.PlotlyJSONEncoder),
        'graph2': json.dumps(list(graph_data2), cls=plotly.utils.PlotlyJSONEncoder),
        'bar_chart': json.dumps(list(bar_chart_data), cls=plotly.utils.PlotlyJSONEncoder)
    }

    # trigger event
    pusher_CT.trigger("crypto", "data-updated", data)


# create schedule for retrieving prices
scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(
    func=retrieve_data,
    trigger=IntervalTrigger(seconds=10),
    id='prices_retrieval_job',
    name='Retrieve prices every 10 seconds',
    replace_existing=True)
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


# run Flask app
app.run(debug=True, use_reloader=False)
