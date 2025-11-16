import io
import datetime

from supabase import acreate_client
import matplotlib.pyplot as plt


class DatabaseService:
    def __init__(self,supabase_url, supabase_key):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.client = None
    async def create_client(self):
        self.client = await acreate_client(self.supabase_url, self.supabase_key)

    async def get_all_users(self) -> list:
        """returns a list with every user_id"""
        response = await self.client.table('users').select('user_id').execute()
        users = [item['user_id'] for item in response.data]
        return users

    async def create_user(self, user_id: int, role: str, refer_id: int):
        """create user"""
        try:
            if user_id in await self.get_all_users():
                print('User already exists')
            else:
                new_user = {
                    'user_id': user_id,
                    'role': role,
                    'refer_id': refer_id,
                }
                response = await self.client.table('users').insert(new_user).execute()
                if response:
                    print('User added')
        except Exception as e:
            print(f'Error in create_user: {e}')

    async def delete_user(self,user_id: int):
        '''delete user by user_id'''
        try:
            response = await self.client.table('users').delete().eq('user_id', user_id).execute()
        except Exception as e:
            print(f'Error in delete_question: {e}')

    async def get_user_stats(self,user_id: int) -> dict:
        '''returns a dict of all stats'''
        try:
            user_id = int(user_id)
            if user_id not in await self.get_all_users():
                print('No such user, creating...')
                await self.create_user(user_id, "user", 0)
            response = await self.client.table('users').select('*').eq('user_id', user_id).execute()
            user_data = response.data[0]
            return user_data
        except Exception as e:
            print(f'Error in get_user_stats: {e}')

    async def change_user_stat(self, user_id: int, stat_name: str, new_value):
        '''change one specific stat by its name and its new value'''
        try:
            new_response = {f'{stat_name}': new_value}
            if user_id not in await self.get_all_users():
                print(f'No such user_id for change_user_stat: {user_id}')
            else:
                response = await self.client.table('users').update(new_response).eq('user_id', user_id).execute()
        except Exception as e:
            print(f'Error in change_user_stat: {e}')

    async def change_user_stats(self,user_id: int, role: str, refer_id: int, surveys_count: int, last_survey_index: int,
                                sex: str,
                                age: int, education: str, all_user_global_attempts: list):
        """change all stats for given user_id (function waits for every stat to be given)"""
        try:
            new_response = {
                'role': role,
                'refer_id': refer_id,
                'last_survey_index': last_survey_index,
                'surveys_count': surveys_count,
                'sex': sex,
                'age': age,
                'education': education,
                'all_user_global_attempts': all_user_global_attempts
            }
            if user_id not in await self.get_all_users():
                print(f'No such user_id for change_user_stats: {user_id}')
            else:
                response = await self.client.table('users').update(new_response).eq('user_id', user_id).execute()
        except Exception as e:
            print(f'Error in change_user_stats: {e}')

    async def add_user_answer(self,user_id: int, attempt_global_index: int, survey_index: int, question_index: int,
                              response_text: str,
                              response_date: str):
        try:
            new_response = {
                'user_id': user_id,
                'survey_index': survey_index,
                'question_index': question_index,
                'response_text': response_text,
                'response_date': response_date,
                'attempt_global_index': attempt_global_index
            }
            response = await self.client.table('user_responses').insert(new_response).execute()
        except Exception as e:
            print(f'Error in add_user_answer: {e}')

    async def all_questions(self):
        '''returns list of dicts: {'question_index':, 'survey_index':, 'question_text':}'''
        try:
            response = await self.client.table('all_questions').select(
                'question_index, survey_index, question_text').execute()
            return sorted(response.data, key=lambda x: (x['survey_index'], x['question_index']))
        except Exception as e:
            print(f'Error in all_questions: {e}')

    async def get_answers_by_global_attempt(self,attempt_global_index: int):
        try:
            response = await self.client.table('user_responses').select('*').eq('attempt_global_index',
                                                                             attempt_global_index).execute()
            return response.data
        except Exception as e:
            print(f'Error in get_answers_by_global_attempt: {e}')

    async def all_global_attempts(self):
        '''returns a list of all existing global attempts'''
        try:
            response = await self.client.table('user_responses').select('attempt_global_index').execute()
            return [elem['attempt_global_index'] for elem in response.data]
        except Exception as e:
            print(f'Error in all_questions: {e}')
    async def all_global_attempts_results(self):
        '''returns a list of all existing global attempts'''
        try:
            response = await self.client.table('survey_results').select('attempt_global_index').execute()
            return [elem['attempt_global_index'] for elem in response.data]
        except Exception as e:
            print(f'Error in all_questions: {e}')

    async def add_question(self,question_index: int, survey_index: int, question_text: str):
        try:
            new_response = {
                'survey_index': int(survey_index),
                'question_index': int(question_index),
                'question_text': str(question_text)
            }

            if new_response in await self.all_questions():
                print('This question exists')
            else:
                response = await self.client.table('all_questions').insert(new_response).execute()
        except Exception as e:
            print(f'Error in add_gad7_answer: {e}')

    async def change_question(self, question_index: int, survey_index: int, new_question_text: str):
        '''change question text by its question_index and survey_index'''
        try:
            new_response = {'question_text': new_question_text}
            response = await self.client.table('all_questions').update(new_response).eq('question_index',
                                                                                     question_index).eq(
                'survey_index', survey_index).execute()
        except Exception as e:
            print(f'Error in change_question: {e}')

    async def change_question_index(self,question_index: int, survey_index: int, new_question_index: int):
        '''change question index by its question_index and survey_index'''
        try:
            new_response = {'question_index': new_question_index}
            response = await self.client.table('all_questions').update(new_response).eq('question_index',
                                                                                     question_index).eq(
                'survey_index', survey_index).execute()
        except Exception as e:
            print(f'Error in change_question_index: {e}')

    async def delete_question(self,question_index: int, survey_index: int):
        '''delete question by its question_index and survey_index'''
        try:
            response = await self.client.table('all_questions').delete().eq('question_index', question_index).eq(
                'survey_index',
                survey_index).execute()
        except Exception as e:
            print(f'Error in delete_question: {e}')

    async def add_survey_result(self,user_id: int, attempt_global_index: int, survey_index: int, date: str, result: int):
        '''add a result for a single survey attempt'''
        try:
            new_response = {
                'user_id': user_id,
                'attempt_global_index': attempt_global_index,
                'survey_index': survey_index,
                'date': date,
                'result': result
            }

            if attempt_global_index in await self.all_global_attempts_results():
                print(f'Global attempt with index {attempt_global_index} already exists')
            else:
                response = await self.client.table('survey_results').insert(new_response).execute()
        except Exception as e:
            print(f'Error in add_survey_result: {e}')

    async def get_surveys_results(self,user_id: int):
        try:
            response = await self.client.table('survey_results').select('*').eq('user_id', user_id).execute()
            return response.data[0]
        except Exception as e:
            print(f'Error in get_surveys_results: {e}')

    async def create_results_chart(self, user_id: int, survey_index: int, type='linear'):  # type can be 'linear', 'area' or 'bar'
        '''creates a chart for all user's results in a given survey'''

        try:
            response = await self.client.table('survey_results').select('*').eq('user_id', user_id).eq('survey_index',survey_index).execute()
            print(response)
            data_with_datetime = []
            for item in response.data:
                date_str = item['date']
                try:
                    dt_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                except Exception:
                    print(f"Invalid date format: {date_str}")
                    continue
                data_with_datetime.append({
                    'date': date_str,
                    'datetime': dt_obj,
                    'result': item['result']
                })
            data_sorted = sorted(data_with_datetime, key=lambda x: x['datetime'])
            if not data_sorted:
                print('No data found')
                return False
            data_x = [elem['date'] for elem in data_sorted]
            data_y = [elem['result'] for elem in data_sorted]
            plt.figure()
            if type == 'linear':
                plt.plot(data_x, data_y)
                plt.xlabel('Дата прохождения')
                plt.ylabel('Уровень стресса')
                plt.xticks(rotation=45)
            elif type == 'area':
                plt.fill_between(data_x, data_y, alpha=0.3, color='blue')
                plt.plot(data_x, data_y, color='blue', alpha=0.8)
                plt.xlabel('Дата прохождения')
                plt.ylabel('Уровень стресса')
                plt.xticks(rotation=45)
            elif type == 'bar':
                plt.bar(data_x, data_y, color='blue', alpha=0.5)
                plt.xlabel('Дата прохождения')
                plt.ylabel('Уровень стресса')
                plt.xticks(rotation=45)
            plt.title('Динамика уровня стресса')
            plt.grid(True)
            plt.tight_layout()
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png')
            img_buffer.seek(0)
            plt.close()

            return img_buffer

        except Exception as e:
            print(f'Error in create_results_chart: {e}')



