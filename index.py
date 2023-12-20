# let's import the flask
from flask import Flask, render_template, request, redirect, url_for, Response
import os # importing operating system module
import re
import nltk
import json
from nltk.corpus import stopwords
from collections import Counter
from nltk.tokenize import word_tokenize
from bson.objectid import ObjectId
from bson.json_util import dumps
from pymongo.mongo_client import MongoClient
from datetime import datetime

uri = os.environ.get("MongoURI")

# Create a new client and connect to the server
client = MongoClient(uri)

db = client['thirty_days_of_python'] 

app = Flask(__name__)
# to stop caching static file
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

nltk.data.path.append('./nltk_data')


def custom_strftime(value, format='%Y-%m-%d %I:%M %p'):
    return value.strftime(format)

# Adding the custom filter to Flask app
app.jinja_env.filters['strftime'] = custom_strftime

def calculate_lexical_density(words):
    stop_words = set(stopwords.words('english'))
    filtered_words = [word for word in words if word.isalpha() and word not in stop_words]

    total_words = len(words)
    lexical_words = sum(1 for word in filtered_words if word.isalpha())

    if total_words == 0:
        return 0
    lexical_density = (lexical_words / total_words) * 100
    return f"{lexical_density:.2f}"


@app.route('/') # this decorator create the home route
def home ():
    techs = {"Frontend": ['HTML', 'CSS', 'JavaScript'], "Backend": ['Flask', 'Python', 'MongoDB']}
    name = '30 Days Of Python Programming'
    return render_template('home.html', techs=techs, name = name, title = 'Home')

@app.route('/about')
def about():
    name = '30 Days Of Python Programming'
    return render_template('about.html', name = name, title = 'About Us')

@app.route('/result')
def result():
    counted_words = request.args.get('counted_words')
    words_list = json.loads(counted_words)
    return render_template('result.html', counted_words=words_list)

@app.route('/post', methods= ['GET','POST'])
def post():
    name = 'Text Analyzer'
    if request.method == 'GET':
         return render_template('post.html', name = name, title = name)
    if request.method =='POST':
        content = request.form['content']
        cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '',content)
        words = word_tokenize(cleaned_text)
        chars = ''.join(words)
        counted_words = Counter(words)
        tuple_words = [(key, value) for key, value in counted_words.items()]
        data = {
            'lexical_density': calculate_lexical_density(words),
            'counted_words': json.dumps(tuple_words),
            'most_frequent_word': counted_words.most_common(1)[0][0],
            'num_of_words': len(words),
            'num_of_char': len(chars)
        }
        return redirect(url_for('result', **data))


@app.route('/api/v1.0/students', methods = ['GET'])
def students ():
    return Response(dumps(db.students.find()), mimetype='application/json')

@app.route('/students/add', methods = ['POST', 'GET'])
def create_student ():
    if request.method == 'GET':
        return render_template('/students/add.html')
    if request.method =='POST':
        name = request.form['name']
        country = request.form['country']
        city = request.form['city']
        skills = request.form['skills'].split(', ')
        bio = request.form['bio']
        birthyear = request.form['birthyear']
        created_at = datetime.now()
        student = {
            'name': name,
            'country': country,
            'city': city,
            'birthyear': birthyear,
            'skills': skills,
            'bio': bio,
            'created_at': created_at

        }
        db.students.insert_one(student)
        return redirect(url_for('list_students'))

@app.route('/api/v1.0/students/<id>', methods = ['POST', 'PUT', 'GET']) # this decorator create the home route
def update_student (id):
    if request.method == 'GET':
        student = db.students.find({'_id':ObjectId(id)})
        return render_template('/students/update.html', student=student)
    if request.method =='PUT':
        query = {"_id":ObjectId(id)}
        name = request.form['name']
        country = request.form['country']
        city = request.form['city']
        skills = request.form['skills'].split(', ')
        bio = request.form['bio']
        birthyear = request.form['birthyear']
        created_at = datetime.now()
        student = {
            'name': name,
            'country': country,
            'city': city,
            'birthyear': birthyear,
            'skills': skills,
            'bio': bio,
            'created_at': created_at

        }
        db.students.update_one(query, student)
        # return Response(dumps({"result":"a new student has been created"}), mimetype='application/json')
        return redirect(url_for('list_students'))

    if request.method == 'POST':
        db.students.delete_one({"_id":ObjectId(id)})
        return redirect(url_for('list_students'))

@app.route('/students')
def list_students():
    return render_template('students.html', students=db.students.find())