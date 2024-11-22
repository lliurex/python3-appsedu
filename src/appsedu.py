#!/usr/bin/python3
import urllib
from urllib.request import Request
from urllib.request import urlretrieve
from bs4 import BeautifulSoup as bs
# wget https://portal.edu.gva.es/appsedu/aplicacions-lliurex/
EDUAPPS_URL="https://portal.edu.gva.es/appsedu/aplicacions-lliurex/"

class manager():
	def __init__(self,*args,**kwargs):
		self.dbg=True
	#def __init__

	def _debug(self,msg):
		if self.dbg:
			dbg="eduapps: {}".format(msg)
			print(dbg)
	#def _debug

	def getApplications(self):
		self._debug("Fetching {}".format(EDUAPPS_URL))
		rawcontent=self._fetchUrl(EDUAPPS_URL)
		bscontent=bs(rawcontent,"html.parser")
		appInfo=bscontent.find_all("td",["column-1","column-2","column-5","column-7"])
		applications=[]
		columnAuth=None
		columnName=[]
		columnCats=""
		columnIcon=None
		for column in appInfo:
			appName=None
			if (column.attrs["class"][0]=="column-1"):
				columnIcon=column.img
			if (column.attrs["class"][0]=="column-2"):
				columnName=column.find_all("a",href=True)
			if (column.attrs["class"][0]=="column-5"):
				columnCats=column.text
			if (column.attrs["class"][0]=="column-7"):
				columnAuth=column.text
			for data in columnName:
				appUrl=data["href"]
				appName=data.text
			if appName:
				if columnIcon==None:
					print("NO ICON FOR {}".format(appName))
					continue
				appIcon=columnIcon["src"]
				cats=[]
				for cat in columnCats.split(","):
					cats.append(cat.strip())
				applications.append({"app":appName,"icon":appIcon,"auth":columnAuth,"categories":cats,"url":appUrl})
				columnAuth=None
				columnName=[]
				columnCats=""
				columnIcon=None
		return(applications)
	#def getApplications
	
	def getApplication(self,appUrl):
		self._debug("Getting details for {}".format(appUrl))
		application={}
		rawcontent=self._fetchUrl(appUrl)
		bscontent=bs(rawcontent,"html.parser")
		b=bscontent.find_all("div","entry-content")
		for i in b:
			img=i.find("img")
			if img:
				application["icon"]=img["src"]
			rel=i.find("div","acf-view__versio-field acf-view__field")
			if rel:
				application["versions"]={"eduapp":rel.text.strip()}
				#rebostPkg["icon"]=img["src"]
			desc=i.find("div","acf-view__descripcio-field acf-view__field")
			if desc:
				application["description"]=desc.text.strip()
				application['summary']=application["description"].split(".")[0]
			homepage=i.find("div","acf-view__url_editor-link acf-view__link")
			if homepage:
				application["homepage"]=homepage.text.strip()
			auth=i.find("div","acf-view__estat_val-choice acf-view__choice")
			if auth:
				reject=i.find("div","acf-view__motiu_de_no_autoritzacio_val-choice acf-view__choice")
			if reject:
				application["description"]+="****{}".format(reject.text.strip())
				application["bundle"]={"eduapp":"banned"}
			groups=i.find("acf-view__usuaris_autoritzats_val-choice acf-view__choice")
			ident=i.find("acf-view__identitat_val-choice acf-view__choice")
			ambit=i.find("div","acf-view__ambit_educatiu_val-label acf-view__label")
		return(application)
	#def getApplication

	def _fetchUrl(self,url=""):
		if len(url)==0:
			url=EDUAPPS_URL
		content=''
		req=Request(url, headers={'User-Agent':'Mozilla/5.0'})
		try:
			with urllib.request.urlopen(req,timeout=10) as f:
				content=(f.read().decode('utf-8'))
		except Exception as e:
			print("Couldn't fetch {}".format(url))
			print("{}".format(e))
		return(content)
	#def _fetchUrl

def main():
	obj=eduHelper()
	return (obj)

