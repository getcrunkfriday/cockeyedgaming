import youtube_dl
import config


ydl_info_options={'outtmpl': '%(id)s %(title)s'}
ydl_download_options={
	'outtmpl': config.MUSIC_DL_LOCATION+'%(id)s.%(ext)s',
	'format': 'bestaudio/best',
	'postprocessors': [{
		'key': 'FFmpegExtractAudio',
		'preferredcodec': 'mp3',
		'preferredquality': '192'
	}]
}

def get_vid_info(vid):
    with youtube_dl.YoutubeDL(ydl_info_options) as ydl:
        result=ydl.extract_info(vid,download=False)
        id_tuple=ydl.prepare_filename(result)
        vidid=id_tuple.split()[0]
        title=" ".join(id_tuple.split()[1:])
        return (vidid,title,result)
    return False

def download_vid(vid):
	with youtube_dl.YoutubeDL(ydl_download_options) as ydl:
		return ydl.download([vid])
