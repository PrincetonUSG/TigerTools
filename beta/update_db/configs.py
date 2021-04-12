# ---------------------------------------------------------------------
# configs.py
# Contains methods and specifications for accessing MobileApp API
# adapted from https://github.com/vr2amesh/COS333-API-Code-Examples/
# blob/master/MobileApp/python/configs.py
# ---------------------------------------------------------------------

import requests
import json
import base64

class Configs:
	def __init__(self):
		self.CONSUMER_KEY = "I2_wnTy6MhO5O7yXyW3TeentlGka"
		self.CONSUMER_SECRET = "FJA27aTR4c7thfkFsegm01PyBJEa"
		self.BASE_URL="https://api.princeton.edu:443/mobile-app/1.0.0"
		self.COURSE_COURSES="/courses/courses"
		self.COURSE_TERMS="/courses/terms"
		self.DINING_LOCATIONS="/dining/locations"
		self.DINING_EVENTS="/dining/events"
		self.DINING_MENU="/dining/menu"
		self.PLACES_OPEN="/places/open"
		self.EVENTS_EVENTS="/events/events"
		self.REFRESH_TOKEN_URL="https://api.princeton.edu:443/token"
		self._refreshToken(grant_type="client_credentials")

	def _refreshToken(self, **kwargs):
		req = requests.post(self.REFRESH_TOKEN_URL, data=kwargs, 
			headers={"Authorization": "Basic " + base64.b64encode(bytes(self.CONSUMER_KEY + ":" + self.CONSUMER_SECRET, "utf-8")).decode("utf-8")},)
		text = req.text
		response = json.loads(text)
		self.ACCESS_TOKEN = response["access_token"]