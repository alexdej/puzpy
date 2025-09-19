import pytest

from tests import roundtrip_test


class PuzTestItem(pytest.Item):
    def __init__(self, name, path, **kwargs):
        super().__init__(name, **kwargs)
        self.filename = path

    def runtest(self):
        roundtrip_test(self.filename)


class PuzTestFile(pytest.File):
    def collect(self):
        return [PuzTestItem.from_parent(self, name='file', path=self.path)]


@pytest.hookimpl
def pytest_collect_file(file_path, path, parent):
    if file_path.match('testfiles/*.puz'):
        return PuzTestFile.from_parent(parent, path=file_path)
