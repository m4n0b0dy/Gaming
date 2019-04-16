#this is just for the demo
import scraperwiki
import lxml.html
from PIL import Image
import requests
from io import BytesIO
import numpy as np
from IPython.display import display
RECUR_LIM = 15

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
					img_link = 'http://www.vgchartz.com/'+recur_attr_pull(tds[1], 'src').strip()
				except:
					#if missing, pull the alt
					img_link = recur_attr_pull(tds[1], 'alt').strip()
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
				games[title+'-:-'+console] = {'pos':pos,'img_link':img_link,'game_url':game_url,'console':console,'publisher':publisher,
							'developer':developer,'vg_score':vg_score,'critic_score':critic_score,'user_score':user_score,
							'shipped':shipped,'sales':sales,'date':date}
			except Exception as e:
				print(e, bad, len(tds))
				diff_html.append(tds)
				bad +=1
	return games, diff_html