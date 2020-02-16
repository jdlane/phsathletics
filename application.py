from flask import Flask, render_template, redirect, request, session, url_for, send_from_directory
import os
import csv
from cs50 import SQL
from tempfile import mkdtemp
import psycopg2
from werkzeug.utils import secure_filename
from flask_session import Session

app = Flask(__name__, static_url_path = "", static_folder = "statics")

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = "slide_pics"

#sess = Session(app)

#db = SQL(os.environ.get("DATABASE_URL"))
db = SQL("postgres://owetrzsawsbciy:64c6bba7e0eff84f8d5976fbb7ddf952b76be2a52c65885edb6523f446c7b8b5@ec2-52-55-59-250.compute-1.amazonaws.com:5432/ddgvmapjoelu1m")

#contact list, structure: {name, position, email}
contacts = [
  {'name': None, 'position': None, 'email': None, 'season': None}
  ]

#news list, structure: {text}
news = [
  {'info': None}
]

#upcoming, structure {text, date}
upcoming = [
  {'info': None, 'date': None}
]

#links, structure {text, url}
links = [
  {'info': None, 'url': None}
]

#slideshow pics, structure {image path, description}
slide_pics = [
  {'image': None, 'description': None}
]

def sort_pics(arr):
  done = False
  arr.remove("file.gitignore")
  while not done:
    done = True
    for i in range(len(arr)):
      num = int(arr[i].split(".")[0])
      num2 = int(arr[i-1].split(".")[0])
      if i != 0 and num < num2:
        a = arr[i]
        b = arr[i-1]
        arr[i-1] = a
        arr[i] = b
        done = False
  return arr

def add_to_table(table_name, data):
  if table_name == "news":
    add_news(data)
  if table_name == "upcoming":
    add_upcoming(data)
  if table_name == "links":
    add_links(data)
  if table_name == "contacts":
    add_contacts(data)

def delete_from_table(table_name, row_id):
  if table_name == "news":
    delete_news(row_id)
  if table_name == "contacts":
    delete_contacts(row_id)
  if table_name == "upcoming":
    delete_upcoming(row_id)
  if table_name == "links":
    delete_links(row_id)

def get_contacts():
    return db.execute("SELECT * FROM contacts")

def add_contacts(data):
  return db.execute("INSERT INTO contacts (name, position, email, season) VALUES (:name, :position, :email, :season)", name=data[0], position=data[1], email=data[2], season=data[3])

def delete_contacts(row_id):
  db.execute("DELETE FROM contacts WHERE id = :rid", rid=row_id)

def get_news():
  return db.execute("SELECT * FROM news")

def add_news(data):
  db.execute("INSERT INTO news (info) VALUES (:info)", info=data[0])

def delete_news(row_id):
  db.execute("DELETE FROM news WHERE id = :rid", rid=row_id)

def get_links():
  return db.execute("SELECT * from links")

def add_links(data):
  db.execute("INSERT INTO links (info, url) VALUES (:info, :url)", info=data[0], url=data[1])

def delete_links(row_id):
  db.execute("DELETE FROM links WHERE id = :rid", rid=row_id)

def get_upcoming():
  return db.execute("SELECT * FROM upcoming")

def add_upcoming(data):
  db.execute("INSERT INTO upcoming (info, date) VALUES (:info, :date)", info=data[0], date=data[1])

def delete_upcoming(row_id):
  db.execute("DELETE FROM upcoming WHERE id = :rid", rid=row_id)

def get_slide_pics():
  #open file
  paths = os.listdir(app.config["UPLOAD_FOLDER"])
  paths = sort_pics(paths)
  items = []
  for path in paths:
    if path != "file.gitignore":
      pic_data = db.execute("SELECT description, id FROM slide_pics WHERE id = :pid", pid = path.split(".")[0])[0]
      items.append({'image': path, 'description': pic_data['description'], 'id': pic_data['id']})
  return items

def add_slide_pic(pic, name):
  pic_id = db.execute("SELECT id FROM slide_pics ORDER by id DESC LIMIT 1")
  if not pic_id:
    pic_id = 1
  else:
    pic_id = pic_id[0]["id"]
  pic = db.execute("SELECT image FROM slide_pics WHERE id = :pid", pid = pic_id)[0]["image"]
  blob = bytes(pic)
  blob = str(blob, "utf-8")
  blob = bytearray.fromhex(blob)
  path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(str(int(pic_id))+"."+name))
  with open(path, "wb") as file:
    file.write(blob)
  return path

def delete_slide_pic(index):
  pic_path = str(index)+"."+db.execute("SELECT type FROM slide_pics WHERE id = :index", index=index)[0]["type"]
  if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], pic_path)):
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], pic_path))
  db.execute("DELETE FROM slide_pics WHERE id = :pid", pid = index)

def check_slide_pics():
  paths = os.listdir(app.config["UPLOAD_FOLDER"])
  if len(paths) < 2:
    pics = db.execute("SELECT image, id, type FROM slide_pics")
    for pic in pics:
      blob = bytes(pic["image"])
      blob = str(blob, "utf-8")
      blob = bytearray.fromhex(blob)
      path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(str(pic["id"])+"."+pic["type"]))
      with open(path, "wb") as file:
        file.write(blob)


@app.route('/')
def hello_world():
  check_slide_pics()
  return render_template("index.html", upcoming_events = get_upcoming(), news = get_news(), links = get_links(), slide_pics = get_slide_pics())

#rest API to serve pics
@app.route('/img/<path:filename>')
def send_file(filename):
    return send_from_directory("static/pics", filename)

@app.route('/slide_img/<path:filename>')
def send_slide_file(filename):
    return send_from_directory("slide_pics", filename)

@app.route('/contact')
def contact():
  return render_template("contact.html", contacts=get_contacts())

@app.route('/upcoming_events')
def upcoming_events():
  return render_template("upcoming.html", upcoming=get_upcoming())

@app.route('/news_page')
def news_page():
  return render_template("news.html", news=get_news())

@app.route('/registration')
def registration():
  return render_template("registration.html")

@app.route('/edit_directory')
def edit_directory():
  #if logged in redirect to edit directory
  if session.get("admin"):
    return render_template("editdir.html")
  #else redirect to login
  else:
    return render_template("login.html")

@app.route('/login', methods=["POST", "GET"])
def login():
  #if get request render login page
  if request.method == "GET":
    return render_template("login.html")
  #if post request handle login form
  if request.method == "POST":
    #if fields empty redirect to referrer
    if not request.form.get("username") or not request.form.get("password"):
      return redirect(request.referrer)
    #if correct username/password (subject to change) start admin session and redirect to edit page
    if request.form.get("username") == "phsathletics" and request.form.get("password") == "codingclub2020":
      session.clear()
      session["admin"] = True
      return redirect("/edit_directory")
    return redirect("/")

@app.route('/edit', methods=["GET", "POST"])
def edit():
  #redirect if not logged in as admin
  if not session.get("admin"):
    return redirect("/login")
  if request.method == "GET":
    #if contacts, render edit.html with contacts list
    if request.args.get("info_type") == "contacts":
      return render_template("edit.html", info = get_contacts(), post_to = "contacts", template = contacts)
    #if news, render edit.html with news list
    if request.args.get("info_type") == "news":
      return render_template("edit.html", info = get_news(), post_to = "news", template = news)
    #if upcoming, render edit.html with upcoming list
    if request.args.get("info_type") == "upcoming":
      return render_template("edit.html", info = get_upcoming(), post_to = "upcoming", template = upcoming)
    #if links, render edit.html with links list
    if request.args.get("info_type") == "links":
      return render_template("edit.html", info = get_links(), post_to = "links", template = links)
    #if slide pics, render edit.html with pics list
    if request.args.get("info_type") == "slide_pics":
      return render_template("edit.html", info = get_slide_pics(), post_to = "slide_pics", template = slide_pics)


@app.route('/add_info', methods=["POST"])
def add_info():
  #redirect if not logged in as admin
  if not session.get("admin"):
    return redirect("/login")
  #if form was contacts, add contact to list
  if request.form.get("info_type") == "contacts":
    add_to_table("contacts", [request.form.get("name"), request.form.get("position"), request.form.get("email"), request.form.get("season")])
  #if form was news, add event to list
  if request.form.get("info_type") == "news":
    add_to_table("news", [request.form.get("info")])
  #if form was upcoming, add event to list
  if request.form.get("info_type") == "upcoming":
   add_to_table("upcoming", [request.form.get("info"), request.form.get("date")])
   #if form was links, add link to list
  if request.form.get("info_type") == "links":
   add_to_table("links", [request.form.get("info"), request.form.get("url")])
  #if form was slide pics, add pic
  if request.form.get("info_type") == "slide_pics":
    if not request.files['pic_file']:
      return redirect(request.referrer)
    pic = request.files["pic_file"].stream.read()
    filetype = str(request.files["pic_file"]).split("'")[1].split(".")[1].lower()
    pic = bytearray(pic)
    pic = "".join(format(x, "02x") for x in pic)
    db.execute("INSERT INTO slide_pics (image, type, description) VALUES (:img,:type, :desc)", img=pic, type=filetype, desc = request.form.get("description"))
    add_slide_pic(bytearray(request.files['pic_file']), filetype)
  db.execute("COMMIT")
  return redirect(request.referrer)

@app.route('/delete_info', methods=["GET"])
def delete_info():
  #redirect if not logged in as admin
  if not session.get("admin"):
    return redirect("/login")
  #get info from get request
  info_type = request.args.get("info_type")
  info_id = request.args.get("id")
  #if missing info return to referrer
  if not info_type or not info_id:
    redirect(request.referrer)
  #if list was contacts, remove contact from list
  if info_type == "contacts":
    delete_from_table("contacts", int(info_id))
  #if list was news, remove event from list
  if info_type == "news":
    delete_from_table("news", int(info_id))
  #if list was upcoming, remove event from list
  if info_type == "upcoming":
    delete_from_table("upcoming", int(info_id))
  #if list was links, remove link from list
  if info_type == "links":
    delete_from_table("links", int(info_id))
  #if list was pics, remove pic from csv and file
  if info_type == "slide_pics":
    delete_slide_pic(int(info_id))

  db.execute("COMMIT")
  return redirect(request.referrer)