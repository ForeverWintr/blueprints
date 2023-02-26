from pathlib import Path
import typing as tp
import itertools

import static_frame as sf
import frame_fixtures as ff
import pytest

from assembler.recipes.static_frame import (
    FrameFromDelimited,
    SeriesFromDelimited,
    FrameFromRecipes,
)
from assembler.recipes.general import FromFunction, Object
from assembler.factory import Factory
from assembler import util


@pytest.fixture(scope="module")
def sample_frame() -> sf.Frame:
    return ff.parse("i(I,str)|c(I,str)|v(str,str,bool,float)|s(4,8)").rename(
        index="index"
    )


@pytest.fixture(scope="module")
def row_col_frame() -> sf.Frame:
    return sf.Frame.from_element(
        0, index=[f"i{x}" for x in range(3)], columns=[f"c{x}" for x in range(3)]
    )


@pytest.fixture(scope="module")
def date_index_frame(row_col_frame) -> sf.Frame:
    return


@pytest.fixture
def sample_tsv(sample_frame, tmp_path) -> Path:
    fp = tmp_path / "frame.tsv"
    sample_frame.to_tsv(fp)
    return fp


def test_frame_from_delimited(sample_tsv, sample_frame):
    r = FrameFromDelimited(file_path=sample_tsv, index_column="index")

    frame = Factory().process_recipe(r)
    assert frame.equals(sample_frame)


def test_series_from_delimited(sample_tsv):
    r = SeriesFromDelimited(
        file_path=sample_tsv, column_name="zZbu", index_column="index"
    )

    series = Factory().process_recipe(r)
    assert series.to_pairs() == (
        ("zZbu", "zjZQ"),
        ("ztsv", "zO5l"),
        ("zUvW", "zEdH"),
        ("zkuW", "zB7E"),
    )


@pytest.fixture
def missing_configurations(
    sample_tsv, tmp_path
) -> tp.Iterable[tp.Tuple[Factory, Path, str]]:
    factories = (Factory(), Factory(allow_missing=False))
    fps = (sample_tsv, tmp_path / "not_a_file.tsv")
    cols = ("zZbu", "not-a-column")
    return itertools.product(factories, fps, cols)


def test_allow_missing(missing_configurations, sample_frame):
    # This code to determine what is expected is more complex than I would like.
    for factory, fp, col in missing_configurations:
        recipe = SeriesFromDelimited(
            file_path=fp,
            column_name=col,
            allow_missing=True,
            index_column="index",
            missing_data_fill_value="missing",
        )
        err = None
        if col == "not-a-column":
            err = KeyError
        if fp.name == "not_a_file.tsv":
            err = FileNotFoundError

        if err == KeyError:
            if factory.allow_missing:
                assert factory.process_recipe(recipe).to_pairs() == (
                    ("zZbu", "missing"),
                    ("ztsv", "missing"),
                    ("zUvW", "missing"),
                    ("zkuW", "missing"),
                )
            else:
                with pytest.raises(err):
                    factory.process_recipe(recipe)

        elif err == FileNotFoundError:
            if factory.allow_missing:
                m = factory.process_recipe(recipe)
                assert isinstance(m, util.MissingPlaceholder)
            else:
                with pytest.raises(err):
                    factory.process_recipe(recipe)
        else:
            assert factory.process_recipe(recipe).to_pairs() == (
                ("zZbu", "zjZQ"),
                ("ztsv", "zO5l"),
                ("zUvW", "zEdH"),
                ("zkuW", "zB7E"),
            )


def test_frame_from_recipes(sample_frame):

    # I'm using FromFunction as an easy way to get a recipe that generates Frame/Series.
    series = FromFunction(function=lambda: sample_frame[sf.ILoc[1]])
    frame = FromFunction(function=lambda: sample_frame[sf.ILoc[2:4]])

    concat = FrameFromRecipes(recipes=(series, frame), axis=1)

    f = Factory()
    result = f.process_recipe(concat)
    assert sample_frame[sf.ILoc[1:4]].equals(result)


# row/col select, labels, axis, expected
class FRFixture(tp.NamedTuple):
    name: str
    col_select: sf.GetItemKeyType
    expected_index: str | list[str]
    expected_cols: str | list[str]
    extra: tuple[util.MissingPlaceholder] = ()
    labels: list[str] | None = None
    axis: int = 0

    def __str__(self) -> str:
        return self.name


FROM_RECIPES_CONFIGURATIONS = (
    FRFixture(
        name="simple",
        col_select=[["c0"], "c2"],
        labels=("i1", "i2"),
        expected_index=["i1", "i2"],
        expected_cols=["c0", "c2"],
    ),
    FRFixture(
        name="missing",
        col_select=[["c0"], "c2"],
        extra=(Object(payload=util.MissingPlaceholder(reason="test", fill_value=-1)),),
        labels=("i1", "i2"),
        expected_index=["i1", "i2"],
        expected_cols=["c0", "c2", "missing"],
    ),
    FRFixture(
        name="indexdate",
        col_select=[["c0"], "c2"],
        extra=(Object(payload=util.MissingPlaceholder(reason="test", fill_value=-1)),),
        labels=sf.IndexDate.from_date_range("2022-01-01", "2022-01-03"),
        expected_index=sf.IndexDate.from_date_range("2022-01-01", "2022-01-03"),
        expected_cols=["c0", "c2"],
    ),
)


@pytest.mark.parametrize("fixture", FROM_RECIPES_CONFIGURATIONS, ids=str)
def test_frame_from_recipes_labels(row_col_frame, fixture):
    inputs = [
        FromFunction(function=lambda x=row_col_frame[x]: x) for x in fixture.col_select
    ]
    inputs.extend(fixture.extra)

    recipe = FrameFromRecipes(
        recipes=tuple(inputs),
        labels=Object(payload=fixture.labels),
        axis=1,
        allow_missing=True,
    )
    f = Factory()
    result = f.process_recipe(recipe)
    assert (result.columns == fixture.expected_cols).all()
    assert (result.index == fixture.expected_index).all()

    # test all combinations of these
    # combining frame and columns
    # Missing placeholder
    # Labels
    # Labels multiindex
    # Labels IndexDate
    # Axis
    # Union index/Columns

    # Don't forget fill value.
    # axis 1,0
    # Columns/index None, series, autofactory, multiindex. Surprisingly a frame works too.
    # Missing


def test_frame_from_recipe_index_date(date_index_frame) -> None:
    recipe = FrameFromRecipes(
        recipes=(FromFunction(function=lambda: date_index_frame)),
        axis=1,
    )
    f = Factory()
    result = f.process_recipe(recipe)
    assert 0


def test_frame_from_recipes_missing(sample_frame):
    assert 0


def test_frame_from_recipes_different_index():
    assert 0
