#!/usr/bin/env python

import requests
import bs4
import sqlite3
import subprocess as sp
from bs4 import BeautifulSoup as bs
from pathlib import Path

def get_cover_image():
    chromium_db = str(Path.home().joinpath('.config/chromium/Default/History'))
    script_path = str(Path(__file__).parent.absolute()) + '/'
    cropimage = str(Path(__file__).parent.absolute()) + '/' +'maxresdefault.jpg'
    sp.run(f'rm -f {script_path}History',shell=True,stdout=sp.DEVNULL)
    sp.run(f'rm -f {script_path}*jpg',shell=True,stdout=sp.DEVNULL)
    sp.run(f'rm -f {script_path}*png',shell=True,stdout=sp.DEVNULL)
    sp.run(f'cp -f {chromium_db} {script_path}',shell=True,stdout=sp.DEVNULL)

    con = sqlite3.connect('History')
    cur = con.cursor()
    res = cur.execute('select url from urls\
            where url like "%music.youtube%"\
            order by last_visit_time desc limit 5')
    if res is None:
        exit()

    ytURL = res.fetchone()[0]
    getURL = requests.get(ytURL, headers={"User-Agent":"Mozilla/5.0"})
    parsetoHTML = bs(getURL.content, 'html.parser')
    metacontent = parsetoHTML.find_all('meta', property='og:image')

    # {'property': 'og:image', 'content': 'https://i.ytimg.com/vi/hlS5O0UfYig/maxresdefault.jpg'}
    image = metacontent[0]['content']
    sp.run(f'wget -q {image} -O {script_path}maxresdefault.jpg',
           shell=True,stderr=sp.PIPE)
    sp.run(
    f'convert {script_path}maxresdefault.jpg -background White -gravity center\
            -extent 720x720 {script_path}maxresdefault.jpg'
            ,shell=True,stdout=sp.DEVNULL)
    sp.run(
    f'convert {script_path}maxresdefault.jpg -resize "640x640"\
            {script_path}maxresdefault.jpg',
            shell=True,stdout=sp.DEVNULL)
    #sp.run(f'convert -trim {cropimage} {cropimage}',
    #       shell=True,stdout=sp.DEVNULL)
    return ytURL

if __name__ == '__main__':
    print(get_cover_image())
