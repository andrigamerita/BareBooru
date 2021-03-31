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
		"[BareBooru/Config/Customization/SourceCode]", Config["Customization"]["Source Code"]
	)

# Reading GET requests and responding accordingly.
def ReadGETParameters(RequestPath):
	if RequestPath.lower() == "/" or RequestPath == "/index.html":
		return PatchGeneratorHTML().encode("utf-8")

	elif RequestPath.lower() == "/main.css":
		return MainCSS.encode("utf-8")

	elif RequestPath.lower().startswith("/?search="):
		RequestPathDict = URLParse.parse_qs(RequestPath.lower())
		SearchTokens = RequestPathDict["/?search"][0].split(" ")

		DBReadString = "* FROM Items WHERE Tag LIKE "
		for SearchTokenIndex in range(len(SearchTokens)):
			DBReadString += "'" + SearchTokens[SearchTokenIndex] + "'"
			if SearchTokenIndex < len(SearchTokens)-1:
				DBReadString += " OR Tag LIKE "

		DB = DBConnect()
		DBSelection = DBRead(DB, DBReadString)
		DB.close()

		DBSelectionResults = [[], []]

		GeneratedHTML = ""

		for DBItem in DBSelection:
			pass

		#return PatchGeneratorHTML().replace("[BareBooru/Engine/MainNav]", GeneratedHTML).encode("utf-8")
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
	DBCreateTable(DB, """
		CREATE TABLE IF NOT EXISTS "Items" (
			"Tag"	TEXT,
			"ID"	INTEGER NOT NULL,
			"Info"	TEXT,
			"File"	TEXT
		);
	""")
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