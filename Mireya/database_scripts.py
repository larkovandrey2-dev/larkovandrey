from supabase import AsyncClient, acreate_client
import supabase
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import io
import matplotlib.dates as mdates
import datetime
import asyncio

load_dotenv()





async def create_results_chart(user_id: int, survey_index: int, type='linear'):  # type can be 'linear', 'area' or 'bar'
    '''creates a chart for all user's results in a given survey'''
    supabase = await create_supabase()
    try:
        response = await supabase.table('survey_results').select('*').eq('user_id', user_id).eq('survey_index',
                                                                                                survey_index).execute()
        data_with_datetime = []
        for item in response.data:
            date_str = item['date']
            dt_obj = datetime.datetime.strptime(date_str, '%d.%m.%Y')
            data_with_datetime.append({
                'date': date_str,
                'datetime': dt_obj,
                'result': item['result']
            })
        data_sorted = sorted(data_with_datetime, key=lambda x: x['datetime'])
        if data_sorted == []:
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
        # plt.savefig('C:/Users/Vlad/Desktop/my_plot.png') # to save locally
        img_buffer.seek(0)
        plt.close()

        return img_buffer

    except Exception as e:
        print(f'Error in create_results_chart: {e}')


# create_results_chart(user_id=10,survey_index=1,type='area')
'''
USAGE:

from aiogram.types import BufferedInputFile
img_buffer = create_results_chart(10, 1) # user_id: 10, survey_index: 1

if img_buffer:
    # Создаем объект для отправки
    input_file = BufferedInputFile(
        file=img_buffer.getvalue(),
        filename=f"stress_chart.png"
    )
    # Отправляем
    await message.answer_photo(
        photo=input_file,
        caption="Ваша динамика уровня стресса"
    )
    
    # Закрываем буфер
    img_buffer.close()
'''
