import pytest
from pathlib import Path
from anvil.core.models import Dependency
from anvil.core.parsers.requirements import RequirementsParser
from anvil.core.parsers.pyproject import PyProjectParser

@pytest.fixture
def sample_req_file(tmp_path):
    p = tmp_path / "requirements.txt"
    p.write_text("requests==2.31.0\nnumpy>=1.0.0\n# comment\nflask")
    return p

@pytest.fixture
def sample_pyproject_file(tmp_path):
    p = tmp_path / "pyproject.toml"
    p.write_text("""
[project]
dependencies = [
    "django>=4.0",
    "fastapi==0.100.0"
]
    """)
    return p

def test_requirements_parser(sample_req_file):
    parser = RequirementsParser(sample_req_file)
    assert parser.can_handle()
    
    deps = parser.parse()
    assert len(deps) == 3
    
    d1 = deps[0]
    assert d1.name == "requests"
    assert d1.current_version == "2.31.0"
    assert d1.specifier == "==2.31.0"
    
    d2 = deps[1]
    assert d2.name == "numpy"
    assert d2.current_version is None
    assert d2.specifier == ">=1.0.0"

    d3 = deps[2]
    assert d3.name == "flask"
    assert d3.specifier == ""

def test_pyproject_parser(sample_pyproject_file):
    parser = PyProjectParser(sample_pyproject_file)
    assert parser.can_handle()
    
    deps = parser.parse()
    assert len(deps) == 2
    
    d1 = deps[0]
    assert d1.name == "django"
    assert d1.specifier == ">=4.0"
    
    d2 = deps[1]
    assert d2.name == "fastapi"
    assert d2.current_version == "0.100.0"
