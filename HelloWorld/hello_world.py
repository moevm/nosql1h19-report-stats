import sys
sys.path.append('../')

from src.database.text_processor import TextProcessor
from src.database.reports_data_base import ReportsDataBase
from src.database.report import Report

if __name__ == "__main__":
    actions = '''
        - [0] для тестирования кода в секции для теста
        - [1] для загрузки нового отчёта в БД
        - [2] очистить БД
    '''

    text_processor = TextProcessor()
    db = ReportsDataBase('mongodb://localhost:27017/', 'nosql1h19-report-stats')

    action = int(input(actions))
    if action == 1:
        # Вставка нового отчета в БД

        meta = dict()
        path = input('Путь до файла docx ')
        meta['title'] = input('Название ')
        meta['author'] = input('Автор ')
        meta['group'] = int(input('Группа '))
        meta['department'] = input('Кафедра ')
        meta['course'] = int(input('Курс '))
        meta['faculty'] = input('Факультет ')

        report = Report(path, meta, text_processor)
        inserted_id = db.save_report(report)
        print(f'inserted_id: {inserted_id}')
    elif action == 0:
        # Для тестирования

        print('query by group 6304 all reports in db:')
        for report in db.get_reports_by_group(6304):
            print(f'''
                    title: [{report["title"]}] 
                    num_unique_words: [{report["words"]["total_unique_words"]}]
                    most_popular_words: {report["words"]["most_popular_words"][:5]}
                    ''')

        print('stat of group 6304:')
        for result in db.get_stat_of_group(6304):
            print(f'author: [{result["_id"]}] avg_unique_words: [{result["avg_unique_words"]}]')

        print('stat of groups:')
        for result in db.get_stat_by_groups():
            print(f'group: [{result["_id"]}] total_reports_loaded: [{result["total_reports_loaded"]}]')

        print('stat of author Рыбин А.С.')
        stat = db.get_stat_of_author('Рыбин А.С.')
        print(f'''
                avg_unique_words: [{stat["avg_unique_words"]}],
                total_unique_words: [{stat["total_unique_words"]}]
                unique_words: {stat["unique_words"][:25]}
                ''')
    elif action == 2:
        # Очистка коллекции с отчетами

        db._drop_reports()
    else:
        raise ValueError