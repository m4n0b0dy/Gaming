#these are some libraries I think I will use
import re
from PIL import Image
import numpy as np
import json
import io
from google.protobuf.json_format import MessageToJson

#not good to have here
PROJ = 'vg-analysis'
BUCKET = 'vg-analysis-data'
LOCAL_PATH = '/home/nbdy/Desktop/Local/Data/game_data/'

def flex_open(path, typ, loc=''):
	if loc == 'gcs':
		fs = gcsfs.GCSFileSystem(project=PROJ)
		return fs.open(BUCKET+'/'+path, typ)
	else:
		return open(LOCAL_PATH+path, typ)

def flex_open_img(path, typ, loc=''):
	if loc == 'gcs':
		from google.cloud import vision
		from google.cloud import language_v1
		from google.cloud.language_v1 import enums
		from google.cloud import storage
		import gcsfs
		global STORAGE_CLIENT, VISION_CLIENT, LANGUAGE_CLIENT
		STORAGE_CLIENT = storage.Client()
		VISION_CLIENT = vision.ImageAnnotatorClient()
		LANGUAGE_CLIENT = language_v1.LanguageServiceClient()
		
		bucket = STORAGE_CLIENT.get_bucket(BUCKET)
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
				return 'Invalid path'
				return
			return 'Loaded file into memory'
		else:
			return 'Path saved, file NOT loaded into memory'

	def save(self, path_out='', overwrite=False, write_loc=''):
		if overwrite and self.path_in:
			#if overwriting, save to path in
			path_out = self.path_in
		#if there is no path and no overwrite
		elif not path_out:
			return 'Unable to save, please define path out or define path in and overwrite'
			return
		if '.json' in path_out:
			with flex_open(path_out, 'w', write_loc) as f:
				json.dump(self.data, f)
		elif '.bmp' in path_out:
			self.data = flex_open_img(path_out, 'w', write_loc)#TODO https://pillow.readthedocs.io/en/3.1.x/reference/Image.html
		else:
			return 'Invalid path'

#keeping this class very lean
class game_img(game_par):
	#3 google APIs, they all run off files stored in GCP
	def set_api_vars(self, use_local=False):
		#can use currently loaded image 
		if use_local and self.data:
			self.image = vision.types.Image(content=self.data)
		#or the path to file
		elif self.path_in:
			self.image = vision.types.Image()
			self.image.source.image_uri = 'gs://'+BUCKET+'/'+self.path_in
			
	def gcp_api_objects(self): #not using cause of price, not set to be serialized
		#https://cloud.google.com/vision/docs/object-localizer
		self.img_objects = VISION_CLIENT.object_localization(image=self.image).localized_object_annotations
		return self.img_objects
	
	def gcp_api_properties(self):
		#https://cloud.google.com/vision/docs/detecting-properties
		json_result = MessageToJson(VISION_CLIENT.image_properties(image=self.image).image_properties_annotation)
		self.img_properties = json.loads(json_result)
		return self.img_properties
	
	def gcp_api_labels(self):
		#https://cloud.google.com/vision/docs/labels
		result = VISION_CLIENT.label_detection(image=self.image).label_annotations
		self.img_labels = [{'mid':_.mid, 'description':_.description, 'score':_.score, 'topicality':_.topicality} for _ in result]
		return self.img_labels
	
class game_txt(game_par):
	#3 google APIs, must run off files tored in GCP
	def set_api_vars(self, use_local=False):
		self.document = {"type": enums.Document.Type.PLAIN_TEXT, "language": 'en'} #uses dic with values as base
		self.encoding_type = enums.EncodingType.UTF8
		#same as image, can load from ram or file
		if use_local and self.data:
			self.document["content"] = self.data
		elif self.path_in:
			self.document["gcs_content_uri"] = 'gs://'+BUCKET+'/'+self.path_in
			
	def gcp_api_sentiment(self):
		#https://cloud.google.com/natural-language/docs/analyzing-sentiment#language-sentiment-string-python
		json_result = MessageToJson(LANGUAGE_CLIENT.analyze_sentiment(self.document, encoding_type=self.encoding_type))
		self.txt_sentiment = json.loads(json_result)
		return self.txt_sentiment
		
	def gcp_api_entities(self):
		#https://cloud.google.com/natural-language/docs/analyzing-entities
		json_result =  MessageToJson(LANGUAGE_CLIENT.analyze_entities(self.document, encoding_type=self.encoding_type))
		self.txt_entities = json.loads(json_result)
		return self.txt_entities
		
	def gcp_api_classify(self):#same as other pricey one
		#https://cloud.google.com/natural-language/docs/classifying-text
		self.txt_class =  LANGUAGE_CLIENT.classify_text(self.document)
		return self.txt_class