#!/data/data/com.termux/files/usr/bin/python
import re
import curses
import requests
import os.path

from pprint import pprint

lastmirror_file = "lastmirror.txt"
if not os.path.exists(lastmirror_file):
    pirateproxy_file = "pirateproxy.txt"
    if not os.path.exists(pirateproxy_file) or os.path.getsize(pirateproxy_file) == 0:
        with open(pirateproxy_file, "w") as f:
            r = requests.get("https://piratebayproxy.info/")
            f.write(r.text)
            proxy_html = r.text
    else:
        with open(pirateproxy_file, "r") as f:
            proxy_html = f.read()

    proxysites = re.findall('<td class="site">.*href="([^"]+)"', proxy_html)

    for site in proxysites:
        try:
            r = requests.get(site, timeout=5)
            print(site, r.status_code)
            if r.status_code == 200:
                mirror = site
                with open(lastmirror_file, "w") as f:
                    f.write(site)
                break
        except requests.exceptions.Timeout as e:
            print(site, "timeout")
else:
    with open(lastmirror_file, "r") as f:
        mirror = f.read()

search_text = "spiderman"
piratesearch_file = "piratesearch.txt"
# piratebay/search/SEARCH/PAGE/SORT
if not os.path.exists(piratesearch_file):
    r = requests.get(f'{mirror}/search/{search_text}')
    piratesearch = r.text
    with open(piratesearch_file, "w") as f:
        f.write(piratesearch)
else:
    with open(piratesearch_file, "r") as f:
        piratesearch = f.read()

search_list = []
piratesearch = piratesearch.replace('&nbsp;', ' ')
for r in re.finditer(r"<tr>.*?vertTh.*?</tr>", piratesearch, re.DOTALL):
    r_raw = r.group(0)
    m = re.match(r"""
        .*?<a.*?>(?P<subcategory>.*?)</a.*?
        <a.*?>(?P<category>.*?)</a.*?
        detName.*?href="(?P<torrent_link>.*?)".*?
        >(?P<torrent_name>.*?)<.*?
        href="(?P<torrent_magnet>magnet.*?)".*?
        Uploaded\s*(?P<torrent_date>.*?),.*?
        Size\s*(?P<torrent_size>.*?),.*?
        ULed\s*by.*?
        (<a.*?href="(?P<author_link>.*?)".*?>|
        <i>)(?P<author_name>.*?)<.*?
        <td.*?>(?P<torrent_seeder>.*?)<.*?
        <td.*?>(?P<torrent_leecher>.*?)<.*?
    """, r_raw, re.DOTALL | re.VERBOSE)
    search_list = search_list + [m.groupdict()]

screen = curses.initscr()
curses.start_color()
curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)

mode = "select"

curses.noecho()
curses.cbreak()
screen.keypad(True)
curses.curs_set(0)

maxlen_torrentname = f'{len(max(search_list, key=lambda x: len(x["torrent_name"]))["torrent_name"])}s'
maxlen_torrentsize = f'{len(max(search_list, key=lambda x: len(x["torrent_size"]))["torrent_size"])}s'
maxlen_torrentseeder = f'{len(max(search_list, key=lambda x: len(x["torrent_seeder"]))["torrent_seeder"])}s'
maxlen_torrentleecher = f'{len(max(search_list, key=lambda x: len(x["torrent_leecher"]))["torrent_leecher"])}s'

c = None
current_index = 0
max_index = len(search_list) - 1
while True:
    screen.addstr(0, 0, str(c))
    item = search_list[current_index]
    list_offset = 10
    for i, item in enumerate(search_list):
        selected_item = i == current_index
        appearance = 0
        if selected_item:
            appearance = curses.A_BOLD
        torrent_name = f'{item["torrent_name"]:{maxlen_torrentname}} '
        torrent_size = f'{item["torrent_size"]:{maxlen_torrentsize}} '
        torrent_seeder = f'{item["torrent_seeder"]:{maxlen_torrentseeder}} '
        torrent_leecher = f'{item["torrent_leecher"]:{maxlen_torrentleecher}} '
        screen.addstr(i + list_offset, 0, '')
        screen.addstr(torrent_name, appearance)
        screen.addstr(torrent_size, appearance)
        screen.addstr(torrent_seeder, appearance)
        screen.addstr(torrent_leecher, appearance)
    c = screen.getch()
    screen.clear()
    screen.refresh()
    if mode == "select":
        if c == 27 or c == ord('q'):
            break
        elif c == curses.KEY_UP or c == ord('k'):
            current_index -= 1 if current_index > 0 else 0
        elif c == curses.KEY_DOWN or c == ord('j'):
            current_index += 1 if current_index < max_index else 0
        elif c == ord('s'):
            mode = "search"
    elif mode == "search":
        if c == 27:
            mode = "select"
        elif c == 10:
            current_index += 1 if current_index < max_index else 0

curses.endwin()
