import os, re, secrets, sqlite3
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, jsonify, request, session, send_from_directory, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
BASE=os.path.dirname(os.path.abspath(__file__))
DB_PATH=os.environ.get('DATABASE_PATH',os.path.join(BASE,'school.db'))
app=Flask(__name__,static_folder=None)
app.secret_key=os.environ.get('SECRET_KEY') or 'CHANGE-THIS-BEFORE-DEPLOYMENT-'+secrets.token_hex(24)
app.config.update(SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE','0')=='1',MAX_CONTENT_LENGTH=1_000_000)
app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1)
def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def db():
 c=sqlite3.connect(DB_PATH,timeout=20);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');return c
def init_db():
 with db() as c:
  c.executescript("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT NOT NULL,phone TEXT NOT NULL,email TEXT NOT NULL UNIQUE,password_hash TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'parent',created_at TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY,reference TEXT NOT NULL UNIQUE,parent_id INTEGER REFERENCES users(id),student TEXT NOT NULL,class_name TEXT NOT NULL,guardian TEXT NOT NULL,phone TEXT NOT NULL,email TEXT NOT NULL,previous_school TEXT DEFAULT '',notes TEXT DEFAULT '',status TEXT NOT NULL DEFAULT 'Submitted',school_note TEXT DEFAULT '',created_at TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS enquiries(id INTEGER PRIMARY KEY,name TEXT,email TEXT,phone TEXT,subject TEXT,message TEXT,created_at TEXT);""")
  email=os.environ.get('ADMIN_EMAIL','').strip().lower();password=os.environ.get('ADMIN_PASSWORD','')
  if email and len(password)>=12 and not c.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone():
   c.execute('INSERT INTO users(name,phone,email,password_hash,role,created_at) VALUES(?,?,?,?,?,?)',('School Administrator','',email,generate_password_hash(password),'admin',now()))
def parse_body():
 d=request.get_json(silent=True)
 if not isinstance(d,dict):raise ValueError('Please submit a valid form.')
 return {str(k):str(v).strip() for k,v in d.items() if v is not None}
def error(msg,status=400):return jsonify(error=msg),status
def user():
 uid=session.get('uid')
 if not uid:return None
 with db() as c:return c.execute('SELECT id,name,phone,email,role FROM users WHERE id=?',(uid,)).fetchone()
def require_user(fn):
 @wraps(fn)
 def inner(*a,**kw):
  if not user():return error('Please sign in to continue.',401)
  return fn(*a,**kw)
 return inner
def require_admin(fn):
 @wraps(fn)
 def inner(*a,**kw):
  u=user()
  if not u or u['role']!='admin':return error('Administrator access required.',403)
  return fn(*a,**kw)
 return inner
def new_reference():
 with db() as c:
  while True:
   r='KCSS-'+datetime.now().strftime('%Y')+'-'+secrets.token_hex(3).upper()
   if not c.execute('SELECT 1 FROM applications WHERE reference=?',(r,)).fetchone():return r
@app.get('/')
def home():return send_from_directory(BASE,'index.html')
@app.get('/<path:path>')
def static_file(path):
 if path.startswith('api/'):abort(404)
 full=os.path.abspath(os.path.join(BASE,path))
 if not full.startswith(os.path.abspath(BASE)+os.sep) or not os.path.isfile(full):abort(404)
 return send_from_directory(BASE,path)
@app.get('/api/health')
def health():return jsonify(status='ok')
@app.post('/api/register')
def register():
 try:d=parse_body()
 except ValueError as e:return error(str(e))
 name,phone,email,password,confirm=(d.get(k,'') for k in ('name','phone','email','password','confirm'));email=email.lower()
 if len(name)<2 or len(phone)<5 or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email):return error('Enter a valid name, phone number and email address.')
 if len(password)<10:return error('Use a password with at least 10 characters.')
 if password!=confirm:return error('The passwords do not match.')
 try:
  with db() as c:cur=c.execute('INSERT INTO users(name,phone,email,password_hash,role,created_at) VALUES(?,?,?,?,?,?)',(name,phone,email,generate_password_hash(password),'parent',now()));uid=cur.lastrowid
 except sqlite3.IntegrityError:return error('An account with this email already exists. Please sign in.',409)
 session.clear();session['uid']=uid;return jsonify(ok=True,user={'name':name,'email':email})
@app.post('/api/login')
def login():
 try:d=parse_body()
 except ValueError as e:return error(str(e))
 email=d.get('email','').lower();password=d.get('password','')
 with db() as c:u=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
 if not u or not check_password_hash(u['password_hash'],password):return error('Email or password is incorrect.',401)
 session.clear();session['uid']=u['id'];return jsonify(ok=True,user={'name':u['name'],'email':u['email'],'role':u['role']})
@app.post('/api/admin/login')
def admin_login():
 try:d=parse_body()
 except ValueError as e:return error(str(e))
 email=d.get('email','').lower();password=d.get('password','')
 with db() as c:u=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
 if not u or u['role']!='admin' or not check_password_hash(u['password_hash'],password):return error('Administrator email or password is incorrect.',401)
 session.clear();session['uid']=u['id'];return jsonify(ok=True,user={'name':u['name'],'email':u['email'],'role':u['role']})
@app.post('/api/logout')
def logout():session.clear();return jsonify(ok=True)
@app.get('/api/me')
def me():
 u=user();return jsonify(user=({'id':u['id'],'name':u['name'],'email':u['email'],'phone':u['phone'],'role':u['role']} if u else None))
@app.post('/api/admissions')
def admissions():
 try:d=parse_body()
 except ValueError as e:return error(str(e))
 if any(not d.get(k) for k in ('student','className','guardian','phone','email')):return error('Please complete all required admission fields.')
 if d['className'] not in ['S.1','S.2','S.3','S.4','S.5','S.6']:return error('Choose a valid class.')
 if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',d['email'].lower()):return error('Enter a valid parent email address.')
 u=user();ref=new_reference()
 with db() as c:c.execute('INSERT INTO applications(reference,parent_id,student,class_name,guardian,phone,email,previous_school,notes,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(ref,u['id'] if u and u['role']=='parent' else None,d['student'],d['className'],d['guardian'],d['phone'],d['email'].lower(),d.get('previousSchool','')[:200],d.get('notes','')[:3000],'Submitted',now()))
 return jsonify(ok=True,reference=ref,status='Submitted'),201
@app.get('/api/applications')
@require_user
def applications():
 u=user()
 with db() as c:
  rows=c.execute('SELECT * FROM applications ORDER BY id DESC').fetchall() if u['role']=='admin' else c.execute('SELECT * FROM applications WHERE parent_id=? OR (parent_id IS NULL AND lower(email)=?) ORDER BY id DESC',(u['id'],u['email'].lower())).fetchall()
 return jsonify(items=[dict(id=r['id'],reference=r['reference'],student=r['student'],class_name=r['class_name'],status=r['status'],school_note=r['school_note'],created_at=r['created_at'][:10]) for r in rows])
@app.get('/api/admin/applications')
@require_admin
def admin_applications():
 with db() as c:rows=c.execute('SELECT id,reference,student,class_name,guardian,phone,email,status,school_note,created_at FROM applications ORDER BY id DESC').fetchall()
 return jsonify(items=[dict(r) for r in rows])
@app.patch('/api/admin/applications/<int:app_id>')
@require_admin
def update_application(app_id):
 try:d=parse_body()
 except ValueError as e:return error(str(e))
 status=d.get('status','');note=d.get('school_note','')[:1000]
 if status not in ['Submitted','Under review','Accepted','Waitlisted','Rejected']:return error('Choose a valid application status.')
 with db() as c:
  cur=c.execute('UPDATE applications SET status=?,school_note=? WHERE id=?',(status,note,app_id))
  if not cur.rowcount:return error('Application not found.',404)
 return jsonify(ok=True)
@app.post('/api/contact')
def contact():
 try:d=parse_body()
 except ValueError as e:return error(str(e))
 if not all(d.get(k) for k in ('name','email','subject','message')):return error('Complete the required enquiry fields.')
 with db() as c:c.execute('INSERT INTO enquiries(name,email,phone,subject,message,created_at) VALUES(?,?,?,?,?,?)',(d['name'][:150],d['email'][:250],d.get('phone','')[:50],d['subject'][:200],d['message'][:5000],now()))
 return jsonify(ok=True),201
@app.get('/api/admin/enquiries')
@require_admin
def admin_enquiries():
 with db() as c:rows=c.execute('SELECT id,name,email,phone,subject,message,created_at FROM enquiries ORDER BY id DESC').fetchall()
 return jsonify(items=[dict(r) for r in rows])
init_db()
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.environ.get('PORT','5000')),debug=False)
