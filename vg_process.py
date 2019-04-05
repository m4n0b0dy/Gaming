import pickle
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import time
import pickle
import scraperwiki
import lxml.html

def pull_bnw_photo(url):
	response = requests.get(url)
	img = Image.open(BytesIO(response.content)).convert('L')
	np_img = np.array(img)/255
	return np_img

def save_dic(dic, nm='g'):
	with open(nm+'.pickle', 'wb') as handle:
		pickle.dump(dic, handle, protocol=pickle.HIGHEST_PROTOCOL)

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

def pull_pic(url):
	try:
		img_arr = pull_bnw_photo(url)
	except:
		img_arr = np.array([[0,0],[0,0]])
def pull_summary(url, title):
	try:
		summary = pull_txt_sum(url)
	except:
		summary = title

with open('games.pickle', 'rb') as h:
	games = pickle.load(h)

#make game, scrape pics and summary
games_complete = games
dex = 0
all_games = len(games)
start_time = time.time()
for dex, (nm, ats) in enumerate(games.items()):
	if dex % 100 ==0:
		print("Page#: %s of %s - %s seconds" % (dex,all_games,round(time.time() - start_time,4)))
		save_dic(games_complete,'games_complete')
	games_complete[nm].update({'img_arr':pull_pic(ats['img_link']), 'desc':pull_summary(ats['game_url'], nm)})
save_dic(games_complete,'games_complete')