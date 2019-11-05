'''this library holds 3 main classes based on the data used in modeling.
the three main classes are
	game_demo
	game_img
	game_txt
these all inherit from one class called game_par
	game_par contains loading methods and sotrage abilities
'''

#these are some libraries I think I will use
import re
from PIL import Image
import numpy as np
import json

#GCP api tokens stored offline for security
GCP_TOKS = json.loads()

#parent class holding all init loading and saving methods
class game_par:
	def __init__(self, name, data=None):
		self.name = name
		self.data = data

	#these functions load and save files locally and on GCP
	def load_local(self, local_path_in, pull_file=False):
		self.local_path_in = local_path_in
		if pull_file:
			#TODO loads image from path into self, don't forget the with
			self.data = loads(local_path_in)	
		
	def load_gcp(self, gcp_path_in, pull_file=False):
		self.gcp_path_in = gcp_path_in
		if pull_file:
			#TODO use gsutil to loads
			self.data = gsutil_loads(gcp_path_in)

	def save_local(self, local_path_out='', overwrite=False):
		if overwrite and self.local_path_in:
			#TODO, saves to local file with same name
			#don't forget with
			saves(self.data, self.local_path_in)
		elif local_path_out:
			saves(self.data, local_path_out)
		else:
			print('Unable to save, please define path out or define path in and overwrite')
			
	def save_gcp(self, gcp_path_out='', overwrite=False):
		if overwrite and self.gcp_path_in:
			#TODO, saves to gcp file with same name
			#don't forget with
			saves(self.data, self.gcp_path_in)
		elif gcp_path_out:
			saves(self.data, gcp_path_out)
		else:
			print('Unable to save, please define gcp path out or define gcp path in and overwrite')

class game_img(game_par):
	#3 google APIs, they all run off files stored in GCP
	def gcp_api_faces(self):
		#TODO this runs GCP's facial detectin api
		return #https://cloud.google.com/vision/docs/detecting-faces
	def gcp_api_properties(self):
		#TODO this runs GCP's image properties API
		return #https://cloud.google.com/vision/docs/detecting-properties
	def gcp_api_labels(self):
		#TODO this runs GCP's label detection API
		return #https://cloud.google.com/vision/docs/labels
class game_txt(game_par):
	#3 google APIs, must run off files tored in GCP
	def gcp_api_sentiment(self):
		#TODO runs GCP's sentiment analysis DUAI API
		return #https://cloud.google.com/natural-language/docs/analyzing-sentiment#language-sentiment-string-python
	def gcp_api_ent_sent(self):
		#TODO runs GCP's entity sentiment analysis tool
		return #https://cloud.google.com/natural-language/docs/analyzing-entity-sentiment
	def gcp_api_classify(self):
		#TODO runs GCP's content classfification
		return #https://cloud.google.com/natural-language/docs/classifying-text

