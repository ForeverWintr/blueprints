from __future__ import annotations
import typing as tp
from abc import ABC, abstractmethod
import dataclasses


class Recipe(ABC):
    """Base class for recipes"""

    def get_dependency_recipes(self) -> tuple[Recipe, ...]:
        """Return a tuple of recipes that this recipe depends on"""
        return ()

    @abstractmethod
    def extract_from_dependency(self, *args: tp.Any) -> tp.Any:
        """Given positional dependencies, extract the data that this recipe describes. args will be
        the results of instantiating the recipes returned by `get_dependency_recipes` above"""

    ### Below this line, methods are internal and not intended to be overriden.

    def __init_subclass__(cls, **kwargs) -> None:
        r = dataclasses.dataclass(cls, frozen=True, repr=False, kw_only=True)  # type: ignore
        assert r is cls

    def _is_not_default(
        self, attribute: str, fields: tp.Dict[str, dataclasses.Field]
    ) -> bool:
        """
        Return true if the specified attribute is not its default
        """
        return (
            attribute in fields
            and getattr(self, attribute) is not fields[attribute].default
        )

    def pformat(self, indent="", indent_increase="    "):
        """Generate a multiline representation of this recipe, for easier visual inspection."""
        fields = {f.name: f for f in dataclasses.fields(self)}
        non_default = (
            (k, v) for k, v in fields.items() if self._is_not_default(k, fields)
        )
        to_display = {k: getattr(self, k) for k, _ in non_default}

        lines = [f"{indent}{self.__class__.__name__}("]
        next_indent = indent + indent_increase
        for name, value in to_display.items():
            # For now I assume the only iterable we need to worry about is tuples. This should be
            # enforced somewhere else in the recipe framework,
            if name != "label" and isinstance(value, tuple):
                lines.append(f"{next_indent}{name}=(")
                inner = next_indent + indent_increase
                for sub in value:
                    if isinstance(sub, Recipe):
                        lines.append(
                            f"{sub.pformat(indent=inner, indent_increase=indent_increase)},"
                        )
                    else:
                        lines.append(f"{inner}{sub!r},")
                lines.append(f"{next_indent}),")

            else:
                lines.append(f"{next_indent}{name}={value!r},")

        lines.append(f"{indent})")
        return "\n".join(lines)

    def __repr__(self):
        """Customize repr to only include fields that aren't the default value"""
        return self.pformat()
