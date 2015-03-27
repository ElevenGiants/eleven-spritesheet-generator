import eventlet
eventlet.monkey_patch()
import logging
from eleven.worker import config, http, tasks

# import eventlet.debug
# eventlet.debug.hub_blocking_detection(True)


class SpritesheetGenerator(object):
    def __init__(self):
        self.events = {}

    def main(self):
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
        celery_app = tasks.ElevenCelery(shared, config.secret_key, config.task_timeout, config.http_port, config.amqp_url)
        celery_app.worker_main(['', '-P', 'eventlet'])

    def flask_worker(self, shared):
        flask_app = http.WebServer(shared, config.secret_key, config.asset_host_port, config.asset_url, config.api_url)
        flask_app.run(host='127.0.0.1', port=config.http_port, debug=False)


if __name__ == '__main__':
    SpritesheetGenerator().main()
