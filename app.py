#IMPORTS
from flask import Flask, render_template, session, abort, flash
from flask import redirect, url_for, request, jsonify, send_from_directory
import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sqlite3
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
        conn.close()

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
        
        if role == "A":
            if query:
                # Search by ID, first name, surname, email, or mastery
                search_param = f"%{query}%"
                cursor.execute("""SELECT * FROM Students WHERE 
                               StudentID LIKE ? OR Firstname LIKE ? OR Surname LIKE ? 
                               OR Email LIKE ? OR Mastery LIKE ?""", 
                               (search_param, search_param, search_param, search_param, search_param))
            else:
                cursor.execute("SELECT * FROM Students")
            students = cursor.fetchall()
            cursor.execute("SELECT * FROM Student_info")
            extra_info = cursor.fetchall()
            return render_template("admin_students.html", students=students, info=extra_info, query=query) 
        else:
            if query:
                # Non-admin teachers see all students but can search
                search_param = f"%{query}%"
                cursor.execute("""SELECT * FROM Students WHERE 
                               StudentID LIKE ? OR Firstname LIKE ? OR Surname LIKE ? 
                               OR Email LIKE ? OR Mastery LIKE ?""", 
                               (search_param, search_param, search_param, search_param, search_param))
            else:
                cursor.execute("SELECT * FROM Students")
            students = cursor.fetchall()
            cursor.execute("SELECT * FROM Student_Info")
            extra_info = cursor.fetchall()
            return render_template("students.html", students=students, info=extra_info, query=query)
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
            cursor.execute("INSERT INTO Students (Firstname, Surname, DOB, Gender, Mastery, Yeargroup, Email) VALUES (?, ?, ?, ?, ?, ?, ?)", (firstname, surname, dob, gender, mastery, yeargroup, email ))
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
    
@app.route('/delete_student', methods=['GET', 'POST'])
def delete_student():
    if 'user':
        connection = sqlite3.connect("schooldata.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Students")

        if request.method == 'POST':
            studentid = request.form.get('studentid')
            cursor.execute("DELETE FROM Students WHERE StudentID=?", (studentid))
            cursor.execute("DELETE FROM Student_info WHERE StudentID=?", (studentid))
            connection.commit()
            return redirect(url_for('students'))
        return render_template("delete_student.html")
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










@app.route('/delete_post', methods=['GET', 'POST']) # Delete Post route
def delete_post():
    if 'user' in session:
        connection = sqlite3.connect("schooldata.db")
        cursor = connection.cursor()
        teacherid = cursor.execute("SELECT TeacherID FROM Teachers WHERE Email=?", (session['user'],)).fetchone()[0]
        cursor.execute("SELECT * FROM Posts WHERE TeacherID=?", (teacherid,))
        myposts = cursor.fetchall()
        myposts = myposts[::-1]


        if request.method == 'POST':
            post_id = request.form.get('post_id')
            cursor.execute("DELETE FROM Posts WHERE PostID=? AND TeacherID=?", (post_id,teacherid))
            connection.commit()
            connection.close()
            return redirect(url_for('messages'))
    else:
        return redirect(url_for('login'))
        
    return render_template("delete_post.html", myposts=myposts)



if __name__ == "__main__": # Run the app
    app.run(debug=True)





