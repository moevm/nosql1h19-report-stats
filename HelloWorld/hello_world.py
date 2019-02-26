import binascii
import re
import string
from collections import Counter, deque, namedtuple

import pymongo
import pymorphy2
from docx import Document
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

class TextProcessor:
    def __init__(self, shingle_len=10, extra_stop_words=[]):
        self.shingle_len = shingle_len
        self.punctuation_re = re.compile(f'[{re.escape(string.punctuation)}]')
        self.digits_re = re.compile(r'\d+')
        self.no_words_re = re.compile(r'\W+')
        self.stop_words = stopwords.words('russian') + extra_stop_words
        self.morph = pymorphy2.MorphAnalyzer()

        self.processed_text = dict()
        self.processed_text['symbols'] = dict()
        self.processed_text['text'] = dict()
        self.processed_text['words'] = dict()
        
    def _clean_raw_text(self, raw_text):
        self.processed_text['text']['raw_text'] = raw_text
        self.processed_text['symbols']['total_raw_symbols'] = len(raw_text)

        clean_text = raw_text.lower()
        clean_text = self.punctuation_re.sub('', clean_text)
        clean_text = self.digits_re.sub('', clean_text)
        clean_text = self.no_words_re.sub(' ', clean_text)

        self.processed_text['text']['clean_text'] = clean_text
        self.processed_text['symbols']['total_clean_symbols'] = len(clean_text)

    def _tokenize(self, text):
        raw_words = word_tokenize(text)
        clean_words = [word for word in raw_words if word not in self.stop_words]
        normal_words = [self.morph.parse(word)[0].normal_form for word in clean_words]

        self.processed_text['words']['words'] = normal_words
        self.processed_text['words']['total_words'] = len(normal_words)

        words_counter = Counter(normal_words)

        self.processed_text['words']['unique_words'] = len(words_counter)
        most_popular_words = list(map(lambda word: word[0], words_counter.most_common(5)))
        self.processed_text['words']['most_popular_words'] = most_popular_words
        self.processed_text['words']['persent_unique_words'] = self.processed_text['words']['unique_words'] / self.processed_text['words']['total_words'] * 100.0

    def _get_shingles(self, text):
        shingles = [] 
        for i in range(len(text) - (self.shingle_len - 1)):
            shingles.append(binascii.crc32(' '.join([x for x in text[i : i + self.shingle_len]]).encode('utf-8')))

        self.processed_text['words']['shingles'] = shingles

    def process(self, raw_text):
        self.processed_text['text'].clear()
        self.processed_text['words'].clear()
        self.processed_text['symbols'].clear()

        self._clean_raw_text(raw_text)
        self._tokenize(self.processed_text['text']['clean_text'])
        self._get_shingles(self.processed_text['words']['words'])

        return self.processed_text
    
class Report:
    def __init__(self, docx_text, meta, text_processor):
        self.document = Document(docx_text)
        
        self.date = self.document.core_properties.modified
        self.title = meta['title']
        self.author = meta['author']
        self.group = meta['group']
        self.department = meta['department']
        self.course = meta['course']
        self.faculty = meta['faculty']
        
        raw_text = ' '.join([par.text for par in self.document.paragraphs])
        processed_text = text_processor.process(raw_text)

        self.text = processed_text['text']
        self.words = processed_text['words']
        self.symbols = processed_text['symbols']

    def serialize_db(self):
        serialized_document = {
            'title': self.title,
            'date': self.date,
            'author': self.author,
            'group': self.group,
            'department': self.department,
            'course': self.course,
            'faculty': self.faculty,
            'text': self.text,
            'words': self.words,
            'symbols': self.symbols
        }

        return serialized_document

    @staticmethod
    def compare_shingles(shingles_x, shingles_y):
        x = set(shingles_x)
        y = set(shingles_y)

        min_len = len(x) if len(x) < len(y) else len(y)

        return len(x & y) / min_len * 100.0

class ReportsDataBase:
    def __init__(self, url, db_name):
        self.db = pymongo.MongoClient(url)[db_name]

        self.db['reports'].create_index({'author': 1})
        self.db['reports'].create_index({'group': 1})
        self.db['reports'].create_index({'faculty': 1})
        self.db['reports'].create_index({'department': 1})
        self.db['reports'].create_index({'group': 1, 'course': 1, 'faculty': 1, 'department': 1})
        
        self.last_inserted_reports = deque(maxlen=15)

    def save_report(self, report):
        insert_result = self.db['reports'].insert_one(report.serialize_db())
        inserted_id =  insert_result.inserted_id

        self.last_inserted_reports.appendleft({
            'id': inserted_id,
            'report': report
        })

        return inserted_id

    def save_reports(self, reports):
        reports_to_insert = map(lambda report: report.serialize_db(), reports)
        insert_result = self.db['reports'].insert_many(reports_to_insert)
        insterted_ids = insert_result.insterted_ids

        for report, inserted_id in zip(reversed(reports), insterted_ids):
            self.last_inserted_reports.appendleft({
                'id': inserted_id,
                'report': report
            })

        return insterted_ids

    def _drop_reports(self):
        self.db['reports'].drop()

    def get_report_by_id(self, report_id):
        return self.db['reports'].find_one({'_id': report_id})

    def get_reports_by_author(self, author):
        for report in self.db['reports'].find({'author': author}):
            yield report

    def get_reports_by_group(self, group):
        for report in self.db['reports'].find({'group': group}):
            yield report
    
    def get_reports_by_faculty(self, faculty):
        for report in self.db['reports'].find({'faculty': faculty}):
            yield report

    def get_reports_by_course(self, course):
        for report in self.db['reports'].find({'course': course}):
            yield report

    def get_reports_by_department(self, department):
        for report in self.db['reports'].find({'department': department}):
            yield report

    def get_stat_of_group(self, group):
        return self.db['reports'].aggregate([
            {'$match': {'group': group}},
            {'$group': {
                '_id': '$author', 
                'avg_total_words': {'$avg': '$words.total_words'},
                'avg_unique_words': {'$avg': '$words.unique_words'},
                'avg_persent_unique_words': {'$avg': '$words.persent_unique_words'},
                'most_popular_words': {'$addToSet': '$words.most_popular_words'},
                'avg_total_raw_symbols': {'$avg': '$symbols.total_raw_symbols'},
                'avg_total_clean_symbols': {'$avg': '$symbols.total_clean_symbols'},
                'total_reports_loaded': {'$sum': 1}
                }},
            {'$sort': {'_id': 1, 'avg_unique_words': -1}}
        ])

    def get_stat_by_groups(self, course=None, faculty=None, department=None):
        group = {
            '$group': {
                '_id': '$group',
                'avg_total_words': {'$avg': '$words.total_words'},
                'avg_unique_words': {'$avg': '$words.unique_words'},
                'avg_persent_unique_words': {'$avg': '$words.persent_unique_words'},
                'total_reports_loaded': {'$sum': 1}
            }}

        sort = {'$sort': {'_id': 1}}

        if not course and not faculty and not department:
            return self.db['reports'].aggregate([
                group,
                sort
            ])

        if course and not faculty and not department:
            match = {'$match': {'course': course}}
        elif faculty and not course and not department:
            match = {'$match': {'faculty': faculty}}
            sort = {'$sort': {'_id': 1, 'faculty': 1}}
        elif department and not course and not faculty:
            match = {'$match': {'department': department}}
            sort = {'$sort': {'_id': 1, 'department': 1}}
        elif course and faculty or course and department or faculty and department:
            match_list = []
            if course:
                match_list.append({'course': course})
            if faculty:
                match_list.append({'faculty': faculty})
                sort['$sort']['faculty'] = 1
            if department:
                match_list.append({'department': department})
                sort['$sort']['department'] = 1

            match = {'$match': {'$and': match_list}}

        return self.db['reports'].aggregate([
            match,
            group,
            sort
        ])
        
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

        print('query by group all reports in db:')
        for report in db.get_reports_by_group(6304):
            print(f'author: [{report["author"]}] title: [{report["title"]}] group: [{report["group"]}]')

        print('stat of group:')
        for result in db.get_stat_of_group(6304):
            print(f'author: [{result["_id"]}] avg_unique_words: [{result["avg_unique_words"]}] group: [{report["group"]}]')
    elif action == 2:
        # Очистка коллекции с отчетами

        db._drop_reports()
    else:
        raise ValueError