from __future__ import annotations

class Recipe:
    '''Base class for recipes'''

    @classmethod
    def group_by_dependency(cls, recipes: tuple[Recipe]) -> dict[tuple[Recipe]|None, tuple[Recipe]]:
        '''Given an iterable of recipes of this type, group them by shared dependencies'''
        return {None: recipes}
