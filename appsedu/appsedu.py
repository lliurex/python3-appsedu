#!/usr/bin/python3
import time,os
import urllib
from urllib.request import Request
from urllib.request import urlretrieve
import requests
import subprocess
from random import shuffle
from bs4 import BeautifulSoup as bs
# wget https://portal.edu.gva.es/appsedu/aplicacions-lliurex/
EDUAPPS_URL="https://portal.edu.gva.es/appsedu/aplicacions-lliurex/"
CACHE=os.path.join(os.environ.get("HOME","/tmp"),".cache","appsedu","index.html")
CACHEHTML=os.path.join(os.environ.get("HOME","/tmp"),".cache","appsedu","html")

class manager():
	def __init__(self,*args,**kwargs):
		self.dbg=True
		if not "cache" in kwargs:
			if os.path.isfile(CACHE):
				try:
					self._debug("Removing old cache")
					os.unlink(CACHE)
				except Exception as e:
					print(e)
					pass
		if os.path.exists(os.path.dirname(CACHE))==False:
			os.makedirs(os.path.dirname(CACHE))
		if os.path.exists(CACHEHTML)==False:
			os.makedirs(CACHEHTML)

	#def __init__

	def _debug(self,msg):
		if self.dbg:
			dbg="eduapps: {}".format(msg)
			print(dbg)
	#def _debug
	
	def _readFile(self,fpath):
		fcontent=""
		if os.path.exists(fpath):
			self._debug("Read: {}".format(fpath))
			try:
				with open(fpath,"r") as f:
					fcontent=f.read()
			except TypeError:
				with open(fpath,"rb") as f:
					fcontent=f.read()
			except Exception as e:
				print(e)
		return(fcontent)
	#def _readFile

	def _writeFile(self,fpath,fcontent):
		if os.path.exists(os.path.dirname(fpath))==False:
			try:
				os,makedirs(os.path.dirname(fpath))
			except Exception as e:
				print(e)
			self._debug("Write: {}".format(fpath))
			try:
				with open(CACHE,"w") as f:
					f.write(fcontent)
			except TypeError:
				with open(CACHE,"wb") as f:
					f.write(fcontent)
			except Exception as e:
				print(e)
		return()
	#def _writeFile

	def getApplications(self,cache=True):
		if os.path.exists(CACHE) and cache==True:
			rawcontent=self._readFile(CACHE)
		else:
			self._debug("Fetching {}".format(EDUAPPS_URL))
			rawcontent=self._fetchUrl(EDUAPPS_URL)
			if cache==True:
				self._writeFile(CACHE,rawcontent)
		bscontent=bs(rawcontent,"html.parser")
		#Get all <td> that hold application info
		tdAppArray=bscontent.find_all("td",["column-1","column-2","column-5","column-7"])
		applications=[]
		tdApp={"cName":[],"cCats":"","cIcon":{},"categories":[],"auth":"","icon":"","url":"","app":""}
		#Categories is the last column readed. If fullfiled we got all info from td
		for column in tdAppArray:
			tdApp["cName"]=""
			if (column.attrs["class"][0]=="column-1"):
				tdApp["cIcon"]=column.img
				tdApp["icon"]=tdApp["cIcon"].get("src","")
			elif (column.attrs["class"][0]=="column-2"):
				tdApp["cName"]=column.find("a",href=True)
				tdApp["url"]=tdApp["cName"]["href"]
				tdApp["app"]=tdApp["cName"].text
			elif (column.attrs["class"][0]=="column-5"):
				tdApp["cCats"]=column.text
				for cat in tdApp["cCats"].split(","):
					tdApp["categories"].append(cat.strip())
			elif (column.attrs["class"][0]=="column-7"):
				tdApp["auth"]=column.text
			if len(tdApp["auth"])>0: #Process app, there's auth column
				if tdApp["auth"].startswith("Autorizada - ") or tdApp["auth"].startswith("Autoritzada - ")==False:
					tdApp["categories"].append("Forbidden")
				elif tdApp["auth"].endswith("- Sistema")==True:
					tdApp["categories"].append("Preinstalled")
				applications.append(tdApp)
				tdApp={"cName":[],"cCats":"","cIcon":{},"categories":[],"auth":"","icon":"","url":"","app":""}
		return(applications)
	#def getApplications
	
	def getApplication(self,appUrl):
		application={}
		cFile=os.path.join(CACHEHTML,os.path.basename(appUrl.strip("/")))
		if os.path.exists(cFile)==True:
			self._debug("Getting cache for {}".format(cFile))
			with open(cFile,"rb") as f:
				rawcontent=f.read()
		else:
			self._debug("Getting details for {}".format(appUrl))
			rawcontent=self._fetchUrl(appUrl)
			with open(cFile,"wb") as f:
				f.write(rawcontent)
		application=self.scrapContent(appUrl,rawcontent)
		if "icon" not in application:
			urlopen=False
			curl=True
			while "icon" not in application:
				urlopen=not(urlopen)
				curl=not(curl)
				rawcontent=self._fetchUrl(appUrl,urlopen=urlopen,curl=curl)
				application=self.scrapContent(appUrl,rawcontent)
				if curl==True:
					break
		self._debug("**** END {}****".format(appUrl))
		return(application)
	#def getApplication

	def getCategoriesFromApplications(self,applications=[]):
		if len(applications)==0:
			applications=self.getApplications()
		seen=[]
		appsByCat={}
		for app in applications:
			categories=app.get("categories",[])
			for cat in categories:
				if len(cat)<3:
					continue
			#	if cat=="Forbidden":
			#		cat="No Disponible"
				if cat not in appsByCat:
					appsByCat[cat]=[]
				appsByCat[cat].append(app)
		return(appsByCat)
	#def getCategoriesFromApplications
	
	def getApplicationsFromCategory(self,category):
		categories=self.getCategoriesFromApplications()
		return(categories.get(category,[""]))
	#def getApplicationsForCategory

	def searchApplications(self,app):
		applications=self.getApplications()
		apps=[]
		for application in applications:
			if application["app"].lower().startswith(app.lower()):
				apps.append(application)
		self._debug("Search results")
		self._debug(apps)
		return(apps)
	#def searchApplications

	def _fetchUrl(self,url="",headers={},urlopen=False,curl=False):
		if len(url)==0:
			url=EDUAPPS_URL
		content=''
		if curl==True:
			try:
				content=subprocess.check_output(["curl",url],encoding="utf8")
			except Exception as e:
				print("Curl: {}".format(e))
		elif urlopen==True:
			if not "User-Agent"  in headers:
				headers.update({'User-Agent':'mozilla/5.0 (X11; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0'})
			req=Request(url,headers=headers) 
			try:
				with urllib.request.urlopen(req,timeout=10) as f:
					content=f.read().decode('utf-8')
			except Exception as e:
				print("Urlopen err: {}".format(e))
		else:
			try:
				response=requests.get(url)
				content=response.content
			except Exception as e:
				print("Request err: {}".format(e))
		if content=="":
			print("Couldn't fetch {}".format(url))
		return(content)
	#def _fetchUrl

	def scrapContent(self,appUrl,rawcontent):
		application={}
		bscontent=bs(rawcontent,"html.parser")
		b=bscontent.find_all("div","entry-content")
		for i in b:
			self._debug("INSPECTING {}".format(appUrl))
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
	#def scrapContent

	def getRelatedZomando(self,app):
		epicPkgs=dict.fromkeys(self._getEpicZomandos())
		epicPkg=""
		for epic in epicPkgs.keys():
			if epic.split(".")[0].lower()==app.lower().replace(" ","-"):
				epicPkg=self._getPathForEpi(epic)
			if len(epicPkg)>0:
				break
		if len(epicPkg)==0:
			for epic in epicPkgs.keys():
				epicPkg=self._searchAppInEpi(app,epic)
				if len(epicPkg)>0:
					break
		return(epicPkg)
	#def _getPkgsFromEpic(self):

	def _getEpicZomandos(self):
		cmd=["/usr/sbin/epic","showlist"]
		epicList=[]
		renv = os.environ.copy()
		if len(renv.get("USER",""))==0:
			renv["USER"]="root"
		proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,env=renv)
		output=proc.stdout
		if "EPIC:" in output:
			idx=output.index("EPIC:")
			rawEpicList=output[idx:].replace("EPIC:","")
			epicList=[ epic.strip() for epic in rawEpicList.split(",") ]
		shuffle(epicList)
		return(epicList)
	#def _getEpicZomandos
	
	def _searchAppInEpi(self,app,epic):
		self._debug("Processing {} for {}".format(epic,app))
		renv = os.environ.copy()
		if len(renv.get("USER",""))==0:
			renv["USER"]="root"
		if epic.split(".")[0].lower()!=app.lower().replace(" ","-"):
			cmd=["/usr/sbin/epic","showinfo",epic]
			proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,env=renv)
			output=proc.stdout.split("\n")
			match=False
			for line in output:
				if "Packages availables:" in line or "Application:" in line:
					pkgs=line.split(":")[-1]
					for pkg in pkgs.split(" "):
						if len(pkg)>0:
							if pkg==app.lower():
								match=True
								break
							if pkg.count(".")==2:
								if pkg.split(".")[-1]==app.lower():
									match=True
									break

				if match==True:
					break
			if match==False:
				epic=""
		return(self._getPathForEpi(epic))
	#def _searchAppinEpi

	def _getPathForEpi(self,epic):
		appDir="/usr/share/zero-center/zmds"
		fpath=""
		if epic!="":
			fname=epic.replace(".epi",".zmd")
			listDir=os.scandir(appDir)
			for f in listDir:
				if f.path.endswith(fname):
					fpath=f.path
					break
			if len(fpath)==0:
				for f in lstDir:
						if (fname.split(".")[0] in f) or (fname.split("-")[0] in f):
							fpath=f.path
							break
		return(fpath)
	#def _getZmdFromEpi

def main():
	obj=eduHelper()
	return (obj)

