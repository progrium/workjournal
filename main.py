import time
import datetime
import hashlib

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

UTC_DELTA = datetime.datetime.utcnow() - datetime.datetime.now()

def application():
    return webapp.WSGIApplication(debug=True, url_mapping=[
            ('/', HomeHandler),
            ('/settings', SettingsHandler),
            ('/logout', LogoutHandler),
            ('/(.*)', JournalHandler),  ])

class Profile(db.Model):
    user = db.UserProperty()
    timezone_offset = db.IntegerProperty(default=-8)
    digest_hour = db.IntegerProperty(default=9)
    ask_hour = db.IntegerProperty(default=17)
    
    def today(self):
        today = datetime.datetime.fromtimestamp(time.mktime(datetime.date.today().timetuple()))
        return today + UTC_DELTA + datetime.timedelta(hours=self.timezone_offset)
    
    def now(self):
        return datetime.datetime.now() + UTC_DELTA + datetime.timedelta(hours=self.timezone_offset)
    
    def entry_today(self):
        return Entry.all().filter('user =', self.user) \
            .filter('created >=', self.today()).get()
    
    @property
    def following(self):
        return Profile.all().filter('user !=', self.user)
    
    @property
    def entries(self):
        return Entry.all().filter('user =', self.user).order('-created')
    
    @property
    def gravatar_hash(self):
        return hashlib.md5(self.user.email().strip().lower()).hexdigest()
    
    @property
    def username(self):
        return self.user.nickname().split('@')[0]    
    
    @classmethod
    def get_or_create(cls, user):
        p = cls.all().filter('user =', user).get()
        if not p:
            p = cls(user=user)
            p.put()
        return p

class Entry(db.Model):
    body = db.TextProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)
    user = db.UserProperty(auto_current_user_add=True)
    
    @property
    def date(self):
        return datetime.datetime.fromtimestamp(time.mktime(self.created.date().timetuple()))
    
    @property
    def summary(self):
        return self.body.split('\n\r', 1)[0]
    
    @property
    def details(self):
        if '\n\r' in self.body:
            return self.body.split('\n\r', 1)[-1]
        else:
            return None

class HomeHandler(webapp.RequestHandler):
    @util.login_required
    def get(self):
        profile = Profile.get_or_create(users.get_current_user())
        edit = self.request.query_string == 'edit'
        self.response.out.write(template.render('templates/home.html', locals()))
    
    def post(self):
        profile = Profile.get_or_create(users.get_current_user())
        if self.request.query_string == 'edit':
            e = profile.entry_today()
            e.body = self.request.get('body')
        else:
            e = Entry(body=self.request.get('body'))
        e.put()
        self.redirect(self.request.path)

class SettingsHandler(webapp.RequestHandler):
    @util.login_required
    def get(self):
        profile = Profile.get_or_create(users.get_current_user())
        self.response.out.write(template.render('templates/settings.html', locals()))
    
    def post(self):
        profile = Profile.get_or_create(users.get_current_user())
        profile.timezone_offset = int(self.request.get('timezone_offset'))
        profile.digest_hour = int(self.request.get('digest_hour'))
        profile.ask_hour = int(self.request.get('ask_hour'))
        profile.put()
        self.redirect(self.request.path)

class JournalHandler(webapp.RequestHandler):
    @util.login_required
    def get(self, path):
        profile = Profile.get_or_create(users.get_current_user())
        self.response.out.write(template.render('templates/journal.html', locals()))

class LogoutHandler(webapp.RequestHandler):
    @util.login_required
    def get(self):
        self.redirect(users.create_logout_url('/'))

def main():
    util.run_wsgi_app(application())

if __name__ == '__main__':
    main()
