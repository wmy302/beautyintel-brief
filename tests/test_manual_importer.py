from app.db.models import Source
from app.sources.manual_importer import ManualCSVImporter


def test_manual_importer_reads_csv():
    source = Source(name="手动导入", source_type="manual_csv", url="data/demo/sample_manual_import.csv", language="zh", country_or_region="CN")
    items = ManualCSVImporter().import_file(source)
    assert len(items) >= 8
    assert items[0].title


def test_manual_importer_converts_to_news_item():
    source = Source(name="手动导入", source_type="manual_csv", url="data/demo/sample_manual_import.csv", language="zh", country_or_region="CN")
    item = ManualCSVImporter().import_file(source)[0]
    assert item.source_name
    assert item.content_text

