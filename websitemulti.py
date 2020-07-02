import requests
import tldextract
from bs4 import BeautifulSoup
import time
import urllib.request
from textblob import TextBlob
from spellchecker import SpellChecker
import subprocess
from htmldate import find_date
import re
import language_tool_python
import spacy
import csv
from sys import getsizeof
from multiprocessing import Process
spell = SpellChecker()
print("Enter URL")
url = input()
response = requests.get(url)
with open('info.csv', 'w', newline='') as file:
		writer = csv.writer(file)
		writer.writerow(['TLD', 'INLINKS', 'OUTLINKS', 'PAGELOAD TIME', 'IMAGE TEXT RATIO', 'SUBJECTIVITY', 'POLARITY', 'ADS', 'SPELLING ERRORS', 'LAST MODIFIED', 'CONTACT', 'CORRECT GRAMMAR', 'NOUN', 'VERB', 'ADJECTIVE', 'ADVERB'])
soup = BeautifulSoup(response.text, 'lxml')
def gettld (url):
	tld = tldextract.extract(url).suffix
	return tld
def getdomain (url):
	tld = tldextract.extract(url).suffix
	tld = '.' + tld
	domain = tldextract.extract(url).domain + tld
	return domain
def getoutlinks (url):
	global soup
	internal = []
	external = []
	domain = getdomain(url)
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
	return (internal, external)
def getpageloadtime (url):
	stream = urllib.request.urlopen(url)
	start = time.time()
	stream.read()
	end = time.time()
	return round(start - end, 3)
def getimagesize (url):
	global soup	
	domain = getdomain(url)
	img_tags = soup.find_all('img')
	imglinks = [img['src'] for img in img_tags]
	imgsize = 0
	for img in imglinks:
		if img.startswith('/'):
			if tldextract.extract(img).suffix != tldextract.extract(url).suffix:
				img = 'https://' + domain + img
			else:
				img = 'https:' + img
		try:
			imgsize = imgsize + len(urllib.request.urlopen(img).read())
		except:
			continue
	return imgsize
def getplaintextsize (url):
	global soup
	for script in soup(['script', 'style']):
		script.extract()
	text = soup.get_text()
	#return getsizeof(soup)
	return getsizeof(text)
def getratio (url):
	imgsize = getimagesize(url)
	ptsize = getplaintextsize(url)
	if imgsize == 0:
		return 100
	else:
		ratio = imgsize/(imgsize + ptsize) * 100
		return ratio
def getsentiment (url):
	global soup
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
		ansp = 'Positive'
	elif navg < avg:
		ansp = 'Negative'
	else:
		if pavg == 0:
			ansp = 'Negative'
		elif navg == 0:
			ansp = 'Positive'
		else:
			ansp = 'Neutral'
	if subjective > 0.3:
		anss = 'Subjective'
	else:
		anss = 'Objective'
	return (anss, ansp)
def getads (url):
	global soup
	adrespon = requests.get('https://pgl.yoyo.org/as/serverlist.php?hostformat=adblockplus')
	adso = BeautifulSoup(adrespon.text, 'html.parser')
	lines = adso.text.split('\n')
	adslist = []
	for line in lines:
		if line.startswith('||'):
			adslist.append(getdomain(line[2:-1]))
	anchor = soup.find_all('a')
	images = soup.find_all('img')
	checklist = []
	for tag in anchor:
		tag = tag.get('href')
		if tag:
	 		checklist.append(getdomain(tag))
	# for image in images:
	# 	image = image.get('src')
	# 	if image:
	# 		checklist.append(getdomain(image))
	adcount = 0
	for tag in checklist:
		if tag in adslist:
			adcount = adcount + 1
	return adcount
def getspellingerrors (url):
	global soup
	wordlist = []
	paras = soup.find_all('p')
	for para in paras:
		para = para.text
		p = para.split(' ')
		for word in p:
			s = ''
			for c in word:
				if c.isalpha():
					s = s + c
			if s:
				wordlist.append(s)

	misspelled = spell.unknown(wordlist)
	count = 0
	for word in misspelled:
		if spell.correction(word) != word:
			count = count + 1
	return count
def getdatetime (url):
	global soup
	d = ['Date', 'date']
	lm = ['last-modified', 'last-Modified', 'Last-Modified', 'Last-modified']
	out = subprocess.Popen(['https', '-h', url], stdout = subprocess.PIPE)
	out = out.stdout.readlines()
	flag = False
	for line in out:
		for l  in lm:
			if l in str(line):
				return line.decode("utf-8")[20::]
				flag = True
				break
	if flag == False:
		if find_date(url):
			return find_date(url)
			flag = True
	if flag == False:
		for line in out:
			for date in d:
				if date in str(line):
					return line.decode("utf-8")[11::]
def getemail (url):
	global soup
	for script in soup(['script', 'style']):
		script.extract()
	text = soup.get_text()
	regexemail = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
	lines = text.split('\n')
	emails = []
	for line in lines:
		words = line.split(' ')
		for word in words:
			if re.search(regexemail, word):
				emails.append(word)
	return emails
def checkgrammar (url):
	global soup
	tool = language_tool_python.LanguageTool('en-US')
	for script in soup(['script', 'style']):
		script.extract()
	text = soup.get_text()
	lines = text.split('.')
	count = 0
	for line in lines:
		matches = tool.check(line)
		count = count + len(matches)
	if count > 0:
		return 'No'
	else:
		return 'Yes'
def getpos (url):
	global soup
	poss = ['NOUN', 'VERB', 'ADJ', 'ADV']
	count = {'NOUN': 0, 'VERB' : 0, 'ADJ' : 0, 'ADV' : 0}
	nlp = spacy.load('en_core_web_sm')
	for script in soup(['script', 'style']):
		script.extract()
	text = soup.get_text()
	doc = nlp(text)
	for token in doc:
		if token.pos_ in poss:
			count[token.pos_] = count[token.pos_] + 1
	return count
row1 = []
row2 = []
def p1 (url) :
	global row1
	tld = gettld(url)
	print(tld)
	links = getoutlinks(url)
	inlinks = len(links[0])
	print(inlinks)
	outlinks = len(links[1])
	print(outlinks)
	pltime = getpageloadtime(url)
	print(pltime)
	itratio = getratio(url)
	print(itratio)
	sentiment = getsentiment(url)
	subjective = sentiment[0]
	print(subjective)
	polarity = sentiment[1]
	print(polarity)
	row1 = [tld, inlinks, outlinks, pltime, itratio, subjective, polarity]
def p2 (url):
	global row2
	ads = getads(url)
	print(ads)
	spellerror = getspellingerrors(url)
	print(spellerror)
	lastmod = getdatetime(url)
	print(lastmod)
	contact = getemail(url)
	print(contact)
	grammar = checkgrammar(url)
	print(grammar)
	pos = getpos(url)
	nouns = pos['NOUN']
	print(nouns)
	verb = pos['VERB']
	print(verb)
	adjective = pos['ADJ']
	print(adjective)
	adverb = pos['ADV']
	print(adverb)
	row2 = [ads, spellerror, lastmod, contact, grammar, nouns, verb, adjective, adverb]
def writetocsv (url):
# 	tld = gettld(url)
# 	print(tld)
# 	links = getoutlinks(url)
# 	inlinks = len(links[0])
# 	print(inlinks)
# 	outlinks = len(links[1])
# 	print(outlinks)
# 	pltime = getpageloadtime(url)
# 	print(pltime)
# 	itratio = getratio(url)
# 	print(itratio)
# 	sentiment = getsentiment(url)
# 	subjective = sentiment[0]
# 	print(subjective)
# 	polarity = sentiment[1]
# 	print(polarity)
# 	ads = getads(url)
# 	print(ads)
# 	spellerror = getspellingerrors(url)
# 	print(spellerror)
# 	lastmod = getdatetime(url)
# 	print(lastmod)
# 	contact = getemail(url)
# 	print(contact)
# 	grammar = checkgrammar(url)
# 	print(grammar)
# 	pos = getpos(url)
# 	nouns = pos['NOUN']
# 	print(nouns)
# 	verb = pos['VERB']
# 	print(verb)
# 	adjective = pos['ADJ']
# 	print(adjective)
# 	adverb = pos['ADV']
# 	print(adverb)
# 	row = [tld, inlinks, outlinks, pltime, itratio, subjective, polarity, ads, spellerror, lastmod, contact, grammar, nouns, verb, adjective, adverb]
	row = row1 + row2
	with open('info.csv', 'a+', newline = '') as file:
		writer = csv.writer(file)
		writer.writerow(row)
if __name__=='__main__':
	pr1 = Process(target = p1(url))
	pr1.start()
	pr2 = Process(target = p2(url))
	pr2.start()
	pr1.join()
	pr2.join()
writetocsv(url)