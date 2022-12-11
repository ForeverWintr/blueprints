from pathlib import Path
import typing as tp
import itertools

import static_frame as sf
import frame_fixtures as ff
import pytest

from assembler.recipes.static_frame import FrameFromDelimited, SeriesFromDelimited
from assembler.factory import Factory


@pytest.fixture
def sample_frame() -> sf.Frame:
    return ff.parse("i(I,str)|v(str,str,bool,float)|s(4,8)")


@pytest.fixture
def sample_tsv(sample_frame, tmp_path) -> Path:
    fp = tmp_path / "frame.tsv"
    sample_frame.to_tsv(fp)
    return fp


def test_frame_from_delimited(sample_tsv, sample_frame):
    r = FrameFromDelimited(file_path=sample_tsv, index_column="__index0__")

    frame = Factory().process_recipe(r)
    assert frame.equals(sample_frame)


def test_series_from_delimited(sample_tsv):
    r = SeriesFromDelimited(
        file_path=sample_tsv, column_name="0", index_column="__index0__"
    )

    series = Factory().process_recipe(r)
    assert series.to_pairs() == ((0, "zjZQ"), (1, "zO5l"), (2, "zEdH"), (3, "zB7E"))


@pytest.fixture
def missing_configurations(
    sample_tsv, tmp_path
) -> tp.Iterable[tp.Tuple[Factory, Path, str]]:
    factories = (Factory(), Factory(allow_missing=False))
    fps = (sample_tsv, tmp_path / "not_a_file.tsv")
    cols = ("0", "not-a-column")
    return itertools.product(factories, fps, cols)


def test_allow_missing(missing_configurations, sample_frame):
    # Configurations
    # factory allows and not
    # file exists and not
    # column exists and not

    # TODO make this parametrize
    for factory, fp, col in missing_configurations:
        recipe = SeriesFromDelimited(
            file_path=fp,
            column_name=col,
            allow_missing=True,
            index_column="__index0__",
            missing_data_fill_value="missing",
        )
        err = None
        if col == "not-a-column":
            err = KeyError
        if fp.name == "not_a_file.tsv":
            err = FileNotFoundError

        if err:
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
        else:
            assert factory.process_recipe(recipe).to_pairs() == (
                ("zZbu", "zjZQ"),
                ("ztsv", "zO5l"),
                ("zUvW", "zEdH"),
                ("zkuW", "zB7E"),
            )

    f = Factory()
    # missing column in existing file. With index.
    r = f.process_recipe(
        SeriesFromDelimited(
            file_path=sample_tsv, column_name="not there", index_column="__index0__"
        )
    )

    # missing column in existing file. Without index.
    r = f.process_recipe(
        SeriesFromDelimited(file_path=sample_tsv, column_name="not there")
    )

    # missing file.

    r = f.process_recipe(
        SeriesFromDelimited(file_path=sample_tsv, column_name="not there")
    )
    assert 0
