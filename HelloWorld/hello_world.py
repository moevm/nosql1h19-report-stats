from docx import Document

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

from collections import Counter, deque

import pymorphy2

import re

import string

import binascii

import pymongo

class TextProcessor:
    def __init__(self, shingle_len=10, extra_stop_words=[]):
        self.shingle_len = shingle_len
        self.punctuation_re = re.compile(f'[{re.escape(string.punctuation)}]')
        self.digits_re = re.compile(r'\d+')
        self.no_words_re = re.compile(r'\W+')
        self.stop_words = stopwords.words('russian') + extra_stop_words
        self.morph = pymorphy2.MorphAnalyzer()
        
    def clean_raw_text(self, raw_text):
        raw_text = raw_text.lower()
        raw_text = self.punctuation_re.sub('', raw_text)
        raw_text = self.digits_re.sub('', raw_text)
        raw_text = self.no_words_re.sub(' ', raw_text)

        return raw_text

    def tokenize(self, text):
        raw_words = word_tokenize(text)
        clean_words = [word for word in raw_words if word not in self.stop_words]
        normal_words = [self.morph.parse(word)[0].normal_form for word in clean_words]

        return normal_words

    def get_shingles(self, text):
        shingles = [] 
        for i in range(len(text) - (self.shingle_len - 1)):
            shingles.append(binascii.crc32(' '.join([x for x in text[i : i + self.shingle_len]]).encode('utf-8')))

        return shingles

    def process(self, raw_text):
        clean_text = self.clean_raw_text(raw_text)
        tokens = self.tokenize(clean_text)
        shingles = self.get_shingles(tokens)

        return clean_text, tokens, shingles
    
class Report:
    def __init__(self, docx_text, meta, text_processor):
        self.document = Document(docx_text)
        self.date = self.document.core_properties.modified

        self.title = meta['title']
        self.author = meta['author']
        self.group = meta['group']
        self.course = meta['course']
        self.faculty = meta['faculty']
        
        self.raw_text = ' '.join([par.text for par in self.document.paragraphs])
        self.clean_text, self.tokens, self.shingles = text_processor.process(self.raw_text)

        self.words_counter = Counter(self.tokens)
        self.most_popular_words = self.words_counter.most_common(10)
        self.num_unique_words = len(self.words_counter)

    def most_popular_words(self, num=10):
        return self.words_counter.most_common(num)

    def num_unique_words(self):
        return len(self.words_counter)

    def serialize_db(self):
        document = {
            'title': self.title,
            'meta': {
                'date': self.date,
                'author': self.author,
                'group': self.group,
                'faculty': self.faculty
            },
            'clean_text': self.clean_text,
            'tokens': self.tokens,
            'shingles': self.shingles,
            'most_popular_words': self.most_popular_words,
            'num_unique_words': self.num_unique_words
        }

        return document

    def compare_shingles(shingles_x, shingles_y):
        return len(set(shingles_x) & set(shingles_y))

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

    def get_report_by_id(self, report_id):
        return self.db['reports'].find_one({'_id': report_id})

    def get_reports_by_author(self, author):
        return self.db['reports'].find({'author': author})

    def get_reports_by_group(self, group):
        return self.db['reports'].find({'group': group})
    
    def get_reports_by_faculty(self, faculty):
        return self.db['reports'].find({'faculty': faculty})

    def get_reports_by_course(self, course):
        return self.db['reports'].find({'course': course})

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

    print(f'most used words: {report.most_popular_words}')

    inserted_id = db.save_report(report)
    print(f'inserted id: {inserted_id}')

    report_from_db = db.get_report_by_id(inserted_id)
    print(f'from db by id [title]: {report_from_db["title"]}')