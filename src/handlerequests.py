# ---------------------------------------------------------------------
# handlerequests.py
# Handles Flask app routes
# ---------------------------------------------------------------------

from CASClient import CASClient
from reqlib import ReqLib
from flask import Flask, request, make_response, render_template, redirect, url_for
from flask import json, jsonify
from time import gmtime, strftime
import datetime
from datetimerange import DateTimeRange
import arrow
import json
import psycopg2
import sys
import os
from load_api_data import update, places_open
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import pytz

app = Flask(__name__, template_folder='.')

# Generated by os.urandom(16)
app.secret_key = b'c\xb4@S1g\x1d\x90C\xfc\xb7Y\xc5I\xf5\x16'

# ---------------------------------------------------------------------
@app.route('/')
@app.route('/index')
def landing():
	if CASClient().redirectLanding() == 0:
		return redirect(url_for('display_map'))
	else:
		html = render_template('templates/index.html')
		return make_response(html)

# ---------------------------------------------------------------------
@app.route('/error')
def error_page():
	html = render_template('templates/error.html')
	return make_response(html)

# ---------------------------------------------------------------------
@app.route('/map', methods=['GET'])
def display_map():
	netid = CASClient().authenticate()

	# update all MobileApp API data in database
	update()

	html = render_template('templates/arcgis.html',netid=netid)
	return make_response(html)

# ---------------------------------------------------------------------
'''
Converts a list of tuples and corresponding keys into a
JSON string and returns that JSON string.
'''
def _tuples_to_json(keys, tuples_lists):
	lists = [list(t) for t in tuples_lists]
	record_dict = []
	if lists is not None:
		for record in lists:
			one_record = dict(zip(keys, record))
			record_dict.append(one_record)
	return json.dumps(record_dict)

# ---------------------------------------------------------------------
'''
Returns all the information stored in the table for the amenity
selected by the user in the form of a JSON string.
'''
@app.route('/points', methods=['POST'])
def get_data():
	netid = CASClient().authenticate()
	# update open/closed status of venues
	places_open()
	try:
		# which amenity
		amenity_type = request.get_json().get('amenity_type')

		DATABASE_URL = os.environ['DATABASE_URL']
		dbconnection = psycopg2.connect(DATABASE_URL, sslmode='require')
		dbcursor = dbconnection.cursor()

		if amenity_type == "printers" or amenity_type == "scanners" or amenity_type == "macs":
			# get column names
			dbcursor.execute('CREATE TABLE IF NOT EXISTS id6 (name VARCHAR(100), dbid VARCHAR(4), \
				buildingname VARCHAR(100),locationcode VARCHAR(4), lat VARCHAR(10), long VARCHAR(10), \
				accessible VARCHAR(30), description VARCHAR(80), printers VARCHAR(4), macs VARCHAR(4), \
				scanners VARCHAR(4), room VARCHAR(10), floor VARCHAR(10), locationmore VARCHAR(30), \
				PRIMARY KEY(name, dbid));')
			stmt = 'SELECT * FROM id6 LIMIT 0;'
			dbcursor.execute(stmt)
			cols = [desc[0] for desc in dbcursor.description]

		# get records
		if amenity_type == "printers":
			stmt = 'SELECT * FROM id6 WHERE printers<>%s;'
			dbcursor.execute(stmt,('None',))
			data = dbcursor.fetchall()
			data_json = _tuples_to_json(cols, data)

		elif amenity_type == "scanners":
			stmt = 'SELECT * FROM id6 WHERE scanners<>%s;'
			dbcursor.execute(stmt,('None',))
			data = dbcursor.fetchall()
			data_json = _tuples_to_json(cols, data)

		elif amenity_type == "macs":
			stmt = 'SELECT * FROM id6 WHERE macs<>%s;'
			dbcursor.execute(stmt,('None',))
			data = dbcursor.fetchall()
			data_json = _tuples_to_json(cols, data)

		elif amenity_type == "dining":
			# get column names
			dbcursor.execute('CREATE TABLE IF NOT EXISTS dining (name VARCHAR(100), dbid VARCHAR(4), \
				buildingname VARCHAR(100),locationcode VARCHAR(4), lat VARCHAR(10), long VARCHAR(10), \
				rescollege VARCHAR(30), who VARCHAR(120), payment VARCHAR(500), capacity VARCHAR(6), \
				PRIMARY KEY(name, dbid));')
			stmt = 'SELECT * FROM dining LIMIT 0;'
			dbcursor.execute(stmt)
			cols = [desc[0] for desc in dbcursor.description]
			cols.append('open')
			# get records
			stmt = 'SELECT dining.*,isitopen.open FROM dining \
				INNER JOIN isitopen ON dining.dbid=isitopen.dbid;'
			dbcursor.execute(stmt)
			data = dbcursor.fetchall()
			data_json = _tuples_to_json(cols, data)

		elif amenity_type == "cafes":
			# get column names
			dbcursor.execute('CREATE TABLE IF NOT EXISTS cafes (name VARCHAR(100), dbid VARCHAR(4), \
				buildingname VARCHAR(100), locationcode VARCHAR(4), lat VARCHAR(10), long VARCHAR(10), \
				description VARCHAR(1000), who VARCHAR(120), payment VARCHAR(500), PRIMARY KEY(name, dbid));')
			stmt = 'SELECT * FROM cafes LIMIT 0;'
			dbcursor.execute(stmt)
			cols = [desc[0] for desc in dbcursor.description]
			cols.append('open')
			# get records
			stmt = 'SELECT cafes.*,isitopen.open FROM cafes \
				INNER JOIN isitopen ON cafes.dbid=isitopen.dbid;'
			dbcursor.execute(stmt)
			data = dbcursor.fetchall()
			data_json = _tuples_to_json(cols, data)

		elif amenity_type == "vendingmachines":
			# get column names
			dbcursor.execute('CREATE TABLE IF NOT EXISTS vendingmachines (name VARCHAR(100), dbid VARCHAR(4), \
				buildingname VARCHAR(100), locationcode VARCHAR(4), lat VARCHAR(10), long VARCHAR(10), \
				directions VARCHAR(1000), what VARCHAR(500), payment VARCHAR(500), PRIMARY KEY(name, dbid));')
			stmt = 'SELECT * FROM vendingmachines LIMIT 0;'
			dbcursor.execute(stmt)
			cols = [desc[0] for desc in dbcursor.description]
			# get records
			stmt = 'SELECT * FROM vendingmachines;'
			dbcursor.execute(stmt)
			data = dbcursor.fetchall()
			data_json = _tuples_to_json(cols, data)

		elif amenity_type == "athletics":
			# get column names
			dbcursor.execute('CREATE TABLE IF NOT EXISTS athletics (buildingname VARCHAR(80), sports VARCHAR(60), \
				at VARCHAR(15), long VARCHAR(15), PRIMARY KEY (buildingname))')
			stmt = 'SELECT * FROM athletics LIMIT 0;'
			dbcursor.execute(stmt)
			cols = [desc[0] for desc in dbcursor.description]
			# get records
			stmt = 'SELECT * FROM athletics;'
			dbcursor.execute(stmt)
			data = dbcursor.fetchall()
			data_json = _tuples_to_json(cols, data)

		elif amenity_type == "water":
			# get column names
			dbcursor.execute('CREATE TABLE IF NOT EXISTS water (asset VARCHAR(6), description VARCHAR(110), \
				buildingcode VARCHAR(20), buildingname VARCHAR(80), floor VARCHAR(80), directions VARCHAR(80),\
				PRIMARY KEY (asset))')
			dbcursor.execute('CREATE TABLE IF NOT EXISTS buildings (locationcode VARCHAR(6), \
				buildingname VARCHAR(110), lat VARCHAR(20), long VARCHAR(20), PRIMARY KEY (locationcode))')
			stmt = 'SELECT * FROM water LIMIT 0;'
			dbcursor.execute(stmt)
			cols = [desc[0] for desc in dbcursor.description]
			cols.append('lat')
			cols.append('long')
			# get records
			stmt = 'SELECT water.*, buildings.lat, buildings.long \
				FROM water INNER JOIN buildings ON water.buildingcode \
				LIKE CONCAT(buildings.locationcode,CAST(\'%\' AS VARCHAR(1)));'
			dbcursor.execute(stmt)
			data = dbcursor.fetchall()
			data_json = _tuples_to_json(cols, data)

		dbcursor.close()
		dbconnection.close()

		if data_json == '':
			print('No data available for this amenity:', amenity_type)
		return data_json
	except Exception as e:
		print('Something went wrong with: get_data()', file=sys.stderr)
		print(str(e), file=sys.stderr)
		return redirect(url_for('error_page')), 500

# ---------------------------------------------------------------------
'''
Returns all the information stored in the table for the amenity
selected by the user in the form of a JSON string.
'''
@app.route('/info', methods=['POST'])
def get_info():
	netid = CASClient().authenticate()
	try:
		# which amenity
		amenity_type = request.get_json().get('type')

		# render the corresponding information template
		if amenity_type == "Printer" or amenity_type == "Computer Cluster" or amenity_type == "Scanner":
			html = render_template('templates/info_templates/printers.html',
				description=request.get_json().get("description"),
				accessible=request.get_json().get("accessible"),
				printers=request.get_json().get("printers"),
				scanners=request.get_json().get("scanners"),
				computers=request.get_json().get("computers"))
			return make_response(html)

		elif amenity_type == "Dining hall":
			html = render_template('templates/info_templates/dhalls.html',
				who=request.get_json().get("who"),
				payment=request.get_json().get("payment"),
				open=request.get_json().get("open"),
				capacity=request.get_json().get("capacity"),
				rescollege=request.get_json().get("rescollege"))
			return make_response(html)

		elif amenity_type == "Café":
			html = render_template('templates/info_templates/cafes.html',
				description=request.get_json().get("description"),
				who=request.get_json().get("who"),
				payment=request.get_json().get("payment"),
				open=request.get_json().get("open"))
			return make_response(html)

		elif amenity_type == "Vending Machine":
			html = render_template('templates/info_templates/vending.html',
				directions=request.get_json().get("directions"),
				what=request.get_json().get("what"),
				payment=request.get_json().get("payment"))
			return make_response(html)

		elif amenity_type == "Athletic Facility":
			html = render_template('templates/info_templates/athletics.html',
				sports=request.get_json().get("sports"))
			return make_response(html)

		elif amenity_type == "Bottle-Filling Station":
			html = render_template('templates/info_templates/water.html',
				floor=request.get_json().get("floor"),directions=request.get_json().get("directions"))
			return make_response(html)

	except Exception as e:
		print('Something went wrong with: get_info()', file=sys.stderr)
		print(str(e), file=sys.stderr)
		return '<h6> Unable to display amenity information. Please try again later. </h6>'

# ---------------------------------------------------------------------
'''
Formats submitted work order information into an email and sends email
from tigertoolsprinceton@gmail.com to service@princeton.edu if normal user.
Prints log message to stderr if an error occurs.
'''
@app.route('/wkorder', methods=['POST'])
def format_wkorder():
	netid = CASClient().authenticate()
	try:
		# get location information
		loc_code = ''
		if request.form.get('locationcode') is not None and request.form.get('locationcode') != '':
			loc_code = request.form.get('locationcode')
		if request.form.get('buildingcode') is not None and request.form.get('buildingcode') != '':
			code_comp = request.form.get('buildingcode').split('_')
			loc_code = code_comp[0]

		# email
		email_body = '''<u><strong>Personal Information:</strong></u><br><strong>NetID:</strong> %s<br>
		<strong>First Name:</strong> %s<br> <strong>Last Name:</strong> %s<br><strong>Email:</strong> %s<br>
		<strong>Phone:</strong> %s<br><strong>Contact regarding scheduling?:</strong> %s<br><br>
		<u><strong>Alternate Information:</strong></u><strong><br>Alternate NetID:</strong> %s<br>
		<strong>Alternate First Name:</strong> %s<br><strong>Alternate Last Name:</strong> %s<br>
		<strong>Alternate Email:</strong> %s<br><strong>Alternate Phone:</strong> %s<br><br>
		<u><strong>Request Information:</strong></u><br><strong>Campus:</strong> %s<br>
		<strong>Charge Source:</strong> Operating<br><strong>Location Code:</strong> %s<br>
		<strong>Building:</strong> %s<br><strong>Floor:</strong> %s<br>
		<strong>Room:</strong> %s<br><strong>Detailed request:</strong> %s<br>''' % (request.form.get('netid'),\
			request.form.get('firstname'), request.form.get('lastname'),request.form.get('email'),\
			request.form.get('phone'),request.form.get('contacted'), request.form.get('alt-netid'),\
			request.form.get('alt-firstname'),request.form.get('alt-lastname'),request.form.get('alt-email'), \
			request.form.get('alt-phone'),request.form.get('campus'),loc_code,request.form.get('building'),\
			request.form.get('floor'),request.form.get('room'),request.form.get('description'))
		# course staff
		if netid in ['rdondero\n','whchang\n','satadals\n','pisong\n','anatk\n']:
			message = Mail(from_email='tigertoolsprinceton@gmail.com',to_emails='%s@princeton.edu'%netid,\
				subject='Work order from instructor (TigerTools)',\
			 	html_content=('<center><h3 style="background-color:Orange;">This work order has been submitted \
			 		by a COS 333 instructor; no work order has been submitted to Facilities</h3></center><p><br>\
			 		%s</p>'%email_body))
			sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
			response = sg.send(message)
		# TigerTools team
		if netid in ['indup\n','rl27\n','arebei\n','tigertools\n']:
			message = Mail(from_email='tigertoolsprinceton@gmail.com',to_emails='%s@princeton.edu'%netid,\
				subject='Work order from team (TigerTools)',\
			 	html_content=('<center><h3 style="background-color:Orange;">This work order has been submitted \
			 		by a COS 333 TigerTools team member; no work order has been submitted to Facilities</h3></center><p><br>\
			 		%s</p>'%email_body))
			sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
			response = sg.send(message)
		# normal user
		else:
			message = Mail(from_email='tigertoolsprinceton@gmail.com',to_emails='service@princeton.edu',\
				subject='Work Order Request (TigerTools)',\
				html_content=('<center><h3 style="background-color:Orange;">A work order has been \
					submitted through the TigerTools application</h3></center><p>%s</p>'%email_body))
			sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
			response = sg.send(message)
		html = render_template('templates/arcgis.html', netid=netid)
		return make_response(html)
	except Exception as e:
		print('Something went wrong with: format_wkorder() %s'%netid, file=sys.stderr)
		print(str(e), file=sys.stderr)
		html = render_template('templates/arcgis.html')
		return make_response(html)

# ---------------------------------------------------------------------
'''
Stores a user submitted comment, its submission time, name of the amenity
the comment was written for, as well as the netid of the Princeton user who
submitted the comment to the database.
Prints log message to stderr if an error occurs.
'''
@app.route('/comment', methods=['POST'])
def store_comment():
	netid = CASClient().authenticate()
	try:
		# which amenity
		amenity_name = request.get_json().get('amenityName')

		# Connect to the database
		DATABASE_URL = os.environ['DATABASE_URL']
		dbconnection = psycopg2.connect(DATABASE_URL, sslmode='require')
		dbcursor = dbconnection.cursor()

		# Insert user's comment, submission time, etc. accordingly into the database
		comment_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
		comment = request.get_json().get('textComment')
		dbcursor.execute('CREATE TABLE IF NOT EXISTS comments (netid text, \
			amenity_name text, comment text, submit_time text);')
		query = 'INSERT INTO comments (netid, amenity_name, comment, submit_time) VALUES (%s, %s, %s, %s);'
		data = (netid, amenity_name, comment, comment_time)
		dbcursor.execute(query, data)

		# Commit changes and close database connection
		dbconnection.commit()
		dbcursor.close()
		dbconnection.close()

		html = render_template('templates/arcgis.html')
		return make_response(html)

	except Exception as e:
		print('Something went wrong with: store_comment()', file=sys.stderr)
		print(str(e), file=sys.stderr)
		html = render_template('templates/arcgis.html')
		return make_response(html)

# ---------------------------------------------------------------------
'''
Queries the database for all comments and their timestamps under the
user-selected amenity. Comments found to be 7+ days old are deleted
from the database. Renders and returns a make_response of the html template
displaycomments.html using query results.
Prints log message to stderr if an error occurs.
'''
@app.route('/displaycomments', methods=['POST'])
def show_comments():
	netid = CASClient().authenticate()
	try:
		# which amenity
		amenityName = request.get_json().get('amenityName')

		# Connect to the database
		DATABASE_URL = os.environ['DATABASE_URL']
		dbconnection = psycopg2.connect(DATABASE_URL, sslmode='require')
		dbcursor = dbconnection.cursor()

		# Query the database for comments under the same amenity name
		dbcursor.execute('CREATE TABLE IF NOT EXISTS comments (netid text, \
			amenity_name text, comment text, submit_time text);')
		query = "SELECT * FROM comments WHERE amenity_name = %s;"
		dbcursor.execute(query, (amenityName,))
		comments = dbcursor.fetchall()

		# Humanize comment times and check if comment timestamp is within past 7 days.
		# If a comment is older than 7 days, remove it from the database.
		current_time = datetime.datetime.utcnow()
		delta = datetime.timedelta(days = 7)
		a = current_time - delta
		comments_modified = []
		time_range = DateTimeRange(a, current_time)
		for comment in comments:
			if (comment[3] in time_range):
				comments_modified.append([comment[1], comment[2], arrow.get(comment[3]).humanize()])
			else:
				query = "DELETE FROM comments WHERE netid = %s AND amenity_name = %s AND comment = %s AND submit_time = %s;"
				dbcursor.execute(query, (comment[0], comment[1], comment[2], comment[3],))
		comments_modified.reverse()

		# Commit any changes and close database connection
		dbconnection.commit()
		dbcursor.close()
		dbconnection.close()

		html = render_template('templates/displaycomments.html', data=comments_modified, wasSuccessful = True)
		return make_response(html)

	except Exception as e:
		print('Something went wrong with: show_comments()', file=sys.stderr)
		print(str(e), file=sys.stderr)
		html = render_template('templates/displaycomments.html', data=[], wasSuccessful = False)
		return make_response(html)

# ---------------------------------------------------------------------
'''
Queries the database for all upvotes under the user-selected amenity, and checks
if the user has already "liked" the amenity. Renders and returns a make_response
of the html template displayLikes.html using query results.
Prints log message to stderr if an error occurs.
'''
@app.route('/displayupvotes', methods=['POST'])
def show_upvotes():
	netid = CASClient().authenticate()
	try:
		# which amenity
		amenityName = request.get_json().get('amenityName')

		# Query the database for upvotes under the same amenity name
		DATABASE_URL = os.environ['DATABASE_URL']
		dbconnection = psycopg2.connect(DATABASE_URL, sslmode='require')
		dbcursor = dbconnection.cursor()

		# Query the database for upvotes under the same amenity name
		dbcursor.execute('CREATE TABLE IF NOT EXISTS votes (netid text, \
			amenity_name text, upvotes INTEGER, downvotes INTEGER);')
		dbconnection.commit()
		query = "SELECT SUM(upvotes) FROM votes WHERE amenity_name = %s;"
		dbcursor.execute(query, (amenityName,))
		upvotes = dbcursor.fetchall()[0][0]
		if (upvotes == None): upvotes = 0

		# Check if the current user has already liked this amenity in the past
		dbcursor.execute('SELECT votes.upvotes, votes.downvotes from votes \
			where amenity_name = %s AND netid=%s AND upvotes = 1 AND downvotes = 0', (amenityName, netid,))
		result = dbcursor.fetchone()
		currentlyLiking = True
		if (result == None):
			currentlyLiking = False

		# Close database connection
		dbcursor.close()
		dbconnection.close()

		html = render_template('templates/displayLikes.html', num_of_likes = upvotes, \
			isLiking = currentlyLiking, wasSuccessful = True)
		return make_response(html)

	except Exception as e:
		print('Something went wrong with: show_upvotes()', file=sys.stderr)
		print(str(e), file=sys.stderr)
		html = render_template('templates/displayLikes.html', num_of_likes = "...", wasSuccessful = False, isLiking = False)
		return make_response(html)

# ---------------------------------------------------------------------
'''
Queries the database for all downvotes under the user-selected amenity, and checks
if the user has already "disliked" the amenity. Renders and returns a make_response
of the html template displayDislikes.html using query results.
Prints log message to stderr if an error occurs.
'''
@app.route('/displaydownvotes', methods=['POST'])
def show_downvotes():
	netid = CASClient().authenticate()
	try:
		# which amenity
		amenityName = request.get_json().get('amenityName')

		# Connect to the database
		DATABASE_URL = os.environ['DATABASE_URL']
		dbconnection = psycopg2.connect(DATABASE_URL, sslmode='require')
		dbcursor = dbconnection.cursor()

		# Query the database for downvotes under the same amenity name
		dbcursor.execute('CREATE TABLE IF NOT EXISTS votes (netid text, \
			amenity_name text, upvotes INTEGER, downvotes INTEGER);')
		query = "SELECT SUM(downvotes) FROM votes WHERE AMENITY_NAME = %s;"
		dbcursor.execute(query, (amenityName,))
		downvotes = dbcursor.fetchall()[0][0]
		if (downvotes == None): downvotes = 0

		# Check if the current user has already disliked this amenity in the past
		dbcursor.execute('SELECT votes.upvotes, votes.downvotes from votes where \
			amenity_name = %s AND netid=%s AND downvotes = 1 AND upvotes = 0', (amenityName, netid,))
		result = dbcursor.fetchone()
		currentlyDisliking = True
		if (result == None):
			currentlyDisliking = False

		# Close database connection
		dbcursor.close()
		dbconnection.close()

		html = render_template('templates/displayDislikes.html', num_of_dislikes = downvotes,\
		 isDisliking = currentlyDisliking ,wasSuccessful = True)
		return make_response(html)

	except Exception as e:
		print('Something went wrong with: show_downvotes()', file=sys.stderr)
		print(str(e), file=sys.stderr)
		html = render_template('templates/displayDislikes.html', num_of_dislikes = "...", \
			wasSuccessful = False, isDisliking = False)
		return make_response(html)

# ---------------------------------------------------------------------
'''
Inserts/updates in the database the upvote cast by a user under the currently
selected amenity.
Prints log message to stderr if an error occurs.
'''
@app.route('/placeupvote', methods=['POST'])
def place_upvote():
	netid = CASClient().authenticate()
	try:
		# which amenity
		amenityName = request.get_json().get('amenityName')

		# Connect to the database
		DATABASE_URL = os.environ['DATABASE_URL']
		dbconnection = psycopg2.connect(DATABASE_URL, sslmode='require')
		dbcursor = dbconnection.cursor()

		# Modify the database for upvotes & downvotes under the same amenity
		# name and user's netid
		dbcursor.execute('CREATE TABLE IF NOT EXISTS votes (netid text, \
			amenity_name text, upvotes INTEGER, downvotes INTEGER);')
		dbcursor.execute('SELECT votes.upvotes, votes.downvotes from votes \
			where amenity_name = %s AND netid=%s', (amenityName, netid,))
		result = dbcursor.fetchone()

		# If the user has never cast a vote for this amenity in the past, cast
		# an upvote
		if (result == None):
			query = 'INSERT INTO votes (netid, amenity_name, upvotes, downvotes) VALUES (%s, %s, %s, %s);'
			data = (netid, amenityName, 1, 0)
			dbcursor.execute(query, data)

		else:
			# If the user has most recently cast an upvote for this amenity
			# cancel their upvote
			if (result[0] == 1):
				dbcursor.execute('UPDATE votes set upvotes = 0, downvotes = 0 \
					where amenity_name = %s AND netid=%s', (amenityName, netid,))
			# Otherwise, the user has most recently cast an downvote for this
			# amenity so change their downvote to an upvote
			else:
				dbcursor.execute('UPDATE votes set upvotes = 1, downvotes = 0 \
					where amenity_name = %s AND netid=%s', (amenityName, netid,))

		# Commit changes and close database connection
		dbconnection.commit()
		dbcursor.close()
		dbconnection.close()

		html = render_template('templates/arcgis.html')
		return make_response(html)

	except Exception as e:
		print('Something went wrong with: place_upvote()', file=sys.stderr)
		print(str(e), file=sys.stderr)
		html = render_template('templates/arcgis.html')
		return make_response(html)

#---------------------------------------------------------------------
'''
Updates/inserts in the database the downvote cast by a user under the currently
selected amenity.
Prints log message to stderr if an error occurs.
'''
@app.route('/placedownvote', methods=['POST'])
def place_downvote():
	netid = CASClient().authenticate()

	try:
		# which amenity
		amenityName = request.get_json().get('amenityName')

		# Connect to the database
		DATABASE_URL = os.environ['DATABASE_URL']
		dbconnection = psycopg2.connect(DATABASE_URL, sslmode='require')
		dbcursor = dbconnection.cursor()

		# Modify the database for upvotes & downvotes under the same amenity
		# name and user's netid
		dbcursor.execute('CREATE TABLE IF NOT EXISTS votes (netid text, \
			amenity_name text, upvotes INTEGER, downvotes INTEGER);')
		dbcursor.execute('SELECT votes.upvotes, votes.downvotes from votes \
			where amenity_name = %s AND netid=%s', (amenityName, netid,))
		result = dbcursor.fetchone()

		# If the user has never cast a vote for this amenity in the past, cast
		# a downvote
		if (result == None):
			query = 'INSERT INTO votes (netid, amenity_name, upvotes, downvotes) VALUES (%s, %s, %s, %s);'
			data = (netid, amenityName, 0, 1)
			dbcursor.execute(query, data)

		else:
			# If the user has most recently cast an downvote for this amenity
			# cancel their downvote
			if (result[1] == 1):
				dbcursor.execute('UPDATE votes set upvotes = 0, downvotes = 0 \
					where amenity_name = %s AND netid=%s', (amenityName, netid,))
			# Otherwise, the user has most recently cast an upvote for this
			# amenity so change their upvote to a downvote
			else:
				dbcursor.execute('UPDATE votes set upvotes = 0, downvotes = 1 \
					where amenity_name = %s AND netid=%s', (amenityName, netid,))

		# Commit changes and close database connection
		dbconnection.commit()
		dbcursor.close()
		dbconnection.close()

		html = render_template('templates/arcgis.html')
		return make_response(html)

	except Exception as e:
		print('Something went wrong with: place_downvote()', file=sys.stderr)
		print(str(e), file=sys.stderr)
		html = render_template('templates/arcgis.html')
		return make_response(html)

#-----------------------------------------------------------------------
@app.route('/logout', methods=['GET'])
def logout():
    casClient = CASClient()
    casClient.authenticate()
    casClient.logout()

#-----------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('templates/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('templates/error.html'), 500
