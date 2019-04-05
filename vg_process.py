import numpy as np
from PIL import Image
import requests
from io import BytesIO
import time
import scraperwiki
import lxml.html
import json
from random import shuffle
from os import listdir
from os.path import isfile, join
btch_size = 20

#pulls a photo and convertsit to black and white
def pull_bnw_photo(url):
	response = requests.get(url)
	img = Image.open(BytesIO(response.content)).convert('L')
	np_img = np.array(img)/255
	return np_img.tolist()

#simple function to save dic as json file so many issues with the pickle
def save_j(dic, nm='g'):
	with open(nm+'.json', 'w') as fp:
		json.dump(dic, fp)
#pulls a games summary
def pull_txt_sum(url):
	html = scraperwiki.scrape(url)
	root = lxml.html.fromstring(html)
	gbbs = root.cssselect("div#gameBodyBox")
	for gb in gbbs:
		gb_text = gb.text_content()
		#should be the first one every time but just in case
		if 'Summary' in gb_text:
			desc = gb_text.replace('Summary','')
			desc = desc.strip()
			return desc
	return ''
#these two are try except wrapper functions to not distribut flow
def pull_pic(url):
	try:
		return pull_bnw_photo(url)
	except:
		return [[0,0],[0,0]]
def pull_summary(url, title):
	try:
		return pull_txt_sum(url)
	except:
		return title

#needed to batch these dictionaries as it was getting pretty large
#produces a list of n dictionaries
def batch_dic(dic):
	kys = np.array(list(dic.keys()))
	#splitting with numpy, did it to make sure every game included
	splits = np.array_split(kys,btch_size)
	ret_dics = []
	for split in splits:
		ret_dics.append(dict((k, dic[k]) for k in split))
	return ret_dics

#pull names of every completed game so far, once I've run this script a couple times, I don't want to have to re run previously used games
def pull_completed(path):
	complete_game_files = [f for f in listdir(path) if isfile(join(path, f))]
	complete_games = []
	for complete_game_file in complete_game_files:
		complete_games.extend(list(complete_game_file))
	return set(complete_games)

#run a dictionary, do the function we want to do and save it as a json file
def run_and_save(start_dic, attr, attr_func, l_nm=0):
	ret_games = {}
	for nm, ats in start_dic.items():
		ret_games[nm] = attr_func(ats[attr])
	save_j(ret_games,attr+'/'+l_nm+'-complete')

#unlike other script, this uses batches as files were much larger and saving them all in one file/storing all at once in RAM was killing my pc
#if batched games already exists, load that, otherwise, load in the original games json file, clean out the bad data, batch it, and save the list of batches
try:
	with open('games_as_%s_batches.json' % btch_size, 'rb') as h:
		batches = json.load(h)
	print('Loaded %s game batches' & btch_size)
except:
	#load all of our game data (doesn't have images or desc yet)
	with open('org_games.json', 'rb') as h:
		all_games = json.load(h)
	#clean it to make sure we aren't scraping data we can't use in analysis
	games = {}
	for k, v in unloaded_games.items():
		if v['sales'] != 'N/A' or v['shipped'] != 'N/A':
			games[k] = v
	#divide it up into batches
	batches = batch_dic(games)
	#save batches
	save_j(batches, nm='games_as_%s_batches' % btch_size)
	print('Wrote %s game batches' & btch_size)

#some stuff I like to print out but don't want to load every time
len_games = sum([len(batch) for batch in batches])
len_bathces = len(batches)
start_time = time.time()

completed_game_imgs = pull_completed('img_link/')
#completed_game_sums = pull_completed('game_url/')

#go through each batch
for dex, dic_seg in enumerate(batches):
	#if we loaded the batches, want to make sure we don't re run games
	if not set(dic_seg.keys()) < completed_game_imgs:
		print("Batch#: %s of %s, Batch Size %s of %s total games - %s seconds" % (dex,len_bathces,len(dic_seg),len_games,round(time.time() - start_time,4)))
		#run through a batches game image links, download and save
		run_and_save(dic_seg, 'img_link', pull_pic, str(dex))

#for dex, dic_seg in enumerate(batches):
	#if we loaded the batches, want to make sure we don't re run games
	#if not set(dic_seg.keys()) < completed_game_sums:
	#	print("Batch#: %s of %s, Batch Size %s of %s total games - %s seconds" % (dex,len_bathces,len(dic_seg),len_games,round(time.time() - start_time,4)))
		#run through summaries, download and save
	#	run_and_save(dic_seg, 'game_url', pull_summary, str(dex))