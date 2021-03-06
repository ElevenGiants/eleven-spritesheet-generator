#!/usr/bin/env python

from distutils.core import setup

setup(
    name='eleven-spritesheet-generator',
    version='0.1',
    description='Eleven Spritesheet Generator',
    author='Justin Patrin ',
    author_email='papercrane@reversefold.com',
    url='https://github.com/ElevenGiants/eleven-spritesheet-generator/',
    packages=['eleven'],
    install_requires=[
        'Celery>=3.1',
        'subprocess32>=3.2.6',
        'Flask>=0.10.1',
        'eventlet>=0.17.1',
        'reversefold.util>=1.0.4',
        'docopt>=0.6.2',
    ],
    scripts=['scripts/eleven_spritesheet_generator_worker.py'],
)
