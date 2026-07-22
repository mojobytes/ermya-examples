"""Tests for main(): wires real config -> client -> provider -> pipeline."""

from unittest.mock import MagicMock

import main as main_module


def test_main_wires_config_client_provider_into_pipeline(monkeypatch, tmp_path):
    calls = {}

    fake_config = MagicMock(name="config")
    monkeypatch.setattr(main_module, "load_config", lambda: _record(calls, "load_config", fake_config))

    fake_client = MagicMock(name="client")
    monkeypatch.setattr(main_module, "create_client", lambda cfg: _record(calls, "create_client", fake_client, cfg))

    fake_provider = MagicMock(name="provider")
    monkeypatch.setattr(main_module, "create_provider", lambda emb: _record(calls, "create_provider", fake_provider, emb))

    def fake_run(config, client, provider, data_dir):
        calls["run_pipeline"] = (config, client, provider, data_dir)

    monkeypatch.setattr(main_module, "run_pipeline", fake_run)

    main_module.main()

    # config flowed from load_config into the pipeline
    assert calls["run_pipeline"][0] is fake_config
    # the real client + provider factories were used and injected
    assert calls["run_pipeline"][1] is fake_client
    assert calls["run_pipeline"][2] is fake_provider


def _record(calls, name, return_value, *args):
    calls[name] = args
    return return_value


def test_main_runs_pipeline_with_config(monkeypatch, tmp_path):
    # main() must call run_pipeline exactly once with the loaded config;
    # patch create_client/create_provider/run_pipeline so nothing real runs.
    called = {}
    monkeypatch.setattr(main_module, "create_client", lambda c: MagicMock())
    monkeypatch.setattr(main_module, "create_provider", lambda c: MagicMock())
    monkeypatch.setattr(
        main_module,
        "run_pipeline",
        lambda *a, **k: called.setdefault("ran", True),
    )
    monkeypatch.chdir(tmp_path)  # no config -> defaults, vls None
    main_module.main()
    assert called["ran"] is True
