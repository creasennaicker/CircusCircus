from flask_login import UserMixin
import re
import datetime
from flask_login.login_manager import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash

from forum.app import db, app 


login_manager = LoginManager()
login_manager.init_app(app)

# if __name__ == "__main__":
# 	#runsetup()
# 	port = int(os.environ["PORT"])
# 	app.run(host='0.0.0.0', port=port, debug=True)



#DATABASE STUFF
@login_manager.user_loader
def load_user(userid):
	return User.query.get(userid)


password_regex = re.compile("^[a-zA-Z0-9!@#%&]{6,40}$")
username_regex = re.compile("^[a-zA-Z0-9!@#%&]{4,40}$")
#Account checks
def username_taken(username):
	return User.query.filter(User.username == username).first()
def email_taken(email):
	return User.query.filter(User.email == email).first()
def valid_username(username):
	if not username_regex.match(username):
		#username does not meet password reqirements
		return False
	#username is not taken and does meet the password requirements
	return True
def valid_password(password):
	return password_regex.match(password)
#Post checks
def valid_title(title):
	return len(title) > 4 and len(title) < 140
def valid_content(content):
	return len(content) > 10 and len(content) < 5000


#OBJECT MODELS
class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.Text, unique=True)
	password_hash = db.Column(db.Text)
	email = db.Column(db.Text, unique=True)
	admin = db.Column(db.Boolean, default=False, unique=True)
	posts = db.relationship("Post", backref="user")
	comments = db.relationship("Comment", backref="user")

	def __init__(self, email, username, password):
		self.email = email
		self.username = username
		self.password_hash = generate_password_hash(password)
	def check_password(self, password):
		return check_password_hash(self.password_hash, password)
class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.Text)
	content = db.Column(db.Text)
	comments = db.relationship("Comment", backref="post")
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	subforum_id = db.Column(db.Integer, db.ForeignKey('subforum.id'))
	postdate = db.Column(db.DateTime)

	#cache stuff
	lastcheck = None
	savedresponce = None
	def __init__(self, title, content, postdate):
		self.title = title
		self.content = content
		self.postdate = postdate
	def get_time_string(self):
		#this only needs to be calculated every so often, not for every request
		#this can be a rudamentary chache
		now = datetime.datetime.now()
		if self.lastcheck is None or (now - self.lastcheck).total_seconds() > 30:
			self.lastcheck = now
		else:
			return self.savedresponce

		diff = now - self.postdate

		seconds = diff.total_seconds()
		print(seconds)
		if seconds / (60 * 60 * 24 * 30) > 1:
			self.savedresponce =  " " + str(int(seconds / (60 * 60 * 24 * 30))) + " months ago"
		elif seconds / (60 * 60 * 24) > 1:
			self.savedresponce =  " " + str(int(seconds / (60*  60 * 24))) + " days ago"
		elif seconds / (60 * 60) > 1:
			self.savedresponce = " " + str(int(seconds / (60 * 60))) + " hours ago"
		elif seconds / (60) > 1:
			self.savedresponce = " " + str(int(seconds / 60)) + " minutes ago"
		else:
			self.savedresponce =  "Just a moment ago!"

		return self.savedresponce

class Subforum(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.Text, unique=True)
	description = db.Column(db.Text)
	subforums = db.relationship("Subforum")
	parent_id = db.Column(db.Integer, db.ForeignKey('subforum.id'))
	posts = db.relationship("Post", backref="subforum")
	path = None
	hidden = db.Column(db.Boolean, default=False)
	def __init__(self, title, description):
		self.title = title
		self.description = description

class Comment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	content = db.Column(db.Text)
	postdate = db.Column(db.DateTime)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	post_id = db.Column(db.Integer, db.ForeignKey("post.id"))

	lastcheck = None
	savedresponce = None
	def __init__(self, content, postdate):
		self.content = content
		self.postdate = postdate
	def get_time_string(self):
		#this only needs to be calculated every so often, not for every request
		#this can be a rudamentary chache
		now = datetime.datetime.now()
		if self.lastcheck is None or (now - self.lastcheck).total_seconds() > 30:
			self.lastcheck = now
		else:
			return self.savedresponce

		diff = now - self.postdate
		seconds = diff.total_seconds()
		if seconds / (60 * 60 * 24 * 30) > 1:
			self.savedresponce =  " " + str(int(seconds / (60 * 60 * 24 * 30))) + " months ago"
		elif seconds / (60 * 60 * 24) > 1:
			self.savedresponce =  " " + str(int(seconds / (60*  60 * 24))) + " days ago"
		elif seconds / (60 * 60) > 1:
			self.savedresponce = " " + str(int(seconds / (60 * 60))) + " hours ago"
		elif seconds / (60) > 1:
			self.savedresponce = " " + str(int(seconds / 60)) + " minutes ago"
		else:
			self.savedresponce =  "Just a moment ago!"
		return self.savedresponce


def init_site():
	admin = add_subforum("Forum", "Announcements, bug reports, and general discussion about the forum belongs here")
	add_subforum("Announcements", "View forum announcements here",admin)
	add_subforum("Bug Reports", "Report bugs with the forum here", admin)
	add_subforum("General Discussion", "Use this subforum to post anything you want")
	add_subforum("Other", "Discuss other things here")

def add_subforum(title, description, parent=None):
	sub = db.Subforum(title, description)
	if parent:
		for subforum in parent.subforums:
			if subforum.title == title:
				return
		parent.subforums.append(sub)
	else:
		subforums = Subforum.query.filter(Subforum.parent_id == None).all()
		for subforum in subforums:
			if subforum.title == title:
				return
		db.session.add(sub)
	print("adding " + title)
	db.session.commit()
	return sub
"""
def interpret_site_value(subforumstr):
	segments = subforumstr.split(':')
	identifier = segments[0]
	description = segments[1]
	parents = []
	hasparents = False
	while('.' in identifier):
		hasparents = True
		dotindex = identifier.index('.')
		parents.append(identifier[0:dotindex])
		identifier = identifier[dotindex + 1:]
	if hasparents:
		directparent = subforum_from_parent_array(parents)
		if directparent is None:
			print(identifier + " could not find parents")
		else:
			add_subforum(identifier, description, directparent)
	else:
		add_subforum(identifier, description)

def subforum_from_parent_array(parents):
	subforums = Subforum.query.filter(Subforum.parent_id == None).all()
	top_parent = parents[0]
	parents = parents[1::]
	for subforum in subforums:
		if subforum.title == top_parent:
			cur = subforum
			for parent in parents:
				for child in subforum.subforums:
					if child.title == parent:
						cur = child
			return cur
	return None


def setup():
	siteconfig = open('./config/subforums', 'r')
	for value in siteconfig:
		interpret_site_value(value)
"""
