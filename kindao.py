# -*- coding: utf-8 -*-

import requests, sqlite3, os, sys, md5
import xml.dom.minidom as DOM

VOCAB_PATH = "/Volumes/Kindle/system/vocabulary/"
VOCAB_NAME = "vocab.db"

U_A = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.132 Safari/537.36"
C_T = "application/x-www-form-urlencoded"

HOME_LOGIN = "http://account.youdao.com/login?service=dict&back_url=http://dict.youdao.com/wordbook/wordlist%3Fkeyfrom%3Dnull"
API_LOGIN = "https://logindict.youdao.com/login/acc/login"
FORM_LOGIN = {
	"username" : "",
	"password" : "",
	"product"  : "DICT",
	"app" : "web",
	"tp" : "urstoken",
	"cf" : 3,
	"fr" : 1,
	"type" : 1,
	"ru" : "http://dict.youdao.com/wordbook/wordlist?keyfrom=null",
	"um" : True	
}
HEADER_LOGIN = {
	"User-Agent" : U_A,
	"Content-Type" : C_T,
	"Origin" : "http://account.youdao.com",
	"Host" : "logindict.youdao.com",
	"Referer" : "http://account.youdao.com/login?service=dict&back_url=http://dict.youdao.com/wordbook/wordlist%3Fkeyfrom%3Dnull",
	"Cookie" : ""
}

API_WORDBOOK = "http://dict.youdao.com/wordbook/wordlist?action=add"
FORM_WORDBOOK = {
	"word" : "",
	"phonetic" : "",
	"desc" : "",
	"tags" : ""
}
HEADER_WORDBOOK = {
	"User-Agent" : U_A,
	"Content-Type" : C_T,
	"Origin" : "http://dict.youdao.com",
	"Host" : "dict.youdao.com",
	"Referer" : "http://dict.youdao.com/wordbook/wordlist?keyfrom=null&product=DICT&tp=urstoken&s=true",
	"Cookie" : ""
}

API_TRANSLATION = "http://dict.youdao.com/fsearch?q="

def login(username, password):
	resp_home = requests.get(HOME_LOGIN)
	HEADER_LOGIN["Cookie"] = resp_home.headers["Set-Cookie"]
	FORM_LOGIN["username"] = username
	FORM_LOGIN["password"] = md5.new(password).hexdigest()
	resp_login = requests.post(API_LOGIN, data=FORM_LOGIN, headers=HEADER_LOGIN, allow_redirects=False)
	return resp_login.headers["Set-Cookie"]

def addToWordbook(word, phonetic, desc, tags, cookie):
	HEADER_WORDBOOK["Cookie"] = cookie
	FORM_WORDBOOK["word"] = word
	FORM_WORDBOOK["phonetic"] = phonetic
	FORM_WORDBOOK["desc"] = desc
	FORM_WORDBOOK["tags"] = tags
	requests.post(API_WORDBOOK, data=FORM_WORDBOOK, headers=HEADER_WORDBOOK, allow_redirects=False)

def getTranslation(word):
	resp = requests.get(API_TRANSLATION + word)
	dom = DOM.parseString(resp.content)
	phonetic = ""
	try:
		phonetic = dom.getElementsByTagName("phonetic-symbol")[0].childNodes[0].nodeValue
	except Exception, e:
		pass
	translation = "\n".join([t.childNodes[0].nodeValue for t in dom.getElementsByTagName("content")])
	return (phonetic, translation)

def main():
	if len(sys.argv) != 3:
		print "Parameters Wrong"
		return

	# check kindle volcab
	if not os.path.isfile(VOCAB_PATH + VOCAB_NAME):
		print "Please Connect Your Kindle to Your Computer"
		return
	os.system("cp %s %s" % (VOCAB_PATH + VOCAB_NAME, os.path.dirname(os.path.abspath(__file__))))
	conn = sqlite3.connect(VOCAB_NAME)

	# login youdao
	cookie = login(sys.argv[1], sys.argv[2])

	# add to wordbook
	cursor = conn.cursor()
	cursor.execute("SELECT word_key, book_key, usage FROM LOOKUPS")
	lookups = cursor.fetchall()
	for lookup in lookups:
		word = lookup[0].split(":")[1]
		cursor.execute('SELECT id, title, authors FROM BOOK_INFO WHERE id="%s"' % (lookup[1]))
		book_info = cursor.fetchone()
		book = "<%s>, %s" % (book_info[1], book_info[2])
		translation = getTranslation(word)
		desc = "%s\n----------\n%s\n%s\n" % (translation[1], lookup[2], book)
		addToWordbook(word, translation[0], desc, "kindle", cookie)
		print "Add Word [%s]" % (word)

	cursor.close()
	conn.close()

if __name__ == '__main__':
	main()