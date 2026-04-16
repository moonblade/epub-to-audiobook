"""Pytest configuration and fixtures."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# Test directories
TEST_DIR = Path(__file__).parent
FIXTURES_DIR = TEST_DIR / "fixtures"


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def jobs_dir(temp_dir: Path) -> Path:
    """Create a temporary jobs directory."""
    jobs = temp_dir / "jobs"
    jobs.mkdir()
    return jobs


@pytest.fixture
def uploads_dir(temp_dir: Path) -> Path:
    """Create a temporary uploads directory."""
    uploads = temp_dir / "uploads"
    uploads.mkdir()
    return uploads


@pytest.fixture
def output_dir(temp_dir: Path) -> Path:
    """Create a temporary output directory."""
    output = temp_dir / "output"
    output.mkdir()
    return output


@pytest.fixture
def sample_epub(temp_dir: Path) -> Path:
    """Create a minimal sample EPUB for testing.
    
    Note: This is a minimal valid EPUB structure.
    For real testing, use a proper EPUB file.
    """
    epub_path = temp_dir / "sample.epub"
    
    # Create a minimal EPUB (ZIP file with specific structure)
    import zipfile
    
    with zipfile.ZipFile(epub_path, 'w') as zf:
        # mimetype must be first and uncompressed
        zf.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        
        # META-INF/container.xml
        container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
        zf.writestr('META-INF/container.xml', container_xml)
        
        # OEBPS/content.opf
        content_opf = '''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:identifier id="uid">test-epub-001</dc:identifier>
        <dc:title>Test Book</dc:title>
        <dc:language>en</dc:language>
    </metadata>
    <manifest>
        <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
        <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    </manifest>
    <spine>
        <itemref idref="chapter1"/>
    </spine>
</package>'''
        zf.writestr('OEBPS/content.opf', content_opf)
        
        # OEBPS/chapter1.xhtml
        chapter1 = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 1</title></head>
<body>
<h1>Chapter 1: The Beginning</h1>
<p>This is the first paragraph of the test book. It contains some sample text for testing the EPUB to audio conversion.</p>
<p>Here is another paragraph with more content to ensure we have enough text to test the chunking functionality.</p>
</body>
</html>'''
        zf.writestr('OEBPS/chapter1.xhtml', chapter1)
        
        # OEBPS/nav.xhtml (navigation document)
        nav = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Navigation</title></head>
<body>
<nav epub:type="toc">
<ol>
<li><a href="chapter1.xhtml">Chapter 1: The Beginning</a></li>
</ol>
</nav>
</body>
</html>'''
        zf.writestr('OEBPS/nav.xhtml', nav)
    
    return epub_path
