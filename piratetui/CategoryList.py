from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from piratetui.Category import Category


class CategoryList:
    def __init__(self):
        self._categories: list['Category'] = []

    def add_category(self, category: 'Category'):
        self._categories += [category]

    def __getitem__(self, index):
        return self._categories[index]

    def __len__(self):
        return len(self._categories)
