from piratetui.TorrentItem import TorrentItem

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
        self.max_tct = max(self.max_tct, len(torrentitem.category))
        self.max_tsc = max(self.max_tsc, len(torrentitem.subcategory))
        self.max_tln = max(self.max_tln, len(torrentitem.link))
        self.max_tnm = max(self.max_tnm, len(torrentitem.name))
        self.max_tmn = max(self.max_tmn, len(torrentitem.magnet))
        self.max_tdt = max(self.max_tdt, len(torrentitem.date))
        self.max_tsz = max(self.max_tsz, len(torrentitem.size))
        self.max_tsd = max(self.max_tsd, len(torrentitem.seeder))
        self.max_tlc = max(self.max_tlc, len(torrentitem.leecher))
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