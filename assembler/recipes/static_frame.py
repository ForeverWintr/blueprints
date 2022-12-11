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
    missing_data_exceptions: tp.Type[BaseException] = FileNotFoundError

    def extract_from_dependencies(self, _: Dependencies) -> tp.Any:
        f = self.frame_extract_function(self.file_path, **self.frame_extract_kwargs)
        if self.index_column:
            f = f.set_index(self.index_column)
        return f


# Series from frame needs to provide args
# Series and frame from FS, with extractor function and args?
