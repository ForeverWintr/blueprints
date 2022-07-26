import typing as tp

from frame_factory.recipes import Recipe

class FrameFactory:
    def build_recipe(self, recipes: tp.Iterable[Recipe]) -> tp.Any:
        '''Construct the given recipe, and return whatever it returns.'''
        asdf
