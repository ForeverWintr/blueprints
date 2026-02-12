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
        final_index = sf.Index.from_union(*(x.index for x in not_missing))
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

    @staticmethod
    def _make_column_recipe_pairs(
        frame: sf.Frame,
        requested_by: frozenset[Column],
    ) -> list[tuple[str, Column]]:
        """Return pairs of (column_name, requesting_recipe) for all requesting recipes.
        Note that two recipes may request the same column with different duplicate
        handling."""
        col_to_recipe = {}
        for r in requested_by:
            col_to_recipe.setdefault(r.source_name, []).append(r)

        col_recipe_pairs = []
        for c in frame.columns:
            if c in col_to_recipe:
                for r in col_to_recipe[c]:
                    col_recipe_pairs.append((c, r))
        return col_recipe_pairs

    def extract_from_dependencies(
        self,
        dependencies: Dependencies,
        requested_by: frozenset[Column],
        config: frozendict[str, tp.Any],
    ) -> sf.Frame:
        frame: sf.Frame = dependencies.args[0]

        # Short circuit if there are no duplicates.
        if not frame[self.new_index_label].duplicated().any():
            return frame.set_index(self.new_index_label)

        # There are duplicates. Apply duplicate handlers.

        col_recipe_pairs = self._make_column_recipe_pairs(
            frame=frame, requested_by=requested_by
        )

        index = []
        rows = []
        for new_idx, group in frame.iter_group_items(self.new_index_label):
            index.append(new_idx)
            if group.size == 1:
                # No duplicates; do not call handlers.
                row = [group[c] for c, _ in col_recipe_pairs]
            else:
                row = []
                for colname, recipe in col_recipe_pairs:
                    row.append(recipe.reindex_duplicate_handler(recipe, group))
            rows.append(row)

        columns = [r for _, r in col_recipe_pairs]
        return sf.Frame.from_records(
            rows,
            index=index,
            index_constructor=sf.IndexAutoConstructorFactory,
            columns=columns,
        ).rename(index=self.new_index_label)


class Column(SeriesRecipe):
    """A Column from a frame, optionally reindexed.

    Args:
        name: The name of the resulting series.

        source_name: the name of the source column in `frame`. Defaults to `name`.

        reindex_by: A source column to reindex by.

        reindex_duplicate_handler: If `reindex_by` is set to a column with duplicates,
        this function is called once per each group of duplicate rows. Receives this
        recipe and all columns for each duplicate value.
    """

    name: str
    frame: FrameRecipe
    source_name: str | None = None
    reindex_by: str | None = None
    reindex_duplicate_handler: tp.Callable[[tp.Self, sf.Frame], tp.Any] | None = None

    def __post_init__(self):
        if self.source_name is None:
            object.__setattr__(self, "source_name", self.name)

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
        frame = dependencies.kwargs["frame"]
        series = frame[self]
        return series.rename(self.name)
