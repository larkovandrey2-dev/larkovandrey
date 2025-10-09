import pickle
import pandas
loa = open("sav_lr","rb")
lr_ = pickle.load(loa)
loa.close()
#y_pred = lr_.predict()


async def form_gad7_survey_1(answers,sex,age,education):
    print(answers)
    if sex == 'Мужской':
        sex = 0
    elif sex == 'Женский':
        sex = 1
    if education == 'Высшее образование':
        education = 2
    if education == 'Основное общее образование':
        education = 1
    if education == 'Среднее общее':
        education = 0
    form = {'GAD1':[],'GAD2':[],'GAD3':[],'GAD4':[],'GAD5':[],'GAD6':[],'GAD7':[],'Narcissism':[int(answers[7])],'Gender':[sex],'Age':[age],'Degree':[education],'Playstyle':[int(answers[8])],'PC':[1 if int(answers[9]) == 0 else 0],'Console (PS, Xbox, ...)':[1 if int(answers[9]) == 1 else 0],'Smartphone / Tablet':[1 if int(answers[9]) == 2 else 0],
            'League of Legends':[int(answers[10] == "League of Legends")],'Other':[int(answers[10] == "Other")],'Starcraft 2':[int(answers[10] == "Starcraft 2")],'Counter Strike':[int(answers[10] == "Counter Strike")],'World of Warcraft':[int(answers[10] == "World of Warcraft")],'Hearthstone':[int(answers[10] == "Hearthstone")],'Diablo 3':[int(answers[10] == "Diablo 3")],
            'Heroes of the Storm':[int(answers[10] == "Heroes of the Storm")],'Guild Wars 2':[int(answers[10] == "Guild Wars 2")],'Skyrim':[int(answers[10] == "Skyrim")],'Destiny':[int(answers[10] == "Destiny")]}
    for gad in range(len(answers[:7])):
        form[f'GAD{gad+1}'] = int(answers[gad])
    return form
async def predict_stress_level(gad_form: dict):
    gad_table = pandas.DataFrame.from_dict(gad_form)
    predicted_level = lr_.predict(gad_table)
    level_in_percents = (predicted_level[0]*100)/21
    return int(level_in_percents)





