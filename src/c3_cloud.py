#!/usr/bin/env python

import os
import service
import mapper
import logging


if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    service.app.logger.handlers = gunicorn_logger.handlers
    service.app.logger.setLevel(gunicorn_logger.level)
    service.app.logger.setLevel(logging.DEBUG)

mapper.init()
app = service.app
    
def run():
    service.app.run(debug=True, host='0.0.0.0')
    
if __name__ == '__main__':
    run()
