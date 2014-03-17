import logging
import jinja2
import os
import webapp2

from flask import Flask
from flask import request
from flask import redirect
from functools import wraps
from google.appengine.api import users
from google.appengine.api import mail

from models import Profile, Entry

ADMIN_EMAIL = "progrium@gmail.com"

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
        profile.prompt_hour = int(request.form.get('prompt_hour'))
        profile.put()
        return redirect(request.path)

@app.route('/logout')
@login_required
def logout():
    return redirect(users.create_logout_url('/'))

@app.route('/<username>')
@login_required
def journal(username):
    profile = Profile.get_by_username(username)
    return jinja.get_template('journal.html').render(locals())

@app.route('/_tasks/digest')
def digest():
    sent_count = 0
    for profile in Profile.all():
        try:
            if profile.digest_now:
                send_digest = False
                body = "Hello! Here's what your team is up to:\n\n"
                for p in profile.following:
                    entry = p.entry_yesterday
                    if entry:
                        send_digest = True
                        body += "## {0}\n\n{1}\n\n".format(
                            p.username, entry.summary)
                        if entry.details:
                            body += "More details: {0}{1}\n\n".format(
                                request.url_root, p.username)
                if send_digest:
                    mail.send_mail(sender=ADMIN_EMAIL,
                        to=profile.user.email(),
                        subject="[workjournal] Daily digest",
                        body=body)
                    sent_count += 1
        except Exception, e:
            logging.error(str(e))
    return str(sent_count)

@app.route('/_tasks/prompt')
def prompt():
    sent_count = 0
    for profile in Profile.all():
        try:
            if profile.prompt_now:
                mail.send_mail(sender=ADMIN_EMAIL,
                    to=profile.user.email(),
                    subject="[workjournal] Daily prompt",
                    body="""
Hello!

Take a moment to visit this URL and jot down what you did today:

{0}?edit

Thanks, have a good day!

""".format(request.url_root))
                sent_count += 1
        except Exception, e:
            logging.error(str(e))
    return str(sent_count)
