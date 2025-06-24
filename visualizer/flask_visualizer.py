import json
import collections
import time
from flask import Flask, request
from gevent.pywsgi import WSGIServer
from flask_cors import *


class FlaskVisualizer:
    app = Flask(__name__)
    data_queue = collections.deque(maxlen=10)
    tps_queue = collections.deque(maxlen=10)
    CORS(app, supports_credentials=True)

    @staticmethod
    @app.route('/', methods=['GET'])
    def index():
        return "Hello, World!"

    @staticmethod
    @app.route("/add_tps", methods=["POST"])
    def add_tps():
        data = json.loads(request.data)
        current_timestamp = data["current_time_stamp"]
        current_tps = data["tps"]
        print(data, flush=True)
        FlaskVisualizer.tps_queue.append((current_timestamp, current_tps))
        response_data = {
            "status": "success"
        }
        response_json_str = json.dumps(response_data)
        # 进行响应数据的构建
        headers = {"Content-Type": "application/json"}
        return response_json_str, 200, headers

    @staticmethod
    @app.route('/data_add', methods=["POST"])
    def receive_data():
        # 将传入的请求参数进行解析
        data = json.loads(request.data)
        current_timestamp = data["current_time_stamp"]
        current_data_rate = data["current_data_rate"]
        current_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(float(current_timestamp))))
        FlaskVisualizer.data_queue.append((current_date, current_data_rate))
        response_data = {
            "status": "success"
        }
        response_json_str = json.dumps(response_data)
        # 进行响应数据的构建
        headers = {"Content-Type": "application/json"}
        return response_json_str, 200, headers

    @staticmethod
    @app.route("/data_get", methods=["GET"])
    def get_data():
        # 获取的总是长度为100的队列
        response_data = {
            "attack_rate": {item[0]: item[1] for item in FlaskVisualizer.data_queue},
            "tps":  {item[0]: item[1] for item in FlaskVisualizer.tps_queue}
        }
        response_json_str = json.dumps(response_data)
        headers = {"Content-Type": "application/json"}
        return response_json_str, 200, headers

    def start_server(self):
        http_server = WSGIServer(('10.134.148.77', 13000), FlaskVisualizer.app)
        http_server.serve_forever()


if __name__ == "__main__":
    flask_visualizer = FlaskVisualizer()
    flask_visualizer.start_server()
