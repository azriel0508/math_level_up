from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    #Primary Key:
    id = db.Column(db.Integer, primary_key=True)

    # Basic identity:
    name = db.Column(db.String(50), nullable=False)

    #Game Stats:
    xp = db.Column(db.Integer, default=0)
    stars = db.Column(db.Integer, default=0)
    current_streak = db.Column(db.Integer, default=0)
