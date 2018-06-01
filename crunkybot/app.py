'''
Simple Flask application to test deployment to Amazon Web Services
Uses Elastic Beanstalk and RDS

Author: Scott Rodkey - rodkeyscott@gmail.com

Step-by-step tutorial: https://medium.com/@rodkey/deploying-a-flask-application-on-aws-a72daba6bb80
'''
from __future__ import print_function

from flask import Flask, render_template, request
from flask_oauthlib.client import OAuth
from flask import session, redirect, url_for, jsonify
from threading import Lock
import requests
import json
import config
import logging
#from application import db

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
file_handler = logging.FileHandler(filename='flask_error.log')
file_handler.setLevel(logging.WARNING)
app.logger.addHandler(file_handler)

oauth = OAuth()

twitch = oauth.remote_app('twitch',
                          base_url='https://api.twitch.tv/kraken/',
                          request_token_url=None,
                          access_token_method='POST',
                          access_token_url='https://api.twitch.tv/kraken/oauth2/token',
                          authorize_url='https://api.twitch.tv/kraken/oauth2/authorize',
                          consumer_key=config.TWITCH_CLIENTID, # get at: https://www.twitch.tv/kraken/oauth2/clients/new
                          consumer_secret=config.TWITCH_SECRET,
                          request_token_params={'scope': ["user_read", "channel_check_subscription"]}
                          )

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
	data={}
	if 'twitch_token' in session:
		headers = {'Authorization': ("OAuth " + session['twitch_token'][0])}
		r = requests.get(twitch.base_url, headers=headers)
		r2 = requests.get(twitch.base_url+"user",headers=headers)
		resp=r2.json()
		if 'status' not in resp:
			data['logo']=resp['logo']
			data['display_name']=resp['display_name']
		elif resp['status'] == 400:
			return redirect(url_for('login'))
		else:
			return "Access denied: Error "+`resp['status']`+", "+resp['message']
	return render_template("index.html",data=data)
    #return "Hello World."
@twitch.tokengetter
def get_twitch_token(token=None):
    return session.get('twitch_token')


@app.route('/login')
def login():
    return twitch.authorize(callback=url_for('authorized', _external=True))


@app.route('/login/authorized')
def authorized():
    resp = twitch.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error'],
            request.args['error_description']
        )
    session['twitch_token'] = (resp['access_token'], '')
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
	session.pop('twitch_token', None)
	return redirect(url_for('index'))

if __name__ == '__main__':
    app.run( debug = True)