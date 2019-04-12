from bson import ObjectId
from flask import Flask, render_template, request, redirect, url_for, session, json, send_file

from database.report import Report
from database.reports_data_base import ReportsDataBase
from database.text_processor import TextProcessor
from utils.functions import *

app = Flask(__name__)
app.secret_key = generate_secret_key()

UPLOAD_FOLDER = 'reports/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.db = ReportsDataBase('mongodb://localhost:27017/', 'nosql1h19-report-stats')
app.text_processor = TextProcessor()


@app.route('/')
def main_page():
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'GET':
        return render_template('upload.html', data=request.form)

    if request.method == 'POST':
        try:
            code = validate_input(request.form)
        except ValueError as ex:
            return render_template('upload.html', data=request.form, msg=ex)

        if code == 'OK':
            try:
                path = save_file(request.files['file'], app.config['UPLOAD_FOLDER'])
            except:
                return render_template('upload.html',
                                       data=request.form,
                                       msg='Ошибка загрузки отчета')

            report = Report(path, serialized_meta(request.form), app.text_processor)
            os.remove(path)

            try:
                id_ = app.db.save_report(report)
                return redirect(f'/report_stat/{id_}')

            except:
                return render_template('upload.html',
                                       data=request.form,
                                       msg='Ошибка сохранения отчета')
        else:
            return render_template('upload.html', data=request.form)


@app.route('/report_stat/<id_>')
def report_stat_page(id_):
    try:
        statistics_from_db = app.db.get_report_stat_by_id(ObjectId(id_))
        return render_template('report_stat.html', data={'words': statistics_from_db['words'],
                                                         'symbols': statistics_from_db['symbols']})
    except:
        return render_template('error_page.html',
                               msg='Невозможно получить статистку по загруженному отчету')


@app.route('/groups')
def groups_page():
    try:
        faculties, courses, departments = app.db.get_all_faculties(), \
                                          app.db.get_all_courses(), \
                                          app.db.get_all_departments()
    except:
        render_template('groups.html',
                        msg='Невозможно получить список факультетов/кафедр/групп')

    create_selectors = lambda x: ['Любой'] + sorted(x) if x else ['Любой']

    return render_template('groups.html',
                           faculties=create_selectors(faculties),
                           departments=create_selectors(departments),
                           courses=create_selectors(courses))


@app.route('/groups_stat', methods=['GET', 'POST'])
def return_groups_info():
    try:
        faculty, department, course = request.form['faculty'], request.form['department'], request.form['course']

        course = int(course) if course != 'Любой' else None
        res = app.db.get_stat_by_groups(course=course,
                                        faculty=faculty if faculty != 'Любой' else None,
                                        department=department if department != 'Любой' else None)
    except:
        return json.dumps({})

    data = {}
    for id, stat in enumerate(res):
        data[id] = stat
    return json.dumps(data)


def validate_path(group_num, person=None, report_id=None):
    groups = app.db.get_stat_by_groups()
    if group_num not in [g['_id'] for g in groups]:
        raise Exception()

    if person is not None:
        stat = app.db.get_stat_of_group(int(group_num))
        if person not in [p['_id'] for p in stat]:
            raise Exception()

        if report_id is not None:
            reports = app.db.get_report_stat_by_id(ObjectId(report_id))


@app.route('/groups/<int:group_num>', methods=['GET', 'POST'])
def group_stat_page(group_num):
    try:
        validate_path(group_num=group_num)
    except:
        return render_template('error_page.html',
                               msg=f'Группа {group_num} не найдена в базе данных')

    if request.method == 'GET':
        try:
            stat = app.db.get_stat_of_group(group_num)

            data = []
            for person in stat:
                del person['unique_words']
                data.append(person)

            return render_template('group_stat.html', data=data, group_num=group_num)

        except:
            return render_template('error_page.html',
                                   msg=f'Невозможно получить статистику группы {group_num} из базы данных')

    if request.method == 'POST':
        return redirect(url_for('compare_page',
                                persons=[v for _, v in request.form.items()],
                                group=group_num))


@app.route('/compare')
def compare_page():
    try:
        data = request.args.getlist('persons')
        group = request.args.get('group')
    except:
        return render_template('error_page.html',
                               msg='Некорректные данные для пересечения словарных запасов')
    try:
        res = app.db.get_words_compare(data, group)
    except Exception as e:
        return render_template('error_page.html',
                               msg=f'persons:{data}, group:{group}, error:{e} ')

    return render_template('compare.html', data=res)


@app.route('/groups/<int:group_num>/<person>')
def person_stat_page(group_num, person):
    try:
        validate_path(group_num=group_num, person=person)
    except:
        return render_template('error_page.html',
                               msg=f'{person} не найден в группе {group_num}')

    try:
        total_person_stat = app.db.get_stat_of_author(person)
        del total_person_stat['unique_words']
    except:
        return render_template('error_page.html',
                               msg=f'Невозможно получить статистику для {person}')

    try:
        report_stat = []
        for report in app.db.get_reports_by_author(person):
            report_stat.append({
                'id': report['_id'],
                'title': report['title'],
                'total_words': report['words']['total_words'],
                'total_unique_words': report['words']['total_unique_words'],
                'persent_unique_words': report['words']['persent_unique_words']
            })
    except:
        return render_template('error_page.html',
                               msg=f'Невозможно получить статистику по отчетам для {person}')

    return render_template('person.html',
                           person=person,
                           group_num=group_num,
                           total_person_stat=total_person_stat,
                           report_stat=report_stat)


@app.route('/groups/<int:group_num>/<person>/<report_id>')
def report_page(group_num, person, report_id):
    try:
        validate_path(group_num=group_num, person=person, report_id=report_id)
    except:
        return render_template('error_page.html',
                               msg=f'Некорректная ссылка. Отчет не найден среди отчетов {person} группы {group_num}')

    try:
        report = app.db.get_report_stat_by_id(ObjectId(report_id))
        return render_template('report.html', title=report['title'], data=report)
    except:
        return render_template('error_page.html',
                               msg=f'Невозможно получить статистику по отчету')


@app.route('/groups/<int:group_num>/<person>/<report_id>/bar_graph')
def get_image(group_num, person, report_id):
    try:
        validate_path(group_num=group_num, person=person, report_id=report_id)
        report = app.db.get_report_stat_by_id(ObjectId(report_id))

        image_name = build_bar_graph(report['words']['most_popular_words'])
        return send_file(image_name, mimetype='image/gif')
    except:
        return '', 204


@app.route('/edit/<report_id>', methods=['GET', 'POST'])
def edit_page(report_id):
    try:
        report = app.db.get_report_by_id(ObjectId(report_id))
    except:
        return render_template('error_page.html',
                               msg='Невозможно найти выбранный отчет')

    if request.method == 'GET':
        return render_template('edit.html', id=report_id, data=report)

    if request.method == 'POST':
        try:
            code = validate_input(request.form, is_empty_file=True)
        except ValueError as ex:
            return render_template('edit.html', id=report_id, data=request.form, msg=ex)

        if code == 'OK':
            if 'file' not in request.files.keys() or request.form['file'] == '':
                print(report_id, serialized_meta(request.form))
                app.db.update_report(ObjectId(report_id), serialized_meta(request.form))
                return redirect(f'/groups/{request.form["group"]}/{request.form["author"]}/{report_id}')
            else:
                try:
                    path = save_file(request.files['file'], app.config['UPLOAD_FOLDER'])
                except:
                    return render_template('edit.html',
                                           id=report_id,
                                           data=request.form,
                                           msg='Ошибка редактирования отчета')

                report = Report(path, serialized_meta(request.form), app.text_processor)
                os.remove(path)

                try:
                    app.db.update_report(ObjectId(report_id), report.serialize_db())
                    return redirect(f'/groups/{request.form["group"]}/{request.form["author"]}/{report_id}')

                except:
                    return render_template('edit.html',
                                           id=report_id,
                                           data=request.form,
                                           msg='Ошибка сохранения отчета')
        else:
            return render_template('edit.html', id=report_id, data=request.form)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main_page'))


if __name__ == '__main__':
    app.run(debug=True)
