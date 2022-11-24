import typing as tp
from pathlib import Path

import static_frame as sf

from assembler.recipes.base import Recipe, Call


# From Delimited?
# Multiindex?
# Just pass from_tsv args?
# Series from function? No because I want a frame recipe.
# Series from frame? Frame recipe and column/index? Seems a lot of work to create a frame recipe.
class SeriesFromFile(Recipe):
    """A recipe for a series from a file"""

    file_path: Path
    column_name: str
    index_name: str | None = None
    frame_extract_function: tp.Callable[..., sf.Frame]
    frame_extract_kwargs: hmm

    def get_dependencies(self) -> Call:
        asdf

    def extract_from_dependencies(self, *args: tp.Any) -> tp.Any:
        asdf


class FrameFromFile(Recipe):
    file_path: Path

    def extract_from_dependencies(self, *args: tp.Any) -> tp.Any:
        asdf


# Series from frame needs to provide args
# Series and frame from FS, with extractor function and args?
