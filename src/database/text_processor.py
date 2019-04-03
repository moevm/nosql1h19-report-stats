import re
import string
from collections import Counter

import pymorphy2
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

class TextProcessor:
    def __init__(self, extra_stop_words=[], num_top_words=25):
        self.punctuation_re = re.compile(f'[{re.escape(string.punctuation)}]')
        self.digits_re = re.compile(r'\d+')
        self.no_words_re = re.compile(r'\W+')
        self.stop_words = stopwords.words('russian') + extra_stop_words
        self.morph = pymorphy2.MorphAnalyzer()
        self.num_top_words = num_top_words

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
        words = list(words_counter)

        self.processed_text['words']['total_unique_words'] = len(words)
        self.processed_text['words']['unique_words'] = words
        self.processed_text['words']['most_popular_words'] = words_counter.most_common(self.num_top_words)
        self.processed_text['words']['persent_unique_words'] = self.processed_text['words']['total_unique_words'] / self.processed_text['words']['total_words'] * 100.0

    def process(self, raw_text):
        self.processed_text['text'].clear()
        self.processed_text['words'].clear()
        self.processed_text['symbols'].clear()

        self._clean_raw_text(raw_text)
        self._tokenize(self.processed_text['text']['clean_text'])

        return self.processed_text