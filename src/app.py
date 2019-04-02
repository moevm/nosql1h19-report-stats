import os

from flask import Flask, render_template, request, redirect, url_for, session
from utils.functions import *
from database import *
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = generate_secret_key()

UPLOAD_FOLDER = 'reports/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.db = ReportsDataBase('mongodb://localhost:27017/', 'nosql1h19-report-stats')
app.text_processor = TextProcessor()


def save_file(file):
    print('[+] Saving file:', file)
    filename = secure_filename(file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    print('[+] Saved file:', path)
    return path


@app.route('/')
def main_page():
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        try:
            code = validate_input(request.form)
        except ValueError as ex:
            session['input_data'], session['report_stat'] = None, None
            return render_template('upload.html', data=request.form, msg=ex)

        if code == 'OK':
            path = save_file(request.files['file'])

            session['input_data'] = request.form
            meta = convert_to_meta(request.form)

            report = Report(path, meta, app.text_processor)
            os.remove(path)

            id_ = app.db.save_report(report)
            statistic_from_db = app.db.get_stat_by_id(id_)
            session['report_stat'] = statistic_from_db['words']
            return redirect(url_for('report_stat_page'))
        else:
            return render_template('upload.html', data=request.form)

    if request.method == 'GET':
        return render_template('upload.html', data=request.form)


@app.route('/report_stat')
def report_stat_page():
    if not session['report_stat']:
        return redirect(url_for('main_page'))

    data = session['report_stat']
    session['report_stat'] = None
    return render_template('report_stat.html', data=data)


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
    app.run()
