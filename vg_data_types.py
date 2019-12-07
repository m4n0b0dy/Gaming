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

PROJ = 'vg-analysis'
BUCKET = 'vg-analysis-data'
LOCAL_PATH = '/home/nbdy/Desktop/Local/Data/game_data/'

def flex_open(path, typ, loc=''):
	if loc == 'gcs':
		import gcsfs
		fs = gcsfs.GCSFileSystem(project=PROJ)
		return fs.open(BUCKET+'/'+path, typ)
	else:
		return open(LOCAL_PATH+path, typ)

def flex_open_img(path, typ, loc=''):
	if loc == 'gcs':
		from google.cloud import storage
		import io
		client = storage.Client()
		bucket = client.get_bucket(BUCKET)
		blob = bucket.get_blob(path).download_as_string()
		bytes = io.BytesIO(blob)
		return Image.open(bytes, typ)
	else:
		return Image.open(LOCAL_PATH+path, typ)

#parent class holding all init loading and saving methods
class game_par:
	def __init__(self, name, data=None):
		self.name = name
		self.data = data

	def load(self, path_in, pull_file=False, read_loc=''):
		self.path_in = path_in
		if pull_file:
			#loads game from path into self, don't forget the with
			if '.json' in path_in:
				with flex_open(path_in, 'r', read_loc) as f:
					self.data = json.load(f)
			elif '.bmp' in path_in:
				self.data = flex_open_img(path_in, 'r', read_loc)
			else:
				print('Invalid path')
				return
			print('Loaded file into memory')
		else:
			print('Path saved, file NOT loaded into memory')

	def save(self, path_out='', overwrite=False, write_loc=''):
		if overwrite and self.path_in:
			#if overwriting, save to path in
			path_out = self.path_in
		#if there is no path and no overwrite
		elif not path_out:
			print('Unable to save, please define path out or define path in and overwrite')
			return
		if '.json' in path_out:
			with flex_open(path_out, 'w', write_loc) as f:
				json.dumps(self.data, f)
		elif '.bmp' in path_out:
			self.data = flex_open_img(path_out, 'w', write_loc)# https://pillow.readthedocs.io/en/3.1.x/reference/Image.html
		else:
			print('Invalid path')

#keeping this class very lean
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

