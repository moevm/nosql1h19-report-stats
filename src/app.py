import ast

from flask import Flask, render_template, request, redirect, url_for, session, json

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

            meta = convert_to_meta(request.form)

            report = Report(path, meta, app.text_processor)
            os.remove(path)
            print('[+] Created report')

            try:
                id_ = app.db.save_report(report)
                print(f'[+] Saved report in db with id:{id_}')
            except:
                print('[-] Not saved report')
                return render_template('upload.html',
                                       data=request.form,
                                       msg='Ошибка сохранения отчета в БД')

            try:
                statistics_from_db = app.db.get_report_stat_by_id(id_)
                print('[+] Get stat from report successfully')
                return redirect(url_for('report_stat_page', data={'words': statistics_from_db['words'],
                                                                  'symbols': statistics_from_db['symbols']}))

            except:
                print("[-] Getting stat from db error")
                return render_template('upload.html',
                                       data=request.form,
                                       msg='Невозможно получить статистику по отчету')

        else:
            print(request.form)
            return render_template('upload.html', data=request.form)


@app.route('/report_stat')
def report_stat_page():
    data = request.args['data']

    if data:
        return render_template('report_stat.html', data=ast.literal_eval(data))
    else:
        return redirect(url_for('main_page'))


@app.route('/groups')
def groups_page():
    if request.method == 'GET':
        try:
            faculties, courses, departments = app.db.get_all_faculties(), \
                                              app.db.get_all_courses(), \
                                              app.db.get_all_departments()
        except:
            print("[-] Error get list for groups page from db")
            render_template('groups.html', msg='Невозможно получить список факультетов/кафедр/групп')

        create_selectors = lambda x: ['Любой'] + sorted(x) if x else ['Любой']

        return render_template('groups.html',
                               faculties=create_selectors(faculties),
                               departments=create_selectors(departments),
                               courses=create_selectors(courses))


@app.route('/groups_stat', methods=['GET', 'POST'])
def return_groups_info():
    try:
        faculty, department, course = request.form['faculty'], request.form['department'], request.form['course']
        print(f'[+] Get data from selectors: {course}, {department}, {faculty}')
    except:
        return json.dumps({})

    try:
        course = int(course) if course != 'Любой' else None
    except:
        return json.dumps({})

    res = app.db.get_stat_by_groups(course=course,
                                    faculty=faculty if faculty != 'Любой' else None,
                                    department=department if department != 'Любой' else None)

    data = {}
    for id, stat in enumerate(res):
        data[id] = stat
    return json.dumps(data)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main_page'))


if __name__ == '__main__':
    app.run(debug=True)
