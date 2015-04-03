# eleven-spritesheet-generator
An asynchronous server-side avatar spritesheet generator for Eleven Giants.

Written in Python. Requires `Xvfb`, `arora`, and the flash plugin to be installed and working.

Uses Celery for task management and assumes using rabbitmq for message queueing. Uses Flask to serve the HTML and JS which runs the flash spritesheet generator as well as to provide an API endpoint for the JS to call to let celery know that the task is finished.
