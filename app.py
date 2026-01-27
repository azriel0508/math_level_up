from flask import Flask, render_template, request, redirect, url_for
from questions import QUESTIONS
import random

#Global Variables (Temporary before we add databases):
user_xp = 0 
user_stars = 0
completed_levels = set()
shuffled_questions = {}
current_streak = 0

#Dictionaries:

question_progress = { #This will help us track the progress in each question
    1: 0,
    2: 0,
    3: 0,
    4: 0,
    5: 0,
    6: 0,
}

LEVELS = {
    1: {
        "name": "Beginner", #Current Level
        "unlock_xp": 0, #Amount of xp needed to unlock this level
        "complete_xp": 25, #The maximum xp you gain from this level
        "star_reward": 1, #The amount of stars you get from this level
    },
    2: {
        "name": "Intermediate",
        "unlock_xp": 15,
        "complete_xp": 50,
        "star_reward": 3,
    },
    3: {
        "name": "Advanced",
        "unlock_xp": 40,
        "complete_xp": 75,
        "star_reward": 5,
    },
    4: {
        "name": "Expert",
        "unlock_xp": 65,
        "complete_xp": 100,
        "star_reward": 7,
    },
    5: {
        "name": "Master",
        "unlock_xp": 90,
        "complete_xp": 125,
        "star_reward": 9
    },
    6: {
        "name": "Grandmaster",
        "unlock_xp": 115,
        "complete_xp": 150,
        "star_reward": 11,
    }
}

#This is where we get the current title of the user we give an int which is the amount of stars and we get a string back as the title
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
def get_current_level_id() -> int:
    global user_xp
    unlocked = [ #We have a list that will iterate through the values in the LEVELS.items() and get the amount of the unlock xp. If the userxp is greater than the unlockxp then that level_id will be added to the list
        level_id
        for level_id, data in LEVELS.items()
        if user_xp >= data["unlock_xp"]
    ]
    if not unlocked:
        return 1
    return max(unlocked) #This will get the highest value in the list hence the highest level we have unlocked.

#Routing Systems:

app = Flask(__name__)

@app.route("/")
def home():
    global user_xp, user_stars

    current_level_id = get_current_level_id()
    current_level_name = LEVELS[current_level_id]["name"]
    title = get_title(user_stars)

    return render_template( #This will check the templates folder for the file home.html then execute it
        "home.html",
        xp=user_xp,
        stars=user_stars,
        level=current_level_name,
        title=title,
    ) 

@app.route("/levels")
def level_select():
    global user_xp, user_stars

    #Determine all of the unlocked levels:
    unlocked_levels = []
    for level_id, data in LEVELS.items():
        if user_xp >= data["unlock_xp"]:
            unlocked_levels.append(level_id)

    return render_template(
        "levels.html",
        xp = user_xp,
        stars = user_stars,
        unlocked_levels = unlocked_levels,
        completed_levels = completed_levels,
        levels = LEVELS,
        title = get_title(user_stars)
    )

@app.route("/level/<int:level_id>", methods=["GET", "POST"]) #This allows us to capture the url given by flask: data posted(POST) in the server
def level_page(level_id): #This route is all of the different levels of our system and it also shows if it can be played or not
    global user_xp, user_stars, current_streak

    #Checking if the level exists:
    if level_id not in LEVELS:
        return "Level does not exist."

    level_data = LEVELS[level_id]

    #Checking if this level is unlocked:
    if user_xp < level_data["unlock_xp"]:
        return render_template("locked.html", level=level_data) #this will show that it is still locked so the function ends right here
    
    #Answer:
    questions = list(QUESTIONS[level_id])

    # Initialize shuffled questions once per level
    if level_id not in shuffled_questions:
        questions = list(QUESTIONS[level_id])
        random.shuffle(questions)
        shuffled_questions[level_id] = questions
    else:
        questions = shuffled_questions[level_id]
    
    #This will show that the level is completed
    level_status = None
    if level_id in completed_levels:
        level_status = "✅ This level is already completed. No more XP can be earned here."

    if not questions:
        return "No questions available for this level yet."
    
    current_index = question_progress[level_id]

    if current_index >= len(questions):
        # Level already completed
        level_status = "✅ This level is already completed."
        current_question = None
    else:
        current_question = questions[current_index]

    #Initialising message before post to avoid errors
    message = None

    if request.method == "POST" and current_question:
        #The following variable is reading in user input from the HTML:
        user_answer = request.form.get("answer", "").strip() #This request.form is how flask reads form data posted by HTML. The get is trying to get the form answer but if there is not then return an empty string. The strip removies whitespaces. 

        try:
            user_x = float(user_answer) #Converting the given string from user_answer as a number
        except ValueError:
            message = "Please enter a valid number." #This is when the input of the user cannot be converted to a float or a number
        else:
            if user_x == current_question["answer"]:
                current_streak += 1
                user_xp += 5
                question_progress[level_id] += 1

                if question_progress[level_id] == len(questions):
                    completed_levels.add(level_id)
                    user_stars += LEVELS[level_id]["star_reward"]

                return redirect(url_for("level_page", level_id=level_id)) #here we are basically redirecting to refresh the url and get the updated status without having to post again.

            else:
                current_streak = 0
                message = "Incorrect! Streak reset."
                
    return render_template( #This is where flasks chooses what html to display which is level.html and send all variables to that html which has been processed by python
        "level.html",
        # UI feedback
        result=message,
        level_status=level_status,

        # User stats
        streak=current_streak,
        xp=user_xp,
        stars=user_stars,
        title=get_title(user_stars),

        # Level info
        level=level_data,

        # Question system
        current_question=current_question,
        question_number=question_progress[level_id] + 1,
        total_questions=len(QUESTIONS[level_id]),

        # Progress bar (question-based)
        progress_percent=(question_progress[level_id] / len(QUESTIONS[level_id])) * 100 #Math for progress bar
    )
    
if __name__ == "__main__":
    app.run(debug=True) #This allows us to auto reload or change our python code without having to restart the server. It also gives better error messages.