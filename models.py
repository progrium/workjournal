11import datetime
import hashlib
import time

from google.appengine.ext import db

# Used to normalize to UTC from wherever the app is running
UTC_DELTA = datetime.datetime.utcnow() - datetime.datetime.now()

class Profile(db.Model):
    user = db.UserProperty()
    username = db.StringProperty()
    timezone_offset = db.IntegerProperty(default=-5)
    digest_hour = db.IntegerProperty(default=9)
    prompt_hour = db.IntegerProperty(default=17)

    def today(self):
        today = datetime.datetime.fromtimestamp(time.mktime(datetime.date.today().timetuple()))
        return today + UTC_DELTA + datetime.timedelta(hours=self.timezone_offset)

    def yesterday(self):
        return self.today() - datetime.timedelta(days=1)
    
    def now(self):
        return datetime.datetime.now() + UTC_DELTA + datetime.timedelta(hours=self.timezone_offset)
    
    @property
    def digest_now(self):
    	return self.now().hour == self.digest_hour and self.now().weekday() < 5

    @property
    def prompt_now(self):
    	return self.now().hour == self.prompt_hour and self.now().weekday() < 5

    @property
    def entry_today(self):
        return Entry.all().filter('user =', self.user) \
            .filter('created >=', self.today()).get()

    @property
    def entry_yesterday(self):
        return Entry.all().filter('user =', self.user) \
            .filter('created >=', self.yesterday()) \
            .filter('created <', self.today()).get()
    
    @property
    def following(self):
        return Profile.all().filter('user !=', self.user)
    
    @property
    def entries(self):
        return Entry.all().filter('user =', self.user).order('-created')
    
    @property
    def gravatar_hash(self):
        return hashlib.md5(self.user.email().strip().lower()).hexdigest()
    
    @classmethod
    def get_or_create(cls, user):
        p = cls.all().filter('user =', user).get()
        if not p:
            p = cls(user=user, username=user.nickname().split('@')[0])
            p.put()
        if not p.username:
        	p.username = user.nickname().split('@')[0]
        	p.put()
        return p

    @classmethod
    def get_by_username(cls, username):
    	return cls.all().filter('username =', username).get()

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