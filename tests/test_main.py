import pytest

from superscript import __version__

from typer.testing import CliRunner

from superscript.main import app, convert_versionstring, Version


runner = CliRunner()


def test_version():
    assert __version__ == '0.1.0'


# just change the outcome and cli args

def test_urlfile():
    result = runner.invoke(app, ["urlfile", "https://didierstevens.com/files/software/oledump_V0_0_53.zip"])
    # assert result.exit_code == 0
    assert "oledump" in result.stdout
    assert "{'major': 0, 'minor': 0, 'fix': 53}" in result.stdout
    assert "zip" in result.stdout
    assert "200" in result.stdout


class TestVersioning:
    @pytest.mark.parametrize(
        "test_versionstring,major,minor,fix",
        [
            ("V0_0_53", 0, 0, 53),
            ("V0_53", 0, 53, 0),
            ("v1", 1, 0, 0),
            ("1-2", 1, 2, 0)
        ]
    )
    def test_convert_versionstring(self, test_versionstring, major, minor, fix):
        version = convert_versionstring(test_versionstring)
        assert version['major'] is major
        assert version['minor'] is minor
        assert version['fix'] is fix

    def test_Version(self):
        version = Version("V0_0_53")
        assert "v0.0.53" in version.get_versionstring()
        assert version.next_major() is 1
        assert version.next_minor() is 1
        assert version.next_fix() is 54
