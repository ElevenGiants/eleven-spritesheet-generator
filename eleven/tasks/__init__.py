#!/usr/bin/env python
import multiprocessing

from celery import Celery
from celery.utils.log import get_task_logger


shared = None

log = get_task_logger(__name__)

app = Celery('eleven.tasks', broker='amqp://guest:guest@localhost//')


@app.task
def generateSpritesheets(pc_tsid, avatar_hash):
    #event = multiprocessing.Event()
    # store the data in the shared dict for eleven.http to use
    shared[pc_tsid] = {
        'tsid': pc_tsid,
        'avatar_hash': avatar_hash,
        #'event': event,
    }
    log.warning('%r %r', pc_tsid, avatar_hash)
    # TODO: start up xvfb and chrome with the url

    # wait for the http worker to send us an event saying it's finished
    # TODO: timeout
    #event.wait()
