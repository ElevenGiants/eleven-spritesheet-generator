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


shared = None

log = get_task_logger(__name__)

app = Celery('eleven.tasks', broker='amqp://guest:guest@localhost//')
# app.conf.CELERYD_HIJACK_ROOT_LOGGER = False
app.conf.CELERYD_LOG_LEVEL = logging.DEBUG


class Error(StandardError):
    pass


@app.task
def generateSpritesheets(pc_tsid, actuals, base_hash):
    event = Event()
    # store the data in the shared dict for eleven.http to use
    shared[pc_tsid] = {
        'tsid': pc_tsid,
        'actuals': actuals,
        'avatar_hash': base_hash,
        'event': event,
    }
    log.info('generateSpritesheets started for %r', pc_tsid)
    log.debug('generateSpritesheets data %r %r %r', pc_tsid, actuals, base_hash)

    xvfb = xvfb_threads = browser = browser_threads = None
    try:
        log.info('Starting Xvfb for %s' % (pc_tsid,))
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
                break
            multiproc.terminate_subproc(xvfb, xvfb_threads)
            log.debug('Display number %i appears to be in use, trying the next one', DISPLAY_NUM)
            # if the process is done, we need to try another display
        if xvfb.returncode is not None:
            raise Error('No free display found for use with Xvfb')

        # TODO: get this from the web app
        tsid_signed = URLSafeSerializer('eleven_giants').dumps(pc_tsid)

        env = os.environ.copy()
        env['DISPLAY'] = ':%i' % (DISPLAY_NUM,)
        url = 'http://127.0.0.1:5000/generate/%s' % (tsid_signed,)
        log.info('Loading URL %s for %s' % (url, pc_tsid))
        browser = subprocess.Popen(
            ['arora', url],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        browser.stdin.close()
        (_, _, browser_threads) = multiproc.run_subproc(browser, '[browser] ', wait=False)

        # TODO: timeout
        # wait for the http worker to send us an event saying that the browser hit the done API
        event.wait()
        log.info('generateSpritesheets done for %r', pc_tsid)
        del shared[pc_tsid]
    finally:
        if browser is not None:
            log.info('terminating browser proc')
            browser.terminate()
            multiproc.terminate_subproc(browser, browser_threads)
        if xvfb is not None:
            log.info('terminating xvfb proc')
            xvfb.terminate()
            multiproc.terminate_subproc(xvfb, xvfb_threads)
    log.info('finished')
