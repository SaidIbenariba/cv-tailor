from jobhunt import store


def test_load_sheet_creates_empty_with_columns(tmp_path):
    df = store.load_sheet(tmp_path / "jobs.xlsx")
    assert list(df.columns) == store.COLUMNS
    assert len(df) == 0


def test_upsert_appends_new_rows_as_NEW(job_factory):
    df = store.empty_frame()
    df = store.upsert(df, [job_factory(id="a"), job_factory(id="b")])
    assert len(df) == 2
    assert set(df["Status"]) == {"NEW"}


def test_upsert_is_idempotent_across_reruns(job_factory):
    df = store.empty_frame()
    df = store.upsert(df, [job_factory(id="a")])
    df = store.update_status(df, "a", "SENT")
    # Re-discovering the same job must not duplicate it or reset its status.
    df = store.upsert(df, [job_factory(id="a"), job_factory(id="c")])
    assert len(df) == 2
    assert df.loc[df["id"] == "a", "Status"].iloc[0] == "SENT"
    assert df.loc[df["id"] == "c", "Status"].iloc[0] == "NEW"


def test_update_status_sets_extra_fields(job_factory):
    df = store.empty_frame()
    df = store.upsert(df, [job_factory(id="a")])
    df = store.update_status(df, "a", "SCORED", Score=72)
    row = df.loc[df["id"] == "a"].iloc[0]
    assert row["Status"] == "SCORED"
    assert row["Score"] == 72


def test_save_and_reload_roundtrip(tmp_path, job_factory):
    path = tmp_path / "jobs.xlsx"
    df = store.empty_frame()
    df = store.upsert(df, [job_factory(id="a", title="DS Role")])
    store.save_sheet(df, path)
    reloaded = store.load_sheet(path)
    assert reloaded.loc[reloaded["id"] == "a", "title"].iloc[0] == "DS Role"
