async def get_student_result(answers):
    print(answers)
    try:
        scale = {"Нет": 0, "Скорее нет, чем да": 1, "Скорее да, чем нет": 2, "Да": 3}
        digit_answers = [scale[ans] for ans in answers]
        max_result = 6
        student_result = sum(digit_answers)
        result_in_percentage = (student_result / max_result) * 100
        return int(result_in_percentage)
    except Exception as e:
        print(e)
        return -1

