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

            session['input_data'] = request.form
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
                statistic_from_db = app.db.get_report_stat_by_id(id_)
                print('[+] Get stat from report successfully')
                return redirect(url_for('report_stat_page', data={'words': statistic_from_db['words'],
                                                                  'symbols': statistic_from_db['symbols']}))

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

    if not data:
        return redirect(url_for('main_page'))

    return render_template('report_stat.html', data=ast.literal_eval(data))


@app.route('/select')
def select_page():
    if request.method == 'GET':
        try:
            faculties = app.db.get_all_faculties()
            courses = app.db.get_all_courses()
            departments = app.db.get_all_departments()
        except:
            print("[-] Error get list for select page from db")
            render_template('select.html', msg='Невозможно получить список факультетов/кафедр/групп')

        return render_template('select.html',
                               faculties=faculties,
                               departments=departments,
                               courses=courses)


@app.route('/get_data_for_select', methods=['GET', 'POST'])
def return_groups_info():
    try:
        faculty = request.form['faculty']
        department = request.form['department']
        course = request.form['course']
        print(f'[+] Get data from selectors: {course}, {department}, {faculty}')
    except:
        return json.dumps({})

    if faculty == 'Любой':
        faculty = None

    if department == 'Любой':
        department = None

    if course == 'Любой':
        course = None

    res = app.db.get_stat_by_groups(course=course, faculty=faculty, department=department)

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
