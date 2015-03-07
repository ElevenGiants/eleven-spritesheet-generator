import logging
import eventlet
eventlet.monkey_patch()

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
        import eleven.tasks
        from eleven.tasks import app as celery_app

        eleven.tasks.shared = shared
        celery_app.worker_main(['', '-P', 'eventlet'])

    def flask_worker(self, shared):
        import eleven.http
        flask_app = eleven.http.WebServer(shared)
        flask_app.run(host='127.0.0.1', port=5000, debug=False)


if __name__ == '__main__':
    SpritesheetGenerator().main()
