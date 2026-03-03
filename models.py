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

#We have a one to many relationship with our level progress
class UserLevelProgress(db.Model):
    __tablename__ = "user_level_progress"

    id = db.Column(db.Integer, primary_key=True)

    # Foreign key to User
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Level number (1–6)
    level_id = db.Column(db.Integer, nullable=False)

    # Progress tracking
    questions_completed = db.Column(db.Integer, default=0)
    is_completed = db.Column(db.Boolean, default=False)

    # Relationship back to user (This is because we have a one to many relationship)
    user = db.relationship("User", backref="levels")
