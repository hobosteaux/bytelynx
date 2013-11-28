import urllib3

def check_in():
	# Commented out to be nice while building / testing lots.
	#http = urllib3.PoolManager()
	#r = http.request('GET', 'http://myip.dnsdynamic.org/')
	#return str(r.data, 'UTF-8')

	return '127.0.0.1'

if __name__ == 'main':
	print(check_in())
