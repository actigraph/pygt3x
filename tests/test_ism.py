from pygt3x.reader import FileReader


def test_ism_enabled(ism_enabled_file, ism_disabled_file):
    with FileReader(ism_enabled_file) as reader:
        df_enabled = reader.to_pandas()
        assert reader.idle_sleep_mode_activated
    with FileReader(ism_disabled_file) as reader:
        df_disabled = reader.to_pandas()
        assert not reader.idle_sleep_mode_activated
    assert (df_enabled.X.groupby(level=0).count() == 1).all()
    assert (
        df_enabled.loc[1616169537:1616169574, "X"]
        == df_enabled.loc[1616169537:1616169574, "X"].iloc[0]
    ).all()
    assert (df_enabled.index == df_disabled.index).all()
