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
from google.cloud import vision
from google.cloud import language_v1
from google.cloud.language_v1 import enums

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
		self.path_in = None
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
				json.dump(self.data, f)
		elif '.bmp' in path_out:
			self.data = flex_open_img(path_out, 'w', write_loc)#TODO https://pillow.readthedocs.io/en/3.1.x/reference/Image.html
		else:
			print('Invalid path')

#keeping this class very lean
class game_img(game_par):
	#3 google APIs, they all run off files stored in GCP
	def set_api_vars(self, use_local=False):
		self.client = vision.ImageAnnotatorClient()
		#can use currently loaded image 
		if use_local and self.data:
			self.image = vision.types.Image(content=self.data)
		#or the path to file
		elif self.path_in:
			self.image = vision.types.Image()
			self.image.source.image_uri = 'gs://'+BUCKET+'/'+self.path_in
			
	def gcp_api_objects(self):
		#https://cloud.google.com/vision/docs/object-localizer
		self.img_objects = self.client.object_localization(image=self.image).localized_object_annotations
		return self.img_objects
	
	def gcp_api_properties(self):
		#https://cloud.google.com/vision/docs/detecting-properties
		self.img_properties = self.client.image_properties(image=self.image).image_properties_annotation
		return self.img_properties
	
	def gcp_api_labels(self):
		#https://cloud.google.com/vision/docs/labels
		self.img_labels = self.client.label_detection(image=self.image).label_annotations
		return self.img_labels
	
class game_txt(game_par):
	#3 google APIs, must run off files tored in GCP
	def set_api_vars(self, use_local=False):
		self.client = language_v1.LanguageServiceClient()
		self.document = {"type": enums.Document.Type.PLAIN_TEXT, "language": 'en'} #uses dic with values as base
		self.encoding_type = enums.EncodingType.UTF8
		#same as image, can load from ram or file
		if use_local and self.data:
			self.document["content"] = self.data
		elif self.path_in:
			self.document["gcs_content_uri"] = 'gs://'+BUCKET+'/'+self.path_in
			
	def gcp_api_sentiment(self):
		#https://cloud.google.com/natural-language/docs/analyzing-sentiment#language-sentiment-string-python
		self.txt_sentiment = self.client.analyze_sentiment(self.document, encoding_type=self.encoding_type)
		return self.txt_sentiment
	
	def gcp_api_ent_sent(self):
		#https://cloud.google.com/natural-language/docs/analyzing-entity-sentiment
		self.txt_ent_sentiment =  self.client.analyze_entity_sentiment(self.document, encoding_type=self.encoding_type)
		return self.txt_ent_sentiment
	
	def gcp_api_classify(self):
		#https://cloud.google.com/natural-language/docs/classifying-text
		self.txt_class =  self.client.classify_text(self.document)
		return self.txt_class