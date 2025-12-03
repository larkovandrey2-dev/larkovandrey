async def get_student_result(answers):
    try:
        scale = {"Нет": 0, "Скорее нет, чем да": 1, "Скорее да, чем нет": 2, "Да": 3}

        digit_answers = []
        if answers and not str(answers[0]).isdigit():
            for ans in answers:
                clean_ans = str(ans).strip()
                digit_answers.append(scale.get(clean_ans, 0))
        else:
            digit_answers = [int(a) for a in answers]
        weights = {
            1: 2.5,
            2: 2.5,
            3: 2.0,
            4: 1.5,
            5: 1.0,
            6: 2.0,
            7: 1.5,
            8: 0.5,
        }

        weighted_sum = 0
        max_possible_sum = 0

        for i, ans in enumerate(digit_answers):
            w = weights.get(i, 1.0)

            weighted_sum += ans * w
            max_possible_sum += 3 * w

        if max_possible_sum == 0:
            return 0
        result_in_percentage = (weighted_sum / max_possible_sum) * 100
        return int(result_in_percentage)

    except Exception as e:
        print(f"Error in student result: {e}")
        return -1