import json
import numpy as np
import pandas as pd
import time
import string
import random
from sklearn.random_projection import SparseRandomProjection
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from joblib import dump, load
from operator import itemgetter
from collections import Counter
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

#import findspark
#findspark.init('/usr/local/spark')
#import pyspark

#max image dimemensions (for padding)
MAX_IMG_LEN = 800
MAX_IMG_WIDTH = 800

#stop words checking this runs on o(1) instead of o(n) https://stackoverflow.com/questions/19560498/faster-way-to-remove-stop-words-in-python
_stop_words = stopwords.words('english')
SW_DIC = Counter(_stop_words)
_stop_words = None
#using a porter stemmer as well
STMR = PorterStemmer()
#and punctuation remover
TRNSLTR = str.maketrans('', '', string.punctuation)

#check if it's a number
def is_num(v1):
	r1 = v1.replace('m','')
	try:
		return float(r1)
	except:
		#return lowest possible sales value
		return 0.01

def load_batches(path, batch_nums):
	ret_dic = {}
	for f in batch_nums:
		try:
			with open(path+str(f)+'-complete.json', 'rb') as f:
				ret_dic.update(json.load(f))
		except Exception as e:
			print(e, path+str(f)+'-complete.json')
	return ret_dic

#functions to manipulate image and text data
def tr_none(n):
	return n

#this used when training ISPR and also when transforming data
def tr_img(img):
	np_img = np.array(img)
	#if dim aren't 2 it's broken
	if np_img.ndim != 2:
		np_img = np.zeros((MAX_IMG_LEN, MAX_IMG_WIDTH))
	length, width = np_img.shape
	#pad it if it's not the right length, add 0s to right and bottom
	padded = np.append(np_img, np.zeros((length, MAX_IMG_WIDTH-width)),1)
	padded = np.append(padded, np.zeros((MAX_IMG_LEN-length, MAX_IMG_WIDTH)),0)
	#flatten image	
	return np.array(padded).flatten()

#this used to filter stop words and stem words
def tr_txt(txt):
	ret_txt = []
	no_punc = txt.translate(TRNSLTR).lower()
	for word in no_punc.split(' '):
		if word == ' ' or word == '':
			continue
		if SW_DIC[word]==0:
			#stem word
			ret_txt.append(STMR.stem(word))
	return ' '.join(ret_txt)

#needed to perform decomposition in batches, so made a function for it, don't need if lots of RAM
def batch_train_decomposer(data_path, dec_model, batch_order, tr_typ, nm=''):
	start_time = time.time()
	for cnt, batch_nums in enumerate(batch_order):
		#transforms text or image based on the function we feed
		data = [tr_typ(data) for data in load_batches(data_path, batch_nums).values()]
		dec_model = dec_model.fit(data)
		if cnt % 10 == 0:
			print('Finished %s in %s sec'%(cnt+1, round(time.time() - start_time,4)))
			print(dump(dec_model, 'models/'+nm+'.joblib'))
	#store model for later
	print(dump(dec_model, 'models/'+nm+'.joblib'))
	print(nm+' made')
	return dec_model

#inspired by my new linux server to use the one letter commands
#meant to index attributes with certain methods to not repeat methods
TYP_CON = {'i':'self.img_data','t':'self.text_data','d':'self.dem_data','l':'self.labels','n':'self.nms'}
#same but has data paths
PATH_CON = {'i':'imgs/img_batch_','t':'text/txt_batch_','d':'dem/dem_batch_','l':'labels/labels_batch_','n':'names/names_batch_'}
#transformation dic
TR_CON = {'i':tr_img,'t':tr_img,'':tr_none}
#object to clean and save data
class clean_batch():
	def __init__(self, org_btchs, batched_data, btch_num, train_data=True):
		#keep track of where this will be saved, which batches first went into this
		self.org_btchs = org_btchs
		self.btch_num = btch_num
		self.nms, self.dem_data, self.labels = [],[],[]
		#remember if training or testing/validating data
		self.train_data = train_data
		self.tt  = '' if train_data else 'test-val/'
		#go through batch and parse into 3 data types and labels while maintaining order - IMPT
		#can feed in multiple batches as model data will be bigger
		for nm, atts in batched_data.items():
			self.nms.append(nm)
			x_data = list(set(atts)-{'shipped','sales'})
			self.dem_data.append(list(itemgetter(*x_data)(atts)))
			self.labels.append(max(is_num(atts['shipped']),is_num(atts['sales'])))

	#save data with batch number (save with batch number to match with labels and other data)
	def save_data(self, typs=[]):
		for typ in typs:
			with open('data/'+self.tt+PATH_CON[typ]+str(self.btch_num)+'.json', 'w') as f:
				json.dump(eval(TYP_CON[typ]), f)

	#loads in data from path which comes from data type (WORKS WITH MEGA BATCHES NOT FOR SMALL BATCHES)
	def load_data(self, typs=[]):
		for typ in typs:
			with open('data/'+self.tt+PATH_CON[typ]+str(self.btch_num)+'.json', 'rb') as f:
				exec(TYP_CON[typ]+'=json.load(f)')

	#delete data to save RAM and speed
	def clear_data(self,typs=[]):
		if typs == 'all':
			self.img_data, self.text_data, self.dem_data, self.labels, self.nms = [None]*5
			return
		#references variable via string in typ_con
		for typ in typs:
			exec(TYP_CON[typ]+'=None')

	#this reduces dimensionality of data by running through a decomposition model
	def decompose_data(self, data, reduc_mod, typ='',tr_func=tr_none):
		#name by name to make sure in the same order
		ordered_data = []
		#go through this batches names in order
		for nm in self.nms:
			#if missing value, we need to keep the order still
			if nm not in data:
				if typ == 'i':
					ordered_data.append(np.zeros((MAX_IMG_LEN, MAX_IMG_WIDTH)).flatten())
				elif typ == 't':
					ordered_data.append(nm)
			#apply the transformation function (originally for both data, now just image)
			else:
				ordered_data.append(tr_func(data[nm]))
		#assign the attribute now that it's been decomposed (never actually store raw data permantely)
		exec(TYP_CON[typ]+'=reduc_mod.transform(ordered_data).tolist()')
