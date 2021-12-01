# -*- coding: utf-8 -*-
"""
Created on Sat Oct 30 10:57:36 2021

@author: Peter De Winne
@email: peter.de.winne@vub.be
@studentnumber: 0556725
@education: bachelor industrial siences

de 404 pagen en 403 page komen van freefrontend
"""
from flask_bcrypt import Bcrypt
from flask_qrcode import QRcode
from flask import Flask
from flask import render_template, url_for, flash, request, redirect, Response
import sqlite3
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from forms import LoginForm, RegisterForm, Create_classForm, Register4classForm, Create_Course
from datetime import datetime as dt
import secrets
secret_key = secrets.token_hex(16)
app = Flask(__name__,template_folder='templates')
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
QRcode(app)
app.config['SECRET_KEY'] = secret_key
BASE = ''

"""---CLASS-User---------------------------------------------------------------------------------------------------------------------------------"""
class User(UserMixin):
     def __init__(self, id, email, password, firstname, lastname, admin):
          self.id = id
          self.email = email
          self.password = password
          self.firstname = firstname
          self.lastname = lastname
          self.adm = admin
     def is_active(self):
         return self.is_active()
     def is_anonymous(self):
         return False
     def is_authenticated(self):
         return self.authenticated
     def is_active(self):
         return True
     def get_id(self):
         return self.id
     def get_admin(self):
          if self.adm == 1:
               return True
          else:
               return False
"""---login-manager--------------------------------------------------------------------------------------------------------------------"""
@login_manager.user_loader
def load_user(user_id):
   conn = sqlite3.connect('database.db')
   curs = conn.cursor()
   curs.execute("SELECT * from user where userid = (?)",[user_id])
   lu = curs.fetchone()
   conn.close()
   if lu is None:
      return None
   else:
      return User(int(lu[0]), lu[1], lu[2], lu[3], lu[4], lu[5])

"""---@app.route----------------------------------------------------------------------------------------------------------------------------------------"""
@app.route("/login", methods=['GET','POST'])
def login():
     if current_user.is_authenticated:
          return redirect(request.args.get("next") or url_for("index"))
     form = LoginForm()
     if form.validate_on_submit():
          try:
               conn = sqlite3.connect('database.db')
               curs = conn.cursor()
               curs.execute("SELECT * FROM user where mail = (?)",[form.email.data])
               user = curs.fetchone()
               Us = load_user(user[0])
               conn.close()
               if form.email.data == Us.email and bcrypt.check_password_hash(Us.password, form.password.data):
                    login_user(Us, remember=form.remember.data)
                    name = Us.firstname + ' ' + Us.lastname
                    flash('Logged in successfully '+ name)
                    return redirect(request.args.get("next") or url_for("index"))
               else:
                    flash('Password or email wrong.')
          except:
               flash('You don not have a acount.')
     return render_template('login.html',title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
     logout_user()
     flash('You have successfully logged yourself out.')
     return redirect(url_for('index'))


@app.route("/")
def index():
     if current_user.is_authenticated:
          return redirect(url_for('home'))
     else: return redirect(url_for('login'))
def Base():
    return request.remote_addr

@app.route("/register", methods=['GET','POST'])
def register():
     form = RegisterForm()
     if form.validate_on_submit():
          try:
               conn = sqlite3.connect('database.db')
               curs = conn.cursor()
               curs.execute("INSERT INTO user (mail, password, firstname, lastname, role) values (?,?,?,?,0)",(form.email.data, bcrypt.generate_password_hash(form.password.data), form.first.data, form.last.data))
               conn.commit()
               conn.close()
               flash("registration succesfull")
               return redirect(url_for('home'))
          except:
               flash("E-mail already registerd")
     return render_template('register.html',title='register', form=form)

@app.route('/home')
@login_required
def home():
     return render_template("home.html")

@app.route('/courses')
@login_required
def courses():
     user = current_user
     if current_user.get_admin():
          return redirect(url_for('admin'))
     con = sqlite3.connect('database.db')
     con.row_factory = sqlite3.Row
     cur = con.cursor()
     cur.execute("SELECT course.courseid, course.name, course.semester, course.year, usercourse.role FROM course INNER JOIN USERCOURSE ON usercourse.courseid = course.courseid WHERE usercourse.userid = ? AND usercourse.role = 'student'",[int(user.get_id())])
     students = cur.fetchall()
     cur.execute("SELECT course.courseid, course.name, course.semester, course.year, usercourse.role FROM course INNER JOIN USERCOURSE ON usercourse.courseid = course.courseid WHERE usercourse.userid = ? AND usercourse.role = 'teacher'",[int(user.get_id())])
     teachers = cur.fetchall()
     con.close()
     return render_template("courses.html", students=students, teachers = teachers, title='courses')

@app.route('/course/<course_id>')
@login_required
def course(course_id):
     us = current_user
     con = sqlite3.connect('database.db')
     con.row_factory = sqlite3.Row
     cur = con.cursor()
     cur.execute("SELECT role FROM usercourse WHERE userid= ? AND courseid = ?",[int(us.get_id()),int(course_id)])
     role = cur.fetchone()
     if role[0] != 'teacher':     
          return render_template("403.html")
     else:
          con = sqlite3.connect('database.db')
          con.row_factory = sqlite3.Row
          cur = con.cursor()
          cur.execute("SELECT user.firstname, user.lastname, user.mail, usercourse.role FROM user INNER JOIN usercourse ON user.userid = usercourse.userid WHERE usercourse.courseid=?",[course_id])
          users = cur.fetchall()
          cur.execute("SELECT classid, start, end FROM class WHERE courseid=?",[course_id])
          dates = cur.fetchall()
          con.close()
          return render_template("course.html", users = users,dates = dates, course_id = course_id, role = role)

@app.route('/create_class/<course_id>', methods=['GET','POST'])
@login_required
def create_class(course_id):
     us = current_user
     con = sqlite3.connect('database.db')
     con.row_factory = sqlite3.Row
     cur = con.cursor()
     cur.execute("SELECT role FROM usercourse WHERE userid= ? AND courseid = ?",[int(us.get_id()),int(course_id)])
     role = cur.fetchone()
     if role[0] != 'teacher':     
          return render_template("403.html")
     else:
          print("help")
          form = Create_classForm()
          if form.validate_on_submit():
               start_str = form.year.data + '-'+ form.month.data + '-' + form.day.data + ' ' +  form.start_h.data + ':' + form.start_m.data
               end_str = form.year.data + '-'+ form.month.data + '-' + form.day.data + ' ' +  form.end_h.data + ':' + form.end_m.data
               start = dt.strptime(start_str, '%Y-%m-%d %H:%M')
               end = dt.strptime(end_str, '%Y-%m-%d %H:%M')
               if end > start:
                    try:
                         conn = sqlite3.connect('database.db')
                         curs = conn.cursor()
                         curs.execute("INSERT INTO class (courseid, start, end) values (?,?,?)",(course_id, start, end))
                         conn.commit()
                         conn.close()
                         flash("registration succesfull")
                         return redirect(url_for('course', course_id = course_id))
                    except:
                         flash("Didn't create class")
               else: flash ("End before start")
     return render_template('create_class.html', form = form)

@app.route('/clas/<class_id>')
@login_required
def clas(class_id):
     us = current_user
     con = sqlite3.connect('database.db')
     con.row_factory = sqlite3.Row
     cur = con.cursor()
     cur.execute("SELECT usercourse.role FROM USERCOURSE INNER JOIN CLASS ON USERCOURSE.courseid = CLASS.courseid WHERE class.classid = ? AND usercourse.userid = ?",[str(class_id),str(us.get_id())])
     role = cur.fetchone()
     if role[0] == 'teacher':
          QR = 'http://' + Base() + '/register4class/' + str(class_id)
          con = sqlite3.connect('database.db')
          con.row_factory = sqlite3.Row
          cur = con.cursor()
          cur.execute("SELECT user.firstname, user.lastname, user.mail FROM user INNER JOIN ATTENDANCE ON user.userid = ATTENDANCE.userid WHERE ATTENDANCE.classid = ?", [class_id])
          attending = cur.fetchall()

          return render_template('class.html', QR_code = QR, attending = attending)
     else:
          return render_template("403.html")

@app.route('/remove_class/<class_id>')
@login_required
def remove_class(class_id):
     us = current_user
     con = sqlite3.connect('database.db')
     con.row_factory = sqlite3.Row
     cur = con.cursor()
     cur.execute("SELECT usercourse.role FROM USERCOURSE INNER JOIN CLASS ON USERCOURSE.courseid = CLASS.courseid WHERE class.classid = ? AND usercourse.userid = ?",[str(class_id),str(us.get_id())])
     role = cur.fetchone()
     con.close()
     if role[0] == 'teacher':
          con = sqlite3.connect('database.db')
          con.row_factory = sqlite3.Row
          cur = con.cursor()
          cur.execute("SELECT courseid FROM CLASS WHERE classid = ?",[str(class_id)])
          course_id = cur.fetchone()[0]
          cur.execute("DELETE FROM class WHERE Classid = ?", [str(class_id)])
          con.commit()
          cur.execute("DELETE FROM attendance WHERE Classid = ?", [str(class_id)])
          con.commit()
          con.close()
          return redirect(url_for('course', course_id = course_id))
     else:
          return render_template("403.html")
@app.route('/admin')
@login_required
def admin():
     if current_user.get_admin():
          con = sqlite3.connect('database.db')
          con.row_factory = sqlite3.Row
          cur = con.cursor()
          cur.execute("SELECT * FROM  COURSE ORDER BY year DESC",)
          courses = cur.fetchall()
          con.close()
          return render_template("adcourse.html", courses = courses, title="Admin courses")
     else:
          return render_template("403.html")
@app.route('/admin/<course_id>')
@login_required
def adminCourse(course_id):
     if current_user.get_admin():
          con = sqlite3.connect('database.db')
          con.row_factory = sqlite3.Row
          cur = con.cursor()
          cur.execute("SELECT DISTINCT user.userid, user.firstname, user.lastname, user.mail FROM USER WHERE USER.userid NOT IN (SELECT DISTINCT USER.userid FROM  USER INNER JOIN USERCOURSE on user.userid = usercourse.userid WHERE usercourse.courseid=?)", [course_id])
          users = cur.fetchall()
          cur.execute("SELECT DISTINCT user.userid, user.firstname, user.lastname, user.mail, usercourse.role FROM  USER INNER JOIN USERCOURSE on user.userid = usercourse.userid WHERE usercourse.courseid=?", [course_id])
          students = cur.fetchall()
          con.close()
          return render_template("aduser2course.html", title="Admin courses", users=users, course_id=course_id, students=students)
     else:
          return render_template("403.html")

@app.route('/remove4course')
@login_required
def remove4course():
     if current_user.get_admin():
          course_id = request.args.get('course_id', None)
          user_id = request.args.get('user_id', None)
          con = sqlite3.connect('database.db')
          con.row_factory = sqlite3.Row
          cur = con.cursor()
          cur.execute("DELETE FROM USERCOURSE WHERE userid = ? AND courseid=?", [user_id,course_id])
          con.commit()
          con.close()
          return redirect(url_for('adminCourse', course_id = course_id))
     else:
          return render_template("403.html")

@app.route('/add2course')
@login_required
def ad2course():
     if current_user.get_admin():
          course_id = request.args.get('course_id', None)
          user_id = request.args.get('user_id', None)
          role = request.args.get('role', None)
          con = sqlite3.connect('database.db')
          con.row_factory = sqlite3.Row
          cur = con.cursor()
          cur.execute("INSERT INTO usercourse (userid, courseid, role) VALUES (?,?,?)", [user_id,course_id,role])
          con.commit()
          con.close()
          return redirect(url_for('adminCourse', course_id = course_id))
     else:
          return render_template("403.html")

@app.route('/addCourse', methods=['GET','POST'] )
@login_required
def addCourse():
     if current_user.get_admin():
          form = Create_Course()
          if form.validate_on_submit():
               name = form.name.data
               semester = form.semester.data
               year = form.year.data
               con = sqlite3.connect('database.db')
               con.row_factory = sqlite3.Row
               cur = con.cursor()
               cur.execute("SELECT courseid FROM course where name = ? AND semester = ? AND year = ?", [name, semester, year])
               course = cur.fetchone()
               con.close()
               if course == None:
                    con = sqlite3.connect('database.db')
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    cur.execute("INSERT INTO COURSE (name, semester, year) VALUES (?,?,?)", [name, semester, year])
                    con.commit()
                    con.close()
                    return redirect(url_for('admin'))
               else: flash("Course already exists")
          return render_template("addCourse.html", form=form)
     else:
          return render_template("403.html")

@app.route('/removeCourse/<course_id>')
@login_required
def removeCourse(course_id):
     if current_user.get_admin():
          con = sqlite3.connect('database.db')
          con.row_factory = sqlite3.Row
          cur = con.cursor()
          cur.execute("DELETE FROM course WHERE courseid = ?", [course_id])
          con.commit()
          cur.execute("DELETE FROM usercourse WHERE courseid = ?", [course_id])
          con.commit()
          cur.execute("DELETE FROM class WHERE courseid = ?", [course_id])
          con.commit()
          con.close()
          return redirect(url_for('admin'))
     else:
          return render_template("403.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def page_not_found(e):
    return render_template('403.html'), 404

if __name__ == "__main__":
     app.run(debug=True, host='0.0.0.0')
 