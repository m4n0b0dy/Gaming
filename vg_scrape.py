'''this script for scraping from vg chartz.
/home/nbdy/Desktop/Cloud/Projects/game_dir/Gaming
if run on server, this script will keep running even when local pc asleep
'''
#import pdb
#these are some libraries I think I will use
import re
import scraperwiki
import lxml.html
from PIL import Image
import requests
from io import BytesIO
import numpy as np
from IPython.display import display
import json
from time import sleep
from random import shuffle
import os
#used for one recursion function
RECUR_LIM = 15
#used for when to predict success
CHECK_IN = 400

#little write/read json functions
def write_json(data, path):
	with open(path+'.json', 'w') as f:
		json.dump(data, f)

def read_json(path):
	with open(path+'.json') as f:
		return json.load(f)

#used in the pull
def recur_attr_pull(el, fnd='src', tried=0):
	#five child element max search
	if RECUR_LIM == tried:
		return 'N/A'
	#if didn't find it, search next child
	elif fnd not in el.attrib:
		ans = recur_attr_pull(el.getchildren()[0], fnd, tried+1)
	#if found, return the answer
	else:
		return el.attrib[fnd]
	return ans

#this can scrape a full page of video game output (multiple games)
#hate try except but necessary crutch in scraping programming
def scrape_page(url):
	html = scraperwiki.scrape(url)
	root = lxml.html.fromstring(html)
	diff_html = []
	games = {}
	bad = 0
	for tr in root.cssselect("tr"):
		tds = tr.cssselect("td")
		if len(tds) == 12:
			try:
				#pos or ranking
				pos = tds[0].text_content().strip()
				try:
					#go through children until find attribute we're loooking for
					img_url = 'http://www.vgchartz.com/'+recur_attr_pull(tds[1], 'src').strip()
				except:
					#if missing, pull the alt
					img_url = recur_attr_pull(tds[1], 'alt').strip()
				#url to game itself to be used in summary pull
				game_url = 'http://www.vgchartz.com/'+recur_attr_pull(tds[1], 'href').strip()
				title = tds[2].text_content().replace('Read the review','').strip()
				console = recur_attr_pull(tds[3], 'alt').strip()
				publisher = tds[4].text_content().strip()
				developer = tds[5].text_content().strip()
				vg_score = tds[6].text_content().strip()
				critic_score = tds[7].text_content().strip()
				user_score = tds[8].text_content().strip()
				shipped = tds[9].text_content().strip()
				sales = tds[10].text_content().strip()
				date = tds[11].text_content().strip()
				games[title+'_-_'+console] = {'pos':pos,'img_url':img_url,'game_url':game_url,'console':console,'publisher':publisher,
							'developer':developer,'vg_score':vg_score,'critic_score':critic_score,'user_score':user_score,
							'shipped':shipped,'sales':sales,'date':date}
			except Exception as e:
				print(e, bad, len(tds))
				diff_html.append(tds)
				bad +=1
	return games, diff_html

#pulls the text from a game url
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

#pulls image from url
def pull_img(url):
	response = requests.get(url)
	return Image.open(BytesIO(response.content))#.convert('RGB')

def main():
	#ran first scrape succesful, needed to make changes on second
	try:
		all_games = read_json('GAME_INFO')
		bad_urls = read_json('BAD_GAMES')
		print('\n\n---Loaded game info and bad game info from json---\n\n')
	except Exception as e:
		print(e)
		#if the games file is missing
		#load in all the urls to scrape form json file
		all_pages = read_json('ALL_PAGE_URLS')
		#shuffling to not overload server
		shuffle(all_pages)
		#run through pages and scrape basic info
		all_games = {}
		bad_urls = []
		for dex, page in enumerate(all_pages):
			upd_games, bads = scrape_page(page)
			#update and extend our new games
			all_games.update(upd_games)
			bad_urls.extend(bads)

			if dex*100 % CHECK_IN == 0:
				print('Epoch #%s' % dex)
				print('Succesfully scraped %s total games' % len(all_games))
				print('Failed to scrape %s total games' % len(bad_urls))
			sleep(.001)
		#save a json file with all this info, keep over writing it
		#writing all at once, writining continually took way too long
		write_json(all_games, 'GAME_INFO')
		#do the exact same with the bad urls
		write_json(bad_urls, 'BAD_GAMES')
		print('\n\n---Scraped and saved all pages meta data, moving to game images---\n\n')
		#once that is done, run through all_games and scrape image
	sleep(1)
	#once that is done, run through all_games and scrape images
	dex, succ, fail, pre = 0,0,0,0
	#adding this because scraping was succesful for some games already
	already_scraped = set(os.listdir("/home/nbdy/Desktop/Local/Data/game_data/imgs/"))
	for game, atts in all_games.items():
		if 'img_'+game.replace(' ','').replace('/','--')+'.bmp' in already_scraped:
			pre+=1
			continue
		try:
			#scrape the page, save resutls into a image file with name of game
			img = pull_img(atts['img_url'])
			out_path = '/home/nbdy/Desktop/Local/Data/game_data/imgs/img_'+game.replace(' ','').replace('/','--')+'.bmp'
			#save file with gamename as file naem and image as content
			img.save(out_path)
			succ += 1
		except Exception as e:
			print("Couldn't pull %s image from %s" % (game, atts['img_url']))
			print(e)
			fail += 1
		if dex % CHECK_IN == 0:
			print('Epoch #%s' % dex)
			print('Succesfully scraped %s total game images' % succ)
			print('Succesfully loaded %s total game images' % pre)
			print('Failed to scrape %s total games images' % fail)
		dex +=1


	dex, succ, fail, pre = 0,0,0,0
	#adding this because scraping was succesful for some games already
	already_scraped = set(os.listdir("/home/nbdy/Desktop/Local/Data/game_data/txts/"))
	for game, atts in all_games.items():
		if 'txt_'+game.replace(' ','').replace('/','--')+'.json' in already_scraped:
			pre+=1
			continue
		try:
			#scrape the page, save resutls into a text file with name of game
			txt = pull_txt_sum(atts['game_url'])
			#had to add this because got games with spaces in it (there could be / too) MAKE SURE YOU REMEMBER THIS AT LOAD TIME
			out_path = '/home/nbdy/Desktop/Local/Data/game_data/txts/txt_'+game.replace(' ','').replace('/','--')
			#save file with gamename as file naem and txt as content
			write_json(txt, out_path)
			succ += 1
		except Exception as e:
			print("Couldn't pull %s description from %s" % (game, atts['game_url']))
			print(e)
			fail += 1
		if dex % CHECK_IN == 0:
			print('Epoch #%s' % dex)
			print('Succesfully scraped %s total game descriptions' % succ)
			print('Succesfully loaded %s total game images' % pre)
			print('Failed to scrape %s total games descriptions' % fail)
		dex +=1

	print('\n\n---Scraped all game texts---')

if __name__ == "__main__":
	main()