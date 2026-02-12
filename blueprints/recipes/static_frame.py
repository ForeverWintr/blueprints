from __future__ import annotations

import functools
import typing as tp
from abc import abstractmethod
from pathlib import Path
import dataclasses

import numpy as np
import static_frame as sf
from frozendict import frozendict

from blueprints import util
from blueprints.constants import MissingDependencyBehavior
from blueprints.recipes.base import Dependencies
from blueprints.recipes.base import DependencyRequest
from blueprints.recipes.base import Recipe
from blueprints.recipes import FromFunction


class SeriesRecipe(Recipe):
    """Abstract class for recipes that return StaticFrame Series"""

    name: str

    @abstractmethod
    def extract_from_dependencies(
        self,
        dependencies: Dependencies,
        requested_by: frozenset[Recipe],
        config: frozendict[str, tp.Any],
    ) -> sf.Series:
        """Extract the data this recipe describes.

        Args:
            dependencies: a Dependencies object corresponding to the DependencyRequest
            returned by `get_dependency_request` above. Dependent recipes have been
            requested_by: The recipes that requested this recipe.
            config: A dictionary containing user defined configuration.
        """


class FrameRecipe(Recipe):
    """Abstract class for recipes that return StaticFrame Frames"""

    name: str

    @abstractmethod
    def extract_from_dependencies(
        self,
        dependencies: Dependencies,
        requested_by: frozenset[Recipe],
        config: frozendict[str, tp.Any],
    ) -> sf.Frame:
        """Extract the data this recipe describes.

        Args:
            dependencies: a Dependencies object corresponding to the DependencyRequest
            returned by `get_dependency_request` above. Dependent recipes have been
            requested_by: The recipes that requested this recipe.
            config: A dictionary containing user defined configuration.
        """


class FrameFromFunction(FrameRecipe):
    name: str
    from_function: FromFunction

    def get_dependency_request(self) -> DependencyRequest:
        """Return a DependencyRequest specifiying recipes that this recipe depends on."""
        return DependencyRequest(self.from_function)

    def extract_from_dependencies(
        self,
        dependencies: Dependencies,
        requested_by: frozenset[Recipe],
        config: frozendict[str, tp.Any],
    ) -> sf.Frame:
        return dependencies.args[0].rename(self.name)


# TODO frame recipe
class _FromDelimited(Recipe):
    """Base class for common file arguments"""

    file_path: Path
    index_column: str | None = None
    frame_extract_function: tp.Callable[..., sf.Frame] = sf.Frame.from_tsv
    frame_extract_kwargs: frozendict = frozendict()

    @classmethod
    def from_serializable_dict(cls, data: dict, key_to_recipe: dict) -> tp.Self:
        data["file_path"] = Path(data["file_path"])
        return super().from_serializable_dict(data, key_to_recipe)

    def to_serializable_dict(self, recipe_to_key: frozendict) -> dict:
        d = super().to_serializable_dict(recipe_to_key)
        d["file_path"] = str(d["file_path"])
        return d


class SeriesFromDelimited(_FromDelimited):
    """A recipe for a series from a file"""

    column_name: str
    missing_data_fill_value: tp.Any = np.nan

    def get_dependency_request(self) -> DependencyRequest:
        """Depends on seriesfromfile"""
        frame_recipe = FrameFromDelimited(
            file_path=self.file_path,
            index_column=self.index_column,
            frame_extract_function=self.frame_extract_function,
            frame_extract_kwargs=self.frame_extract_kwargs,
            allow_missing=self.allow_missing,
        )
        return DependencyRequest(frame_recipe)

    def extract_from_dependencies(
        self,
        dependencies: Dependencies,
        requested_by: frozenset[Recipe],
        config: frozendict[str, tp.Any],
    ) -> sf.Series:
        """Extract the data this recipe describes.

        Args:
            dependencies: a Dependencies object corresponding to the DependencyRequest
            returned by `get_dependency_request` above. Dependent recipes have been
            requested_by: The recipes that requested this recipe.
            config: A dictionary containing user defined configuration.
        """
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

    def extract_from_dependencies(
        self,
        dependencies: Dependencies,
        requested_by: frozenset[Recipe],
        config: frozendict[str, tp.Any],
    ) -> sf.Frame:
        """Extract the data this recipe describes.

        Args:
            dependencies: a Dependencies object corresponding to the DependencyRequest
            returned by `get_dependency_request` above. Dependent recipes have been
            requested_by: The recipes that requested this recipe.
            config: A dictionary containing user defined configuration.
        """
        f = self.frame_extract_function(self.file_path, **self.frame_extract_kwargs)
        if self.index_column:
            f = f.set_index(self.index_column, drop=True)
        return f


class FrameFromColumns(FrameRecipe):
    """Return a frame by horizontal concat of all the provided recipes"""

    recipes: tuple[SeriesRecipe | FrameRecipe, ...]

    ## Class level configuration
    on_missing_dependency: tp.ClassVar[MissingDependencyBehavior] = (
        MissingDependencyBehavior.BIND
    )

    def get_dependency_request(self) -> DependencyRequest:
        return DependencyRequest(*self.recipes)

    def extract_from_dependencies(
        self,
        dependencies: Dependencies,
        requested_by: frozenset[Recipe],
        config: frozendict[str, tp.Any],
    ) -> sf.Frame | util.MissingPlaceholder:
        """Extract the data this recipe describes.

        Args:
            dependencies: a Dependencies object corresponding to the DependencyRequest
            returned by `get_dependency_request` above. Dependent recipes have been
            requested_by: The recipes that requested this recipe.
            config: A dictionary containing user defined configuration.
        """

        not_missing = [
            x for x in dependencies.args if not isinstance(x, util.MissingPlaceholder)
        ]
        final_index = sf.Index.from_union(x.index for x in not_missing)
        to_concat = []
        for r in self.recipes:
            d = dependencies.recipe_to_result[r]
            if isinstance(d, util.MissingPlaceholder):
                try:
                    label = r.name
                except AttributeError:
                    # Not all recipes have labels.
                    label = d.reason
                d = sf.Series.from_element(d.fill_value, name=label, index=final_index)

            to_concat.append(d)

        return sf.Frame.from_concat(to_concat, axis=1)


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

    recipes: tuple[SeriesRecipe | FrameRecipe, ...]
    labels: Recipe | None = None
    axis: int = 0

    ## Class level configuration
    on_missing_dependency: tp.ClassVar[MissingDependencyBehavior] = (
        MissingDependencyBehavior.BIND
    )

    def get_dependency_request(self) -> DependencyRequest:
        r = DependencyRequest(*self.recipes)
        if self.labels is not None:
            r.kwargs["labels"] = self.labels
        return r

    def extract_from_dependencies(
        self,
        dependencies: Dependencies,
        requested_by: frozenset[Recipe],
        config: frozendict[str, tp.Any],
    ) -> sf.Frame | util.MissingPlaceholder:
        """Extract the data this recipe describes.

        Args:
            dependencies: a Dependencies object corresponding to the DependencyRequest
            returned by `get_dependency_request` above. Dependent recipes have been
            requested_by: The recipes that requested this recipe.
            config: A dictionary containing user defined configuration.
        """

        direction = "columns"
        if self.axis:
            direction = "index"

        not_missing = [
            x for x in dependencies.args if not isinstance(x, util.MissingPlaceholder)
        ]
        labels = dependencies.kwargs.get("labels")
        if labels is None:
            labels = functools.reduce(
                sf.Index.union, (getattr(x, direction) for x in not_missing)
            )
        elif isinstance(labels, util.MissingPlaceholder):
            # The frame can't be built without labels. Propagate missing.
            return labels
        elif not isinstance(labels, sf.Index):
            labels = sf.IndexAutoConstructorFactory(name=None)(labels)

        to_concat = []
        for r in self.recipes:
            d = dependencies.recipe_to_result[r]
            if isinstance(d, util.MissingPlaceholder):
                try:
                    label = r.label
                except AttributeError:
                    # Not all recipes have labels.
                    label = d.reason
                d = sf.Series.from_element(d.fill_value, name=label, index=labels)

            to_concat.append(d)

        label_kwarg = {direction: labels}
        return sf.Frame.from_concat(to_concat, axis=self.axis, **label_kwarg)


class _Reindexer(FrameRecipe):
    """Used internally when a recipe requests column(s) from a reindexed frame. Not
    intended as a standalone recipe"""

    frame: FrameRecipe
    new_index_label: str
    name: str = dataclasses.field(init=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "name", self.frame.name)

    def get_dependency_request(self) -> DependencyRequest:
        return DependencyRequest(self.frame)

    def extract_from_dependencies(
        self,
        dependencies: Dependencies,
        requested_by: frozenset[Column],
        config: frozendict[str, tp.Any],
    ) -> sf.Frame:
        frame: sf.Frame = dependencies.args[0]

        # Sort for stability between runs.
        requestors = sorted(requested_by, key=lambda r: r.name)
        requested_cols = sorted(set(r.name for r in requestors)) + [
            self.new_index_label
        ]

        # Filter frame to only contain requested cols. We don't know how to handle
        # duplicates otherwise.
        frame = frame[requested_cols]

        # Short circuit if there are no duplicates.
        if not frame[self.new_index_label].duplicated().any():
            return frame.set_index(self.new_index_label)

        # There are duplicates. Apply duplicate handlers.
        index = []
        rows = []
        for new_idx, group in frame.iter_group_items(self.new_index_label):
            if group.shape[0] == 1:
                raise NotImplementedError("TR WIP")
            else:
                raise NotImplementedError("TR WIP")


def assert_all_equal(col: str, group: sf.Frame) -> tp.Any:
    """A duplicate handler for ReindexedFrame that fails if the duplicates are not identical, then returns the first"""
    raise NotImplementedError("TR WIP")


class ReindexedFrame(FrameRecipe):
    """A Frame with one of its columns set as index

    Args:
        frame: A recipe that produces the frame to be reindexed.
        new_index_label: The column to reindex by.

        column_to_duplicate_handler: A mapping from column label to a duplicate handling
        function. The function receives the column name and each group of duplicates,
        and should return a single value. For example, when reindexing security level
        weights by company id, the function will be called for each company that has
        more than one security. It will recieve all rows corresponding to that company,
        and should return a single number representing that company's weight. The
        resulting frame is guaranteed to contain all columns mentioned in this mapping,
        but may also contain other columns.
    """

    frame: FrameRecipe
    new_index_label: str
    column_to_duplicate_handler: frozendict[
        str, tp.Callable[[str, sf.Frame], tp.Any]
    ] = frozendict()

    name: str = dataclasses.field(init=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "name", self.frame.name)

    def get_dependency_request(self) -> DependencyRequest:
        return DependencyRequest(self.frame)

    def extract_from_dependencies(
        self,
        dependencies: Dependencies,
        requested_by: tuple[Column, ...],
        config: frozendict[str, tp.Any],
    ) -> sf.Frame:
        [frame] = dependencies.args

        # Short circuit if there are no duplicates.
        if not frame[self.new_index_label].duplicated().any():
            return frame.set_index(self.new_index_label)

        dup_hanlders = self.column_to_duplicate_handler
        if self.new_index_label not in dup_hanlders:
            raise NotImplementedError("TR WIP")


class Column(SeriesRecipe):
    """A Column from a frame, optionally reindexed"""

    name: str
    frame: FrameRecipe
    reindex_by: str | None = None
    reindex_duplicate_handler: tp.Callable[[str, sf.Frame], tp.Any] | None = None

    def get_dependency_request(self) -> DependencyRequest:
        return DependencyRequest(
            frame=_Reindexer(frame=self.frame, new_index_label=self.reindex_by)
        )

    def extract_from_dependencies(
        self,
        dependencies: Dependencies,
        requested_by: tuple[Column, ...],
        config: frozendict[str, tp.Any],
    ) -> sf.Series:
        # ReindexedFrame has already ensured the index is set as we requested.
        return dependencies.kwargs[self.name]
