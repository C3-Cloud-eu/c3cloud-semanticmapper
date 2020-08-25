#!/usr/bin/env python

import os
import service
import mapper
# from service import application
from service import app as application

# todo?
mapper.init()

# def run():
#     service.app.run(debug=False, host='0.0.0.0')


if __name__ == '__main__':
    # mapper.init()
    application.run(debug=False, host='0.0.0.0')

