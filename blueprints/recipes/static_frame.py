from __future__ import annotations

import functools
import typing as tp
from pathlib import Path
from abc import abstractmethod

import numpy as np
import static_frame as sf
from frozendict import frozendict

from blueprints import util
from blueprints.constants import MissingDependencyBehavior
from blueprints.recipes.base import Dependencies, DependencyRequest, Recipe


class SeriesRecipe(Recipe):
    """Abstract class for recipes that return StaticFrame Series"""

    name: str

    @abstractmethod
    def extract_from_dependencies(self, dependencies: Dependencies) -> sf.Series:
        """Given a Dependencies object corresponding to the DependencyRequest returned
        by `get_dependency_request`, extract the data that this recipe describes and
        return a Series."""


class FrameRecipe(Recipe):
    """Abstract class for recipes that return StaticFrame Frames"""

    name: str

    @abstractmethod
    def extract_from_dependencies(self, dependencies: Dependencies) -> sf.Frame:
        """Given a Dependencies object corresponding to the DependencyRequest returned
        by `get_dependency_request`, extract the data that this recipe describes and
        return a Frame."""


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
        self, dependencies: Dependencies
    ) -> sf.Frame | util.MissingPlaceholder:
        """Missing dependencies become series using the final index. Missing index
        propogates."""
        not_missing = [
            x for x in dependencies.args if not isinstance(x, util.MissingPlaceholder)
        ]
        to_concat = []
        for r in self.recipes:
            d = dependencies.recipe_to_result[r]
            if isinstance(d, util.MissingPlaceholder):
                try:
                    label = r.name
                except AttributeError:
                    # Not all recipes have labels.
                    label = d.reason
                d = sf.Series.from_element(d.fill_value, name=label, index=labels)

            to_concat.append(d)

        label_kwarg = {direction: labels}
        return sf.Frame.from_concat(to_concat, axis=self.axis, **label_kwarg)


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
        self, dependencies: Dependencies
    ) -> sf.Frame | util.MissingPlaceholder:
        """Missing dependencies become series using the final index. Missing index
        propogates."""

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
