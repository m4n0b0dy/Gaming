import json
game_ls = []
last_page = 285
for i in range(1,last_page+1):
	url = 'http://www.vgchartz.com/games/games.php?page='+str(i)+'&results=200&name=&console=&keyword=&publisher=&genre=&order=TotalSales&ownership=Both&boxart=Both&banner=Both&showdeleted=&region=All&goty_year=&developer=&direction=DESC&showtotalsales=1&shownasales=0&showpalsales=0&showjapansales=0&showothersales=0&showpublisher=1&showdeveloper=1&showreleasedate=1&showlastupdate=0&showvgchartzscore=1&showcriticscore=1&showuserscore=1&showshipped=1&alphasort=&showmultiplat=No'	
	game_ls.append(url)
	print(i)
wrt = 'ALL_PAGE_URLS.json'
with open(wrt, 'w') as f:
	json.dump(game_ls, f)