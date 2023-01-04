import typing as tp
from pathlib import Path

import static_frame as sf
import numpy as np
from frozendict import frozendict

from assembler.recipes.base import Recipe, DependencyRequest, Dependencies


class _FromDelimited(Recipe):
    """Base class for common file arguments"""

    file_path: Path
    index_column: str | None = None
    frame_extract_function: tp.Callable[..., sf.Frame] = sf.Frame.from_tsv
    frame_extract_kwargs: frozendict = frozendict()


# From Delimited?
# Multiindex?
# Just pass from_tsv args?
# Series from function? No because I want a frame recipe.
# Series from frame? Frame recipe and column/index? Seems a lot of work to create a frame recipe.
# Maybe that's fine given how early this is.
class SeriesFromDelimited(_FromDelimited):
    """A recipe for a series from a file"""

    column_name: str
    missing_data_fill_value: tp.Any = np.nan

    def get_dependencies(self) -> DependencyRequest:
        """Depends on seriesfromfile"""
        frame_recipe = FrameFromDelimited(
            file_path=self.file_path,
            index_column=self.index_column,
            frame_extract_function=self.frame_extract_function,
            frame_extract_kwargs=self.frame_extract_kwargs,
            allow_missing=self.allow_missing,
        )
        return DependencyRequest(frame_recipe)

    def extract_from_dependencies(self, dependencies: Dependencies) -> tp.Any:
        frame = dependencies.args[0]

        try:
            series = frame[self.column_name]
        except KeyError:
            if dependencies.metadata.factory_allow_missing and self.allow_missing:
                series = sf.Series.from_element(
                    self.missing_data_fill_value,
                    index=frame.index,
                    name=self.column_name,
                )
            else:
                raise

        return series


class FrameFromDelimited(_FromDelimited):
    """A recipe for a frame from a file"""

    missing_data_exceptions: tp.Type[BaseException] = FileNotFoundError

    def extract_from_dependencies(self, _: Dependencies) -> tp.Any:
        f = self.frame_extract_function(self.file_path, **self.frame_extract_kwargs)
        if self.index_column:
            f = f.set_index(self.index_column, drop=True)
        return f


class FrameFromConcat(Recipe):
    """Create a frame by concatenating the result of other recipes (all of which should return frames or series).

    Args:
        columns: a tuple of recipes, each of which should return a frame or series. By default, the indexes will be unioned.
        index: A recipe that produces a static_frame Index subclass. If provided, this index will be used for the resulting frame.
    """

    columns: tuple[Recipe, ...]
    index: Recipe | None = None
    axis: int = 0

    def get_dependencies(self) -> DependencyRequest:
        return DependencyRequest(*self.columns, index=self.index)

    def extract_from_dependencies(self, dependencies: Dependencies) -> sf.Frame:
        return sf.Frame.from_concat(
            dependencies.args, index=dependencies.kwargs["index"], axis=self.axis
        )


# Series from frame needs to provide args
# Series and frame from FS, with extractor function and args?
