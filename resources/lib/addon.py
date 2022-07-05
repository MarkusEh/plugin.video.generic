import os
import time
import datetime
import string
import sys
import urllib.parse
import requests
import json

import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
import xbmcplugin
import xbmcvfs

import YDStreamExtractor as StreamExtractor
import YDStreamUtils as StreamUtils


from bs4 import BeautifulSoup

#xbmc.log("sys.argv" + str(sys.argv), xbmc.LOGERROR)
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urllib.parse.parse_qs(sys.argv[2][1:])
list_width_str = xbmcplugin.getSetting(addon_handle, "list_width")
#xbmc.log("list_width_str: " + str(list_width_str), xbmc.LOGERROR)
if list_width_str == '':
  list_width = 0
else:
  list_width = int(list_width_str)

xbmcplugin.setContent(addon_handle, 'movies')

def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)

def getSites():
    j_filename = xbmcvfs.translatePath("special://userdata/addon_data/plugin.video.generic/sites.json")
    with xbmcvfs.File(j_filename, "r") as j_file:
      try:
        j_string = j_file.read()
      except:
        xbmc.log("non-utf8 characters in file " + j_filename, xbmc.LOGERROR)
        return None
      try:
        data = json.loads(j_string)
      except:
        xbmc.log("ERROR parsing json file " + j_filename, xbmc.LOGERROR)
        return None
    return data

def AddCommand(commands, name, mode, url):
    if mode == "parse":
      site = args.get('site', [''])[0]
      p_url = build_url({'mode': 'folder', 'scrape_url': url, 'site': site})
#     xbmc.log("p_url=" + str(p_url), xbmc.LOGERROR)
      runner = "ActivateWindow(10025," + str(p_url) + ",return)"
    else:
      runner = "RunScript(plugin.video.generic, {}, \"{}\")".format(str(mode), str(url))
#     xbmc.log("runner=" + str(runner), xbmc.LOGERROR)
    commands.append(( str(name), runner, ))

def play_video(url):
   vid = StreamExtractor.getVideoInfo(url)
   if vid:
      if vid.hasMultipleStreams():
          vlist = []
          for info in vid.streams():
              vlist.append(info['title'] or '?')
          idx = xbmcgui.Dialog().select('Select Video',vlist)
          if idx >= 0:
            vid.selectStream(idx)
      StreamUtils.play(vid.streamURL())
#     li = xbmcgui.ListItem()
#     li.setProperty('IsPlayable', 'true')
#     li.setPath(vid.streamURL() )
#     xbmcplugin.setResolvedUrl(int(sys.argv[ 1 ]),True,li)

mode = args.get('mode', ['folder0'])

def addFolder(folder, name, addTime = 0):
    max_line_length = 30
    url = build_url({'mode': 'files', 'folder': folder})
    created_on_timestamp = int(time.time() ) + addTime
    createdon = str( datetime.datetime.fromtimestamp(created_on_timestamp) )
    li = xbmcgui.ListItem(name, offscreen = True)
    folder_lb = ''
    for i in range(0, len(folder), max_line_length):
        folder_lb = folder_lb + '\n' + folder[i:i+max_line_length]
    li.setInfo(type='video', infoLabels={'plot': createdon + '\n' + folder_lb, 'sorttitle':createdon, 'dateadded': createdon})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

if mode[0] == 'files':
    current_folder = args.get('folder', ['/media'])[0]
    parent_folder = os.path.dirname(current_folder)
    addFolder(parent_folder, "<up>", 100)
    dirs, files = xbmcvfs.listdir(current_folder)

    for dir in dirs:
      new_folder = os.path.join(current_folder, dir)
      addFolder(new_folder, dir, 0)
    for file in files:
# search string
      search_str = os.path.splitext(file)[0]
      filep = os.path.join(current_folder, file)
      created_on_timestamp = xbmcvfs.Stat(filep).st_mtime() 
      createdon = str( datetime.datetime.fromtimestamp(created_on_timestamp) )
#     xbmc.log("filedate= " + createdon, xbmc.LOGERROR)
      li = xbmcgui.ListItem(file, offscreen = True)
      li.setInfo(type='video', infoLabels={'plot': createdon + '\n' + file + '\nsearch:\n' + search_str, 'sorttitle':createdon, 'dateadded': createdon})
      li.setContentLookup(True)
      li.setProperty('IsPlayable', 'true')
# add context menu
      commands = []
# root_url ist url der internet Seite, auf der wir nach dem String suchen.
# funktioniert so nicht mehr
#     scrape_url = root_url + '/search/?query=' + search_str
#     AddCommand(commands, "parse", "parse", scrape_url)
#     li.addContextMenuItems( commands )
      xbmcplugin.addDirectoryItem(handle=addon_handle, url=filep,
                                listitem=li, isFolder=False)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.endOfDirectory(addon_handle)

def insertLineBreakIfNeeded(line, list_width):
  line_len = len(line)
  if line_len <= list_width: return line
  mid = line.find(" ", int(line_len / 2))
  if mid < 0:
     mid = int(line_len / 2)
     return "{}\n{}".format(line[0:mid], line[mid:])
  else:
     return "{}\n{}".format(line[0:mid], line[mid + 1:])

if mode[0] == 'folder0':
  yt_download = xbmcaddon.Addon('script.module.youtube.dl')
  rootFolder = yt_download.getSetting("last_download_path")
  url = build_url({'mode': 'files', 'folder': rootFolder})
  li = xbmcgui.ListItem("local files", offscreen = True)
  xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                              listitem=li, isFolder=True)
  sites = getSites()
  if not sites is None:
    for site in sites.keys():
      url = build_url({'mode': 'folder', 'site': site, 'display_folders': 'true' })
      li = xbmcgui.ListItem(site, offscreen = True)
      xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)
  xbmcplugin.endOfDirectory(addon_handle)

def ignoreUrl(tag, attribute, base_url):
  mv_href = tag.get(attribute)
  if mv_href is None: return True
  if mv_href == "": return True
  if mv_href == "#": return True
  if mv_href == "/": return True
  if mv_href ==  base_url      : return True
  if mv_href ==  base_url + "/": return True
  if mv_href.startswith("http") and not mv_href.startswith(base_url): return True
  if mv_href.startswith("//") and not mv_href.startswith(base_url[6:]): return True
  if mv_href.find("javascript:") != -1: return True
  if mv_href.endswith("contact-us"): return True
  if mv_href.find("content-removal") != -1: return True
  if mv_href.endswith("dmca"): return True
  if mv_href.endswith("advertising"): return True
  return False

def imgSpecial1(tag):
  for div_tag in tag.find_all("div"):
    attributeValue = div_tag.get("class")
    if attributeValue is None: continue
    if not "logo" in attributeValue: continue
    attributeValue = div_tag.get("style")
    if attributeValue is None: continue
    posa = attributeValue.find("https://")
    if posa == -1: continue
    pose = attributeValue[posa:].find("'")
    if pose == -1: continue
    return attributeValue[posa:posa+pose]
  return ""

def defaultImg(a_tag):
  mv_image = a_tag.find("img")
  if not mv_image is None:
    for img_url_attribute in ["data-src", "data-original", "data-image", "src"]:
      img_url = mv_image.get(img_url_attribute, "")
      if img_url != "": return img_url
  return ""

def defaultTitle(a_tag):
  for a_title_attribute in ["title", "alt", "data-statistic-name"]:
    title = a_tag.get(a_title_attribute, "")
    if title != "": return title
  mv_image = a_tag.find("img")
  if not mv_image is None:
    for img_title_attribute in ["alt"]:
      title = mv_image.get(img_title_attribute, "")
      if title != "": return title
  return a_tag.text

def sanitizeUrl(url, base_url):
  if url == "": return url
  if url.startswith("http"): return url
  urle = urllib.parse.quote(url)
  if urle.startswith("//"): return "https:" + urle
  if urle[0] == "/": return base_url + urle
  else: return f"{base_url}/{urle}"

def checkAttribute(attribute, tag, match_check) -> bool:
# all values listed in attribute + "es" in match_check are required
# return true if all required values are available in attribute of tag
    requiredAttributeValues = match_check.get(attribute + "es")
    if requiredAttributeValues is None: return True

    attributeValue = tag.get(attribute)
    if attributeValue is None: return False
    for requiredAttributeValue in requiredAttributeValues:
      if not requiredAttributeValue in attributeValue: return False
    return True

def checkHref(href, match_check) -> bool:
# return true if href matches all href requirements defined in match_check
    href_contains_l = match_check.get("href_contains")
    if href_contains_l is None: return True
    for href_contains in href_contains_l:
      if href_contains[0] == "^":
        if not href.startswith(href_contains[1:]): return False
      else:
        if href.find(href_contains) == -1: return False
    return True

class site_parse_interface:
  def __init__(self, a_tag, match_check, base_url):
    self.ignore_ = True
    self.title = ""
    if not checkAttribute("class", a_tag, match_check): return
# all required classes are in the class attibute
    self.mv_href = a_tag.get("href")
    if not checkHref(self.mv_href, match_check): return
# href requirements are met
    if not self.checkImg(a_tag, match_check): return
    if self.img_url == "":
      a_script = a_tag.find("script")
      if not a_script is None:
        xbmc.log("script found, url:  \"{}\"".format(str( self.mv_href )), xbmc.LOGERROR)
#       xbmc.log("script found, text: \"{}\"".format(str( a_script.text )), xbmc.LOGERROR)
        sp = a_script.text.find("<img src=\"")
        if sp != -1:
          xbmc.log("script + img found, url: \"{}\"".format(str( self.mv_href )), xbmc.LOGERROR)
          h = a_script.text[sp + 10:]
          hf = h.find("\"")
          if hf != -1: self.img_url = h[:hf]
# img_url_attribute and img_title_attribute requirements are met
    if not self.checkTitle(a_tag, match_check, "a_title", "a_title_attribute"): return
# title requirements are met
    
# all checks done, match found
    self.img_url = sanitizeUrl(self.img_url, base_url)
    self.mv_href = sanitizeUrl(self.mv_href, base_url)
    self.action_ = match_check.get("action", "video")
    self.ignore_ = False

  def checkImg(self, tag, match_check) -> bool:
# return true if the img tag matches all requirements defined in match_check
# also, set self.img_url and self.title if data for that are available in the img tag
    if "img_url_attribute" in match_check.keys() or "img_title_attribute" in match_check.keys():
      mv_image = tag.find("img")
      if mv_image is None: return False
      img_url_attribute = match_check.get("img_url_attribute")
      if not img_url_attribute is None:
        self.img_url = mv_image.get(img_url_attribute)
        if self.img_url is None: return False
        if self.img_url == "": return False
      else: self.img_url = ""
      img_title_attribute = match_check.get("img_title_attribute")
      if not img_title_attribute is None:
        self.title = mv_image.get(img_title_attribute)
        if self.title is None: return False
    elif "img_special1" in match_check.keys():
      self.img_url = imgSpecial1(tag)
    else:
      self.img_url = defaultImg(tag)
    return True

  def checkTitle(self, tag, match_check, title_text, title_attribute) -> bool:
# return true if the title matches all requirements defined in match_check, and generic requirements
# also, set self.title
#   if "a_title" in match_check.keys() or "a_title_attribute" in match_check.keys():
    if title_text in match_check.keys() or title_attribute in match_check.keys():
      a_title = match_check.get(title_text)
      if not a_title is None:
        if a_title: self.title = tag.text
      a_title_attribute = match_check.get(title_attribute)
      if not a_title_attribute is None:
        self.title = tag.get(a_title_attribute)
        if self.title is None: return False
    else:
      if self.title == "": self.title = defaultTitle(tag)
    if self.title == "":
# still no title found, set title to basename of href
      if self.mv_href.endswith("/"):
        self.title = os.path.basename(os.path.dirname(self.mv_href))
      else:
        self.title = os.path.basename(self.mv_href)
# sanitize title
    self.title = self.title.replace('\n',' ')
    self.title.strip()
# ignore entries with some titles:
    for excludedTitle in ["Login", "Logout", "Account", "Sign up", "Signup", "Developers", "Contacts", "DMCA"]:
      if self.title == excludedTitle: return False
    for excludedTitlePart in ["upload", "signin", "signup", "Add to"]:
      if self.title.find(excludedTitlePart) != -1: return False
    return True

  def action(self) -> bool:
    return self.action_
  def ignore(self) -> bool:
    return self.ignore_
  def url(self) -> str:
    return self.mv_href
  def name(self) -> str:
    return self.title
  def img(self) -> str:
    return self.img_url

class site_parse_interface_others(site_parse_interface):
  def __init__(self, tag, match_check, base_url):
    self.ignore_ = True
    self.title = ""
    if not checkAttribute("class", tag, match_check): return
# all required classes are in the class attibute
    href_attribute = match_check.get("href_attribute")
    if href_attribute is None:
      xbmc.log("\"href_attribute\" missing in \"option_tags\"", xbmc.LOGERROR)
      return
    if ignoreUrl(tag, href_attribute, base_url): return
    self.mv_href = tag.get(href_attribute)
    if not checkHref(self.mv_href, match_check): return
    if not self.checkImg(tag, match_check): return
    if not self.checkTitle(tag, match_check, "option_title_text", "option_title_attribute"): return
    
# all checks done, match found
    self.img_url = sanitizeUrl(self.img_url, base_url)
    self.mv_href = sanitizeUrl(self.mv_href, base_url)
    self.action_ = match_check.get("action", "video")
    self.ignore_ = False

def line_action(parseInterface, site, hrefs, dict_):
    if parseInterface.action() == "break": return
    mv_href = parseInterface.url()
    if parseInterface.action().endswith("_get_href_img"):
      img_thumbnail_url = dict_.get(mv_href, "")
    else:
      img_thumbnail_url = parseInterface.img()
    if parseInterface.action() == "href_img":
      dict_[mv_href] = img_thumbnail_url
      xbmc.log("href_img: mv_href: " + str(mv_href), xbmc.LOGERROR)
      xbmc.log("img_thumbnail_url: " + str(img_thumbnail_url), xbmc.LOGERROR)
      return
    if mv_href in hrefs: return
    hrefs.add(mv_href)
    mv_title  = parseInterface.name()
    is_folder = parseInterface.action().startswith("folder")

    mv_title_lb = insertLineBreakIfNeeded(mv_title, list_width)
    xbmc.log("mv_href: " + str([mv_href]), xbmc.LOGERROR)
    xbmc.log("mv_title:    \"{}\"".format(str([mv_title])), xbmc.LOGERROR)
    xbmc.log("mv_title_lb: \"{}\"".format(str([mv_title_lb])), xbmc.LOGERROR)
    xbmc.log("img_thumbnail_url: " + str(img_thumbnail_url), xbmc.LOGERROR)
    li = xbmcgui.ListItem(mv_title_lb, offscreen = True)
    
    li.setInfo(type='video', infoLabels={'plot': "{}\n{}\n{}".format(mv_title, mv_href, insertLineBreakIfNeeded(img_thumbnail_url, 80)), 'title': mv_title_lb})

# fanart: Hintergrund unter der Liste. Auch Bild im fanart Anzeigemodus
# clearlogo: Als Bild waehrend der Wiedergabe rechts oben, anstelle des Titels
# thumb (?): Zwingend, erscheint beim Anzeigen des Plots waehrend dem Abspielen links neben Plot
    li.setArt({ 'thumb': img_thumbnail_url, 'poster': img_thumbnail_url,
      'banner' : img_thumbnail_url, 'fanart': img_thumbnail_url,
      'clearart': img_thumbnail_url, 'clearlogo': img_thumbnail_url,
      'landscape': img_thumbnail_url, 'icon': img_thumbnail_url })

    if is_folder:
      url = build_url({'mode': 'folder', 'scrape_url': mv_href, 'site': site})
    else:
      url = build_url({'mode': 'play', 'scrape_url': mv_href})
# add context menu
      commands = []
      AddCommand(commands, "download", "download", mv_href)
      AddCommand(commands, "parse", "parse", mv_href)
      AddCommand(commands, "play", "play", mv_href)
      li.addContextMenuItems( commands )
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                          listitem=li, isFolder=is_folder)

def foldersVideos(soupeddata, site, site_json, display_folders):
  dict_ = {}
  hrefs = set()
  for x in soupeddata.find_all("a"):
    if ignoreUrl(x, "href", site_json["url"]): continue
    found = False
    for match_check in site_json["a_tags"]:
      parseInterface = site_parse_interface(x, match_check, site_json["url"])
      if parseInterface.ignore(): continue
      found = True
      line_action(parseInterface, site, hrefs, dict_)
      break
    if not found:
      parseInterface = site_parse_interface(x, {"action": "folder"}, site_json["url"])
      if not parseInterface.ignore(): line_action(parseInterface, site, hrefs, dict_)

  match_checks = site_json.get("option_tags")
  if not match_checks is None:
    for x in soupeddata.find_all("option"):
      for match_check in match_checks:
        parseInterface = site_parse_interface_others(x, match_check, site_json["url"])
        if parseInterface.ignore(): continue
        line_action(parseInterface, site, hrefs, dict_)


  xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
  xbmcplugin.endOfDirectory(addon_handle)

if mode[0] == 'folder':
  site = args.get('site', [''])[0]
  if site != '':
    site_json = getSites()[site]
    if not site_json is None:
      display_folders = args.get('display_folders', [''])[0] == "true"
      scrape_url = args.get('scrape_url', [site_json["url"]])[0]
# see https://techpatterns.com/downloads/firefox/useragentswitcher.xml
# e.g.: "Mozilla/5.0 (Windows NT 6.2; rv:20.0) Gecko/20121202 Firefox/20.0"
#       "Mozilla/5.0 (X11; Linux i686 on x86_64; rv:2.0.1) Gecko/20100101 Firefox/4.0.1 Fennec/2.0.1"
# console browser "Lynx/2.8.7dev.4 libwww-FM/2.14 SSL-MM/1.4.1 OpenSSL/0.9.8d"
# Browsers - Linux 
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5"
#     "Mozilla/5.0 (X11; Linux x86_64; rv:15.0) Gecko/20120724 Debian Iceweasel/15.02"
#     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.49 Safari/537.36"
#      mozhdr = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'}
      mozhdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5'}
      sb_get = requests.get(scrape_url, headers = mozhdr)
    #    xbmc.log("request content: " + str(sb_get.content), xbmc.LOGERROR)
      soupeddata = BeautifulSoup(sb_get.content, "html.parser")
      foldersVideos(soupeddata, site, site_json, display_folders)

elif mode[0] == 'play':
   final_link = args['scrape_url'][0]
   play_video(final_link)

