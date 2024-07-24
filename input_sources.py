import re
import youtube_dl

def match_youtube_url(url):
    return re.match(r'(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+', url)



def get_input_command(url,start_time):
    if match_youtube_url(url):
        video_data = get_video_details(url,"1080p")
        command = f"-ss {start_time} -i \"{video_data['video_url']}\" -ss {start_time} -i \"{video_data['audio_url']}\""
        return command
    if url.endswith(".png"):
        return (f"-loop 1 -i {url}")

    else:
        command= f"-ss {start_time} -i {url}"
    return command


def get_video_details(url, resolution):
    if resolution not in {'1080p', '720p', '480p', 'mp3'}:
        return False

    ydl_opts = {'outtmpl': '%(id)s.%(ext)s','source_address':'0.0.0.0'}
    ydl = youtube_dl.YoutubeDL(ydl_opts)

    with ydl:
        result = ydl.extract_info(url, download=False)

    video = result['entries'][0] if 'entries' in result else result

    response = {
        'name': video['title'],
        'uploader_id': video['uploader_id'],
        'channel': video['channel_url'],
        'found': False
    }


    for res in video['formats']:
        if  res['acodec'] == 'opus':
            response['audio_url'] = res['url']

        if 'format_note' in res:
            is_res_matched = res['format_note'] in {resolution, resolution+'60', resolution+'50'}
            if is_res_matched:
                response['video_url'] = res['url']
                response['found'] = True


    return response
