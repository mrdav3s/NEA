#IMPORTS
from flask import Flask, render_template, session, abort, flash, send_from_directory
from flask import redirect, url_for, request, jsonify, send_from_directory
import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sqlite3, csv, os, io
from flask_mail import Mail, Message
import random


app = Flask(__name__)
app.secret_key = 'StudsightSecretKey123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
# mysql = MySQL(app)

# Flask-Mail config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'doludavid@gmail.com'
app.config['MAIL_PASSWORD'] = 'David12345!'
app.config['MAIL_DEFAULT_SENDER'] = 'doludavid15@gmail.com'

mail = Mail(app)


def generate_pin():
    return str(random.randint(100000, 999999))




def get_db():
    conn = sqlite3.connect("schooldata.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # important if you use FK constraints
    return conn


@app.route('/') # Home route
def home():
    return render_template("home.html")

connection = sqlite3.connect("accounts.db")
cursor = connection.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
               (ID INTEGER PRIMARY KEY AUTOINCREMENT,email TEXT, password TEXT)''')
connection.commit()
connection.close()



@app.route('/register', methods=['GET', 'POST']) # Register route
def register():
    if request.method == 'POST':
        email = request.form.get('email')


        conn = sqlite3.connect('schooldata.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Teachers WHERE email=?", (email,))
        user = cursor.fetchone()

        if user:
            conn.close()
            conn2 = sqlite3.connect('accounts.db')
            cursor = conn2.cursor()
            cursor.execute("SELECT * FROM users WHERE email=?", (email,))
            user2 = cursor.fetchone()
            conn2.close()

            if user2:
                flash('Account already exists. Please login.')
                return redirect(url_for('login'))
            else:
                password = request.form.get('password')
                confiirm_password = request.form.get('confirm_password')
                if password != confiirm_password:
                    flash('Passwords do not match. Please try again.')
                    return redirect(url_for('register'))
                
                conn2 = sqlite3.connect('accounts.db')
                cursor = conn2.cursor()
                cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
                conn2.commit()
                conn2.close()
                flash('Registration successful! Please login.')
                return redirect(url_for('login'))
        else:
            return redirect(url_for('register'))
    return render_template("register.html")





@app.route('/login', methods=['GET', 'POST']) # Login route
def login():
    if request.method == 'POST':
        email = request.form.get('email').lower()
        password = request.form.get('password')

        conn = sqlite3.connect('schooldata.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Teachers WHERE Email=?", (email,))
        user = cursor.fetchone()
        conn.close()

        conn2 = sqlite3.connect('accounts.db')
        cursor = conn2.cursor()

        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user2 = cursor.fetchone()
        conn2.close()

        if user:
            connection = sqlite3.connect("accounts.db")
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
            account = cursor.fetchone()
            

            if account:
                session['user'] = email
                return redirect(url_for('dashboard'))
            elif user2: 
                flash('Incorrect password. Try again.')
            else:
                flash('No account found with that email. Please register.')
                return redirect(url_for('register'))
        
        else:
            flash('Invalid email. Try again.')

    return render_template("login.html")




@app.route('/forgot_password', methods=['GET', 'POST']) # Forgot Password route
def forgot_password():
    connection = sqlite3.connect("accounts.db")
    cursor = connection.cursor()
    if request.method == 'POST':
        email = request.form.get('email')

        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        if user:
            pin = generate_pin()
            session['reset_pin'] = pin
            session['reset_email'] = email
            msg = Message('Password Reset PIN', recipients=[email])
            msg.body = f'Your password reset PIN is: {pin}'
            mail.send(msg)

            flash('Password reset link sent to your email.')
        else:
            flash('Email not found. Please try again.')
    return render_template("forgot_password.html")


@app.route('/verify_pin', methods=['GET', 'POST']) # Verify PIN route
def verify_pin():
    if request.method == 'POST':
        entered_pin = request.form.get('pin')
        if entered_pin == session.get('reset_pin'):
            flash('PIN verified! You can now reset your password.')
            return redirect(url_for('reset_password'))
        else:
            flash('Invalid PIN. Please try again.')
    return render_template("verify_pin.html")



@app.route('/reset_password', methods=['GET', 'POST']) # Reset Password route
def reset_password():
    connection = sqlite3.connect("accounts.db")
    cursor = connection.cursor()
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password == confirm_password:
            cursor.execute("UPDATE users SET password=? WHERE email=?", (new_password, session.get('reset_email')))
            connection.commit()
            flash('Password reset successful! Please login.')
            return redirect(url_for('login'))
        else:
            flash('Passwords do not match. Please try again.')
    return render_template("reset_password.html")

@app.route('/logout') # Logout route
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/dashboard') # Dashboard route
def dashboard():
    connection = sqlite3.connect("schooldata.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Teachers WHERE Email=?", (session['user'],))
    teacher = cursor.fetchall()
    if 'user' in session:
        for t in teacher:
            firstname = t[1]
            surname = t[2]
            gender = t[3]
            email = t[4]
            
        return render_template("dashboard.html", user=session['user'], firstname=firstname, surname=surname, gender=gender, email=email)
    else:
        flash('You must be logged in to view the dashboard.')
        return redirect(url_for('login'))


@app.route('/profile') # Profile route
def profile():
    connection = sqlite3.connect("schooldata.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Teachers WHERE Email=?", (session['user'],))
    teacher = cursor.fetchall()
    if 'user' in session:
        for t in teacher:
            id = t[0]
            firstname = t[1]
            surname = t[2]
            gender = t[3]
            email = t[4]
            subjectid = t[6]
        cursor.execute("SELECT * FROM Subjects WHERE SubjectID=?", (subjectid,))
        subjects = cursor.fetchall()
        for s in subjects:
            subjectname = s[1]
        cursor.execute("SELECT * FROM Teacher_info WHERE TeacherID=?", (int(id),))
        details = cursor.fetchall()
        for info in details:
            personal_email = info[2]
            dob = info[3]
            qualifications = info[4]
        return render_template("profile.html", firstname=firstname, 
                               surname=surname, gender=gender, 
                               email=email, subjectname=subjectname, 
                               personal_email=personal_email, dob=dob, 
                               qualifications=qualifications)
    else:
        return redirect(url_for('login'))   





# @app.route('/messages') # Messages route
# def messages():
#     if 'user' in session:
#         return render_template("messages.html")
#     else:
#         flash('You must be logged in to view messages.')


@app.route('/message_page')
def message_page():
    if 'user' in session:
        connection = sqlite3.connect("schooldata.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Teachers WHERE Email=?", (session['user'],))
        teacher = cursor.fetchall()
        if 'user' in session:
            for t in teacher:
                subject = t[6]
            
            
            if subject == 1:
                return render_template('admin_message.html')
            elif subject == 2:
                return render_template('maths.html')
            elif subject == 3:
                return render_template('english.html')
            elif subject == 4:
                return render_template('science.html')
            elif subject == 5:
                return render_template('computing.html')
            elif subject == 6:
                return render_template('history.html')
            else:
                return redirect(url_for('message_page'))
        else:
            return redirect(url_for('login'))





@app.route("/messages", methods =['GET', 'POST'])
def messages():
    if 'user' in session:
        connection = sqlite3.connect("schooldata.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Posts")
        posts = cursor.fetchall()
        cursor.execute("SELECT * FROM Teachers")
        teachers = cursor.fetchall()
        posts = posts[::-1]
        return  render_template("messages.html", posts=posts, teachers=teachers)
    else:
        return redirect(url_for('login'))
    

@app.route("/maths_messages", methods = ['GET', 'POST'])
def maths_messages():
    if 'user' in session:
        connection = sqlite3.connect("schooldata.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM M_Posts")
        posts = cursor.fetchall()
        cursor.execute("SELECT * FROM Teachers")
        teachers = cursor.fetchall()
        posts = posts[::-1]
        return  render_template("maths_messages.html", posts=posts, teachers=teachers)
    else:
        return redirect(url_for('login'))
    

@app.route("/english_messages", methods = ['GET', 'POST'])
def english_messages():
    if 'user' in session:
        connection = sqlite3.connect("schooldata.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM E_Posts")
        posts = cursor.fetchall()
        cursor.execute("SELECT * FROM Teachers")
        teachers = cursor.fetchall()
        posts = posts[::-1]
        return  render_template("english_messages.html", posts=posts, teachers=teachers)
    else:
        return redirect(url_for('login'))
    
@app.route("/science_messages", methods = ['GET', 'POST'])
def science_messages():
    if 'user' in session:
        connection = sqlite3.connect("schooldata.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM S_Posts")
        posts = cursor.fetchall()
        cursor.execute("SELECT * FROM Teachers")
        teachers = cursor.fetchall()
        posts = posts[::-1]
        return  render_template("science_messages.html", posts=posts, teachers=teachers)
    else:
        return redirect(url_for('login'))

@app.route("/computing_messages", methods = ['GET', 'POST'])
def computing_messages():
    if 'user' in session:
        connection = sqlite3.connect("schooldata.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM C_Posts")
        posts = cursor.fetchall()
        cursor.execute("SELECT * FROM Teachers")
        teachers = cursor.fetchall()
        posts = posts[::-1]
        return  render_template("computing_messages.html", posts=posts, teachers=teachers)
    else:
        return redirect(url_for('login'))



@app.route("/history_messages", methods = ['GET', 'POST'])
def history_messages():
    if 'user' in session:
        connection = sqlite3.connect("schooldata.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM H_Posts")
        posts = cursor.fetchall()
        cursor.execute("SELECT * FROM Teachers")
        teachers = cursor.fetchall()
        posts = posts[::-1]
        return  render_template("history_messages.html", posts=posts, teachers=teachers)
    else:
        return redirect(url_for('login'))












@app.route('/view_post/<int:post_id>') # View Post route
def view_post(post_id):
    if 'user' in session:
        connection = sqlite3.connect("schooldata.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Posts WHERE PostID=?", (post_id,))
        post = cursor.fetchone()
        if post:
            return render_template("view_post.html", post=post)
        else:
            return redirect(url_for('messages'))
    else:
        return redirect(url_for('login'))
    




@app.route('/new_post/<board>', methods=['GET', 'POST'])
def new_post(board):
    if 'user' in session:
        if request.method == 'POST':
            # Get teacher ID
            connection = sqlite3.connect("schooldata.db")
            cursor = connection.cursor()
            cursor.execute("SELECT TeacherID FROM Teachers WHERE Email=?", (session['user'],))
            teacher = cursor.fetchone()
            teacherid = teacher[0]

            # Get form data
            title = request.form.get('title')
            content = request.form.get('content')
            date = str(datetime.date.today())
            time = datetime.datetime.now().strftime("%H:%M")
            attachments = request.files.get('attachments').filename if request.files.get('attachments') else None

            # Reconnect to insert post
            connection = sqlite3.connect("schooldata.db")
            cursor = connection.cursor()

            # Insert into correct board table
            if board == 'general':
                cursor.execute("""
                    INSERT INTO Posts (Title, Content, Date, Time, Attachments, TeacherID)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, content, date, time, attachments, teacherid))
                connection.commit()
                connection.close()
                return redirect(url_for('messages'))

            elif board == 'computing':
                cursor.execute("""
                    INSERT INTO C_Posts (Title, Content, Date, Time, Attachments, TeacherID)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, content, date, time, attachments, teacherid))
                connection.commit()
                connection.close()
                return redirect(url_for('computing_messages'))

            elif board == 'maths':
                cursor.execute("""
                    INSERT INTO M_Posts (Title, Content, Date, Time, Attachments, TeacherID)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, content, date, time, attachments, teacherid))
                connection.commit()
                connection.close()
                return redirect(url_for('maths_messages'))

            elif board == 'english':
                cursor.execute("""
                    INSERT INTO E_Posts (Title, Content, Date, Time, Attachments, TeacherID)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, content, date, time, attachments, teacherid))
                connection.commit()
                connection.close()
                return redirect(url_for('english_messages'))

            elif board == 'science':
                cursor.execute("""
                    INSERT INTO S_Posts (Title, Content, Date, Time, Attachments, TeacherID)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, content, date, time, attachments, teacherid))
                connection.commit()
                connection.close()
                return redirect(url_for('science_messages'))

            elif board == 'history':
                cursor.execute("""
                    INSERT INTO H_Posts (Title, Content, Date, Time, Attachments, TeacherID)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, content, date, time, attachments, teacherid))
                connection.commit()
                connection.close()
                return redirect(url_for('history_messages'))

        return render_template("new_post.html", board=board)
    else:
        return redirect(url_for('login'))




@app.route('/delete_post/<board>', methods=['GET', 'POST']) # Delete Post route
def delete_post(board):
    if 'user' in session:
        connection = sqlite3.connect("schooldata.db")
        cursor = connection.cursor()
        teacherid = cursor.execute("SELECT TeacherID FROM Teachers WHERE Email=?", (session['user'],)).fetchone()[0]


        if request.method == 'POST':
            if board == 'general':
                myposts = cursor.execute("SELECT * FROM Posts WHERE TeacherID=?", (teacherid,)).fetchall()
                myposts = myposts[::-1]
                postid = request.form.get('postid')
                cursor.execute("DELETE FROM Posts WHERE PostID=?", (postid,))
                connection.commit()
                return redirect(url_for('messages'))
            
            elif board == 'computing':
                myposts = cursor.execute("SELECT * FROM C_Posts WHERE TeacherID=?", (teacherid,)).fetchall()
                myposts = myposts[::-1]
                postid = request.form.get('postid')
                cursor.execute("DELETE FROM C_Posts WHERE PostID=?", (postid,))
                connection.commit()
                return redirect(url_for('computing_messages'))
            
            elif board == 'maths':
                myposts = cursor.execute("SELECT * FROM M_Posts WHERE TeacherID=?", (teacherid,)).fetchall()
                myposts = myposts[::-1]
                postid = request.form.get('postid')
                cursor.execute("DELETE FROM M_Posts WHERE PostID=?", (postid,))
                connection.commit()
                return redirect(url_for('maths_messages'))
            
            elif board == 'english':
                myposts = cursor.execute("SELECT * FROM E_Posts WHERE TeacherID=?", (teacherid,)).fetchall()
                myposts = myposts[::-1]
                postid = request.form.get('postid')
                cursor.execute("DELETE FROM E_Posts WHERE PostID=?", (postid,))
                connection.commit()
                return redirect(url_for('english_messages'))
            
            elif board == 'science':
                myposts = cursor.execute("SELECT * FROM S_Posts WHERE TeacherID=?", (teacherid,)).fetchall()
                myposts = myposts[::-1]
                postid = request.form.get('postid')
                cursor.execute("DELETE FROM S_Posts WHERE PostID=?", (postid,))
                connection.commit()
                return redirect(url_for('science_messages'))
            
            elif board == 'history':
                myposts = cursor.execute("SELECT * FROM H_Posts WHERE TeacherID=?", (teacherid,)).fetchall()
                myposts = myposts[::-1]
                postid = request.form.get('postid')
                cursor.execute("DELETE FROM H_Posts WHERE PostID=?", (postid,))
                connection.commit()
                return redirect(url_for('history_messages'))
            
        return render_template("delete_post.html", myposts=myposts)
            
    else:
        return redirect(url_for('login'))
       





@app.route('/students') # Students route
def students():
    connection = sqlite3.connect("schooldata.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Teachers WHERE Email=?", (session['user'],))
    teacher = cursor.fetchall()
    if 'user' in session:
        for t in teacher:
            role = t[5]
        
        # Get search query from GET parameter
        query = request.args.get('query', '').strip()
        
        if query:
            # Search by ID, first name, surname, email, year, or mastery
            search_param = f"%{query}%"
            cursor.execute("""SELECT * FROM Students WHERE 
                            StudentID LIKE ? OR Firstname LIKE ? OR Surname LIKE ? 
                            OR Email LIKE ? OR YearGroup LIKE ? OR Mastery LIKE ?""", 
                            (search_param, search_param, search_param, search_param, search_param, search_param))
        else:
            cursor.execute("SELECT * FROM Students")

        students = cursor.fetchall()
        extra_info = cursor.execute("SELECT * FROM Student_info").fetchall()
        if role == "A":
            return render_template("admin_students.html", students=students, info=extra_info, query=query) 
        else:
            return render_template("base_students.html", students=students, info=extra_info, query=query)
    else:
        return redirect(url_for('login'))
    




@app.route('/add_student', methods=['GET', 'POST']) # Add Student route
def add_student():
    if 'user' in session:
        if request.method == 'POST':
            firstname = request.form.get('firstname').title()
            surname = request.form.get('surname').title()
            gender = request.form.get('gender')
            yeargroup = request.form.get('yeargroup')
            dob = request.form.get('dob')
            mastery = request.form.get('mastery').upper()
            email = request.form.get('email').lower()

            parentname = request.form.get('parentname')
            parentnumber = request.form.get('parentnumber')
            address = request.form.get('address')
            nationality = request.form.get('nationality')
            countryofbirth = request.form.get('countryofbirth')
            enrollmentdate = request.form.get('enrollmentdate')

            conditions = request.form.get('conditions')
            medication = request.form.get('medications')
            allergies = request.form.get('allergies')
            needs = request.form.get('needs')


            connection = sqlite3.connect("schooldata.db")
            cursor = connection.cursor()
            cursor.execute("INSERT INTO Students (Firstname, Surname, DOB, Gender, Mastery, Yeargroup, Email) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (firstname, surname, dob, gender, mastery, yeargroup, email ))
            connection.commit()
            cursor.execute("SELECT StudentID FROM Students WHERE Firstname=? AND Surname=? AND DOB=?", (firstname, surname, dob))
            student = cursor.fetchone()
            student_id = student[0]
            cursor.execute("INSERT INTO Student_Info (StudentID, Parentname, Parentnumber, Address, Nationality, countryofbirth, Enrollmentdate) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                           (student_id, parentname, parentnumber, address, nationality, countryofbirth, enrollmentdate))
            connection.commit()
            cursor.execute("INSERT INTO Medical_Info (StudentID, Conditions, Medication, Allergies, Needs) VALUES (?, ?, ?, ?, ?)", 
                           (student_id, conditions, medication, allergies, needs))
            connection.commit()
            connection.close()
            return redirect(url_for('students'))
        return render_template("add_student.html")
    else:
        return redirect(url_for('login'))
    



@app.route('/view_student/<int:student_id>') # View Student route
def view_student(student_id):
    if 'user' in session:
        connection = sqlite3.connect("schooldata.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Students WHERE StudentID=?", (student_id,))
        student = cursor.fetchone()
        cursor.execute("SELECT * FROM Student_info WHERE StudentID=?", (student_id,))
        info = cursor.fetchall()
        cursor.execute("SELECT * FROM Medical_info WHERE StudentID=?", (student_id,))
        medical = cursor.fetchone()
        if student:
            return render_template("view_student.html", student=student, info=info, medical=medical)
        else:
            return redirect(url_for('students'))
    else:
        return redirect(url_for('login'))



EXPECTED_HEADERS = [
    "Firstname","Surname","DOB","Gender","Mastery","Yeargroup","Email",
    "Parentname","Parentnumber","Address","Nationality","CountryofBirth","EnrollmentDate",
    "Conditions","Medication","Allergies","Needs"
]

SYSTEM_FIELDS = [
    "Firstname","Surname","DOB","Gender","Mastery","Yeargroup","Email",
    "Parentname","Parentnumber","Address","Nationality","CountryOfBirth","EnrollmentDate",
    "Conditions","Medication","Allergies","Needs"
]


@app.route('/import_students', methods=['GET', 'POST'])
def import_students():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files.get('csv_file')

        if not file or file.filename == "":
            return redirect(request.url)

        try:
            stream = io.StringIO(file.stream.read().decode("utf-8-sig"))
            reader = csv.reader(stream)
            headers = next(reader)
            headers = [h.strip() for h in headers]
            headers[0] = headers[0].replace('\ufeff', '')
            rows = list(reader)
            
            if len(rows) == 0:
                return redirect(request.url)
            
            if headers == EXPECTED_HEADERS:
                conn = sqlite3.connect("schooldata.db")
                cursor = conn.cursor()

                imported = 0
                skipped = 0

                for i, row in enumerate(rows, start=2):
                    if len(row) != len(EXPECTED_HEADERS):
                        skipped += 1
                        continue

                    (
                        firstname, surname, dob, gender, mastery, yeargroup, email,
                        parentname, parentnumber, address,  nationality, cob, enrolldate,
                        conditions, medication, allergies, needs
                    ) = row


                    cursor.execute("""
                        INSERT INTO Students 
                        (Firstname, Surname, DOB, Gender, Mastery, Yeargroup, Email)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (firstname, surname, dob, gender, mastery, yeargroup, email))

                    student_id = cursor.lastrowid
                    cursor.execute("""
                        INSERT INTO Student_Info
                        (StudentID, Parentname, Parentnumber, Address, Nationality, countryofbirth, Enrollmentdate)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (student_id, parentname, parentnumber, address, nationality, cob, enrolldate))
                    cursor.execute("""
                        INSERT INTO Medical_Info
                        (StudentID, Conditions, Medication, Allergies, Needs)
                        VALUES (?, ?, ?, ?, ?)
                    """, (student_id, conditions, medication, allergies, needs))
                    
                    imported += 1
                    
                conn.commit()
                conn.close()

                if imported > 0:    
                    flash(f'Successfully imported {imported} students.', 'success')
                if skipped > 0:
                    flash(f'Skipped {skipped} rows due to errors.', 'error')

                return redirect(url_for('import_students'))
            
            else:
                session['uploaded_headers'] = headers
                session['uploaded_rows'] = rows
                return redirect(url_for('map_headers'))
            
        except Exception as e: 
            flash('An error occurred while processing the file.', 'error')
            return redirect(request.url)
    return render_template('import_students.html')



@app.route('/download_student_template')
def download_student_template():
    if 'user' not in session:
        return redirect(url_for('login'))

    return send_from_directory(
        directory="static",
        path="student_import_template.csv",
        as_attachment=True
    )




@app.route('/map_headers', methods=['GET', 'POST'])
def map_headers():
    if 'user' not in session:
        return redirect(url_for('login'))

    uploaded_headers = session.get('uploaded_headers')

    if not uploaded_headers:
        return redirect(url_for('import_students'))

    if request.method == 'POST':
        mapping = {}
        for h in uploaded_headers:
            selected = request.form.get(h)
            if selected:
                mapping[h] = selected

        session['header_mapping'] = mapping
        return redirect(url_for('confirm_mapped_import'))

    return render_template(
        "map_headers.html",
        uploaded_headers=uploaded_headers,
        system_fields=SYSTEM_FIELDS
    )



@app.route('/confirm_mapped_import')
def confirm_mapped_import():
    if 'user' in session:
        rows = session.get('uploaded_rows')
        mapping = session.get('header_mapping')

        if not rows or not mapping:
            return redirect(url_for('import_students'))

        conn = sqlite3.connect("schooldata.db")
        cursor = conn.cursor()

        for row in rows:
            row_data = dict(zip(session['uploaded_headers'], row))

            data = {field: "" for field in SYSTEM_FIELDS}
            for csv_col, system_col in mapping.items():
                data[system_col] = row_data.get(csv_col, "")

            cursor.execute("""
                INSERT INTO Students
                (Firstname, Surname, DOB, Gender, Mastery, Yeargroup, Email)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data["Firstname"], data["Surname"], data["DOB"],
                data["Gender"], data["Mastery"], data["Yeargroup"], data["Email"]
            ))

            student_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO Student_Info
                (StudentID, Parentname, Parentnumber, Address, Nationality, countryofbirth, Enrollmentdate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                student_id, data["Parentname"], data["Parentnumber"],
                data["Address"], data["Nationality"],
                data["CountryOfBirth"], data["EnrollmentDate"]
            ))

            cursor.execute("""
                INSERT INTO Medical_Info
                (StudentID, Conditions, Medication, Allergies, Needs)
                VALUES (?, ?, ?, ?, ?)
            """, (
                student_id, data["Conditions"], data["Medication"],
                data["Allergies"], data["Needs"]
            ))

        conn.commit()
        conn.close()

        session.pop('uploaded_headers', None)
        session.pop('uploaded_rows', None)
        session.pop('header_mapping', None)

        return redirect(url_for('import_students'))
    else:
        return redirect(url_for('login'))



@app.route("/students/delete", methods=["GET"])
def delete_students():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    # check role
    cur.execute("SELECT * FROM Teachers WHERE Email=?", (session["user"],))
    teacher = cur.fetchone()
    if not teacher or teacher[5] != "A":
        conn.close()
        return redirect(url_for("students"))  # only admin can delete

    query = request.args.get("query", "").strip()

    if query:
        search_param = f"%{query}%"
        cur.execute("""SELECT * FROM Students WHERE
                       StudentID LIKE ? OR Firstname LIKE ? OR Surname LIKE ?
                       OR Email LIKE ? OR YearGroup LIKE ? OR Mastery LIKE ?""",
                    (search_param, search_param, search_param, search_param, search_param, search_param))
    else:
        cur.execute("SELECT * FROM Students")

    students = cur.fetchall()
    extra_info = cur.execute("SELECT * FROM Student_info").fetchall()
    conn.close()

    return render_template("delete_students.html", students=students, info=extra_info, query=query)


@app.route("/students/delete/confirm", methods=["POST"])
def confirm_delete_students():
    if "user" not in session:
        return redirect(url_for("login"))

    selected_ids = request.form.getlist("delete_ids")  # list of checked student IDs (strings)

    if not selected_ids:
        flash("No students selected.", "error")
        return redirect(url_for("delete_students"))

    # fetch details for confirmation page
    conn = get_db()
    cur = conn.cursor()

    placeholders = ",".join("?" for _ in selected_ids)
    cur.execute(f"SELECT * FROM Students WHERE StudentID IN ({placeholders})", selected_ids)
    selected_students = cur.fetchall()

    conn.close()

    return render_template("confirm_delete_students.html",
                           selected_students=selected_students,
                           selected_ids=selected_ids)


@app.route("/students/delete/final", methods=["POST"])
def final_delete_students():
    if "user" not in session:
        return redirect(url_for("login"))

    selected_ids = request.form.getlist("selected_ids")
    if not selected_ids:
        flash("Nothing to delete.", "error")
        return redirect(url_for("delete_students"))

    conn = get_db()
    cur = conn.cursor()

    try:
        placeholders = ",".join("?" for _ in selected_ids)

        # delete from child tables first (prevents FK errors if not using CASCADE)
        cur.execute(f"DELETE FROM Timetable WHERE StudentID IN ({placeholders})", selected_ids)
        cur.execute(f"DELETE FROM Attendance WHERE StudentID IN ({placeholders})", selected_ids)
        cur.execute(f"DELETE FROM Medical_Info WHERE StudentID IN ({placeholders})", selected_ids)
        cur.execute(f"DELETE FROM Student_Info WHERE StudentID IN ({placeholders})", selected_ids)

        # finally delete from Students
        cur.execute(f"DELETE FROM Students WHERE StudentID IN ({placeholders})", selected_ids)

        conn.commit()
        flash(f"Deleted {len(selected_ids)} student(s) successfully.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Delete failed: {e}", "error")

    finally:
        conn.close()

    return redirect(url_for("students"))











#FOR THE WORD DOC

# @app.route('/students') # Students route
# def students():
#     if 'user'in session:
#         connection = sqlite3.connect("schooldata.db")
#         cursor = connection.cursor()
#         cursor.execute("SELECT * FROM Teachers WHERE Email=?", (session['user'],))
#         teacher = cursor.fetchall()
#         if 'user' in session:
#             for t in teacher:
#                 role = t[5]
        
#         students = cursor.execute("SELECT * FROM Students").fetchall()
#         extra_info = cursor.execute("SELECT * FROM Student_info").fetchall()
#         if role == "A":
#             return render_template("admin_students.html", students=students, info=extra_info)  
#         else:
#             return render_template("base_students.html", students=students, info=extra_info)
#     else:
#         return redirect(url_for('login'))
    












if __name__ == "__main__": # Run the app
    app.run(debug=True)




