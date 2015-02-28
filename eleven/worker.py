import logging
import multiprocessing
import time


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

        manager = multiprocessing.Manager()
        shared = manager.dict()

        self.celery_worker = multiprocessing.Process(name='celery_worker', target=self.celery_worker, args=(shared,))
        self.celery_worker.start()
        self.flask_server = multiprocessing.Process(name='flask_server', target=self.flask_worker, args=(shared,))
        self.flask_server.start()
        try:
            while True:
                time.sleep(0.1)
        finally:
            self.celery_worker.terminate()
            self.flask_server.terminate()

    def celery_worker(self, shared):
        import eleven.tasks
        from eleven.tasks import app as celery_app

        eleven.tasks.shared = shared
        celery_app.worker_main()

    def flask_worker(self, shared):
        import eleven.http
        '''
        from eleven.http import app as flask_app

        eleven.http.shared = shared
        '''
        flask_app = eleven.http.WebServer(shared)
        flask_app.run(host='0.0.0.0', debug=False)


if __name__ == '__main__':
    SpritesheetGenerator().main()
