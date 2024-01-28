from flask import Flask, render_template, url_for, redirect, flash, request,jsonify
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import wtforms
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, URL
from flask_bootstrap import Bootstrap
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os


YOUR_DOMAIN = 'http://localhost:4224'

app = Flask(__name__)

app.config['SECRET_KEY'] = 'anotveryrandomstringofletters'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
db = SQLAlchemy()
db.init_app(app)
bootstrap = Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)


import stripe
# This is your test secret API key.
stripe.api_key = 'apikeygoeshereorsaveittoaenv'

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(Users, user_id)


class Tasks(db.Model):
    __tablename__ = "Tasks"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=False, nullable=False)
    summary = db.Column(db.String, unique=False, nullable=False)
    description = db.Column(db.String, unique=False, nullable=False)
    status = db.Column(db.String, unique=False, nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey("Users.id"))
    task_owner = relationship("Users", back_populates="task")


class Users(db.Model,UserMixin):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=False, nullable=False)
    password = db.Column(db.String, unique=False, nullable=False)
    FirstName = db.Column(db.String, unique=False, nullable=True)
    LastName = db.Column(db.String, unique=False, nullable=True)
    status = db.Column(db.Boolean, unique=False, nullable=False)

    task = relationship("Tasks", back_populates="task_owner")

class AddTask(FlaskForm):
    name = StringField("Task Name", validators=[DataRequired()])
    summary = StringField("Task Summary", validators=[DataRequired()])
    description = TextAreaField("Description of the Task", validators=[DataRequired()])
    submit = SubmitField("Submit Task")


class Login(FlaskForm):
    username = StringField("User name", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class NewUser(FlaskForm):
    username = StringField("User name", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    firstname = StringField("First Name")
    lastname = StringField("Last Name")
    submit = SubmitField("Sign Up")


with app.app_context():
    db.create_all()


@app.route('/', methods=["GET", "POST"])
def index():
    addtask = AddTask()
    if current_user.is_authenticated:
        todo = db.session.execute(db.select(Tasks).where(Tasks.status == 'todo', Tasks.userid == current_user.id))
        a = todo.scalars().all()
        inprogress = db.session.execute(db.select(Tasks).where(Tasks.status == 'inprogress', Tasks.userid == current_user.id))
        b = inprogress.scalars().all()
        done = db.session.execute(db.select(Tasks).where(Tasks.status == 'done', Tasks.userid == current_user.id))
        c = done.scalars().all()
        if addtask.validate_on_submit():
            if current_user.is_authenticated:
                db.session.add(
                    Tasks(
                        name = addtask.data.get('name'),
                        summary = addtask.data.get('summary'),
                        description = addtask.data.get('description'),
                        status = 'todo',
                        task_owner = current_user
                    )
                )
                db.session.commit()
            else:
                flash('You need to login to add a task')
        return render_template("index.html", todo=a, inprogress=b, done=c, form=addtask)
    return render_template("index.html", form=addtask)


@app.route('/updatestatus/<int:taskid>&<string:newstatus>', methods=["GET", "POST"])
def updatestatus(taskid, newstatus):
    task = db.get_or_404(Tasks, taskid)
    task.status = newstatus
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/signup.html', methods=['GET','POST'])
def signup():
    form = NewUser()
    if form.validate_on_submit():
        usernames = db.session.execute(db.select(Users)).scalars().all()
        for user in usernames:
            if user.username == form.username:
                flash('Email address is already in use')
        new_user = Users(
            FirstName = form.firstname.data,
            LastName = form.lastname.data,
            username = form.username.data,
            password = generate_password_hash(password=form.password.data, method='pbkdf2:sha256', salt_length=8),
            status = True
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("signup.html", form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    login_form = Login()
    if login_form.validate_on_submit():
        result = db.session.execute(db.select(Users).where(Users.username == login_form.username.data)).scalar()
        if check_password_hash(result.password, login_form.password.data):
            print("1")
            login_user(result)
            return redirect(url_for('index'))
        else:
            flash("Email address and password combination is not valid")
    return render_template("login.html", form=login_form)



@app.route('/create-checkout-session', methods=['POST', 'GET'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': 'price_1OdcubEPKi7ZoyeW49sH8p6z',
                    "quantity": 1
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success.html',
            cancel_url=YOUR_DOMAIN + '/cancel.html',
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)


if __name__ == "__main__":
    app.run(debug=True, port=4242)