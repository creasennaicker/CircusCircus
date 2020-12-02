from flask import *
#from flask.ext.login import LoginManager, login_required, current_user, logout_user, login_user
from flask_login import LoginManager, current_user, login_user, logout_user
import datetime

from flask_login.utils import login_required
from forum.app import app
from flask_sqlalchemy import SQLAlchemy

from flask_login import UserMixin
import re
import datetime
from flask_login.login_manager import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy(app)

#VIEWS

@app.route('/')
def index():
	subforums = Subforum.query.filter(Subforum.parent_id == None).order_by(Subforum.id)
	return render_template("subforums.html", subforums=subforums)

@app.route('/subforum')
def subforum():
	subforum_id = int(request.args.get("sub"))
	subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
	if not subforum:
		return error("That subforum does not exist!")
	posts = Post.query.filter(Post.subforum_id == subforum_id).order_by(Post.id.desc()).limit(50)
	if not subforum.path:
		subforum.path = generateLinkPath(subforum.id)

	subforums = Subforum.query.filter(Subforum.parent_id == subforum_id).all()
	return render_template("subforum.html", subforum=subforum, posts=posts, subforums=subforums, path=subforum.path)

@app.route('/loginform')
def loginform():
	return render_template("login.html")


@login_required
@app.route('/addpost')
def addpost():
	subforum_id = int(request.args.get("sub"))
	subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
	if not subforum:
		return error("That subforum does not exist!")

	return render_template("createpost.html", subforum=subforum)

@app.route('/viewpost')
def viewpost():
	postid = int(request.args.get("post"))
	post = Post.query.filter(Post.id == postid).first()
	if not post:
		return error("That post does not exist!")
	if not post.subforum.path:
		subforum.path = generateLinkPath(post.subforum.id)
	comments = Comment.query.filter(Comment.post_id == postid).order_by(Comment.id.desc()) # no need for scalability now
	return render_template("viewpost.html", post=post, path=subforum.path, comments=comments)

#ACTIONS

@login_required
@app.route('/action_comment', methods=['POST', 'GET'])
def comment():
	post_id = int(request.args.get("post"))
	post = Post.query.filter(Post.id == post_id).first()
	if not post:
		return error("That post does not exist!")
	content = request.form['content']
	postdate = datetime.datetime.now()
	comment = Comment(content, postdate)
	current_user.comments.append(comment)
	post.comments.append(comment)
	db.session.commit()
	return redirect("/viewpost?post=" + str(post_id))

@login_required
@app.route('/action_post', methods=['POST'])
def action_post():
	subforum_id = int(request.args.get("sub"))
	subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
	if not subforum:
		return redirect(url_for("subforums"))

	user = current_user
	title = request.form['title']
	content = request.form['content']
	#check for valid posting
	errors = []
	retry = False
	if not valid_title(title):
		errors.append("Title must be between 4 and 140 characters long!")
		retry = True
	if not valid_content(content):
		errors.append("Post must be between 10 and 5000 characters long!")
		retry = True
	if retry:
		return render_template("createpost.html",subforum=subforum,  errors=errors)
	post = Post(title, content, datetime.datetime.now())
	subforum.posts.append(post)
	user.posts.append(post)
	db.session.commit()
	return redirect("/viewpost?post=" + str(post.id))


@app.route('/action_login', methods=['POST'])
def action_login():
	username = request.form['username']
	password = request.form['password']
	user = User.query.filter(User.username == username).first()
	if user and user.check_password(password):
		login_user(user)
	else:
		errors = []
		errors.append("Username or password is incorrect!")
		return render_template("login.html", errors=errors)
	return redirect("/")


@login_required
@app.route('/action_logout')
def action_logout():
	#todo
	logout_user()
	return redirect("/")

@app.route('/action_createaccount', methods=['POST'])
def action_createaccount():
	username = request.form['username']
	password = request.form['password']
	email = request.form['email']
	errors = []
	retry = False
	if username_taken(username):
		errors.append("Username is already taken!")
		retry=True
	if email_taken(email):
		errors.append("An account already exists with this email!")
		retry = True
	if not valid_username(username):
		errors.append("Username is not valid!")
		retry = True
	# if not valid_password(password):
	# 	errors.append("Password is not valid!")
	# 	retry = True
	if retry:
		return render_template("login.html", errors=errors)
	user = User(email, username, password)
	if user.username == "admin":
		user.admin = True
	db.session.add(user)
	db.session.commit()
	login_user(user)
	return redirect("/")

def error(errormessage):
	return "<b style=\"color: red;\">" + errormessage + "</b>"

def generateLinkPath(subforumid):
	links = []
	subforum = Subforum.query.filter(Subforum.id == subforumid).first()
	parent = Subforum.query.filter(Subforum.id == subforum.parent_id).first()
	links.append("<a href=\"/subforum?sub=" + str(subforum.id) + "\">" + subforum.title + "</a>")
	while parent is not None:
		links.append("<a href=\"/subforum?sub=" + str(parent.id) + "\">" + parent.title + "</a>")
		parent = Subforum.query.filter(Subforum.id == parent.parent_id).first()
	links.append("<a href=\"/\">Forum Index</a>")
	link = ""
	for l in reversed(links):
		link = link + " / " + l
	return link


#from forum.app import db, app 


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
	sub = Subforum(title, description)
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


db.create_all()
if not Subforum.query.all():
		init_site()

