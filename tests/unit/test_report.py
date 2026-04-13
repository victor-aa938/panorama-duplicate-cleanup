"""Unit tests for report generation."""
import pytest
import os
import json
import tempfile

from src.utils.report import ReportGenerator


def test_generate_html_report():
    """Test HTML report generation."""
    reporter = ReportGenerator()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        html_path = f.name
    
    try:
        reporter.generate_html(html_path)
        
        with open(html_path, 'r') as f:
            content = f.read()
        
        # Check for report title in h1 tag
        assert "<h1>Duplicate Service Cleanup Report</h1>" in content
    finally:
        os.unlink(html_path)


def test_generate_json_report():
    """Test JSON report generation."""
    reporter = ReportGenerator()
    
    report = reporter.generate_json()
    
    assert "generated_at" in report
    assert "summary" in report
    assert "details" in report


def test_add_result():
    """Test adding results to report."""
    reporter = ReportGenerator()
    
    reporter.add_result("cleanup", {"services": 100})
    reporter.add_result("deletion", {"deleted": 5})
    
    assert len(reporter._reports) == 2


def test_get_aggregated_summary():
    """Test aggregated summary generation."""
    reporter = ReportGenerator()
    
    reporter.add_result("cleanup", {"services_collected": 100})
    reporter.add_result("deletion", {"services_deleted": 5})
    
    summary = reporter._get_aggregated_summary()
    
    assert summary["total_services"] == 100
    assert summary["services_deleted"] == 5
