class Category:
    def __init__(
        self,
        id: str = None,
        name: str = None,
        link: str = None,
        category_type: str = None,
    ):
        self.name = name
        self.id = id
        self.link = link
        self.type = category_type