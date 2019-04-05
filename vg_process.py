import numpy as np
from PIL import Image
import requests
from io import BytesIO
import time
import scraperwiki
import lxml.html
import json
from os import listdir
from os.path import isfile, join
#more comments, a bit more complex than my other scrape
btch_size = 200
attr_to_pull = 'img_link'

#pulls a photo and convertsit to black and white
def pull_bnw_photo(url):
	response = requests.get(url)
	img = Image.open(BytesIO(response.content)).convert('L')
	#rounding to minimize storage use
	np_img = np.around(np.array(img)/255, decimals=4)
	return np_img.tolist()

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

#simple function to save dic as json file so many issues with the pickle
def save_j(dic, nm='g', do='w'):
	with open(nm+'.json', do) as fp:
		json.dump(dic, fp)

#these two are try except wrapper functions to not distribut flow
def pull_pic(url):
	try:
		return pull_bnw_photo(url)
	except:
		return [[0.0,0.0],[0.0,0.0]]
def pull_summary(url):
	try:
		return pull_txt_sum(url)
	except:
		return url

#needed to batch these dictionaries as it was getting pretty large, produces a list of n dictionaries
#IMPT, this shuffles, so everytime this is remade, order is different. Cna't compare to previously written files with different batch
def batch_dic(dic):
	kys = np.array(list(dic.keys()))
	np.random.shuffle(kys)
	#splitting with numpy, did it to make sure every game included
	splits = np.array_split(kys,btch_size)
	ret_dics = []
	for split in splits:
		ret_dics.append(dict((k, dic[k]) for k in split))
	return ret_dics

#pull names of every completed game so far, once I've run this script a couple times, I don't want to have to re run previously used games
#takes a while so going to save an external list as well
def pull_completed(path):
	file_nms = [f for f in listdir(path) if isfile(join(path, f))]
	complete_games = []
	for file_nm in file_nms:
		with open(path+file_nm, 'rb') as h:
			complete_game_file = json.load(h)
		complete_games.extend(list(complete_game_file.keys()))
		print('Loaded completed game library %s'%path+file_nm)
	return complete_games

#run a dictionary, do the function we want to do and save it as a json file
def run_and_save(start_dic, attr, attr_func, l_nm=0):
	ret_games = {}
	for nm, ats in start_dic.items():
		ret_games[nm] = attr_func(ats[attr])
	save_j(ret_games,attr+'/'+l_nm+'-complete')

#unlike other script, this uses batches as files were much larger and saving them all in one file/storing all at once in RAM was killing my pc
#if batched games already exists, load that, otherwise, load in the original games json file, clean out the bad data, batch it, and save the list of batches
#wanted to keep this the same for train tst splitting
try:
	with open('games_as_%s_batches.json' % btch_size, 'rb') as h:
		batches = json.load(h)
	print('Loaded %s game batches' % btch_size)
except:
	#load all of our game data (doesn't have images or desc yet)
	with open('org_games.json', 'rb') as h:
		all_games = json.load(h)
	#clean it to make sure we aren't scraping data we can't use in analysis
	games = {}
	for k, v in all_games.items():
		if v['sales'] != 'N/A' or v['shipped'] != 'N/A':
			games[k] = v
	#divide it up into batches
	batches = batch_dic(games)
	#save batches
	save_j(batches, nm='games_as_%s_batches' % btch_size)
	print('Wrote %s game batches' % btch_size)

#look for a completed games list, if it doesn't exist make one
try:
	with open(attr_to_pull+'/completed_games.json', 'rb') as f:
		completed_games = json.load(f)
	print('Loaded %s list of completed_games' % attr_to_pull)
except:
	#this takes a while with all that json so I wanted to try to shorten it
	completed_games = pull_completed(attr_to_pull+'/')
	save_j(completed_games, attr_to_pull+'/completed_games')
	print('Wrote %s list of completed_games' % attr_to_pull)

#feed in function based on what we're pulling
func_dic = {'img_link':pull_pic, 'game_url':pull_summary}
#some stuff I like to print out but don't want to load every time
len_games = sum([len(batch) for batch in batches])
len_bathces = len(batches)
start_time = time.time()

#go through each batch
for dex, dic_seg in enumerate(batches):
	#if we loaded the batches, want to make sure we don't re run games
	if not (set(dic_seg.keys()) < set(completed_games) or set(dic_seg.keys()) == set(completed_games)):
		print("Batch #%s of %s, Batch Size %s of %s total games - %s seconds" % (dex,len_bathces,len(dic_seg),len_games,round(time.time() - start_time,4)))
		#run through a batches game image links or game urls, download and save
		run_and_save(dic_seg, attr_to_pull, func_dic[attr_to_pull], str(dex))
		save_j(list(dic_seg.keys())+completed_games,attr_to_pull+'/completed_games')
	else:
		print("Batch #%s is already loaded in %s/" % (str(dex),attr_to_pull))