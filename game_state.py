#This class allows us to map to our database, it describes what the table looks like (a SCHEMA):
#Data structure definition:
class GameState:
    def __init__(self):
        self.user_xp = 0
        self.user_stars = 0
        self.current_streak = 0
        self.completed_levels = set()

        self.question_progress = {
            1: 0, 2: 0, 3: 0,
            4: 0, 5: 0, 6: 0
        }

        self.shuffled_questions = {}