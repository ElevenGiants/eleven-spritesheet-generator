from flask import Flask, render_template, abort
from itsdangerous import URLSafeSerializer, BadSignature


class WebServer(object):
    def __init__(self, shared, config):
        self.app = Flask(__name__)
        self.shared = shared

        self.app.secret_key = config.secret_key
        self.asset_host_port = config.asset_host_port
        self.asset_url = config.asset_url
        self.api_url = config.api_url

        self.generate = self.app.route('/generate/<payload>')(self.generate)
        self.done = self.route('/done/<payload>', self.done)

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
        pc_data['event'].send()

        # no content
        return ('done', 204)

    def run(self, *args, **kwargs):
        return self.app.run(*args, **kwargs)
