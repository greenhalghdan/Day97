from flask import Flask, render_template, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import wtforms
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, URL
from flask_bootstrap import Bootstrap

app = Flask(__name__)

app.config['SECRET_KEY'] = 'anotveryrandomstringofletters'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
db = SQLAlchemy()
db.init_app(app)
bootstrap = Bootstrap(app)


class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=False, nullable=False)
    summary = db.Column(db.String, unique=False, nullable=False)
    description = db.Column(db.String, unique=False, nullable=False)
    status = db.Column(db.String, unique=False, nullable=False)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=False, nullable=False)
    password = db.Column(db.String, unique=False, nullable=False)
    name = db.Column(db.String, unique=False, nullable=False)
    status = db.Column(db.String, unique=False, nullable=False)


class AddTask(FlaskForm):
    name = StringField("Task Name", validators=[DataRequired()])
    summary = StringField("Task Summary", validators=[DataRequired()])
    description = TextAreaField("Description of the Task", validators=[DataRequired()])
    submit = SubmitField("Submit Task")


class Login(FlaskForm):
    username = StringField("User name", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


with app.app_context():
    db.create_all()


@app.route('/', methods=["GET", "POST"])
def index():
    todo = db.session.execute(db.select(Tasks).where(Tasks.status == 'todo'))
    a = todo.scalars().all()
    inprogress = db.session.execute(db.select(Tasks).where(Tasks.status == 'inprogress'))
    b = inprogress.scalars().all()
    done = db.session.execute(db.select(Tasks).where(Tasks.status == 'done'))
    c = done.scalars().all()
    addtask = AddTask()
    if addtask.validate_on_submit():
        db.session.add(
            Tasks(
                name = addtask.data.get('name'),
                summary = addtask.data.get('summary'),
                description = addtask.data.get('description'),
                status = 'todo',
            )
        )
        db.session.commit()
    return render_template("index.html", todo=a, inprogress=b, done=c, form=addtask)


@app.route('/updatestatus/<int:taskid>&<string:newstatus>', methods=["GET", "POST"])
def updatestatus(taskid, newstatus):
    task = db.get_or_404(Tasks, taskid)
    task.status = newstatus
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)