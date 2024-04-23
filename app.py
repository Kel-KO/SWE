from multiprocessing import connection
import os
from contextlib import closing
from datetime import datetime
import psycopg2
from tempfile import mkdtemp



from flask import Flask, flash, redirect, render_template, request, url_for
from flask_mysqldb import MySQL


#app config and db connection----------------------------------------success
app = Flask(__name__)

app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "naijaboyz123"
app.config['MYSQL_DB'] = "swe"
##
mysql = MySQL(app)



########index page configuration: login and create new account system-----------------------success
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "GET":
        # display basic index page when app is loaded
        return render_template("index.html")
    else:
        # when user inputs are filled check for match in database
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username, password FROM accounts WHERE username = %s AND password = %s", (username, password))
        result = cur.fetchone()

        if result:
            # Username and password match found
            user_id = result[0]  # Fetch the first element (id) from the tuple
            return redirect('/user/' + str(user_id))  # Redirect to the user page with user_id
        else:
            # No match found
            rspns = 'INVALID USERNAME OR PASSWORD'
            return rspns

        cur.close()








##new user route redirecting user to the create a new accounrt page/ insert user and their info into database---------------------------success
@app.route('/newuser', methods=['GET','POST'])
def newuser():
    if request.method == "GET":
        # display basic display new user page
        return render_template("newacct.html")
    else:
        ##add new user into accounts table in database
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO accounts (username, password) VALUES(%s,%s)", (username, password))
        mysql.connection.commit()  # Commit the changes to the database

        ##get the id of the inserted record
        cur.execute("SELECT LAST_INSERT_ID()")
        account_id = cur.fetchone()[0]

        ##add new userinfo into userinfo table in database
        name = request.form['name']
        age = request.form['age']
        heightft = request.form['heightft']
        heightin = request.form['heightin']
        currweight = request.form['currentweight']
        goalweight = request.form['goalweight']
        cur.execute("INSERT INTO userinfo (id, name, age, heightft, heightin, current_weight, goal_weight) VALUES(%s,%s,%s,%s,%s,%s,%s)", (account_id, name, age, heightft, heightin, currweight, goalweight))
        mysql.connection.commit()  # Commit the changes to the database
        cur.close()

        return redirect('/')  # Redirect to the index page




@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
def user(user_id):
    if request.method == "GET":
        # Display user's page
        cur = mysql.connection.cursor()

        # Query to display user info
        cur.execute("SELECT * FROM userinfo WHERE id = %s", (user_id,))
        row = cur.fetchone()
        if row:
            name = row[1]
            age = row[2]
            heightft = row[3]
            heightin = row[4]
            currweight = row[5]
            goalweight = row[6]
        cur.close()

        # Query to display random message
        cur = mysql.connection.cursor()
        cur.execute("SELECT message FROM messages ORDER BY RAND() LIMIT 1;")
        message = cur.fetchone()[0]
        cur.close()

        # Query to display workout
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM workouts ORDER BY RAND() LIMIT 1;")
        row = cur.fetchone()
        if row:
            type_workout = row[1]
            workout = row[2]
            sets = row[3]
            cals = row[4]
        cur.close()

        # Query to add clocked workout to database and display workout history

        # Display workout history for this user
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM userhistory WHERE user_id = %s", (user_id,))
        history = cur.fetchall()
        cur.close()

        now = datetime.now()
        return render_template("userhomepage.html", now=now, history=history, type_workout=type_workout,
                               workout=workout, sets=sets, cals=cals, message=message, name=name, age=age,
                               heightft=heightft, heightin=heightin, currweight=currweight, goalweight=goalweight)

    else:
        # Update user info in the database
        cur = mysql.connection.cursor()
        cur.execute("UPDATE userinfo SET name=%s, age=%s, heightft=%s, heightin=%s, current_weight=%s, goal_weight=%s WHERE id=%s",
                    (request.form['name'], request.form['age'], request.form['heightft'], request.form['heightin'],
                     request.form['currentweight'], request.form['goalweight'], user_id))
        mysql.connection.commit()
        cur.close()
        return render_template("userhomepage.html", now=now, history=history, type_workout=type_workout,
                       workout=workout, sets=sets, cals=cals, message=message, name=name, age=age,
                       heightft=heightft, heightin=heightin, currweight=currweight, goalweight=goalweight)


##clockin system backend---------------------------------------incomplete
@app.route('/clock_in/<int:user_id>', methods=['POST'])
def clock_in(user_id):
    if request.method == 'POST':
        workout = request.form['workout']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO userhistory (workout, date_time, user_id) VALUES (%s, %s, %s)", (workout, datetime.now(), user_id))
        mysql.connection.commit()
        cur.close()

        return 'Workout clocked in successfully!', 200
    else:
        return 'Method not allowed', 405



##update user info backend--------------------------------------success
@app.route('/updateinfo/<int:user_id>', methods=['GET','POST'])
def updateinfo(user_id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        cur.execute("UPDATE userinfo SET name=%s, age=%s, heightft=%s, heightin=%s, current_weight=%s, goal_weight=%s WHERE id=%s",
                    (request.form['name'], request.form['age'], request.form['heightft'], request.form['heightin'],
                     request.form['currentweight'], request.form['goalweight'], user_id))
        mysql.connection.commit()
        cur.close()
        return redirect(f'/user/{user_id}')

    else:
        cur.execute("SELECT * FROM userinfo WHERE id = %s", (user_id,))
        user_info = cur.fetchone()
        cur.close()
        if user_info:
            return render_template('updateinfo.html', user_info=user_info, user_id=user_id)

        else:
            return 'User not found', 404


##add workout backend---------------------------------------------------------------success
@app.route('/add_workout', methods=['POST'])
def add_workout():
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO workouts (type, name, sets, calories) VALUES (%s, %s, %s, %s)",
                (request.form['type'], request.form['name'], request.form['sets'], request.form['calories']))
    mysql.connection.commit()
    cur.close()
    return '', 204  # Return an empty response with status code 204 (No Content)


        ### Get updated user info
        ##cur.execute("SELECT * FROM userinfo WHERE id = %s", (user_id,))
        ##row = cur.fetchone()
        ##cur.close()

        ### Return updated user info as JSON
        ##response = {
        ##    'name': row[1],
        ##    'age': row[2],
        ##    'heightft': row[3],
        ##    'heightin': row[4],
        ##    'currweight': row[5],
        ##    'goalweight': row[6]
        ##}



#######route to user account that is stored in the database----------------------------------------------------------incomplete
#####@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
#####def user(user_id):
#####    if request.method == "GET":
#####        # Display user's page
#####        cur = mysql.connection.cursor()
#####
#####        # Query to display user info
#####        cur.execute("SELECT * FROM userinfo WHERE id = %s", (user_id,))
#####        row = cur.fetchone()
#####        if row:
#####            name = row[1]  # Assuming name is the second column in the table
#####            age = row[2]  # Assuming age is the third column in the table
#####            heightft = row[3]  # Assuming heightft is the fourth column in the table
#####            heightin = row[4]  # Assuming heightin is the fifth column in the table
#####            currweight = row[5]  # Assuming current_weight is the sixth column in the table
#####            goalweight = row[6]  # Assuming goal_weight is the seventh column in the table
#####        cur.close()
#####
#####        # Query to display random message
#####        cur = mysql.connection.cursor()
#####        cur.execute("SELECT message FROM messages ORDER BY RAND() LIMIT 1;")
#####        message = cur.fetchone()[0]
#####        cur.close()
#####
#####        # Query to display workout
#####        cur = mysql.connection.cursor()
#####        cur.execute("SELECT * FROM workouts ORDER BY RAND() LIMIT 1;")
#####        row = cur.fetchone()
#####        if row:
#####            type_workout = row[1]
#####            workout = row[2]
#####            sets = row[3]
#####            cals = row[4]  # Assuming current_weight is the fifth column in the table
#####        cur.close()
#####
#####        # Query to add clocked workout to database and display workout history
#####
#####        # Display workout history for this user
#####        cur = mysql.connection.cursor()
#####        cur.execute("SELECT * FROM userhistory WHERE user_id = %s", (user_id,))
#####        history = cur.fetchall()
#####        cur.close()
#####
#####        now = datetime.now()
#####        return render_template("userhomepage.html", now=now, history=history, type_workout=type_workout,
#####                               workout=workout, sets=sets, cals=cals, message=message, name=name, age=age,
#####                               heightft=heightft, heightin=heightin, currweight=currweight, goalweight=goalweight)
#####
#####    elif request.method == "POST":
#####        # Update user info in the database
#####        cur = mysql.connection.cursor()
#####        cur.execute("UPDATE userinfo SET name=%s, age=%s, heightft=%s, heightin=%s, current_weight=%s, goal_weight=%s WHERE id=%s",
#####                    (request.form['name'], request.form['age'], request.form['heightft'], request.form['heightin'],
#####                     request.form['currentweight'], request.form['goalweight'], user_id))
#####        mysql.connection.commit()
#####        cur.close()
#####
#####        # Redirect to the same route to refresh the page
#####        return redirect(url_for('user', user_id=user_id))





##test route for hardcoded user kel-----------------------------------success(adjust /user route to fit to any user currently in the database)
##@app.route('/userkel', methods=['GET','POST'])
##def userkel():
##    if request.method == "GET":
##        # display basic kel's page
##        cur = mysql.connection.cursor()
##
##        #query to display user info--------------------------------half complete. needs to be adjusted to fit any user
##        name = 'Kel Onyewuenyi'
##        cur.execute("SELECT * FROM userinfo WHERE name = %s", (name))
##        row = cur.fetchone()
##        if row:
##            age = row[2]  # Assuming age is the second column in the table
##            heightft = row[3]  # Assuming heightft is the third column in the table
##            heightin = row[4]  # Assuming heightin is the fourth column in the table
##            currweight = row[5]  # Assuming current_weight is the fifth column in the table
##            goalweight = row[6]  # Assuming goal_weight is the sixth column in the table
##            cur.close()
##        
##
##        #query to display random message-----------------------------------------complete
##        cur = mysql.connection.cursor()
##        cur.execute("SELECT message FROM messages ORDER BY RAND() LIMIT 1;")
##        message = str(cur.fetchall())
##        cur.close()
##
##
##        #query to display workout--------------------------------------------complete
##        cur = mysql.connection.cursor()
##        cur.execute("SELECT * FROM workouts ORDER BY RAND() LIMIT 1;")
##        row = cur.fetchone()
##        if row:
##            type_workout = row[1]  
##            workout = row[2]  
##            sets = row[3]  
##            cals = row[4]  # Assuming current_weight is the fifth column in the table
##            cur.close()
##        
##        #query to add clocked workout to database and display workout history-----------------------incomplete
##
##        #display workout history for this user
##        cur = mysql.connection.cursor()
##        cur.execute("SELECT * FROM userhistory")
##        row = cur.fetchall()
##        history = row
##        cur.close()
##
##
##        now = datetime.now()
##        return render_template("kel.html", history=history, type_workout=type_workout, workout=workout, sets=sets, cals=cals, message=message, name=name, age=age, heightft=heightft, heightin=heightin, currweight=currweight, goalweight=goalweight)
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##
##@app.route('/userzoe')
##def userzoe():
##    ##if request.method == "GET":
##        # display basic index page
##        return render_template("zoe.html")
##
##@app.route('/userwali')
##def userwali():
##    ##if request.method == "GET":
##        # display basic index page
##        return render_template("wali.html")
##
##
##if __name__ == "__main__":
##    app.run(debug=True)
##    