import pickle
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import time
import pickle
import scraperwiki
import lxml.html

def confloat(value):
	try:
		return float(value)
	except ValueError:
		return 0

def pull_bnw_photo(url):
	response = requests.get(url)
	img = Image.open(BytesIO(response.content)).convert('L')
	np_img = np.array(img)/255
	return np_img

def save_dic(dic, nm='g'):
	with open(nm+'.pickle', 'wb') as handle:
		pickle.dump(dic, handle, protocol=pickle.HIGHEST_PROTOCOL)

def pull_summary(url):
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

class game():
	def __init__(self,title,score,date,developer,url,rank,publisher,sales,shipped,user_score,vg_score):
		self.title=title
		self.score=score
		self.date=date
		self.developer=developer
		self.url=url
		self.rank=rank
		self.publisher = publisher
		sales_chk = max(confloat(sales), confloat(shipped))
		self.sales = sales_chk if sales_chk != 0 else np.nan
		self.user_score=user_score
		self.vg_score=vg_score
	def pull_pic(self, url):
		try:
			self.img_arr = pull_bnw_photo(url)
		except:
			self.img_arr = np.array([[0,0],[0,0]])
	def pull_summary(self):
		try:
			self.summary = pull_summary(self.url)
		except:
			self.summary = self.title

with open('games.pickle', 'rb') as h:
	games = pickle.load(h)

#make game, scrape pics and summary
game_objs = {}
bads = []
dex = 0
all_games = len(games)
start_time = time.time()
for nm, ats in games.items():
	if dex % 500 ==0:
		print("Page#: %s of %s - %s seconds - Scraped:%s, Failed:%s" % (dex,all_games,round(time.time() - start_time,4),len(game_objs),len(bads)))
		save_dic(game_objs,'game_objects')
	try:
		game_obj = game(nm,ats['critic_score'],ats['date'],ats['developer'],ats['game_url'],ats['pos'],ats['publisher'],
					   ats['sales'].replace('m',''),ats['shipped'].replace('m',''),ats['user_score'],ats['vg_score'])
		game_obj.pull_pic(ats['img_link'])
		game_obj.pull_summary()
		game_objs[nm] = game_obj
	except Exception as e:
		print(nm,' ',e)
		bads.append(nm)
	dex +=1
	time.sleep(.0000001)
save_dic('game_objects')