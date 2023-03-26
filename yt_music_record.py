#!/usr/bin/env python

# Daniel Mendoza
# Robotics Engineer

# mail: dm.dmnix@gmail.com
# Free as in Freedom :)

import bs4
import dbus
import json
import lz4.block
import pathlib
import os
import re
import sys
import subprocess as sp
from chromium import get_cover_image as gc
from time import time

fpath = pathlib.Path.home().joinpath('.mozilla/firefox')
frecovery = fpath.glob('*default*release*/sessionstore-backups/recovery.jsonlz4')

user = os.environ['USER']
videos = str(pathlib.Path.home()) + '/Music/'
pics = str(pathlib.Path.home()) + '/Documents/GITREPOS/music.dmweb/images/'
melodies_txt = str(pathlib.Path.home()) + '/Documents/GITREPOS/music.dmweb/Melodies.txt'
script_path = str(pathlib.Path(__file__).parent.absolute()) + '/'
sp.run(f'rm -f {script_path}*.mp4',shell=True,stdout=sp.DEVNULL)
sp.run(f'rm -f {script_path}*.png',shell=True,stdout=sp.DEVNULL)
audio_sources = sp.Popen(['pactl','list','short','sources'],
                         stdout=sp.PIPE,stderr=sp.PIPE,text=True
                         ).communicate()[0].strip()
audio_ouput = re.search(r'(?<=\s)alsa_output[^\s]+',audio_sources).group(0)
utf_fwdslasah = "\U00002044"

bus = dbus.SessionBus()

services = []
for service in bus.list_names():
    if service.startswith('org.mpris.MediaPlayer2.'):
        try:
            browser = re.findall(r'\bc[hromium]*\b|\bf[irefox]*\b',service)
        except IndexError:
            sys.exit("[ERROR] Web player not found")
            continue
        if browser:
            services.append(service)

# Check which service is in Playing state
# If Firefox & Chromim are in Paused State
# Firefox will be set to default web player
if services:
    for s in services:
        web_player = dbus.SessionBus().get_object(s, '/org/mpris/MediaPlayer2')
        meta = dbus.Interface(web_player,
                dbus_interface='org.freedesktop.DBus.Properties')
        metadata = meta.GetAll('org.mpris.MediaPlayer2.Player')
        if metadata['PlaybackStatus'] == 'Playing':
            # print('PLAYING')
            current_player = s
            break
        elif 'firefox' in s:
            # print('FFOX')
            current_player = s # Firefox as default player
        else:
            # print(f'FOUND: {s}')
            current_player = s
else:
    sys.exit('[ERROR] Web player not found')

if len(sys.argv) > 1:
    if sys.argv[1] == 'mpqtile':
        print(metadata['PlaybackStatus'])
        sys.exit()

web_device = dbus.Interface(web_player, dbus_interface='org.mpris.MediaPlayer2.Player')
song = metadata['Metadata']['xesam:title'].replace("/",f"{utf_fwdslasah}")
album = metadata['Metadata']['xesam:album'].replace("/",f"{utf_fwdslasah}")
artist = str(metadata['Metadata']['xesam:artist'][0]).replace("/",f"{utf_fwdslasah}")

if metadata['PlaybackStatus'] != 'Playing':
    web_device.PlayPause()

# OUTPUT
def print_to_terminal():
    data = f"""

        {'Album':<7}: {album}
        {'Artist':<7}: {artist}
        {'Song':<7}: {song}
        {'Cover':<7}: {album_cover}

    """
    return data


# Get album cover - wget and imagemagick required
def cover(image):
    # Validate if the size of the album cover is 640x640
    # if the size is different it will be changed to 640x640
    image_size1 = sp.Popen(
            ['file', image], stdout=sp.PIPE)
    image_size2 = sp.Popen(
            ["awk {'print $5\"x\"$7'}"],
            shell=True, stdin=image_size1.stdout, stdout=sp.PIPE)
    image_size1.stdout.close()
    image_size3 = sp.Popen(
            ['tr', '-d', '\,'],
            text=True, stdin=image_size2.stdout, stdout=sp.PIPE, stderr=sp.PIPE)
    image_size2.stdout.close()
    size = image_size3.communicate()[0]
    if size not in ('540x540','544x544','640x640','720x720'):
         convert = sp.Popen(
                 ['convert', image, 
                     '-resize', '640x640!', image],
                 stdout=sp.PIPE,
                 stderr=sp.DEVNULL)
         convert.communicate()[0]
    return image


# Check if the track already exists
def mp4_exists(track):
    counter = 0
    track_exists = pathlib.Path(track)
    while track_exists.is_file():
        counter += 1
        track = f'{videos}{artist} : {album} : {song}_{counter}.mp4'
        track_exists = pathlib.Path(track)
    return track


# Record ("30" secs) audio from your computer
# Also fades out audio 5 secs before finished
def record(audio,image):

    recorded = sp.Popen(
            ['ffmpeg','-y','-framerate','1','-i',f'{image}',
            '-f','pulse','-i',audio_ouput,
             '-metadata',f'artist={artist}',
             '-metadata',f'album={album}',
             '-metadata',f'title={song}',
             '-t','30','-vf','format=yuv420p','-af','afade=t=out:st=25:d=5',
             audio],stdout=sp.PIPE, stderr=sp.PIPE)

    return recorded.communicate()


# This adds a thumbnail in video_out
def get_and_set_image(video_in,video_out,image):
    # ffmpeg -i 'NTO : Apnea : Paul.mp4' -i maxresdefault.jpg -map 1 -map 0 -c copy -disposition:0 attached_pic output.mp4
    setImage = sp.Popen(
            ['ffmpeg','-y','-i',f'{video_in}',
             '-i',f'{image}','-map','1','-map','0',
             '-c','copy','-disposition:0','attached_pic',f'{video_out}'
             ],stdout=sp.PIPE, stderr=sp.PIPE)
    return setImage.communicate()


track = f'{videos}{artist} : {album} : {song}.mp4'
track = mp4_exists(track)
audio_out = f'{script_path}out.mp4'
song_to_record = f'{script_path}{artist} : {album} : {song}.mp4'

if 'chromium' in current_player:
    print('[STARTED]')
    URL = gc()
    album_cover = script_path + 'maxresdefault.jpg'
else:
    URL = False
    album_cover = metadata['Metadata']['mpris:artUrl'].replace('file://','')

print(print_to_terminal())
#record(audio_out,album_cover)
#cover(album_cover)
#get_and_set_image(audio_out,track,album_cover)

# Get YouTube Music URL from Chromium
def get_ytmusic_url():
    '''
    [FIREFOX WEB BROWSER]:

    No argument required
    '''
    for f in frecovery:
        b = f.read_bytes()
        if b[:8] == b'mozLz40\0':
            b = lz4.block.decompress(b[8:])

        # load as json
        j = json.loads(b)
        if 'windows' in j.keys():
            for w in j['windows']:
                for t in w['tabs']:
                    i = t['index'] - 1
                    if 'music.youtube' in t['entries'][i]['url']:
                        URL = t['entries'][i]['url']
    return URL

# txt file that records the current playing song URL
def write_to_txt():
    '''
    [TXT]: Pass a txt file if you want to store URLs
    '''
    with open(melodies_txt,'r+') as txt:
        for line in txt.readlines():
            if f'{album} : {song} : {URL}' in line:
                return
        txt.write(f'{album} : {song} : {URL}\n')


if os.path.isfile(melodies_txt):
    if URL:
        write_to_txt()
    else:
        URL = get_ytmusic_url()
        write_to_txt()


if os.path.isdir(pics):
    if not os.path.isfile(f'{pics}{album}.png'):
        sp.run(
                f'convert {album_cover} -resize "320x320" "{pics}{album}.png"',
                shell=True,stdout=sp.DEVNULL)
