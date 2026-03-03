from flask import Flask, render_template, request, redirect, url_for, session
from models import User
from models import UserLevelProgress
from questions import QUESTIONS
import random

#The following connects our Database to Flask:
from models import db
import models

#Shuffled questions should NOT be global per user long-term
#For now we keep them temporary (memory only)
shuffled_questions = {}


LEVELS = {
    1: {"name": "Beginner", "unlock_xp": 0, "complete_xp": 25, "star_reward": 1},
    2: {"name": "Intermediate", "unlock_xp": 15, "complete_xp": 50, "star_reward": 3},
    3: {"name": "Advanced", "unlock_xp": 40, "complete_xp": 75, "star_reward": 5},
    4: {"name": "Expert", "unlock_xp": 65, "complete_xp": 100, "star_reward": 7},
    5: {"name": "Master", "unlock_xp": 90, "complete_xp": 125, "star_reward": 9},
    6: {"name": "Grandmaster", "unlock_xp": 115, "complete_xp": 150, "star_reward": 11},
}


#This is where we get the current title of the user
def get_title(total_stars: int) -> str:
    if total_stars >= 36:
        return "Archwizard of Arithmetic"
    elif total_stars >= 29:
        return "Chronicle Computist"
    elif total_stars >= 23:
        return "Spellbinder of Sums"
    elif total_stars >= 18:
        return "Arc Calculator"
    elif total_stars >= 14:
        return "Theorem Tamer"
    elif total_stars >= 10:
        return "Glyph Grinder"
    elif total_stars >= 7:
        return "Arcane Analyst"
    elif total_stars >= 5:
        return "Scroll Solver"
    elif total_stars >= 3:
        return "Rune Reader"
    elif total_stars >= 1:
        return "Pebble Thinker"
    else:
        return "Unranked"


#To get the current level that we are in:
#Now correctly uses DATABASE user instead of globals
def get_current_level_id(user) -> int:
    unlocked = [
        level_id
        for level_id, data in LEVELS.items()
        if user.xp >= data["unlock_xp"]  # Now reading from DB column
    ]
    if not unlocked:
        return 1
    return max(unlocked)


#This allows us to get the full user progress from our database:
#If the user doesn't have progress yet we create a new one
def get_level_progress(user, level_id):
    progress = UserLevelProgress.query.filter_by(
        user_id=user.id,
        level_id=level_id
    ).first()

    #If no row exists in DB, we create it
    if not progress:
        progress = UserLevelProgress(
            user_id=user.id,
            level_id=level_id
        )
        db.session.add(progress)
        db.session.commit()

    return progress


#Routing Systems:

app = Flask(__name__)

#Flask stores sessions in cookies, we sign them using secret key
app.secret_key = "dev-secret-key"

#Database configuration:
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///math.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name", "").strip()

        if not name:
            return render_template("login.html", error="Name is required")

        user = User.query.filter_by(name=name).first()

        #If user does not exist → create one
        if not user:
            user = User(name=name)
            db.session.add(user)
            db.session.commit()

        #Store ONLY user ID in session
        session["user_id"] = user.id

        return redirect(url_for("home"))

    return render_template("login.html")


#Helper Function:
def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    #Query DB using primary key
    return User.query.get(user_id)


@app.route("/")
def home():
    user = get_current_user()

    if not user:
        return redirect(url_for("login"))

    current_level_id = get_current_level_id(user)
    current_level_name = LEVELS[current_level_id]["name"]
    title = get_title(user.stars)

    return render_template(
        "home.html",
        xp=user.xp,
        stars=user.stars,
        level=current_level_name,
        title=title,
    )


@app.route("/levels")
def levels():
    user = get_current_user()

    if not user:
        return redirect(url_for("login"))

    unlocked_levels = []
    for level_id, data in LEVELS.items():
        if user.xp >= data["unlock_xp"]:
            unlocked_levels.append(level_id)

    return render_template(
        "levels.html",
        xp=user.xp,
        stars=user.stars,
        unlocked_levels=unlocked_levels,
        levels=LEVELS,
        title=get_title(user.stars)
    )


@app.route("/level/<int:level_id>", methods=["GET", "POST"])
def level_page(level_id):

    user = get_current_user()

    if not user:
        return redirect(url_for("login"))

    #Checking if the level exists:
    if level_id not in LEVELS:
        return "Level does not exist."

    level_data = LEVELS[level_id]

    #Checking if unlocked based on DB xp
    if user.xp < level_data["unlock_xp"]:
        return render_template("locked.html", level=level_data)

    #Get persistent level progress from DB
    progress = get_level_progress(user, level_id)

    #Initialize shuffled questions once per level (memory only for now)
    if level_id not in shuffled_questions:
        questions = list(QUESTIONS[level_id])
        random.shuffle(questions)
        shuffled_questions[level_id] = questions
    else:
        questions = shuffled_questions[level_id]

    current_index = progress.questions_completed

    if current_index >= len(questions):
        current_question = None
        level_status = "✅ This level is already completed."
    else:
        current_question = questions[current_index]
        level_status = None

    message = None

    if request.method == "POST" and current_question:
        user_answer = request.form.get("answer", "").strip()

        try:
            user_x = float(user_answer)
        except ValueError:
            message = "Please enter a valid number."
        else:
            if user_x == current_question["answer"]:

                #Increase streak in DB
                user.current_streak += 1

                #Increase XP in DB
                user.xp += 5

                #Increase progress in DB
                progress.questions_completed += 1

                #If level completed:
                if progress.questions_completed == len(questions):
                    progress.is_completed = True
                    user.stars += level_data["star_reward"]

                #Commit ALL DB changes
                db.session.commit()

                return redirect(url_for("level_page", level_id=level_id))
            else:
                user.current_streak = 0
                db.session.commit()
                message = "Incorrect! Streak reset."

    return render_template(
        "level.html",
        result=message,
        level_status=level_status,
        streak=user.current_streak,
        xp=user.xp,
        stars=user.stars,
        title=get_title(user.stars),
        level=level_data,
        current_question=current_question,
        question_number=progress.questions_completed + 1,
        total_questions=len(QUESTIONS[level_id]),
        progress_percent=(progress.questions_completed / len(QUESTIONS[level_id])) * 100
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)