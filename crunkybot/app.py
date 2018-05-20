'''
Simple Flask application to test deployment to Amazon Web Services
Uses Elastic Beanstalk and RDS

Author: Scott Rodkey - rodkeyscott@gmail.com

Step-by-step tutorial: https://medium.com/@rodkey/deploying-a-flask-application-on-aws-a72daba6bb80
'''
from __future__ import print_function

from flask import Flask, render_template, request
from threading import Lock
import logging
#from application import db

app = Flask(__name__)
file_handler = logging.FileHandler(filename='/tmp/election_error.log')
file_handler.setLevel(logging.WARNING)
app.logger.addHandler(file_handler)

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():    
    return render_template("index.html")
    #return "Hello World."

if __name__ == '__main__':
    app.run( debug = True)