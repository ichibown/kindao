# -*- coding: utf-8 -*-

import requests, sqlite3, os, sys, md5, json
import xml.dom.minidom as DOM

VOCAB_PATH = "/Volumes/Kindle/system/vocabulary/"
VOCAB_NAME = "vocab.db"

U_A = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.132 Safari/537.36"
C_T = "application/x-www-form-urlencoded"

HOME_LOGIN = "http://account.youdao.com/login?service=dict&back_url=http://dict.youdao.com/wordbook/wordlist%3Fkeyfrom%3Dnull"
HOME_LOGIN_LE = "http://langeasy.com.cn/"
API_LOGIN = "https://logindict.youdao.com/login/acc/login"
API_LOGIN_LE = "http://langeasy.com.cn/login.action"
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
FORM_LOGIN_LE = {
	"name" : "",
	"passwd" : "",
}
HEADER_LOGIN_LE = {
	"User-Agent" : U_A,
	"Content-Type" : C_T,
	"Origin" : "http://langeasy.com.cn",
	"Host" : "langeasy.com.cn",
	"Upgrade-Insecure-Requests" : 1,
	"Referer" : "http://langeasy.com.cn/",
	"Cookie" : "",
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
API_WORDBOOK_LE = "http://langeasy.com.cn/insertNewWord.action"
FORM_WORDBOOK = {
	"word" : "",
	"phonetic" : "",
	"desc" : "",
	"tags" : ""
}
FORM_WORDBOOK_LE = {
	"newwordlist" : ""
}
FROM_NEWWORDLIST_LE = {
	"word" : "",
	"course" : "*",
	"wordidx" : "*",
	"infoidx" : "100",
	"selection" : "*",
	"info" : "",
	"opcode" : "1"
}
HEADER_WORDBOOK = {
	"User-Agent" : U_A,
	"Content-Type" : C_T,
	"Origin" : "http://dict.youdao.com",
	"Host" : "dict.youdao.com",
	"Referer" : "http://dict.youdao.com/wordbook/wordlist?keyfrom=null&product=DICT&tp=urstoken&s=true",
	"Cookie" : ""
}
HEADER_WORDBOOK_LE = {
	"User-Agent" : U_A,
	"Content-Type" : C_T,
	"Origin" : "http://langeasy.com.cn",
	"Host" : "langeasy.com.cn",
	"Referer" : "http://langeasy.com.cn/newword.action",
	"Cookie" : ""	
}

API_TRANSLATION = "http://dict.youdao.com/fsearch?q="

# login youdao
def login(username, password):
	resp_home = requests.get(HOME_LOGIN)
	HEADER_LOGIN["Cookie"] = resp_home.headers["Set-Cookie"]
	FORM_LOGIN["username"] = username
	FORM_LOGIN["password"] = md5.new(password).hexdigest()
	resp_login = requests.post(API_LOGIN, data=FORM_LOGIN, headers=HEADER_LOGIN, allow_redirects=False)
	return resp_login.headers["Set-Cookie"]

# login langeasy
def loginLE(username, password):
	resp_home = requests.get(HOME_LOGIN_LE)
	HEADER_LOGIN_LE["Cookie"] = resp_home.headers["Set-Cookie"]
	FORM_LOGIN_LE["name"] = username
	FORM_LOGIN_LE["passwd"] = password
	resp_login = requests.post(API_LOGIN_LE, data=FORM_LOGIN_LE, headers=HEADER_LOGIN_LE, allow_redirects=False)
	return resp_login.headers["Set-Cookie"]

def addToWordbook(word, phonetic, desc, tags, cookie):
	HEADER_WORDBOOK["Cookie"] = cookie
	FORM_WORDBOOK["word"] = word
	FORM_WORDBOOK["phonetic"] = phonetic
	FORM_WORDBOOK["desc"] = desc
	FORM_WORDBOOK["tags"] = tags
	requests.post(API_WORDBOOK, data=FORM_WORDBOOK, headers=HEADER_WORDBOOK, allow_redirects=False)

def addToWordbookLE(word, desc, cookie):
	HEADER_WORDBOOK_LE["Cookie"] = cookie
	FROM_NEWWORDLIST_LE["word"] = word
	FROM_NEWWORDLIST_LE["info"] = desc
	FORM_WORDBOOK_LE["newwordlist"] = json.dumps(FROM_NEWWORDLIST_LE)
	requests.post(API_WORDBOOK_LE, data=FORM_WORDBOOK_LE, headers=HEADER_WORDBOOK_LE, allow_redirects=False)

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
	if len(sys.argv) != 4:
		print "Parameters Wrong"
		return

	# check kindle volcab
	if not os.path.isfile(VOCAB_PATH + VOCAB_NAME):
		print "Please Connect Your Kindle to Your Computer"
		return
	os.system("cp %s %s" % (VOCAB_PATH + VOCAB_NAME, os.path.dirname(os.path.abspath(__file__))))
	conn = sqlite3.connect(VOCAB_NAME)
	wordbook = sys.argv[1]
	is_youdao = True
	if wordbook == "langeasy":
		is_youdao = False
	# login 
	cookie = ""
	if is_youdao:
		cookie = login(sys.argv[2], sys.argv[3])
	else:
		cookie = loginLE(sys.argv[2], sys.argv[3])

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
		if is_youdao:
			addToWordbook(word, translation[0], desc, "kindle", cookie)
		else:
			addToWordbookLE(word, desc, cookie)
		print "Add Word [%s]" % (word)

	cursor.close()
	conn.close()

if __name__ == '__main__':
	main()