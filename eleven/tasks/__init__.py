#!/usr/bin/env python
import logging

from celery import Celery
from celery.utils.log import get_task_logger
from eventlet.event import Event


shared = None

log = get_task_logger(__name__)

app = Celery('eleven.tasks', broker='amqp://guest:guest@localhost//')
# app.conf.CELERYD_HIJACK_ROOT_LOGGER = False
app.conf.CELERYD_LOG_LEVEL = logging.DEBUG


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
    # TODO: start up xvfb and chrome with the url

    # wait for the http worker to send us an event saying it's finished
    # TODO: timeout
    event.wait()
    log.info('generateSpritesheets done for %r', pc_tsid)
