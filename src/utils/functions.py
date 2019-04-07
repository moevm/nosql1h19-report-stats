import os
import shutil
from time import gmtime, strftime

import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt


def validate_input(data, allow_empty=False):
    """ Check input dict strings by regex. """
    import re
    p_text = re.compile(r'^[^@_!#$%^&*()<>?\/|}{~:]+$')
    p_group = re.compile(r'^\d{4}$')
    p_course = re.compile(r'^[1-6]$')
    p_author = re.compile(r'^[^@_!#$%^&*()<>?\/|}{~:\d]+$')
    p_fac = re.compile(r'^(?:ФКТИ|ФЭЛ|ФРТ|ОФ|ФЭМ|ГФ|ФИБС|ФЭА)$')
    p_file = re.compile(r'^[^@_!#$%^&*()<>?\/|}{~:]+.docx$')

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
            if allow_empty and not value:
                continue
            if not re.match(pairs[key]['regex'], value):
                raise ValueError(error_string.format(pairs[key]['name'], pairs[key]['error']))

    return 'OK'


def generate_secret_key():
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


def save_file(file, path):
    if not os.path.exists(path):
        os.makedirs(path)

    filename = file.filename
    print(f'[+] Saving file: {filename}')
    path = os.path.join(path, filename)
    try:
        file.save(path)
        print(f'[+] Saved file: {path}')
        return path

    except:
        print(f'[-] File {path} not saved. Error return.')
        raise OSError("Can't save file")


def build_bar_graph(info):
    prefix = 'bar_graphs'
    shutil.rmtree(prefix, ignore_errors=True)
    if not os.path.exists(prefix):
        os.makedirs(prefix)

    words_stat = list(reversed(info[:10 if len(info) > 10 else len(info)]))

    words = list(map(lambda x: x[0], words_stat))
    stat = list(map(lambda x: x[1], words_stat))
    y_pos = np.arange(len(words))

    fig = plt.figure()
    plt.gcf().subplots_adjust(left=0.2)
    plt.rc('ytick', labelsize=8)

    plt.barh(y_pos, stat, align='center')
    plt.yticks(y_pos, words)
    plt.xlabel('Количество')
    plt.title('Самые популярные слова')

    image_name = prefix + f'/image_{strftime("%Y_%m_%d_%H_%M_%S", gmtime())}.png'
    fig.savefig(image_name)

    return image_name



if __name__ == '__main__':
    pass
