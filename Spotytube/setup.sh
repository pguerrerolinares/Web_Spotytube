#!/bin/bash
pip2 install -r requirements.txt -t lib
virtualenv -p /usr/bin/python2.7 venv && source venv/bin/activate && pip2 install -r requirements.txt
