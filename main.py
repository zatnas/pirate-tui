#!/data/data/com.termux/files/usr/bin/python
import json
import re
import curses
import requests
import os.path
import urllib.parse

from piratetui.CategoryList import CategoryList
from piratetui.Category import Category
from piratetui.Textbox import Textbox
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
    search_url = urllib.parse.quote(search)
    url = f'{hostname}/search/{search_url}/{page}/{sort}/{category}'
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


def select_category(
    screen: 'curses._CursesWindow',
    category_list: CategoryList,
):
    _, cols = screen.getmaxyx()

    win_sy = 7
    win_sx = 12
    win = Window(10, cols - 14, win_sy, win_sx)

    index_category = 0
    offset_category = 0
    max_index_category = len(category_list) - win_sy - 2
    while True:
        lastcategory_file = FILENAMES["lastcategory"]
        win = Window(10, cols - 14, 5, 12, border=True)
        win.draw_border()
        for i in range(offset_category, offset_category + 8):
            screen_index = i - offset_category
            selected = screen_index == index_category
            attrib = curses.A_BOLD if selected else 0
            category = category_list[i]
            win.addstr(screen_index, 1, category.name, attrib)
        win.refresh()
        c = screen.getch()
        win.clear()
        if c == 27 or c == ord('q'):
            return None
        elif c == curses.KEY_UP or c == ord('k'):
            if index_category > 0:
                index_category -= 1
            elif offset_category > 0:
                offset_category -= 1
            else:
                index_category = win_sy
                offset_category = max_index_category + 1
        elif c == curses.KEY_DOWN or c == ord('j'):
            if index_category < win_sy:
                index_category += 1
            elif offset_category <= max_index_category:
                offset_category += 1
            else:
                index_category = 0
                offset_category = 0
        elif c == curses.KEY_LEFT or c == ord('h'):
            if offset_category - (win_sy+1) >= 0:
                offset_category -= win_sy+1
            else:
                offset_category = 0
        elif c == curses.KEY_RIGHT or c == ord('l'):
            if offset_category + (win_sy+1) <= max_index_category:
                offset_category += win_sy+1
            else:
                offset_category = max_index_category + 1
        elif c == curses.KEY_ENTER or c == 10:
            index = offset_category + index_category
            category = category_list[index]
            file_write(lastcategory_file, json.dumps({
                "id": category.id,
                "name": category.name,
            }))
            return category


CATEGORY_TEXT = f"Category"
SUBCATEGORY_TEXT = f"Sub-Category"
TITLE_TEXT = f"Title"
SIZE_TEXT = f"Size"
SEEDERS_TEXT = f"Seeders"
LEECHERS_TEXT = f"Leechers"
CATEGORY_TEXT = f"{CATEGORY_TEXT:{len(CATEGORY_TEXT)}s}"
SUBCATEGORY_TEXT = f"{SUBCATEGORY_TEXT:{17}s}"
TITLE_TEXT = f"{TITLE_TEXT:{len(TITLE_TEXT)}s}"
SIZE_TEXT = f"{SIZE_TEXT:{11}s}"
SEEDERS_TEXT = f"{SEEDERS_TEXT:{len(SEEDERS_TEXT)}s}"
LEECHERS_TEXT = f"{LEECHERS_TEXT:{len(LEECHERS_TEXT)}s}"


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
        search_text = urllib.parse.unquote(file_read(lastsearch_file))
    else:
        search_text = "spiderman"
    if file_exists(search_file):
        piratesearch = file_read(search_file)
    else:
        piratesearch = tpb_get_search(mirror, search_text)

    if file_exists(lastcategory_file):
        category_data = json.loads(file_read(lastcategory_file))
    else:
        category_data = {
            "id": "0",
            "name": "Any",
        }
    category = Category(
        **category_data,
        link="",
        category_type=""
    )
    page = 1
    if file_exists(category_file):
        piratecategory = file_read(category_file)
    else:
        piratecategory = tpb_get_categories(mirror)
    categories = tpb_parse_categories(piratecategory)

    search_list = tpb_parse_search(piratesearch)

    def new_search():
        return tpb_parse_search(tpb_get_search(
            mirror,
            search_text,
            page=page,
            category=category.id
        ))

    def reset_maxlen():
        global max_tcat, max_tscat, max_tname, max_tsize, max_tseeder, max_tleecher
        max_tcat = f'{search_list.max_tct}s'
        max_tscat = f'{search_list.max_tsc}s'
        max_tname = f'{search_list.max_tnm}s'
        max_tsize = f'{search_list.max_tsz}s'
        max_tseeder = f'{search_list.max_tsd}s'
        max_tleecher = f'{search_list.max_tlc}s'
    reset_maxlen()

    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    screen.keypad(True)
    screen.refresh()

    screen_y, screen_x = screen.getmaxyx()

    win1 = Window(9, screen_x, 0, 0, border=True)
    win2 = Window(screen_y - 9, screen_x, 9, 0, border=True)
    searchwin = Window(3, screen_x - 16, 1, 12, border=True)
    searchbox = Textbox(searchwin.window)
    categorywin = Window(3, screen_x - 14, 5, 12, border=True)

    windows = [
        win1,
        win2,
        searchwin,
        categorywin,
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
        lhs_text, lhs_brdr, rhs_text, rhs_brdr = "", "", "", ""
        lhs_text += f" "
        lhs_text += f"{CATEGORY_TEXT}"
        lhs_text += f" │ "
        lhs_text += f"{SUBCATEGORY_TEXT}"
        lhs_text += f" │ "
        lhs_text += f"{TITLE_TEXT}"
        lhs_brdr += f"─"
        lhs_brdr += f"{'─'*len(CATEGORY_TEXT)}"
        lhs_brdr += f"─┼─"
        lhs_brdr += f"{'─'*len(SUBCATEGORY_TEXT)}"
        lhs_brdr += f"─┼─"
        lhs_brdr += f"{'─'*len(TITLE_TEXT)}"
        rhs_text += f"│ "
        rhs_text += f"{SIZE_TEXT}"
        rhs_text += f" │ "
        rhs_text += f"{SEEDERS_TEXT}"
        rhs_text += f" │ "
        rhs_text += f"{LEECHERS_TEXT}"
        rhs_text += f" "
        rhs_brdr += f"┼─"
        rhs_brdr += f"{'─'*len(SIZE_TEXT)}"
        rhs_brdr += f"─┼─"
        rhs_brdr += f"{'─'*len(SEEDERS_TEXT)}"
        rhs_brdr += f"─┼─"
        rhs_brdr += f"{'─'*len(LEECHERS_TEXT)}"
        rhs_brdr += f"─"
        title_maxlen = win2.sx - len(lhs_text) - len(rhs_text) + 4
        win2.addstr(0, 0, lhs_text)
        win2.addstr(1, 0, lhs_brdr)
        win2.addstr(0, win2.sx - len(rhs_text), rhs_text)
        win2.addstr(1, win2.sx - len(rhs_brdr), rhs_brdr)
        win2.addstr(1, len(lhs_brdr), "─" * (win2.sx - len(lhs_brdr) - len(rhs_brdr)))
        i = 0
        for item in search_list:
            selected_item = item == search_list[current_index]
            attribute = curses.A_BOLD if selected_item else 0
            win2.addstr(i+2, 1, "")
            win2.addstr(f'{item.subcategory[0:8]:8s} │ ', attribute)
            win2.addstr(f'{item.category[0:17]:17s} │ ', attribute)
            win2.addstr(i+2, win2.sx - len(rhs_brdr), "│ ", attribute)
            win2.addstr(f'{item.size[0:len(SIZE_TEXT)]:{len(SIZE_TEXT)}s} │ ', attribute)
            win2.addstr(f'{item.seeders[0:len(SEEDERS_TEXT)]:{len(SEEDERS_TEXT)}s} │ ', attribute)
            win2.addstr(f'{item.leechers[0:len(LEECHERS_TEXT)]:{len(LEECHERS_TEXT)}s}', attribute)
            name_line = 0
            for name_part in [item.name[x:x+title_maxlen] for x in range(0, len(item.name), title_maxlen)]:
                if name_line == 0:
                    win2.addstr(i+2, 32, name_part, attribute)
                else:
                    win2.addstr(i+2, 1, "", attribute)
                    win2.addstr(" "*len(CATEGORY_TEXT) + " │ ", attribute)
                    win2.addstr(" "*len(SUBCATEGORY_TEXT) + " │ ", attribute)
                    win2.addstr(f"{name_part:{title_maxlen}s} │ ", attribute)
                    win2.addstr(" "*len(SIZE_TEXT) + " │ ", attribute)
                    win2.addstr(" "*len(SEEDERS_TEXT) + " │ ", attribute)
                if len(name_part) < title_maxlen:
                    break
                name_line += 1
                if len(item.name) > title_maxlen * name_line:
                    i += 1
                else:
                    break
            i += 1
        win1.addstr(0, 0, str(c))
        win1.addstr(1, 4, "Search: ")
        win1.addstr(5, 2, "Category: ")
        searchwin.addstr(0, 1, search_text)
        categorywin.addstr(0, 1, category.name)
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
            search_list = new_search()
            reset_maxlen()
            max_index = len(search_list) - 1
        elif c == ord('p'):
            if page <= 1:
                continue
            page -= 1
            search_list = new_search()
            reset_maxlen()
            max_index = len(search_list) - 1
        elif c == ord('s'):
            searchwin.clear()
            searchwin.refresh()
            curses.curs_set(1)
            search_text = searchbox.edit()
            curses.curs_set(0)
            current_index = 0
            page = 0
            search_list = new_search()
            reset_maxlen()
            max_index = len(search_list) - 1
        elif c == ord('r'):
            page = 1
            search_list = new_search()
            reset_maxlen()
            max_index = len(search_list) - 1
        elif c == ord('c'):
            selected_category = select_category(screen, categories)
            if selected_category:
                category = selected_category


curses.wrapper(main)
