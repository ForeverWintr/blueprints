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
    return ff.parse("v(str,str,bool,float)|s(4,8)")


@pytest.fixture
def sample_tsv(sample_frame, tmp_path) -> Path:
    fp = tmp_path / "frame.tsv"
    sample_frame.to_tsv(fp)
    return fp


def test_frame_from_delimited(sample_tsv):
    expected = sf.Frame.from_tsv(sample_tsv)

    r = FrameFromDelimited(file_path=sample_tsv)

    frame = Factory().process_recipe(r)
    assert frame.equals(expected)


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
    yield factories, fps, cols


def test_allow_missing(missing_configurations):
    # Configurations
    # factory allows and not
    # file exists and not
    # column exists and not

    # TODO make this a parameter
    for factory, fp, col in missing_configurations:
        asdf

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
