#!/data/data/com.termux/files/usr/bin/python
import json
import re
import curses
import curses.textpad
import requests
import os.path
import urllib.parse

from pprint import pprint

FILENAMES = {
    "mirror": "mirror.txt",
    "proxy": "proxy.txt",
    "search": "search.txt",
    "category": "category.txt",
    "lastsearch": "lastsearch.txt",
    "lastcategory": "lastcategory.txt",
}


class TorrentItem(object):
    def __init__(self, groupdict):
        self.torrent_category: str = groupdict["torrent_category"]
        self.torrent_subcategory: str = groupdict["torrent_subcategory"]
        self.torrent_link: str = groupdict["torrent_link"]
        self.torrent_name: str = groupdict["torrent_name"]
        self.torrent_magnet: str = groupdict["torrent_magnet"]
        self.torrent_date: str = groupdict["torrent_date"]
        self.torrent_size: str = groupdict["torrent_size"]
        self.torrent_seeder: str = groupdict["torrent_seeder"]
        self.torrent_leecher: str = groupdict["torrent_leecher"]
        _ = groupdict["author_link"]
        self.author_link: str = _
        if not _:
            self.author_link: str = ""
        self.author_name: str = groupdict["author_name"]


class TorrentItems(object):
    def __init__(self):
        self._items: list[TorrentItem] = []
        self.max_tct = 0
        self.max_tsc = 0
        self.max_tln = 0
        self.max_tnm = 0
        self.max_tmn = 0
        self.max_tdt = 0
        self.max_tsz = 0
        self.max_tsd = 0
        self.max_tlc = 0
        self.max_aln = 0
        self.max_anm = 0

    def add(self, torrentitem: TorrentItem):
        self._items.append(torrentitem)
        self.max_tct = max(self.max_tct, len(torrentitem.torrent_category))
        self.max_tsc = max(self.max_tsc, len(torrentitem.torrent_subcategory))
        self.max_tln = max(self.max_tln, len(torrentitem.torrent_link))
        self.max_tnm = max(self.max_tnm, len(torrentitem.torrent_name))
        self.max_tmn = max(self.max_tmn, len(torrentitem.torrent_magnet))
        self.max_tdt = max(self.max_tdt, len(torrentitem.torrent_date))
        self.max_tsz = max(self.max_tsz, len(torrentitem.torrent_size))
        self.max_tsd = max(self.max_tsd, len(torrentitem.torrent_seeder))
        self.max_tlc = max(self.max_tlc, len(torrentitem.torrent_leecher))
        self.max_aln = max(self.max_aln, len(torrentitem.author_link))
        self.max_anm = max(self.max_anm, len(torrentitem.author_name))

    def __getitem__(self, index) -> TorrentItem:
        return self._items[index]

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index >= len(self._items):
            raise StopIteration
        self._index += 1
        return self._items[self._index - 1]


class Window():
    def __init__(self, window: 'curses._CursesWindow', border: bool):
        self.window = window
        self.border = border

    def refresh(self):
        self.window.refresh()

    def clear(self):
        self.window.clear()

    def draw_border(self, ignore_property: bool = False):
        if not self.border and not ignore_property:
            return
        self.window.border("|", "|", "-", "-", "+", "+", "+", "+")


def file_exists(path: str):
    return os.path.exists(path)


def file_write(path: str, content: str):
    """
    Returns back the content given
    """
    with open(path, "w") as f:
        f.write(content)
    return content


def file_read(path: str):
    with open(path, "r") as f:
        return f.read()


def tpb_get_proxies() -> list[str]:
    mirror_file = FILENAMES["mirror"]
    r = requests.get("https://piratebayproxy.info/")
    mirrors = file_write(mirror_file, r.text)
    mirror_hostnames = re.findall(
        r'<td class="site">.*href="([^"]+)"',
        mirrors,
    )
    return mirror_hostnames


def tpb_test_proxies(mirror_hostnames: list[str]):
    mirror_file = FILENAMES["mirror"]
    for site in mirror_hostnames:
        try:
            r = requests.get(site, timeout=5)
            if r.status_code == 200:
                return file_write(mirror_file, site)
        except Exception:
            raise Exception("No proxy found")


def tpb_get_proxy():
    mirror_hostnames = tpb_get_proxies()
    mirror = tpb_test_proxies(mirror_hostnames)
    return mirror


def tpb_search(
    hostname: str,
    search: str,
    page: int = 1,
    sort: int = 99,
    category: int = 0,
):
    search_file = FILENAMES["search"]
    lastsearch_file = FILENAMES["lastsearch"]
    search = urllib.parse.quote(search)
    url = f'{hostname}/search/{search}/{page}/{sort}/{category}'
    r = requests.get(url)
    file_write(lastsearch_file, search)
    return file_write(search_file, r.text)


def tpb_search_parse(tpb_search: str):
    search_list = TorrentItems()
    tpb_search = tpb_search.replace('&nbsp;', ' ')
    for r in re.finditer(r"<tr>.*?vertTh.*?</tr>", tpb_search, re.DOTALL):
        r_raw = r.group(0)
        m = re.match(r"""
            .*?<a.*?>(?P<torrent_subcategory>.*?)</a.*?
            <a.*?>(?P<torrent_category>.*?)</a.*?
            detName.*?href="(?P<torrent_link>.*?)".*?
            >(?P<torrent_name>.*?)<.*?
            href="(?P<torrent_magnet>magnet.*?)".*?
            Uploaded\s*(?P<torrent_date>.*?),.*?
            Size\s*(?P<torrent_size>.*?),.*?
            ULed\s*by.*?
            (<a.*?href="(?P<author_link>.*?)".*?|<i)>
            (?P<author_name>.*?)<.*?
            <td.*?>(?P<torrent_seeder>.*?)<.*?
            <td.*?>(?P<torrent_leecher>.*?)<.*?
        """, r_raw, re.DOTALL | re.VERBOSE)
        search_list.add(TorrentItem(m.groupdict()))
    return search_list


def tpb_get_categories(hostname: str):
    category_file = FILENAMES["category"]
    r = requests.get(f"{hostname}/browse")
    return file_write(category_file, r.text)


def tpb_parse_categories(tpb_categories: str):
    categories_raw = re.findall(r'<dt>.*?</dd>', tpb_categories, re.DOTALL)
    categories = [{
        "href": "",
        "id": "0",
        "title": "Any",
    }]
    for category_raw in categories_raw:
        main_category = re.search(
            r'''
            <dt>.*?"(?P<href>.*?/.*?/(?P<id>.*?))"
            .*?"(?P<title>.*?)">.*?</dt>
            ''',
            category_raw,
            flags=re.DOTALL | re.VERBOSE
        )
        category_raw = re.sub(
            r'<dt>.*?</dt>',
            '',
            category_raw,
            flags=re.DOTALL
        )
        sub_category = re.finditer(
            r'''
            href="(?P<href>.*?/.*?/(?P<id>.*?))"
            .*?"(?P<title>.*?)"
            ''',
            category_raw,
            flags=re.DOTALL | re.VERBOSE)
        categories += [main_category.groupdict()]
        for subcat in sub_category:
            subcat_dict = subcat.groupdict()
            subcat_dict["title"] = f'{main_category["title"]} - {subcat_dict["title"]}'
            categories += [subcat_dict]
    return categories


def main(screen: 'curses._CursesWindow'):
    mirror_file = FILENAMES["mirror"]
    search_file = FILENAMES["search"]
    category_file = FILENAMES["category"]
    lastsearch_file = FILENAMES["lastsearch"]
    lastcategory_file = FILENAMES["lastcategory"]

    if file_exists(mirror_file):
        mirror = file_read(mirror_file)
    else:
        mirror = tpb_get_proxy()

    if file_exists(lastsearch_file):
        search_text = file_read(lastsearch_file)
    else:
        search_text = "spiderman"
    if file_exists(search_file):
        piratesearch = file_read(search_file)
    else:
        piratesearch = tpb_search(mirror, search_text)

    if file_exists(lastcategory_file):
        _ = json.loads(file_read(lastcategory_file))
        category_text, category_id = _["title"], _["id"]
    else:
        category_text = "Any"
        category_id = 0
    page = 1
    if file_exists(category_file):
        piratecategory = file_read(category_file)
    else:
        piratecategory = tpb_get_categories(mirror)
    categories = tpb_parse_categories(piratecategory)

    search_list = tpb_search_parse(piratesearch)

    max_tcat = f'{search_list.max_tct}s'
    max_tscat = f'{search_list.max_tsc}s'
    max_tname = f'{search_list.max_tnm}s'
    max_tsize = f'{search_list.max_tsz}s'
    max_tseeder = f'{search_list.max_tsd}s'
    max_tleecher = f'{search_list.max_tlc}s'

    mode = "select"

    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    screen.keypad(True)
    screen.refresh()

    _, cols = screen.getmaxyx()

    win1 = curses.newwin(9, cols, 0, 0)
    win2 = curses.newwin(20, cols, 8, 0)
    searchcontainer = curses.newwin(3, cols - 14, 1, 12)
    searchwin = curses.newwin(1, cols - 16, 2, 13)
    searchbox = curses.textpad.Textbox(searchwin)
    categorywin = curses.newwin(3, cols - 14, 5, 12)

    windows = [
        Window(win1, True),
        Window(win2, True),
        Window(searchcontainer, True),
        Window(searchwin, False),
        Window(categorywin, True),
    ]

    def draw_windows():
        [
            (window.draw_border(), window.refresh())
            for window in windows
        ]

    def clear_windows():
        [window.clear() for window in windows]

    c = None
    current_index = 0
    max_index = len(search_list) - 1
    while True:
        for i, item in enumerate(search_list):
            selected_item = i == current_index
            attribute = curses.A_BOLD if selected_item else 0
            win2.addstr(i+1, 1, "")
            [win2.addstr(d, attribute) for d in [
                f'{item.torrent_subcategory:{max_tscat}} ',
                f'{item.torrent_category:{max_tcat}} ',
                f'{item.torrent_name:{max_tname}} ',
                f'{item.torrent_size:{max_tsize}} ',
                f'{item.torrent_seeder:{max_tseeder}} ',
                f'{item.torrent_leecher:{max_tleecher}} ',
            ]]
        win1.addstr(1, 1, str(c))
        win1.addstr(2, 2, "Search: ")
        win1.addstr(6, 2, "Category: ")
        searchwin.addstr(0, 0, search_text)
        categorywin.addstr(1, 1, category_text)
        draw_windows()
        c = screen.getch()
        clear_windows()
        if mode == "select":
            if c == 27 or c == ord('q'):
                break
            elif c == curses.KEY_UP or c == ord('k'):
                current_index -= 1 if current_index > 0 else 0
            elif c == curses.KEY_DOWN or c == ord('j'):
                current_index += 1 if current_index < max_index else 0
            elif c == ord('n'):
                page += 1
                search_list = tpb_search_parse(tpb_search(
                    mirror,
                    search_text,
                    page=page,
                    category=category_id
                ))
            elif c == ord('p'):
                if page <= 1:
                    continue
                page -= 1
                search_list = tpb_search_parse(tpb_search(
                    mirror,
                    search_text,
                    page=page,
                    category=category_id
                ))
            elif c == ord('s'):
                searchwin.clear()
                searchwin.refresh()
                curses.curs_set(1)
                search_text = searchbox.edit()
                curses.curs_set(0)
                current_index = 0
                page = 0
                search_list = tpb_search_parse(tpb_search(
                    mirror,
                    search_text,
                    page=page,
                    category=category_id
                ))
                max_index = len(search_list) - 1
            elif c == ord('c'):
                selected_category = 0
                max_selected_category = len(categories) - 1 - 8
                offset_category = 0
                categorieswin = curses.newwin(10, cols - 14, 7, 12)
                while True:
                    lastcategory_file = FILENAMES["lastcategory"]
                    categorieswin = curses.newwin(10, cols - 14, 5, 12)
                    categorieswin.border("|", "|", "-", "-", "+", "+", "+" ,"+")
                    for i in range(offset_category, offset_category + 8):
                        selected = (i - offset_category) == selected_category
                        attrib = curses.A_BOLD if selected else 0
                        category = categories[i]
                        categorieswin.addstr(i-offset_category+1, 1, category["title"], attrib)
                    categorieswin.refresh()
                    cc = screen.getch()
                    categorieswin.clear()
                    if cc == 27 or cc == ord('q'):
                        break
                    elif cc == curses.KEY_UP or cc == ord('k'):
                        if selected_category > 0:
                            selected_category -= 1
                        else:
                            selected_category = 0
                            if offset_category > 0:
                                offset_category -= 1
                    elif cc == curses.KEY_DOWN or cc == ord('j'):
                        if selected_category < 7:
                            selected_category += 1
                        else:
                            selected_category = 7
                            if offset_category <= max_selected_category:
                                offset_category += 1
                    elif cc == curses.KEY_ENTER or cc == 10:
                        category = categories[offset_category + selected_category]
                        category_id = category["id"]
                        category_text = category["title"]
                        file_write(lastcategory_file, json.dumps({
                            "id": category_id,
                            "title": category_text,
                        }))
                        break



curses.wrapper(main)
