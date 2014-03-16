import jinja2
import os
import webapp2

from flask import Flask
from flask import request
from flask import redirect
from functools import wraps
from google.appengine.api import users

from models import Profile, Entry

def nl2br(value):
    return value.replace('\n','<br>\n')

def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not users.get_current_user():
            return redirect(users.create_login_url(request.url))
        return func(*args, **kwargs)
    return decorated_view

jinja = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates"),)
jinja.filters['nl2br'] = nl2br

app = Flask('workjournal')

@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'GET':
        profile = Profile.get_or_create(users.get_current_user())
        edit = request.query_string == 'edit'
        return jinja.get_template('home.html').render(locals())

    elif request.method == 'POST':
        profile = Profile.get_or_create(users.get_current_user())
        if request.query_string == 'edit':
            e = profile.entry_today
            e.body = request.form.get('body')
        else:
            e = Entry(body=request.form.get('body'))
        e.put()
        return redirect(request.path)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'GET':
        profile = Profile.get_or_create(users.get_current_user())
        return jinja.get_template('settings.html').render(locals())

    elif request.method == 'POST':
        profile = Profile.get_or_create(users.get_current_user())
        profile.timezone_offset = int(request.form.get('timezone_offset'))
        profile.digest_hour = int(request.form.get('digest_hour'))
        profile.ask_hour = int(request.form.get('ask_hour'))
        profile.put()
        return redirect(request.path)

@app.route('/logout')
@login_required
def logout():
    return jinja.get_template('journal.html').render(locals())

@app.route('/<username>')
@login_required
def journal(username):
    profile = Profile.get_or_create(users.get_current_user())
    return jinja.get_template('journal.html').render(locals())
