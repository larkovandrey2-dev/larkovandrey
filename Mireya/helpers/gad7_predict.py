import pickle
import pandas
from bot.config import MODEL_PATH

loa = open(MODEL_PATH, "rb")
lr_ = pickle.load(loa)
loa.close()


async def form_gad7_survey_1(answers, sex, age, education):
    """Form GAD-7 survey data. Handles missing optional answers gracefully."""
    if sex == 'Мужской' or sex is None:
        sex = 0
    elif sex == 'Женский':
        sex = 1
    
    if education == 'Высшее образование' or education is None:
        education = 2
    elif education == 'Основное общее образование':
        education = 1
    elif education == 'Среднее общее':
        education = 0
    
    try:
        if len(answers) < 7:
            print(f"Not enough answers: {len(answers)}")
            return {}
        
        answers_int = []
        for ans in answers:
            try:
                answers_int.append(int(ans))
            except (ValueError, TypeError):
                answers_int.append(0)
        
        while len(answers_int) < 11:
            answers_int.append(0)
        
        game_list = [
            "League of Legends", "Starcraft 2", "Counter Strike", "World of Warcraft",
            "Hearthstone", "Diablo 3", "Heroes of the Storm", "Guild Wars 2",
            "Skyrim", "Destiny"
        ]
        
        narcissism = answers_int[7] if len(answers_int) > 7 else 0
        playstyle = answers_int[8] if len(answers_int) > 8 else 0
        device = answers_int[9] if len(answers_int) > 9 else 0
        
        game_answer = answers[10] if len(answers) > 10 else ""
        if isinstance(game_answer, (int, float)):
            game_str = ""
        else:
            game_str = str(game_answer).strip()
        
        form = {
            'GAD1': [answers_int[0]],
            'GAD2': [answers_int[1]],
            'GAD3': [answers_int[2]],
            'GAD4': [answers_int[3]],
            'GAD5': [answers_int[4]],
            'GAD6': [answers_int[5]],
            'GAD7': [answers_int[6]],
            'Narcissism': [narcissism],
            'Gender': [sex],
            'Age': [age],
            'Degree': [education],
            'Playstyle': [playstyle],
            'PC': [1 if device == 0 else 0],
            'Console (PS, Xbox, ...)': [1 if device == 1 else 0],
            'Smartphone / Tablet': [1 if device == 2 else 0],
            'League of Legends': [int(game_str == "League of Legends")],
            'Other': [int(game_str not in game_list and game_str not in ["0", "1", "2", "3"])],
            'Starcraft 2': [int(game_str == "Starcraft 2")],
            'Counter Strike': [int(game_str == "Counter Strike")],
            'World of Warcraft': [int(game_str == "World of Warcraft")],
            'Hearthstone': [int(game_str == "Hearthstone")],
            'Diablo 3': [int(game_str == "Diablo 3")],
            'Heroes of the Storm': [int(game_str == "Heroes of the Storm")],
            'Guild Wars 2': [int(game_str == "Guild Wars 2")],
            'Skyrim': [int(game_str == "Skyrim")],
            'Destiny': [int(game_str == "Destiny")]
        }
        return form
    except Exception as e:
        print(f"Error in form_gad7_survey_1: {e}")
        import traceback
        traceback.print_exc()
        return {}


async def predict_stress_level(gad_form: dict):
    """Predict stress level from GAD-7 form data."""
    if not gad_form or gad_form == {}:
        return -1
    
    try:
        gad_table = pandas.DataFrame.from_dict(gad_form)
        predicted_level = lr_.predict(gad_table)
        level_in_percents = (predicted_level[0] * 100) / 21
        return int(level_in_percents)
    except Exception as e:
        print(f"Error in predict_stress_level: {e}")
        import traceback
        traceback.print_exc()
        return -1
