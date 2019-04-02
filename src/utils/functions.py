def validate_input(data, allow_empty=false):
    """ Check input dict strings by regex. """
    import re
    p_text = re.compile(r'^[^@_!#$%^&*()<>?\/|}{~:]+$')
    p_group = re.compile(r'^\d{4}$')
    p_course = re.compile(r'^[1-6]$')
    p_title = re.compile(r'^[^@_!#$%^&*()<>?\/|}{~:\d]+$')
    p_fac = re.compile(r'^(?:ФКТИ|ФЭЛ|ФРТ|ОФ|ФЭМ|ГФ|ФИБС|ФЭА)$')
    p_file = re.compile(r'^[^@_!#$%^&*()<>?\/|}{~:]+\.docx$')

    error_string = 'Поле "{}" {}'

    pairs = {
        'author':
            {'name': 'Автор', 'regex': p_title,
             'error': 'не должно содержать спец.символы и цифры'},
        'title':
            {'name': 'Название отчета', 'regex': p_text,
             'error': 'не должно содержать спец.символы'},
        'faculty':
            {'name': 'Факультет', 'regex': p_fac,
             'error': 'должно быть одним из вариантов: ФКТИ, ФЭЛ, ФРТ, ОФ, ФЭМ, ГФ, ФИБС, ФЭА'},
        'department':
            {'name': 'Кафедра', 'regex': p_text,
             'error': 'не должно содержать спец.символы'},
        'course':
            {'name': 'Курс', 'regex': p_course,
             'error': 'должно быть числом от 1 до 6'},
        'group':
            {'name': 'Группа', 'regex': p_group,
             'error': 'должно быть четырзначным числом'},
        'file':
            {'name': 'Файл', 'regex': p_file,
             'error': 'должно оканчиваться на .docx и не содержать спец.символы'},
    }

    for key, value in data.items():
        if key in pairs:
            if allow_empty and not value:
                continue
            if not re.match(pairs[key]['regex'], value):
                raise ValueError(error_string.format(pairs[key]['name'], pairs[key]['error']))

    return 'OK'


def generate_secret_key():
    import os
    return os.urandom(24)


def convert_to_meta(form):
    return {
        'title': form['title'],
        'author': form['author'],
        'group': int(form['group']),
        'department': form['department'],
        'course': int(form['course']),
        'faculty': form['faculty'],
    }


if __name__ == '__main__':
    pass
