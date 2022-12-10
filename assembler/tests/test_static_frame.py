import static_frame as sf
import frame_fixtures as ff
import pytest

from assembler.recipes.static_frame import FrameFromDelimited, SeriesFromDelimited
from assembler.factory import Factory


@pytest.fixture
def sample_frame() -> sf.Frame:
    return ff.parse("v(str,str,bool,float)|s(4,8)")


def test_frame_from_delimited(tmp_path, sample_frame):
    fp = tmp_path / "frame.tsv"
    sample_frame.to_tsv(fp)
    expected = sf.Frame.from_tsv(fp)

    r = FrameFromDelimited(file_path=fp)

    frame = Factory().process_recipe(r)
    assert frame.equals(expected)


def test_series_from_delimited(tmp_path, sample_frame):
    fp = tmp_path / "frame.tsv"
    sample_frame.to_tsv(fp)
    r = SeriesFromDelimited(file_path=fp, column_name="0", index_column="__index0__")

    series = Factory().process_recipe(r)
    assert series.to_pairs() == ((0, "zjZQ"), (1, "zO5l"), (2, "zEdH"), (3, "zB7E"))
