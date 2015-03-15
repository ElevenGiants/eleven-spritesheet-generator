#!/usr/bin/env python
import logging
import os
import time

from celery import Celery
from celery.utils.log import get_task_logger
from eventlet.event import Event
from eventlet.green import subprocess
from itsdangerous import URLSafeSerializer
from reversefold.util import multiproc


class Error(StandardError):
    pass


class ElevenCelery(object):
    def __init__(self, shared, config):
        self.shared = shared

        self.secret_key = config.secret_key
        self.task_timeout = config.task_timeout
        self.http_port = config.http_port

        self.log = get_task_logger(__name__)

        self.app = Celery('eleven.tasks', broker=config.amqp_url)
        # self.app.conf.CELERYD_HIJACK_ROOT_LOGGER = False
        self.app.conf.CELERYD_LOG_LEVEL = logging.DEBUG

        self.generateSpritesheets = self.app.task()(self.generateSpritesheets)

    def generateSpritesheets(self, pc_tsid, actuals, base_hash):
        event = Event()
        # store the data in the shared dict for eleven.http to use
        self.shared[pc_tsid] = {
            'tsid': pc_tsid,
            'actuals': actuals,
            'avatar_hash': base_hash,
            'event': event,
        }
        self.log.info('generateSpritesheets started for %r', pc_tsid)
        self.log.debug('generateSpritesheets data %r %r %r', pc_tsid, actuals, base_hash)

        # We need to loop here in case the displays are already being used. We loop until
        # we find a free display.
        xvfb = xvfb_threads = browser = browser_threads = None
        try:
            self.log.info('Starting Xvfb for %s' % (pc_tsid,))
            for DISPLAY_NUM in xrange(0, 100):
                xvfb = subprocess.Popen(
                    ['Xvfb', ':%i' % (DISPLAY_NUM,)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                xvfb.stdin.close()
                (_, _, xvfb_threads) = multiproc.run_subproc(xvfb, '[xvfb]    ', wait=False)
                # sleep for 1s to see if it's going to die
                time.sleep(1)
                if xvfb.returncode is None:
                    # Xvfb is running
                    break
                # we got a returncode, so Xvfb exited before it should have, terminate and
                # try the next display number
                multiproc.terminate_subproc(xvfb, xvfb_threads)
                self.log.debug('Display number %i appears to be in use, trying the next one', DISPLAY_NUM)
            if xvfb.returncode is not None:
                raise Error('No free display found for use with Xvfb')

            tsid_signed = URLSafeSerializer(self.secret_key).dumps(pc_tsid)

            # grab the existing environment variables and add/change DISPLAY to the one Xvfb
            # is running on.
            env = os.environ.copy()
            env['DISPLAY'] = ':%i' % (DISPLAY_NUM,)
            url = 'http://127.0.0.1:%i/generate/%s' % (self.http_port, tsid_signed)
            self.log.info('Loading URL %s for %s' % (url, pc_tsid))
            browser = subprocess.Popen(
                ['arora', url],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
            browser.stdin.close()
            (_, _, browser_threads) = multiproc.run_subproc(browser, '[browser] ', wait=False)

            start = time.time()
            while time.time() - start < self.task_timeout:
                # wait for the http worker to send us an event saying that the browser hit the done API
                if event.ready():
                    break
                time.sleep(0.05)
            if not event.ready():
                raise Exception('Spritesheet generation exceeded task timeout %is' % (self.task_timeout,))
            self.log.info('generateSpritesheets done for %r', pc_tsid)
        finally:
            if browser is not None:
                self.log.info('terminating browser proc')
                browser.terminate()
                multiproc.terminate_subproc(browser, browser_threads)
            if xvfb is not None:
                self.log.info('terminating xvfb proc')
                xvfb.terminate()
                multiproc.terminate_subproc(xvfb, xvfb_threads)
            del self.shared[pc_tsid]
        self.log.info('finished')

    def worker_main(self, *args, **kwargs):
        self.app.worker_main(*args, **kwargs)
