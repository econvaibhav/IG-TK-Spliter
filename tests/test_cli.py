"""Installed entry points, bounded prompts and installation diagnostics."""
import argparse
from types import SimpleNamespace

import pytest

from spliter import __version__
from spliter import cli as command_line
from spliter import doctor

from .conftest import cli, run_command


def test_installed_console_and_module_entry_points():
    console = run_command(["spliter", "--version"], text=True)
    module = cli("--version")
    assert console.stdout.strip() == module.stdout.strip() == f"Spliter {__version__}"
    assert "--platform" in cli("--help").stdout


@pytest.mark.parametrize("value,canonical", [
    ("ig", "instagram"), ("Instagram", "instagram"),
    ("tk", "tiktok"), (" TIKTOK ", "tiktok"),
])
def test_platform_aliases(value, canonical):
    assert command_line.parse_platform(value) == canonical


def test_missing_platform_fails_without_prompt(videos):
    result = cli(videos["odd_silent"], expected=2)
    assert "--platform" in result.stderr
    assert "non-interactive" in result.stderr
    assert "Platform [1/2]" not in result.stdout


def test_terminal_menu_retries_then_accepts(monkeypatch, capsys):
    monkeypatch.setattr(command_line.sys, "stdin", SimpleNamespace(isatty=lambda: True))
    answers = iter(["not a platform", "2"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    assert command_line.choose_platform(argparse.ArgumentParser()) == "tiktok"
    assert "Enter 1 / instagram / ig" in capsys.readouterr().out


def test_terminal_menu_handles_eof(monkeypatch, capsys):
    monkeypatch.setattr(command_line.sys, "stdin", SimpleNamespace(isatty=lambda: True))

    def exhausted_input(prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", exhausted_input)
    with pytest.raises(SystemExit) as stopped:
        command_line.choose_platform(argparse.ArgumentParser())
    assert stopped.value.code == 2
    assert "No platform selected" in capsys.readouterr().err


def test_terminal_menu_interrupt_is_clean(monkeypatch, tmp_path):
    monkeypatch.setattr(command_line.sys, "stdin", SimpleNamespace(isatty=lambda: True))

    def interrupted_input(prompt):
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", interrupted_input)
    assert command_line.main([str(tmp_path / "not_opened.mp4")]) == 130
    assert not list(tmp_path.iterdir())


def test_doctor_performs_real_encoder_check():
    result = cli("doctor")
    assert "Templates: 6 readable PNGs" in result.stdout
    assert "H.264/AAC export: encoded and verified" in result.stdout
    assert "Ready to split recordings." in result.stdout


def test_doctor_reports_missing_encoder(monkeypatch, capsys):
    original_run = doctor.run_command

    def encoder_unavailable(command):
        if "libx264" in command:
            raise RuntimeError("Unknown encoder 'libx264'")
        return original_run(command)

    monkeypatch.setattr(doctor, "run_command", encoder_unavailable)
    assert doctor.main([]) == 1
    output = capsys.readouterr().out
    assert "FAIL H.264/AAC export" in output
    assert "Unknown encoder 'libx264'" in output
    assert "Ready to split recordings." not in output
