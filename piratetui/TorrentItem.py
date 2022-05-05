class TorrentItem(object):
    def __init__(self, groupdict: dict):
        self.category: str = groupdict["torrent_category"]
        self.subcategory: str = groupdict["torrent_subcategory"]
        self.link: str = groupdict["torrent_link"]
        self.name: str = groupdict["torrent_name"]
        self.magnet: str = groupdict["torrent_magnet"]
        self.date: str = groupdict["torrent_date"]
        self.size: str = groupdict["torrent_size"]
        self.seeders: str = groupdict["torrent_seeder"]
        self.leechers: str = groupdict["torrent_leecher"]
        _ = groupdict["author_link"]
        self.author_link: str = _
        if not _:
            self.author_link: str = ""
        self.author_name: str = groupdict["author_name"]