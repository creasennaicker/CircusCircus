from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from forum.database import Subforum, init_site

app = Flask(__name__)
app.config.update(
    TESTING=True,
    SECRET_KEY=b'kristofer',
	SITE_NAME = "Schooner",
	SITE_DESCRIPTION = "a schooner forum",
	SQLALCHEMY_DATABASE_URI='sqlite:////tmp/database.db'
)

db = SQLAlchemy(app)

db.create_all()
if not Subforum.query.all():
		init_site()
