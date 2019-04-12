import pymongo

class ReportsDataBase:
    def __init__(self, url, db_name):
        self.db = pymongo.MongoClient(url)[db_name]

        self.db['reports'].create_index('group')
        self.db['reports'].create_index('author')
        self.db['reports'].create_index('title')
        
        self.db['reports'].create_index([
            ('group', pymongo.ASCENDING),
            ('author', pymongo.ASCENDING)
        ])
        
        self.db['reports'].create_index([
            ('group', pymongo.ASCENDING), 
            ('faculty', pymongo.ASCENDING), 
            ('department', pymongo.ASCENDING)
        ])

    def _drop_reports(self):
        self.db['reports'].drop()
        
    def save_report(self, report):
        insert_result = self.db['reports'].insert_one(report.serialize_db())
        inserted_id =  insert_result.inserted_id

        return inserted_id

    def save_reports(self, reports):
        reports_to_insert = map(lambda report: report.serialize_db(), reports)
        insert_result = self.db['reports'].insert_many(reports_to_insert)
        insterted_ids = insert_result.insterted_ids

        return insterted_ids

    def update_report(self, report_id, update_dict):
        self.db['reports'].update_one({'_id': report_id}, {'$set': update_dict})

    def get_all_faculties(self):
        return sorted(self.db['reports'].distinct('faculty'))

    def get_all_courses(self):
        return sorted(self.db['reports'].distinct('course'))

    def get_all_departments(self):
        return sorted(self.db['reports'].distinct('department'))

    def get_report_by_id(self, report_id):
        return self.db['reports'].find_one({'_id': report_id})

    def get_report_stat_by_id(self, report_id):
        report = self.get_report_by_id(report_id)
        
        report.pop('text', None)
        report['words'].pop('unique_words', None)

        return report

    def get_reports_by_author(self, author):
        for report in self.db['reports'].find({'author': author}).sort('title'):
            yield report

    def get_reports_by_group(self, group):
        for report in self.db['reports'].find({'group': group}).sort('author'):
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

    def get_stat_of_author(self, author):
        cur = self.db['reports'].aggregate([
            {'$match': {'author': author}},
            {'$group': {
                '_id': None, 
                'avg_total_words': {'$avg': '$words.total_words'},
                'avg_unique_words': {'$avg': '$words.total_unique_words'},
                'avg_persent_unique_words': {'$avg': '$words.persent_unique_words'},
                'unique_words': {'$addToSet': '$words.unique_words'},
                'avg_total_raw_symbols': {'$avg': '$symbols.total_raw_symbols'},
                'avg_total_clean_symbols': {'$avg': '$symbols.total_clean_symbols'},
                'total_reports_loaded': {'$sum': 1},
                }
            },
            {'$addFields': {
                'unique_words': {
                    '$reduce': {
                        'input': '$unique_words',
                        'initialValue': [],
                        'in': {'$setUnion': ['$$value', '$$this']}
                    }
                }
                }
            },
            {'$addFields': {'total_unique_words': {'$size': '$unique_words'}}}
        ])

        return cur.next()

    def get_stat_of_group(self, group):
        return self.db['reports'].aggregate([
            {'$match': {'group': group}},
            {'$group': {
                '_id': '$author', 
                'avg_total_words': {'$avg': '$words.total_words'},
                'avg_unique_words': {'$avg': '$words.total_unique_words'},
                'avg_persent_unique_words': {'$avg': '$words.persent_unique_words'},
                'unique_words': {'$addToSet': '$words.unique_words'},
                'avg_total_raw_symbols': {'$avg': '$symbols.total_raw_symbols'},
                'avg_total_clean_symbols': {'$avg': '$symbols.total_clean_symbols'},
                'total_reports_loaded': {'$sum': 1}
                }
            },
            {'$addFields': {
                'unique_words': {
                    '$reduce': {
                        'input': '$unique_words',
                        'initialValue': [],
                        'in': {'$setUnion': ['$$value', '$$this']}
                    }
                }
                }
            },
            {'$addFields': {'total_unique_words': {'$size': '$unique_words'}}},
            {'$sort': {'_id': 1, 'total_unique_words': -1}}
        ])

    def get_stat_by_groups(self, course=None, faculty=None, department=None):
        group = {
            '$group': {
                '_id': '$group',
                'avg_total_words': {'$avg': '$words.total_words'},
                'avg_unique_words': {'$avg': '$words.total_unique_words'},
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
            sort['$sort']['faculty'] = 1
        elif department and not course and not faculty:
            match = {'$match': {'department': department}}
            sort['$sort']['department'] = 1
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

    def get_words_compare(self, authors, group):
        match_list = []
        for author in authors:
            match_list.append({'author': author})

        match = {
            '$match': {
                '$and':
                    [
                        {'group': group},
                        {'$or': match_list}
                    ]
            }
        }

        query = self.db['reports'].aggregate([
            match,
            {'$group:': {
                '_id': '$author', 
                'unique_words': {'$addToSet': '$words.unique_words'}
            }},
            {'$addFields': {
                'unique_words': {
                    '$reduce': {
                        'input': '$unique_words',
                        'initialValue': [],
                        'in': {'$setUnion': ['$$value', '$$this']}
                    }
                }
                }
            },
            {'$sort': {'_id': 1}}
        ])

        compare = {}

        for author in query:
            compare[author['_id']] = dict()

            for other_author in query:
                if other_author['_id'] == author['_id']:
                    compare[author['_id']][author['_id']] = float('nan')
                else:
                    author_unique_words = set(author['unique_words']),
                    other_author_unique_words = set(other_author['unique_words'])

                    author_num_unique_words = len(author_unique_words)
                    other_author_num_unique_words = len(other_author_unique_words)

                    compare[author['_id']][other_author['_id']] = len(set.intersection(
                        author_unique_words,
                        other_author_unique_words
                    )) / min(author_num_unique_words, other_author_num_unique_words) * 100.0

        return compare