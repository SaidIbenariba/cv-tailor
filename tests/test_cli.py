from jobhunt import cli, store


def test_run_discover_scores_and_persists(tmp_path, monkeypatch, base_config, job_factory):
    jobs = [
        job_factory(id="ds", title="Data Scientist",
                    description="python deep learning nlp data"),
        job_factory(id="barista", title="Barista", description="make coffee"),
    ]
    monkeypatch.setattr(cli, "load_config", lambda p: base_config)
    monkeypatch.setattr(cli, "discover", lambda c: jobs)

    xlsx = tmp_path / "jobs.xlsx"
    cli.run_discover(prefs="x", sheet=xlsx)

    df = store.load_sheet(xlsx)
    assert df.loc[df["id"] == "ds", "Status"].iloc[0] == "SCORED"
    assert df.loc[df["id"] == "barista", "Status"].iloc[0] == "FILTERED"


def test_build_parser_has_three_commands():
    parser = cli.build_parser()
    sub = {a.dest: a for a in parser._subparsers._group_actions}  # noqa: SLF001
    args = parser.parse_args(["send", "--dry-run"])
    assert args.command == "send"
    assert args.dry_run is True
    assert parser.parse_args(["discover"]).command == "discover"
    assert parser.parse_args(["draft"]).command == "draft"
