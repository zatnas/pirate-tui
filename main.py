#!/data/data/com.termux/files/usr/bin/python
import json
import re
import curses
import curses.textpad
import requests
import os.path
import urllib.parse

from piratetui.CategoryList import CategoryList
from piratetui.Category import Category
from piratetui.TorrentItem import TorrentItem
from piratetui.TorrentItems import TorrentItems
from piratetui.Window import Window

FILENAMES = {
    "mirror": "mirror.txt",
    "proxy": "proxy.txt",
    "search": "search.txt",
    "category": "category.txt",
    "lastmirror": "lastmirror.txt",
    "lastsearch": "lastsearch.txt",
    "lastcategory": "lastcategory.txt",
}


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
    lastmirror_file = FILENAMES["lastmirror"]
    for site in mirror_hostnames:
        try:
            r = requests.get(site, timeout=5)
            if r.status_code == 200:
                return file_write(lastmirror_file, site)
        except Exception:
            continue
    raise Exception("No proxy found")


def tpb_get_proxy():
    mirror_hostnames = tpb_get_proxies()
    mirror = tpb_test_proxies(mirror_hostnames)
    return mirror


def tpb_get_search(
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


def tpb_parse_search(tpb_search: str):
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
    categories = CategoryList()
    categories_raw = re.findall(r'<dt>.*?</dd>', tpb_categories, re.DOTALL)
    categories.add_category(Category(
        name="Any",
        id="0",
        link="",
        category_type="MainCategory",
    ))
    for category_raw in categories_raw:
        main_category = re.search(
            r'''
            <dt>.*?"(?P<link>.*?/.*?/(?P<id>.*?))"
            .*?"(?P<name>.*?)">.*?</dt>
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
        sub_categories = re.finditer(
            r'''
            href="(?P<link>.*?/.*?/(?P<id>.*?))"
            .*?"(?P<name>.*?)"
            ''',
            category_raw,
            flags=re.DOTALL | re.VERBOSE)
        categories.add_category(Category(
            **main_category.groupdict(),
            category_type="MainCategory",
        ))
        for sub_category in sub_categories:
            subcat_dict = sub_category.groupdict()
            subcat_dict["name"] = f'{main_category["name"]} - {subcat_dict["name"]}'
            categories.add_category(Category(
                **subcat_dict,
                category_type="SubCategory",
            ))
    return categories


def main(screen: 'curses._CursesWindow'):
    mirror_file = FILENAMES["mirror"]
    search_file = FILENAMES["search"]
    category_file = FILENAMES["category"]
    lastmirror_file = FILENAMES["lastmirror"]
    lastsearch_file = FILENAMES["lastsearch"]
    lastcategory_file = FILENAMES["lastcategory"]

    if file_exists(lastmirror_file):
        mirror = file_read(lastmirror_file)
    else:
        mirror = tpb_get_proxy()

    if file_exists(lastsearch_file):
        search_text = file_read(lastsearch_file)
    else:
        search_text = "spiderman"
    if file_exists(search_file):
        piratesearch = file_read(search_file)
    else:
        piratesearch = tpb_get_search(mirror, search_text)

    category = Category()
    if file_exists(lastcategory_file):
        _ = json.loads(file_read(lastcategory_file))
        category.name = _["name"]
        category.id = _["id"]
    else:
        category.name = "Any"
        category.id = "0"
    page = 1
    if file_exists(category_file):
        piratecategory = file_read(category_file)
    else:
        piratecategory = tpb_get_categories(mirror)
    categories = tpb_parse_categories(piratecategory)

    search_list = tpb_parse_search(piratesearch)

    max_tcat = f'{search_list.max_tct}s'
    max_tscat = f'{search_list.max_tsc}s'
    max_tname = f'{search_list.max_tnm}s'
    max_tsize = f'{search_list.max_tsz}s'
    max_tseeder = f'{search_list.max_tsd}s'
    max_tleecher = f'{search_list.max_tlc}s'


    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    screen.keypad(True)
    screen.refresh()

    _, cols = screen.getmaxyx()

    win1 = curses.newwin(9, cols, 0, 0)
    win2 = curses.newwin(17, cols, 9, 0)
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
            win2.addstr(f'{item.torrent_subcategory:{max_tscat}} │ ', attribute)
            win2.addstr(f'{item.torrent_category:{max_tcat}} │ ', attribute)
            win2.addstr(f'{item.torrent_name:{max_tname}} ', attribute)
            win2.addstr(i+1, cols - 10 - search_list.max_tsz - search_list.max_tsd - search_list.max_tlc, f' │ {item.torrent_size:{max_tsize}} ', attribute)
            win2.addstr(i+1, cols - 6 - search_list.max_tsd - search_list.max_tlc, f'│ {item.torrent_seeder:{max_tseeder}} ', attribute)
            win2.addstr(i+1, cols - 4 - search_list.max_tlc, f'│ {item.torrent_leecher:{max_tleecher}} ', attribute)
        win1.addstr(1, 1, str(c))
        win1.addstr(2, 2, "Search: ")
        win1.addstr(6, 2, "Category: ")
        searchwin.addstr(0, 0, search_text)
        categorywin.addstr(1, 1, category.name)
        draw_windows()
        c = screen.getch()
        clear_windows()
        if c == 27 or c == ord('q'):
            break
        elif c == curses.KEY_UP or c == ord('k'):
            current_index -= 1 if current_index > 0 else 0
        elif c == curses.KEY_DOWN or c == ord('j'):
            current_index += 1 if current_index < max_index else 0
        elif c == ord('n'):
            page += 1
            search_list = tpb_parse_search(tpb_get_search(
                mirror,
                search_text,
                page=page,
                category=category.id
            ))
            max_index = len(search_list) - 1
        elif c == ord('p'):
            if page <= 1:
                continue
            page -= 1
            search_list = tpb_parse_search(tpb_get_search(
                mirror,
                search_text,
                page=page,
                category=category.id
            ))
            max_index = len(search_list) - 1
        elif c == ord('s'):
            searchwin.clear()
            searchwin.refresh()
            curses.curs_set(1)
            search_text = searchbox.edit()
            curses.curs_set(0)
            current_index = 0
            page = 0
            search_list = tpb_parse_search(tpb_get_search(
                mirror,
                search_text,
                page=page,
                category=category.id,
            ))
            max_tcat = f'{search_list.max_tct}s'
            max_tscat = f'{search_list.max_tsc}s'
            max_tname = f'{search_list.max_tnm}s'
            max_tsize = f'{search_list.max_tsz}s'
            max_tseeder = f'{search_list.max_tsd}s'
            max_tleecher = f'{search_list.max_tlc}s'
            max_index = len(search_list) - 1
        elif c == ord('r'):
            page = 1
            search_list = tpb_parse_search(tpb_get_search(
                mirror,
                search_text,
                page=page,
                category=category.id
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
                _ = Window(categorieswin, True)
                _.draw_border()
                for i in range(offset_category, offset_category + 8):
                    selected = (i - offset_category) == selected_category
                    attrib = curses.A_BOLD if selected else 0
                    category = categories[i]
                    categorieswin.addstr(i-offset_category+1, 1, category.name, attrib)
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
                    file_write(lastcategory_file, json.dumps({
                        "id": category.id,
                        "name": category.name,
                    }))
                    break


curses.wrapper(main)
