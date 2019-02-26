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
        self.processed_text['words']['most_popular_words'] = words_counter.most_common(10)
        self.processed_text['words']['persent_unique_words'] = self.processed_text['words']['unique_words'] / self.processed_text['words']['total_words'] * 100.0

    def _get_shingles(self, text):
        shingles = [] 
        for i in range(len(text) - (self.shingle_len - 1)):
            shingles.append(binascii.crc32(' '.join([x for x in text[i : i + self.shingle_len]]).encode('utf-8')))

        self.processed_text['words']['shingles'] = shingles

    def process(self, raw_text):
        self.processed_text.clear()

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
            'faculty': self.faculty,
            'text': self.text,
            'words': self.words,
            'symbols': self.symbols
        }

        return serialized_document

    def compare_shingles(shingles_x, shingles_y):
        x = set(shingles_x)
        y = set(shingles_y)

        min_len = len(x) if len(x) < len(y) else len(y)

        return len(x & y) / min_len * 100.0

ReportFromDB = namedtuple('ReportFromDB', 
['title', 'date', 'author', 'group', 'faculty', 'text', 'words', 'symbols'])

class DataBase:
    def __init__(self, url, db_name):
        self.db = pymongo.MongoClient(url)[db_name]
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

    def get_report_by_id(self, report_id):
        return ReportFromDB(**self.db['reports'].find_one({'_id': report_id}, {'_id': 0}))

    def get_reports_by_author(self, author):
        for report in self.db['reports'].find({'author': author}, {'_id': 0}):
            yield ReportFromDB(**report)

    def get_reports_by_group(self, group):
        for report in self.db['reports'].find({'group': group}, {'_id': 0}):
            yield ReportFromDB(**report)
    
    def get_reports_by_faculty(self, faculty):
        for report in self.db['reports'].find({'faculty': faculty}, {'_id': 0}):
            yield ReportFromDB(**report)

    def get_reports_by_course(self, course):
        for report in self.db['reports'].find({'course': course}, {'_id': 0}):
            yield ReportFromDB(**report)

if __name__ == "__main__":
    text_processor = TextProcessor()
    db = DataBase('mongodb://localhost:27017/', 'nosql1h19-report-stats')

    report = Report('IDZRybinA_S_Var_15.docx', {
        'title': 'Курсовая по БД',
        'author': 'rybin', 
        'group': 6304,
        'course': 2,
        'faculty': 'FKTI'
        }, text_processor)

    print(f'most used words: {report.words["most_popular_words"]}')

    inserted_id = db.save_report(report)
    print(f'inserted id: {inserted_id}')

    report_from_db = db.get_report_by_id(inserted_id)
    print(f'from db by id [title]: {report_from_db.title}')

    reports_from_db = db.get_reports_by_author('rybin')
    for report in reports_from_db:
        print(f'from db by author [title]: {report.title}')
