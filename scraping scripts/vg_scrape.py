import scraperwiki
import lxml.html
import numpy as np
import time
import json
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

#scrape a search page, pull all the games and save desired content
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

#simple function to save dic as json file so many issues with the pickle
def save_dic(dic, nm='games'):
	with open(nm+'.json', 'w') as fp:
		json.dump(dic, fp)

page_urls = []
for dex in range(1,280):
	page_urls.append('http://www.vgchartz.com/games/games.php?page='+str(dex)+'&results=200&name=&console=&keyword=&publisher=&genre=&order=TotalSales&ownership=Both&boxart=Both&banner=Both&showdeleted=&region=All&goty_year=&developer=&direction=&showtotalsales=1&shownasales=0&showpalsales=0&showjapansales=0&showothersales=0&showpublisher=1&showdeveloper=1&showreleasedate=1&showlastupdate=0&showvgchartzscore=1&showcriticscore=1&showuserscore=1&showshipped=1&alphasort=&showmultiplat=No')

#this doesn't use batches because it is much smaller and faster, just keeps writing to same file
game_pages = {}
bads = []
start_time = time.time()
for dex, page in enumerate(page_urls):
	if dex % 10 ==0:
		print("Page#: %s of %s - %s seconds - Scraped:%s, Failed:%s" % (dex,280,round(time.time() - start_time,4),len(game_pages),len(bads)))
		save_dic(game_pages)
	page_pulled, bad = scrape_page(page)
	if len(page_pulled) != 200:
		print(page)
	game_pages.update(page_pulled)
	bads.extend(bad)
	time.sleep(.00001)
save_dic(game_pages)