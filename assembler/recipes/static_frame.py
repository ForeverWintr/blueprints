import typing as tp
from pathlib import Path

import static_frame as sf
from frozendict import frozendict

from assembler.recipes.base import Recipe, DependenciesNeeded


class _FromDelimited(Recipe):
    """Base class for common file arguments"""

    file_path: Path
    index_column: str | None = None
    frame_extract_function: tp.Callable[..., sf.Frame] = sf.Frame.from_tsv
    frame_extract_kwargs: frozendict = frozendict()
    allow_missing: bool = False
    missing_data_exceptions: tp.Type[BaseException] = FileNotFoundError


# From Delimited?
# Multiindex?
# Just pass from_tsv args?
# Series from function? No because I want a frame recipe.
# Series from frame? Frame recipe and column/index? Seems a lot of work to create a frame recipe.
# Maybe that's fine given how early this is.
class SeriesFromDelimited(_FromDelimited):
    """A recipe for a series from a file"""

    column_name: str

    def get_dependencies(self) -> DependenciesNeeded:
        """Depends on seriesfromfile"""
        frame_recipe = FrameFromDelimited(
            file_path=self.file_path,
            index_column=self.index_column,
            frame_extract_function=self.frame_extract_function,
            frame_extract_kwargs=self.frame_extract_kwargs,
        )
        return DependenciesNeeded(frame_recipe)

    def extract_from_dependencies(self, dependencies: DependenciesNeeded) -> tp.Any:
        return frame[self.column_name]


class FrameFromDelimited(_FromDelimited):
    def extract_from_dependencies(self, *args: tp.Any) -> tp.Any:
        return self.frame_extract_function(self.file_path, **self.frame_extract_kwargs)


# Series from frame needs to provide args
# Series and frame from FS, with extractor function and args?
