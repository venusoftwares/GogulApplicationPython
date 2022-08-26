#app.py
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import psycopg2 #pip install psycopg2 
import psycopg2.extras
 
app = Flask(__name__)
app.secret_key = "Cairocoders-Ednalan"
 
DB_HOST = "localhost"
DB_NAME = "table"
DB_USER = "postgres"
DB_PASS = "2311"
 
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
  
# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')
 
# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])
  
# Index
@app.route('/')
def index():
    return render_template('home.html')
 

# Articles
@app.route('/articles')
def articles():
    # Create cursor
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
  
    # Get articles
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result is None:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()
 
#Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor    
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
  
    # Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()
    return render_template('article.html', article=article)
  
# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
          
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # Execute query
        cur.execute("INSERT INTO user_flask(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
        # Commit to DB
        conn.commit()
        # Close connection
        cur.close()
        flash('You are now registered and can log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)
 
# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']
  
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
  
        # Get user by username
        result = cur.execute("SELECT * FROM user_flask WHERE username = %s", [username])
  
        if result is None:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']
  
            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username
  
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
  
    return render_template('login.html')
 
# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap
 
# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))
  
# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
  
    result = cur.execute("SELECT * FROM articles WHERE author = %s", [session['username']])
  
    articles = cur.fetchall()
  
    if result is None:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()
 
 # About
@app.route('/about')
@is_logged_in
def about():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    g = "SELECT students.id, fname, lname, email, father, mother, mobile FROM students INNER JOIN details ON students.id = details.id"
    ####SELECT * FROM students FULL OUTER JOIN details ON students.id = details.id
    cur.execute(g) # Execute the SQL
    lusers = cur.fetchall()
    return render_template('about.html',lusers = lusers)


# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
  
        # Create Cursor
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
  
        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))
        # Commit to DB
        conn.commit()
        #Close connection
        cur.close()
        flash('Article Created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)
 
# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
  
    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)
    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']
  
    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']
        # Create Cursor
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))
        # Commit to DB
        conn.commit()
        #Close connection
        cur.close()
        flash('Article Updated', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form=form)
  
  
# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
  
    # Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])
    # Commit to DB
    conn.commit()
    #Close connection
    cur.close()
    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))


#Students
@app.route('/students')
@is_logged_in
def Index1():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    s = "SELECT * FROM students"
    cur.execute(s) # Execute the SQL
    list_users = cur.fetchall()
    return render_template('index1.html', list_users = list_users)


#Add_Student
@app.route('/add_student', methods=['POST'])
@is_logged_in
def add_student():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        cur.execute("INSERT INTO students (fname, lname, email) VALUES ('"+fname+"', '"+lname+"', '"+email+"')", )
        conn.commit()
        flash('Student Added successfully')
        return redirect(url_for('Index'))
 
#Edit_Student 
@app.route('/edit/<id>', methods = ['POST', 'GET'])
@is_logged_in
def get_employee(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    cur.execute('SELECT * FROM students WHERE id = %s', (id))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('edit.html', student = data[0])

#Update_Student 
@app.route('/update/<id>', methods=['POST'])
@is_logged_in
def update_student(id):
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
         
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            UPDATE students
            SET fname = %s,
                lname = %s,
                email = %s
            WHERE id = %s
        """, (fname, lname, email, id))
        flash('Student Updated Successfully')
        conn.commit()
        return redirect(url_for('Index'))

#Delete_Student 
@app.route('/delete/<string:id>', methods = ['POST','GET'])
@is_logged_in
def delete_student(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    cur.execute('DELETE FROM students WHERE id = {0}'.format(id))
    conn.commit()
    flash('Student Removed Successfully')
    return redirect(url_for('Index1'))
  
if __name__ == '__main__':
 app.run(debug=True)
