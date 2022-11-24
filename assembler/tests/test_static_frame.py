import static_frame as sf
import frame_fixtures as ff
import pytest

from assembler.recipes.static_frame import SeriesFromFile
from assembler.factory import Factory


@pytest.fixture
def sample_frame() -> sf.Frame:
    return ff.parse("v(str,str,bool,float)|s(4,8)")


def test_series_from_file(tmp_path, sample_frame):
    fp = tmp_path / "frame.tsv"
    sample_frame.to_tsv(fp)
    r = SeriesFromFile(file_path=fp)

    series = Factory.process_recipe(r)
    assert 0
