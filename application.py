from flask import Flask, render_template, redirect, request, session, url_for, send_from_directory
import os
import csv
from cs50 import SQL
from tempfile import mkdtemp
from werkzeug.utils import secure_filename
from flask_session import Session

app = Flask(__name__, static_url_path = "", static_folder = "statics")

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = "slide_pics"

Session(app)

db = SQL("postgres://cemmcsvkpzgdtv:5dc36ed6cbed9383d30de9807a6046a608dcd4fdef709f776aa4fddd9cfb77de@ec2-23-21-13-88.compute-1.amazonaws.com:5432/dffm9h2stdsa4i")

#contact list, structure: {name, position, email}
contacts = [
  {'name': None, 'position': None, 'email': None, 'season': None}
  ]

#news list, structure: {text}
news = [
  {'text': None}
]

#upcoming, structure {text, date}
upcoming = [
  {'text': None, 'date': None}
]

#links, structure {text, url}
links = [
  {'text': None, 'url': None}
]

#slideshow pics, structure {image path, description}
slide_pics = [
  {'image': None, 'description': None}
]

def add_to_table(table_name, data):
  if table_name == "news":
    add_news(data)
  if table_name == "upcoming":
    add_upcoming(data)
  if table_name == "links":
    add_links(data)
  if table_name == "contacts":
    add_contacts(data)

def delete_from_csv(filename, index):
  #open file
  contents = []
  csv_read = open(filename, 'r')
  reader = csv.reader(csv_read, delimiter=' ', quotechar='|')
  for item in reader:
    contents.append(item)
  csv_read.close()

  csv_write = open(filename, "w")
  writer = csv.writer(csv_write, delimiter=' ', quotechar='|' ,quoting=csv.QUOTE_MINIMAL)
  i = 0
  for item in contents:
    if i != index:
      writer.writerow(item)
    i+=1
  csv_write.close()

def get_contacts():
    return db.execute("SELECT * FROM contacts;")

def add_contacts(data):
  return db.execute("INSERT INTO contacts(name, position, email, season) VALUES (:name, :position, :email, :season)", name=data[0], position=data[1], email=data[2], season=data[3])

def get_news():
  return db.execute("SELECT * FROM news;")

def add_news(data):
  db.execute("INSERT INTO news(info) VALUES (:info)", info=data[0])

def get_links():
  return db.execute("SELECT * from links;")

def add_links(data):
  db.execute("INSERT INTO links(info, url) VALUES (:news, :url)", info=data[0], url=data[1])

def get_upcoming():
  return db.execute("SELECT * FROM upcoming;")

def add_upcoming(data):
  db.execute("INSERT INTO upcoming(info, date) VALUES (:news, :date)", info=data[0], date=data[1])

def get_slide_pics():
  #open file
  with open("slide_pics.csv", newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=' ', quotechar='|')
    #convert reader format to list of dicts
    items = list(slide_pics)
    for item in reader:
      items.append({'image': item[0], 'description': item[1]})
    return items

def add_slide_pic(pic, description):
  pic.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(pic.filename)))
  #add_to_csv("slide_pics.csv", [pic.filename, description])

def delete_slide_pic(index):
  pic_path = get_slide_pics()[index+1]["image"]
  delete_from_csv("slide_pics.csv", index)
  if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], pic_path)):
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], pic_path))

@app.route('/')
def hello_world():
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
    if request.form.get("username") == "0" and request.form.get("password") == "0":
      session.clear()
      session["admin"] = True;
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
      return render_template("edit.html", info = get_contacts(), post_to = "contacts")
    #if news, render edit.html with news list
    if request.args.get("info_type") == "news":
      return render_template("edit.html", info = get_news(), post_to = "news")
    #if upcoming, render edit.html with upcoming list
    if request.args.get("info_type") == "upcoming":
      return render_template("edit.html", info = get_upcoming(), post_to = "upcoming")
    #if links, render edit.html with links list
    if request.args.get("info_type") == "links":
      return render_template("edit.html", info = get_links(), post_to = "links")
    #if slide pics, render edit.html with pics list
    if request.args.get("info_type") == "slide_pics":
      return render_template("edit.html", info = get_slide_pics(), post_to = "slide_pics")


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
    add_to_table("news", [request.form.get("text")])
  #if form was upcoming, add event to list
  if request.form.get("info_type") == "upcoming":
   add_to_table("upcoming", [request.form.get("text"), request.form.get("date")])
   #if form was links, add link to list
  if request.form.get("info_type") == "links":
   add_to_table("links", [request.form.get("text"), request.form.get("url")])
  #if form was slide pics, add pic
  if request.form.get("info_type") == "slide_pics":
    if not request.files['pic_file']:
      return redirect(request.referrer)
    add_slide_pic(request.files['pic_file'], request.form.get("description"))
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
    delete_from_csv("contacts.csv", int(info_id))
  #if list was news, remove event from list
  if info_type == "news":
    delete_from_csv("news.csv", int(info_id))
  #if list was upcoming, remove event from list
  if info_type == "upcoming":
    delete_from_csv("upcoming.csv", int(info_id))
  #if list was links, remove link from list
  if info_type == "links":
    delete_from_csv("links.csv", int(info_id))
  #if list was pics, remove pic from csv and file
  if info_type == "slide_pics":
    delete_slide_pic(int(info_id))

  return redirect(request.referrer)