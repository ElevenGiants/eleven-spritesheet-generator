import eventlet
eventlet.monkey_patch()
import logging
from eleven.worker import http, tasks

# import eventlet.debug
# eventlet.debug.hub_blocking_detection(True)


class SpritesheetGenerator(object):
    def __init__(
        self,
        asset_host_port,
        asset_url,
        api_url,
        secret_key,
        task_timeout,
        amqp_url,
        http_port
    ):
        self.events = {}
        self.asset_host_port = asset_host_port
        self.asset_url = asset_url
        self.api_url = api_url
        self.secret_key = secret_key
        self.task_timeout = task_timeout
        self.amqp_url = amqp_url
        self.http_port = http_port

    def run(self):
        formatter = logging.Formatter(
            '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.addHandler(handler)
        root.setLevel(logging.DEBUG)

        shared = {}

        self.celery_worker = eventlet.spawn(self.celery_worker, shared)
        self.flask_server = eventlet.spawn(self.flask_worker, shared)
        self.celery_worker.wait()
        self.flask_server.wait()

    def celery_worker(self, shared):
        celery_app = tasks.ElevenCelery(
            shared,
            self.secret_key,
            self.task_timeout,
            self.http_port,
            self.amqp_url)
        celery_app.worker_main(['', '-P', 'eventlet'])

    def flask_worker(self, shared):
        flask_app = http.WebServer(
            shared,
            self.secret_key,
            self.asset_host_port,
            self.asset_url,
            self.api_url)
        flask_app.run(host='127.0.0.1', port=self.http_port, debug=False)
