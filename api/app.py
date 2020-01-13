from flask import Flask, request, jsonify, render_template
from redis import Redis, RedisError
from datetime import datetime
import requests
import sys
import os
import socket

# Connect to Redis
host = os.getenv("GET_HOSTS_FROM", "redis"))
redis = Redis(host=host, db=0, socket_connect_timeout=2, socket_timeout=2)
app = Flask(__name__)

default_api_info = """<h1>API - Temperatures</h1>
    <p><strong>GET /nuevo/:data</strong> to add new data</p>
    <p><strong>GET /nuevo/404</strong> to close the server</p>
    <p><strong>GET /flush</strong> to clean Redis server</p>
    <p><strong>GET /listar</strong> to get all the temperature data</p>
    <p><strong>GET /grafica</strong> to get the graph</p>
    <p><strong>GET /listajson</strong> to get the last 10 temperature data</p>
    """
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/', methods=['GET'])
def home():
    return default_api_info

@app.errorhandler(404)
def page_not_found(e):
    return default_api_info

# A route to flush the Redis server
@app.route('/flush', methods=['GET'])
def api_flush():
    try:
        redis.flushall()
        for i in range (10):
            redis.lpush("temperature#timestamp",datetime.now().strftime("%Y/%m/%d, %H:%M:%S"))
            redis.lpush("temperature#data",0)
    except:
        return """<h1>API - Temperatures</h1>
            <p>Cannot connect to Redis</p>
            """

    return """<h1>API - Temperatures</h1>
        <p>Redis flushed</p>
        """

# A route to get all the temperature data
@app.route('/listar', methods=['GET'])
def api_list():
    all_data = []
    try:
        for i in range (redis.llen("temperature#timestamp")):
            timestamp = redis.lindex("temperature#timestamp",i).decode("utf-8")
            data = redis.lindex("temperature#data",i).decode("utf-8")
            all_data.append({"data" : data , "timestamp" : timestamp})
    except:
        all_data.append({"data" : 404 , "timestamp" : 404})
    return jsonify(all_data)

# A route to get the last 10 temperature data
@app.route("/listajson", methods=['GET'])
def api_ten():
    all_data = []
    try:
        if (redis.llen("temperature#timestamp") > 10):
            for i in range (10):
                timestamp = redis.lindex("temperature#timestamp",i).decode("utf-8")
                data = redis.lindex("temperature#data",i).decode("utf-8")
                all_data.append({"data" : data , "timestamp" : timestamp})
        else:
            for i in range (redis.llen("temperature#timestamp")):
                timestamp = redis.lindex("temperature#timestamp",i).decode("utf-8")
                data = redis.lindex("temperature#data",i).decode("utf-8")
                all_data.append({"data" : data , "timestamp" : timestamp})
    except:
        all_data.append({"data" : 404 , "timestamp" : 404})
    return jsonify(all_data)

# A route to add new data
@app.route('/nuevo/<string:data>', methods=['GET'])
def api_new(data):
    try: 
        data = int(data)
    except ValueError:
        return """<h1>API - Temperatures</h1>
        <p>INCORRECT DATA</p>
        """
    
    if (data==404):
        shutdown_server()
        return """<h1>API - Temperatures</h1>
            <p>Server Down</p>
            """

    try:
        redis.lpush("temperature#timestamp",datetime.now().strftime("%Y/%m/%d, %H:%M:%S"))
        redis.lpush("temperature#data",data)
    except:
        return """<h1>API - Temperatures</h1>
            <p>Cannot connect to Redis</p>
            """

    return """<h1>API - Temperatures</h1>
        <p>Data inserted</p>
        """

# A route to show a graph
@app.route('/grafico' ,methods=['GET'])
def api_graph():

    line_labels = []
    line_values = []
    response = requests.get("http://localhost/listajson")

    for dictionary in response.json():
        line_labels.append(dictionary["timestamp"])
        line_values.append(dictionary["data"])
    
    return render_template('line_chart.html', title='API - Temperatures', max=20, labels=line_labels, values=line_values)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)