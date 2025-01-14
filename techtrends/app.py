import sqlite3, datetime, logging, sys
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
 
# Define the Flask application
app = Flask(__name__)

# set logger to handle STDOUT and STDERR
stdout_handler = logging.StreamHandler(sys.stdout)
stderr_handler = logging.StreamHandler(sys.stderr)
handlers = [stderr_handler, stdout_handler]

#format output
format_output = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
logging.basicConfig(format=format_output, level=logging.DEBUG, handlers=handlers, filename='app.log')

# Total amount of posts in the database
post_count = 0
# Total amount of connections to the database
db_connection_count = 0
port=3111

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():      
    global db_connection_count
    db_connection_count += 1
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):    
    global post_count
    post_count +=1
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    connection.close()     
    return post


# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)  
    
    if post is None:
        logging.debug("{}, Non existing article".format(datetime.datetime.now()))
        return render_template('404.html'), 404
    else:
      logging.debug("{}, Article \"{}\" retrived".format(datetime.datetime.now(),post['title']))    
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    logging.debug("{}, \"About us\" retrieved".format(datetime.datetime.now()))
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)', (title, content))
            connection.commit()
            connection.close()
            logging.debug("{}, A new article was created.".format(datetime.datetime.now()))

            return redirect(url_for('index'))

    return render_template('create.html')

# Define the healthcheck
@app.route('/healthz')
def healthz():
    response = app.response_class(
        response=json.dumps({"result":'OK - healthy'}),
        status=200,
        mimetype='application/json'
    )
    app.logger.info("Status request successfull")
    return response

# Define metrics
@app.route('/metrics')  
def metrics():
    response = app.response_class(
        response=json.dumps({'db_connection_count': db_connection_count, 'post_count': post_count}),
        status=200,
        mimetype='application/json'
    )
    app.logger.info("Metrics request successfull")
    logging.debug("{},Endpoint was reached.".format(datetime.datetime.now()))
    return response

# start the application on port 3111
if __name__ == "__main__":
   app.run(host='0.0.0.0', port=port)

