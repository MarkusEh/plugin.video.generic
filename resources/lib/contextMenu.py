import sys
import xbmcgui
import xbmc
import YDStreamExtractor as StreamExtractor
import YDStreamUtils as StreamUtils

xbmc.log("contextMenu: sys.argv=" + str(sys.argv), xbmc.LOGERROR)
mode = sys.argv[1]
url = sys.argv[2]
xbmc.log("url=" + str(url), xbmc.LOGERROR)
xbmc.log("mode=" + str(mode), xbmc.LOGERROR)


def play_video(url):
   force_video = True
   vid = StreamExtractor.getVideoInfo(url)
   if vid:
          if force_video:
              yes = True
          else:
#              yes = xbmcgui.Dialog().yesno(T(32164),T(32165),T(32166),'',T(32167),T(32168))
              yes = xbmcgui.Dialog().yesno('Play Video?','Play the video the link points to,','or follow the link to the page?','','Follow Link','Play Video')
          if yes:
              if vid.hasMultipleStreams():
                  vlist = []
                  for info in vid.streams():
                      vlist.append(info['title'] or '?')
                  idx = xbmcgui.Dialog().select('Select Video',vlist)
                  if idx >= 0:
                    vid.selectStream(idx)
              StreamUtils.play(vid.streamURL())

def downloadVideo(url):
            vid = StreamExtractor.getVideoInfo(url)
            if vid:
                if vid.hasMultipleStreams():
                    vlist = []
                    for info in vid.streams():
                        vlist.append(info['title'] or '?')
                    idx = xbmcgui.Dialog().select('Select Video',vlist)
                    if idx < 0: return
                    vid.selectStream(idx)
                StreamExtractor.handleDownload(vid,bg=True)

if mode == "download":
  downloadVideo(url)
elif mode == "play":
  play_video(url)
