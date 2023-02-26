import typing as tp
from pathlib import Path
import functools

import static_frame as sf
import numpy as np
from frozendict import frozendict

from assembler.recipes.base import Recipe, DependencyRequest, Dependencies
from assembler.constants import MissingDependencyBehavior
from assembler import util


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


# FrameFromVerticalConcat
# FrameVertical
# FrameHorizontal
# FrameFromConcatH
# FrameFromConcatV
# FrameFromHConcat

# FrameFromRecipes
# concat = Vertical/Horizontal


# Do I still need index? Could call it 'filter'. But is it better to filter in the
# recipe itself? Doing so would let us apply a
# 'reindex_fill_value'/'missing_fill_value'. Also, an index allows you to expand missing values. In fact we might want it to ALWAYS be index. Or always allow both index and columns?
# Hconcat with series and columns would be weird. Would need to select series by label. You might also have missing data with no missing fill value. That's too complicate.

# Labels? Applied to index for vcat and columns for hcat.


class FrameFromRecipes(Recipe):
    """Create a frame by concatenating the result of other recipes (all of which should
    return frames or series).

    Args:
        recipes: a tuple of recipes, each of which should return a frame or series. By
        default, the indexes will be unioned.

        labels: A recipe, the result of which is used for the index labels in horizontal
        concatenation or column labels in vertical concatenation.

        axis: Argument to Frame.from_concat. 0 for vertical concatenation, 1 for
        horizontal.
    """

    recipes: tuple[Recipe, ...]
    labels: Recipe | None = None
    axis: int = 0

    ## Class level configuration
    on_missing_dependency: tp.ClassVar[
        MissingDependencyBehavior
    ] = MissingDependencyBehavior.BIND

    def get_dependencies(self) -> DependencyRequest:
        r = DependencyRequest(*self.recipes)
        if self.labels is not None:
            r.kwargs["labels"] = self.labels
        return r

    def extract_from_dependencies(self, dependencies: Dependencies) -> sf.Frame:
        """Missing dependencies become series using the final index. Missing index
        propogates."""

        not_missing = [
            x for x in dependencies.args if not isinstance(x, util.MissingPlaceholder)
        ]
        index = dependencies.kwargs.get("labels")
        if index is None:
            index = functools.reduce(sf.Index.union, (x.index for x in not_missing))
        elif not isinstance(index, sf.Index):
            index = sf.IndexAutoConstructorFactory(name=None)(index)

        to_concat = []
        for d in dependencies.args:
            if isinstance(d, util.MissingPlaceholder):
                d = sf.Series.from_element(d.fill_value, index=index, name=d.label)

            to_concat.append(d)

        return sf.Frame.from_concat(to_concat, index=index, axis=self.axis)


# Series from frame needs to provide args
# Series and frame from FS, with extractor function and args?
