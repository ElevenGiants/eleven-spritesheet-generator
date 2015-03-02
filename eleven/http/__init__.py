from flask import Flask, render_template, abort
from itsdangerous import URLSafeSerializer, BadSignature


class WebServer(object):
    def __init__(self, shared, asset_host_port='192.168.23.23:8000', asset_url='http://192.168.23.23:8000/', api_url='http://192.168.23.23:9001/', secret_key='eleven_giants'):
        self.app = Flask(__name__)
        self.app.secret_key = secret_key
        self.shared = shared
        self.asset_host_port = asset_host_port
        self.asset_url = asset_url
        self.api_url = api_url

        self.generate = self.app.route('/generate/<payload>')(self.generate)
        self.done = self.route('/done/<payload>', self.generate)

    def route(self, route, func):
        return self.app.route(route)(func)

    def get_serializer(self, secret_key=None):
        if secret_key is None:
            secret_key = self.app.secret_key
        return URLSafeSerializer(secret_key)

    def parse_payload(self, payload):
        s = self.get_serializer()
        try:
            return s.loads(payload)
        except BadSignature:
            abort(404)

    def generate(self, payload):
        tsid = self.parse_payload(payload)

        if tsid not in self.shared:
            abort(404)

        pc_data = self.shared[tsid]

        data = {
            'tsid': tsid,
            'asset_host_port': self.asset_host_port,
            'asset_server': self.asset_url,
            'actuals': pc_data['actuals'],
            'base_hash': pc_data['avatar_hash'],
            'ava_settings': {},
            'api_url': self.api_url,
            'player_tsid': tsid,
        }
        return render_template('index.html', **data)

    def done(self, payload):
        tsid = self.parse_payload(payload)

        if tsid not in self.shared:
            abort(404)

        pc_data = self.shared[tsid]
        pc_data['event'].set()

        # no content
        abort(204)

    def run(self, *args, **kwargs):
        return self.app.run(*args, **kwargs)
