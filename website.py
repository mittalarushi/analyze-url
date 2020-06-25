import requests
import tldextract
from bs4 import BeautifulSoup
import time
import urllib.request
from textblob import TextBlob
print("Enter URL")
urlinput = input()
internal = []
external = []
def gettld (url):
	tld = tldextract.extract(url).suffix
	return tld
def getdomain (url):
	tld = tldextract.extract(url).suffix
	tld = '.' + tld
	domain = tldextract.extract(url).domain + tld
	return domain
def getoutlinks (url):
	global internal, external
	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'lxml')
	links = soup.find_all('a')
	for link in links:
		link = link.get('href')
		if link:
			if link.startswith('#'):
				continue
			if link.startswith('/'):
				internal.append(domain + link)
			elif getdomain(link) == domain:
				internal.append(link)
			else:
				external.append(link)
	internal = set(internal)
	external = set(external)
	return len(external)
def getpageloadtime (url):
	stream = urllib.request.urlopen(url)
	start = time.time()
	stream.read()
	end = time.time()
	return round(start - end, 3)
def getimagesize (url):	
	domain = getdomain(url)
	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'html.parser')
	img_tags = soup.find_all('img')
	imglinks = [img['src'] for img in img_tags]
	imgsize = 0
	for img in imglinks:
		if img.startswith('/'):
			if tldextract.extract(img).suffix != tldextract.extract(url).suffix:
				img = 'https://' + domain + img
			else:
				img = 'https:' + img
		imgsize = imgsize + len(urllib.request.urlopen(img).read())
	return imgsize
def getplaintextsize (url):
	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'html.parser')
	for script in soup(['script', 'style']):
		script.extract()
	text = soup.get_text()
	return getsizeof(soup)
def getratio (url):
	imgsize = getimagesize(url)
	ptsize = getplaintextsize(url)
	ratio = imgsize/(imgsize + ptsize) * 100
	return ratio
def getsentiment (url):
	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'html.parser')
	text = soup.find_all('p')
	neg = 0
	pos = 0
	neutral = 0
	cneg = 0
	cpos = 0
	cneutral = 0
	sub = 0
	csub = 0
	for para in text:
		p = TextBlob(para.text)
		polar = p.sentiment.polarity
		subj = p.sentiment.subjectivity
		sub = sub + subj
		csub = csub + 1
		if polar < -0.2:
			cneg = cneg + polar
			neg = neg + polar
		elif polar > 0.2:
			cpos = cpos + 1
			pos = pos + polar
		else:
			cneutral = cneutral + 1
			neutral = neutral + polar
	subjective = sub/csub
	if cpos > 0:
		pavg = pos/cpos
	else:
		pavg = 0
	if cneg > 0:
		navg = neg/cneg
	else:
		navg = 0
	if cneutral > 0:
		neutralavg = neutral/cneutral
	else:
		neutralavg = 0
	avg = (navg + pavg + neutralavg)/(cpos + cneg + cneutral)
	if pavg > avg:
		print('Positive')
	elif navg < avg:
		print('Negative')
	else:
		if pavg == 0:
			print('Negative')
		elif navg == 0:
			print('Positive')
		else:
			print('Neutral')
	if subjective > 0.3:
		print('Subjective')
	else:
		print('Objective')