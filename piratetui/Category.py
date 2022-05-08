from dataclasses import dataclass


@dataclass
class Category:
    name: str
    id: str
    link: str
    category_type: str
