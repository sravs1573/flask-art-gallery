from flask import Flask,redirect,url_for,render_template,request,flash,abort,session,send_file
from flask_session import Session
from key import secret_key,salt1,salt2
from itsdangerous import URLSafeTimedSerializer
from stoken import token
import os
from flask_mysqldb import MySQL
from mail import sendmail
from io import BytesIO
app = Flask(__name__)
app.secret_key = 'NSN@2023'
app.config['SESSION_TYPE']='filesystem'   
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='admin'
app.config['MYSQL_DB']='back_g'
Session(app)
mysql=MySQL(app)
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form['name']
        email=request.form['email']
        password=request.form['password']
        gender=request.form['gender']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from register where name=%s',[name])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*) from register where email=%s',[email])
        count1=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            flash('username already in use')
            return render_template('register.html')
        elif count1==1:
            flash('Email already in use')
            return render_template('register.html')
        data={'name':name,'email':email,'password':password,'gender':gender}
        subject='Email Confirmation'
        body=f"Thanks for signing up\n\nfollow this link for further steps-{url_for('confirm',token=token(data,salt1),_external=True)}"
        sendmail(to=email,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('login'))
    return render_template('register.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        print(request.form)
        name=request.form['name']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT count(*) from register where name=%s and password=%s',[name,password])
        count=cursor.fetchone()[0]
        if count==1:
            session['user']=name
            return redirect(url_for('home'))
            
        else:
            flash('Invalid username or password')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt1,max_age=180)
    except Exception as e:
        abort (404,'Link Expired register again')
    else:
        cursor=mysql.connection.cursor()
        email=data['email']
        cursor.execute('select count(*) from register where email=%s',[email])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('login'))
        else:
            cursor.execute('insert into register values(%s,%s,%s,%s)',[data['name'],data['email'],data['password'],data['gender']])
            mysql.connection.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('login'))


@app.route('/aforget',methods=['GET','POST'])
def aforgot():
    if request.method=='POST':
        id1=request.form['name']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from register where name=%s',[id1])
        count=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            cursor=mysql.connection.cursor()

            cursor.execute('SELECT email  from register where name=%s',[id1])
            email=cursor.fetchone()[0]
            cursor.close()
            subject='Forget Password'
            confirm_link=url_for('areset',token=token(id1,salt=salt2),_external=True)
            body=f"Use this link to reset your password-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Reset link sent check your email')
            return redirect(url_for('login'))
        else:
            flash('Invalid email id')
            return render_template('forgot.html')
    return render_template('forgot.html')


@app.route('/areset/<token>',methods=['GET','POST'])
def areset(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        id1=serializer.loads(token,salt=salt2,max_age=180)
    except:
        abort(404,'Link Expired')
    else:
        if request.method=='POST':
            newpassword=request.form['npassword']
            confirmpassword=request.form['cpassword']
            if newpassword==confirmpassword:
                cursor=mysql.connection.cursor()
                cursor.execute('update  register set password=%s where name=%s',[newpassword,id1])
                mysql.connection.commit()
                flash('Reset Successful')
                return redirect(url_for('login'))
            else:
                flash('Passwords mismatched')
                return render_template('newpassword.html')
        return render_template('newpassword.html')

@app.route('/home')
def home():
    return render_template('dashboard.html')
@app.route('/otp/<otp>/<name>/<email>/<password>/<gender>',methods=['GET','POST'])
def otp(otp,name,password,email,gender):
    if request.method=='POST':
        uotp=request.form['otp']
        if otp==uotp:
            cursor=mysql.connection.cursor()
            lst=[name,email,password,gender]
            query='insert into register values(%s,%s,%s,%s)'
            cursor.execute(query,lst)
            mysql.connection.commit()
            cursor.close()
            flash('Details Registered')
            return redirect(url_for('login'))
        else:
            flash('Wrong OTP')
            return render_template('otp.html',otp=otp,name=name,email=email,password=password,gender=gender)       
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home'))
    else:
        flash("already logged out")
        return redirect(url_for('login'))
@app.route('/additems',methods=['GET','POST'])
def additems():
    if request.method=="POST":
        image=request.files['image']
        id1=genotp()
        cursor=mysql.connection.cursor()
        filename=id1+'.jpg'
        cursor.execute('insert into additems(itemid,name) values(%s,%s)',[id1,session.get('user')])
        mysql.connection.commit()
        cursor.close()
        print(filename)
        path=r"C:\Users\chith\OneDrive\Desktop\backup_g\static"
        image.save(os.path.join(path,filename))
        print('success')
        return redirect(url_for('available'))
    return render_template('additems.html')

@app.route('/available')
def available():
    if session.get('user'):       
        cursor=mysql.connection.cursor()
        cursor.execute('select * from additems where name=%s',[session.get('user')])
        items=cursor.fetchall()
        print(items)
        cursor.close()
        return render_template('gallary.html',items=items)
    else:
        return redirect(url_for('login'))
@app.route('/deleteitem/<itemid>')
def deleteitem(itemid):
    cursor=mysql.connection.cursor()
    cursor.execute('delete from additems where itemid=%s',[itemid])
    mysql.connection.commit()
    cursor.close()
    path=r"C:\Users\chith\OneDrive\Desktop\backup_g\static"
    filename=f"{itemid}.jpg"
    os.remove(os.path.join(path,filename))
    flash('item deleted successfully')
    return redirect(url_for('available'))
@app.route('/additems',methods=['GET','POST'])
def dashboard():
    return render_template('dashboard.html')
@app.route('/album')
def album():
    if session.get('user'):
        return render_template('album.html')
@app.route('/createalbum',methods=['GET','POST'])
def createalbum():
    if request.method=='POST':
        name=request.form['name']
        cursor=mysql.connection.cursor()
        cursor.execute('insert into album_names(album_name,added_by) values(%s,%s)',[name,session.get('user')])
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('cb'))
    return render_template('createalbum.html')
@app.route('/cb')
def cb():
    if session.get('user'):       
        cursor=mysql.connection.cursor()
        cursor.execute('select * from album_names where added_by=%s',[session.get('user')])
        items=cursor.fetchall()
        print(items)
        cursor.close()
        return redirect(url_for('view1'))
    return render_template('createalbum.html',items=items)
    # else:
    #     return redirect(url_for('login'))
@app.route('/move/<itemid>',methods=['GET','POST'])
def move(itemid):
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from album_names where added_by=%s',[session.get('user')])
        items=cursor.fetchall()
        mysql.connection.commit()
        cursor.close()
        return render_template('move.html',items=items,itemid=itemid) 
    else:
        return redirect(url_for('login'))
@app.route('/move1/<itemid>',methods=['GET','POST'])
def move1(itemid):
    if session.get('user'):
        if request.method=='POST':       
            cursor=mysql.connection.cursor()
            '''cursor.execute('select * from album_names where added_by=%s',[session.get('user')])
            items1=cursor.fetchone()[0]
            print(items1)'''
            name=request.form['option']
            cursor.execute('insert into album(albumname,itemid,added_by) values(%s,%s,%s)',[name,itemid,session.get('user')])
            mysql.connection.commit()
            cursor.close()
            return redirect(url_for('view1'))
    else:
        return redirect(url_for('login')) 

@app.route('/view/<album_name>')
def view(album_name):
    if session.get('user'): 
        cursor=mysql.connection.cursor()
        cursor.execute('select * from album where albumname=%s',[album_name])
        items1=cursor.fetchall()
        print(items1)
        cursor.close()
        return render_template('view.html',items1=items1)
    else:
        return redirect(url_for('login'))
@app.route('/view1')
def view1():
    if session.get('user'): 
        cursor=mysql.connection.cursor()
        cursor.execute('select * from album_names where added_by=%s',[session.get('user')])
        items1=cursor.fetchall()
        print(items1)
        cursor.close()
    return render_template('allalbums.html',items1=items1)

app.run(debug=True, use_reloader=True)