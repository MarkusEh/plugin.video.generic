import os
import time
import datetime
import string
import sys
import urllib
import urllib.parse as urlparse
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
args = urlparse.parse_qs(sys.argv[2][1:])
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
#     StreamUtils.play(vid.streamURL())
      li = xbmcgui.ListItem()
      li.setProperty('IsPlayable', 'true')
      li.setPath(vid.streamURL() )
      xbmcplugin.setResolvedUrl(int(sys.argv[ 1 ]),True,li)

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

class site_parse_interface:
  def __init__(self, a_tag, match_check, base_url):
    self.ignore_ = True
    classes = match_check.get("classes")
    if not classes is None:
      class_ = a_tag.get("class")
      if class_ is None: return
      for class_m in classes:
        if not class_m in class_: return
# all required classes are in the class attibute
    self.mv_href = a_tag.get("href")
    if self.mv_href is None: return
    if self.mv_href == "": return
    if self.mv_href == "#": return
    if self.mv_href == "/": return
    href_contains_l = match_check.get("href_contains")
    if not href_contains_l is None:
      for href_contains in href_contains_l:
        if href_contains[0] == "^":
          if not self.mv_href.startswith(href_contains[1:]): return
        else:
          if self.mv_href.find(href_contains) == -1: return
# href requirements are met
    img_url_tag = match_check.get("img_url_tag")
    if not img_url_tag is None:
      mv_image = a_tag.find("img")
      if mv_image is None: return
      self.img_url = mv_image.get(img_url_tag)
      if self.img_url is None: return
      if self.img_url == "": return
      img_title_tag = match_check.get("img_title_tag")
      if not img_title_tag is None:
        self.title = mv_image.get(img_title_tag)
        if self.title is None: return
    else: self.img_url = ""
# img_url_tag and img_title_tag requirements are met
    self.title = ""
    a_title = match_check.get("a_title")
    if not a_title is None:
      if a_title:
        self.title = a_tag.text
    a_title_tag = match_check.get("a_title_tag")
    if not a_title_tag is None:
      self.title = a_tag.get(a_title_tag)
      if self.title is None: return
# title requirements are met
    
# all checks done, match found
    if self.title == "":
      if self.mv_href.endswith("/"):
        self.title = os.path.basename(os.path.dirname(self.mv_href))
      else:
        self.title = os.path.basename(self.mv_href)
    if self.img_url.startswith("//"):
      self.img_url = "https:" + self.img_url
    if (not self.img_url.startswith("http")) and (self.img_url != ""):
      self.img_url = base_url + self.img_url
    if self.mv_href.startswith("//"):
      self.mv_href = "https:" + self.mv_href
    if (not self.mv_href.startswith("http")) and (self.mv_href != ""):
      self.mv_href = base_url + self.mv_href
    self.action_ = match_check.get("action", "video")
    self.ignore_ = False
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

def line_action(parseInterface, site, hrefs, dict_):
    if parseInterface.action() == "break": return
    mv_href = parseInterface.url()
    if mv_href in hrefs: return
    hrefs.add(mv_href)
    if parseInterface.action() == "video_get_href_img":
      img_thumbnail_url = dict_.get(mv_href, "")
    else:
      img_thumbnail_url = parseInterface.img()
    if parseInterface.action() == "href_img":
      dict_[mv_href] = img_thumbnail_url
      return
    mv_title  = parseInterface.name()
    is_folder = parseInterface.action() == "folder"

    xbmc.log("mv_href: " + str(mv_href), xbmc.LOGERROR)
    xbmc.log("mv_title: \"{}\"".format(str(mv_title)), xbmc.LOGERROR)
    xbmc.log("img_thumbnail_url: " + str(img_thumbnail_url), xbmc.LOGERROR)
    li = xbmcgui.ListItem(insertLineBreakIfNeeded(mv_title, list_width), offscreen = True)
    
    li.setInfo(type='video', infoLabels={'plot': "{}\n{}\n{}".format(mv_title, mv_href, img_thumbnail_url), 'title': mv_title})

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
    for match_check in site_json["a_tags"]:
      parseInterface = site_parse_interface(x, match_check, site_json["url"])
      if parseInterface.ignore(): continue
      line_action(parseInterface, site, hrefs, dict_)
      break

  xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
  xbmcplugin.endOfDirectory(addon_handle)

if mode[0] == 'folder':
  site = args.get('site', [''])[0]
  if site != '':
    site_json = getSites()[site]
    if not site_json is None:
      display_folders = args.get('display_folders', [''])[0] == "true"
      scrape_url = args.get('scrape_url', [site_json["url"]])[0]
      mozhdr = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'}
      sb_get = requests.get(scrape_url, headers = mozhdr)
    #    xbmc.log("request content: " + str(sb_get.content), xbmc.LOGERROR)
      soupeddata = BeautifulSoup(sb_get.content, "html.parser")
      foldersVideos(soupeddata, site, site_json, display_folders)

elif mode[0] == 'play':
   final_link = args['scrape_url'][0]
   play_video(final_link)

