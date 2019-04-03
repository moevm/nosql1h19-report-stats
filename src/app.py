import ast

from flask import Flask, render_template, request, redirect, url_for, session

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
            print(request.form)
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
                print('[+] Saved report in db')
            except:
                print('[-] Not saved report')
                return render_template('upload.html',
                                       data=request.form,
                                       msg='Ошибка сохранения отчета в БД')

            try:
                statistic_from_db = app.db.get_report_stat_by_id(id_)
                print(statistic_from_db)

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


@app.route('/select', methods=['GET', 'POST'])
def select_page():
    if request.method == 'GET':
        if 'input_data' in session and session['input_data']:
            newdict = {key: session['input_data'][key] for key in ['faculty', 'department', 'course']}
            return render_template('select.html', data=newdict)
        else:
            return render_template('select.html', data=request.form)

    if request.method == 'POST':
        # TODO empty strings must be allowed
        # try:
        #    code = validate_input(request.form)
        # except ValueError as ex:
        #    return render_template('select.html', data=request.form, msg=str(ex))

        course, faculty, department = request.form['course'], request.form['faculty'], request.form['department']

        list_groups = app.db.get_stat_by_groups(course=course, faculty=faculty, department=department)
        session['list_groups'] = [g for g in list_groups]
        return redirect(url_for('list_groups_page'))


@app.route('/list_groups')
def list_groups_page():
    if not session['list_groups']:
        return redirect(url_for('select_page'))

    data = session['list_groups']
    session['list_groups'] = None
    return render_template('list_groups.html', data=data)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main_page'))


if __name__ == '__main__':
    app.run(debug=True)
