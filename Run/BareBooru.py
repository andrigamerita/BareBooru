#!/usr/bin/python3

# -
# | BareBooru
# | Minimalistic and flexible media tagging tool
# |
# | Copyright (C) 2021, OctoSpacc
# | Licensed under the AGPLv3
# -

import json
import sqlite3
from urllib import parse as URLParse
from os import walk, path, system
from http.server import BaseHTTPRequestHandler
from Include.multithread_http_server import MultiThreadHttpServer

def DBConnect(DBFile="Data/DB.sqlite3"):
    try:
        return sqlite3.connect(DBFile)
    except sqlite3.Error:
        print("[E] Error connecting to DB.")

def DBCreateTable(DB, Table):
	try:
		DB.cursor().execute(Table)
	except sqlite3.Error:
		print("[E] Error creating table in DB.")

def DBInsert(DB, Data):
	Cursor = DB.cursor()
	Cursor.execute("INSERT INTO Items(Tag,ID,Info,File) VALUES(?,?,?,?)", Data)
	DB.commit()
	return Cursor.lastrowid

def DBRead(DB, Data):
	Cursor = DB.cursor()
	Cursor.execute("SELECT " + Data)
	return Cursor.fetchall()

# Scanning of the files in a folder and its subfolders.
def ScanFiles(Folder):
	FileList = []

	for dirpath, dirnames, filenames in walk(Folder):
		FileList += [path.join(dirpath, file) for file in filenames]

	return FileList

# Patching the Generator.html file with specific HTML code.
def PatchGeneratorHTML():
	SourceCodeRef = Config["Customization"]["Source Code"]
	if SourceCodeRef == "" or SourceCodeRef == None or type(SourceCodeRef) == bool:
		SourceCodeRef = "https://gitlab.com/octospacc/BareBooru"

	return HTMLGenerator.replace(
		"[BareBooru/Config/Customization/Name]", Config["Customization"]["Name"]).replace(
		"[BareBooru/Config/Customization/Description]", Config["Customization"]["Description"]).replace(
		"[BareBooru/Config/Customization/SourceCode]", Config["Customization"]["Source Code"])

# Reading GET requests and responding accordingly.
def ReadGETParameters(RequestPath):
	if RequestPath.lower() == "/" or RequestPath == "/index.html":
		return PatchGeneratorHTML().replace("[BareBooru/Engine/MainNav]", "").replace("[BareBooru/Engine/SearchText]", "").encode("utf-8")

	elif RequestPath.lower() == "/main.css":
		return MainCSS.encode("utf-8")

	elif RequestPath.lower().startswith("/?content="):
		try:
			with open("Data/Cache/" + URLParse.parse_qs(RequestPath.lower())["/?contentcache"][0], "rb") as ContentFile:
				return ContentFile.read()
		except:
			print("[D] Failed loading " + RequestPath.lower())

	elif RequestPath.lower().startswith("/?contentcache="):
		try:
			with open("Data/Cache/" + URLParse.parse_qs(RequestPath.lower())["/?contentcache"][0], "rb") as ContentFile:
				return ContentFile.read()
		except:
			print("[D] Failed loading " + RequestPath.lower())

	elif RequestPath.lower().startswith("/?search="):
		HTMLMainNav = ""
		RequestPathDict = URLParse.parse_qs(RequestPath.lower())

		if "/?search" in RequestPathDict:
			SearchTokens = RequestPathDict["/?search"][0]
		else:
			SearchTokens = "*"
		SearchTokensList = SearchTokens.split(" ")

		DBExceptString = ""
		if "-" in SearchTokens:
			ExceptTokensList = []
			DBExceptString += "EXCEPT SELECT * FROM Items WHERE Tag LIKE "

			for SearchTokenIndex in range(len(SearchTokensList)):
				if "-" in SearchTokensList[SearchTokenIndex]:
					ExceptTokensList += [SearchTokensList[SearchTokenIndex]]

			for ExceptTokenIndex in range(len(ExceptTokensList)):
				DBExceptString += '"' + SearchTokensList[SearchTokenIndex] + '"'
				if ExceptTokenIndex < len(ExceptTokensList)-1:
					DBReadString += " OR Tag LIKE "

		if "*" in SearchTokens:
			DBReadString = "* FROM Items " + DBExceptString
		else:
			DBReadString = "* FROM Items WHERE Tag LIKE "
			for SearchTokenIndex in range(len(SearchTokensList)):
				DBReadString += '"' + SearchTokensList[SearchTokenIndex] + '"'
				if SearchTokenIndex < len(SearchTokensList)-1:
					DBReadString += " OR Tag LIKE "
			DBReadString += DBExceptString

		DB = DBConnect()
		DBSelection = DBRead(DB, DBReadString)
		DB.close()

		ItemsPerPage = int(Config["Customization"]["Items Per Page"])
		if len(DBSelection)/ItemsPerPage <= 0.0:
			ResponsePageCount = 1
		else:
			if str(len(DBSelection)/ItemsPerPage) == str(float(int(len(DBSelection)/ItemsPerPage))):
				ResponsePageCount = int(len(DBSelection)/ItemsPerPage)
			else:
				ResponsePageCount = int(len(DBSelection)/ItemsPerPage) + 1

		HTMLMainNav = '<form id="PageChooser"><input type="hidden" name="Search" value="[BareBooru/Engine/SearchText]" />'

		if "page" not in RequestPathDict or int(RequestPathDict["/?page"][0]) <= 1:
			RequestPageNumber = 1

		"""
		if "page" in RequestPathDict and int(RequestPathDict["/?page"][0]) > 0:
			HTMLMainNav += '''
				
			'''
		else:
			HTMLMainNav += '''<span>&nbsp;</span><strong>1</strong>'''
			for PageNumber in range(ResponsePageCount):
				if PageNumber < 5 and PageNumber != 0:
					HTMLMainNav += '''<span>&nbsp;</span><input type="submit" name="Page" value="''' + str(PageNumber+1) + '''" />'''
				else:
					if PageNumber == ResponsePageCount-1:
						HTMLMainNav += '''<span>&nbsp;</span><input type="submit" name="Page" value="''' + str(PageNumber+1) + '''" />'''
		"""

		HTMLMainNav += '''
			<!-- /form -->
			<span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>
			<span>Results: ''' + str(len(DBSelection)) + '''</span>
			<h4>[BareBooru/Engine/SearchText]</h4>
			<form id="SearchResults">
			<!-- input type="submit" name="DummySelection" value="Send" /><br /><br /-->
		'''

		print(SearchTokens)
		print(SearchTokensList)
		print(DBSelection)

		for DBItem in DBSelection:
			print(DBItem)
			HTMLMainNav += '<div class="ThumbnailDiv"><input type="hidden" class="ThumbnailBox" name="Item' + str(DBItem[1]) + '" /><img for="Item' + str(DBItem[1])+ '" class="Thumbnail" src="' + "/?Content=" + str(DBItem[3]) + '" /><span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span></div>'
		HTMLMainNav += '</form>'

		return PatchGeneratorHTML().replace("[BareBooru/Engine/MainNav]", HTMLMainNav).replace("[BareBooru/Engine/SearchText]", SearchTokens).encode("utf-8")

	elif RequestPath.lower().startswith("/?edit"):
		HTMLMainNav = ""
		RequestPathDict = URLParse.parse_qs(RequestPath.lower())
		return "r".encode("utf-8")

	return None

# Setting response content type based on file extension.
def SetContentType(RequestPath):
	if RequestPath.endswith(".png"):
		return "image/png"

	elif RequestPath.endswith(".txt"):
		return "text/plain"

	elif RequestPath.endswith(".css"):
		return "text/css"

	elif RequestPath.endswith(".woff2"):
		return "font/woff2"

	return "text/html"

# Server main operational class.
class ServerClass(BaseHTTPRequestHandler):
	def SetResponse(self, ResponseCode, ContentType, NoCache=False):
		self.send_response(ResponseCode)
		self.send_header("Content-type", ContentType)
		if NoCache:
			self.send_header("Pragma", "no-cache")
		self.end_headers()

	def do_GET(self):
		ResponseContent = ReadGETParameters(self.path)
		ContentType = SetContentType(self.path)

		if ResponseContent == None:
			self.SetResponse(404, "text/html")
			#ResponseContent = PatchHTML("Program/WebUI/Templates/404.html").replace("[HTML:RequestPath]", self.path).encode("utf-8")
		else:
			if self.path.lower().startswith("/?Search="):
				self.SetResponse(200, ContentType, NoCache=True)
			else:
				self.SetResponse(200, ContentType)

		if ResponseContent != None:
			self.wfile.write(ResponseContent)

def Main():
	DB = DBConnect()
	DBCreateTable(DB, 'CREATE TABLE IF NOT EXISTS "Items" ("Tag" TEXT, "ID" INTEGER NOT NULL, "Info" TEXT, "File" TEXT);')
	DB.close()

	try:
		print("[I] Starting BareBooru Server.")
		Server = MultiThreadHttpServer(tuple(Config["Server"]["Address and Port"]), int(Config["Server"]["Threads"]), ServerClass)
		Server.start()

	except KeyboardInterrupt:
		print("[I] KeyboardInterrupt received, closing BareBooru Server.")
		Server.stop()

if __name__ == "__main__":
	try:
		with open("Config.json", "r") as ConfigFile:
			Config = json.load(ConfigFile)
	except:
		print("[E] Error loading Config.json; Cannot continue!")
		exit()

	try:
		with open("Run/Generator.html", "r") as HTMLGeneratorFile:
			HTMLGenerator = HTMLGeneratorFile.read()
	except:
		print("[E] Error loading Generator.html; Cannot continue!")
		exit()

	try:
		with open("Run/Main.css", "r") as MainCSSFile:
			MainCSS = MainCSSFile.read()
	except:
		print("[E] Error loading Generator.html; Cannot continue!")
		exit()

	DB = DBConnect()
	DB.close()

	Main()