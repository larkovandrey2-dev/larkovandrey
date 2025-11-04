from aiogram.fsm.state import StatesGroup, State


class UserChanges(StatesGroup):
    age = State()
    education = State()

class UserConfig(StatesGroup):
    age = State()
    sex = State()
    education = State()


class Questions(StatesGroup):
    questions = State()


class Admins(StatesGroup):
    edit_question = State()
    new_question = State()