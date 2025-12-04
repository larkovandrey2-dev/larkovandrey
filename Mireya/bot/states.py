from aiogram.fsm.state import StatesGroup, State


class UserChanges(StatesGroup):
    age = State()
    education = State()
    sos_contact = State()

class UserConfig(StatesGroup):
    age = State()
    sex = State()
    education = State()


class Questions(StatesGroup):
    questions1 = State()
    questions2 = State()


class Admins(StatesGroup):
    edit_question = State()
    new_question = State()
    edit_role = State()

class UserLLM(StatesGroup):
    answer = State()