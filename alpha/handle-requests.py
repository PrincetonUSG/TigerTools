# ---------------------------------------------------------------------
# handle-requests.py
# Handles app routes
# ---------------------------------------------------------------------

# DO WE NEED TO IMPLEMENT CONCURRENT PROCESSES?

from reqlib import ReqLib
from flask import Flask, request, json, make_response, render_template, redirect
import sys
import os
import csv

app = Flask(__name__, template_folder='.')

# ---------------------------------------------------------------------
# https://levelup.gitconnected.com/building-csv-strings-in-python-32934aed5a9e
class CsvTextBuilder(object):
    def __init__(self):
        self.csv_string = []

    def write(self, row):
        self.csv_string.append(row)

# ---------------------------------------------------------------------
@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def display_home():
	html = render_template('arcgis.html')
	return make_response(html)

# ---------------------------------------------------------------------
@app.route('/points', methods=['POST'])
def get_data():
	req_lib = ReqLib()
	# if request.method == 'POST':
	categoryID = request.get_json().get('categoryid')
	# elif request.method == 'GET':
	# 	categoryID = int(request.args.get('id'))
	data = req_lib.getJSONfromXML(req_lib.configs.DINING_LOCATIONS, categoryID=categoryID,)
	return data

# ---------------------------------------------------------------------
@app.route('/wkorder', methods=['POST'])
def format_wkorder():
	# https://levelup.gitconnected.com/building-csv-strings-in-python-32934aed5a9e
	csvfile = CsvTextBuilder()
	data = [['First Name','Last Name','E-mail','Phone','Alt First Name','Alt Last Name','Alt Email','Alt Phone','Alt NetID', \
	'Contact for Scheduling','Charge Source','Campus','Building','Floor','Room','Description'], \
	[request.form.get('firstname'), request.form.get('lastname'), request.form.get('email'), request.form.get('phone'),
		request.form.get('alt-firstname'), request.form.get('alt-lastname'), request.form.get('alt-email'), \
		request.form.get('alt-phone'), request.form.get('alt-netid'), request.form.get('contacted'), \
		request.form.get('charge-source'), request.form.get('campus'), request.form.get('building'), request.form.get('description')]]
	print(data)
	writer = csv.writer(csvfile)
	writer.writerows(data)
	csv_string = csvfile.csv_string
	# testing
	print(''.join(csv_string))
	# testing
	# print(request.form.get('firstname'), request.form.get('lastname'), request.form.get('email'), request.form.get('phone'),
	# 	request.form.get('alt-firstname'), request.form.get('alt-lastname'), request.form.get('alt-email'), request.form.get('alt-phone'), 
	# 	request.form.get('alt-netid'), request.form.get('contacted'), 'Operating', request.form.get('minors-pets'), request.form.get('grad-faculty'), request.form.get('campus'), 
	# 	request.form.get('building'), request.form.get('floor'),request.form.get('room'),request.form.get('description'))
	html = render_template('arcgis.html')
	return make_response(html)

