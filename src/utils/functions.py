import os


def validate_input(data, is_empty_file=False):
    """ Check input dict strings by regex. """
    import re
    p_text = re.compile(r'^[^@!#$%^&*()<>?\/|}{~:]+$')
    p_group = re.compile(r'^\d{4}$')
    p_course = re.compile(r'^[1-6]$')
    p_author = re.compile(r'^[^@_!#$%^&*()<>?\/|}{~:\d]+$')
    p_fac = re.compile(r'^(?:ФКТИ|ФЭЛ|ФРТ|ОФ|ФЭМ|ГФ|ФИБС|ФЭА)$')
    p_file = re.compile(r'^[^*<>?\/|}{~:]+.docx$')

    error_string = 'Поле "{}" {}'

    pairs = {
        'author':
            {'name': 'Автор', 'regex': p_author,
             'error': 'не должно содержать спец.символы и цифры'},
        'title':
            {'name': 'Название отчета', 'regex': p_text,
             'error': 'должно содержать только буквы, цифры, символы нижнего подчеркивания и тире'},
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
             'error': 'должно быть четырехзначным числом'},
        'file':
            {'name': 'Файл', 'regex': p_file,
             'error': 'должно оканчиваться на .docx и не содержать спец.символов'},
    }

    for key, value in data.items():
        if key in pairs:
            if is_empty_file and key == 'file' and value == '':
                continue
            if not re.match(pairs[key]['regex'], value):
                raise ValueError(error_string.format(pairs[key]['name'], pairs[key]['error']))

    return 'OK'


def generate_secret_key():
    return os.urandom(24)


def serialized_meta(form):
    return {
        'title': form['title'],
        'author': form['author'],
        'group': int(form['group']),
        'department': form['department'],
        'course': int(form['course']),
        'faculty': form['faculty'],
    }


def save_file(file, path):
    if not os.path.exists(path):
        os.makedirs(path)

    filename = file.filename
    path = os.path.join(path, filename)
    try:
        file.save(path)
        return path

    except:
        raise OSError("Can't save file")


if __name__ == '__main__':
    pass
