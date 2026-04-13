"""
Report generation for duplicate service cleanup tool.

Provides functionality to generate HTML and JSON reports of cleanup operations.
"""
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates cleanup operation reports."""

    def __init__(self):
        """Initialize report generator."""
        self._reports: List[Dict] = []

    def generate_html(self, output_path: str) -> str:
        """
        Generate an HTML report of cleanup results.

        Args:
            output_path: Path to save the HTML report

        Returns:
            Path to generated report
        """
        html = self._build_html_report()
        with open(output_path, 'w') as f:
            f.write(html)
        logger.info(f"HTML report saved: {output_path}")
        return output_path

    def generate_json(self, output_path: Optional[str] = None) -> Dict:
        """
        Generate a JSON report of cleanup results.

        Args:
            output_path: Optional path to save JSON report

        Returns:
            JSON report dictionary
        """
        report = self._build_json_report()

        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"JSON report saved: {output_path}")

        return report

    def add_result(self, result_type: str, data: Dict) -> None:
        """
        Add a result to the report.

        Args:
            result_type: Type of result (cleanup, migration, deletion)
            data: Result data to include
        """
        self._reports.append({
            "type": result_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        })

    def _build_html_report(self) -> str:
        """Build HTML report content."""
        html_parts = []
        html_parts.append(self._html_header())
        html_parts.append(self._html_summary())
        html_parts.append(self._html_details())
        html_parts.append(self._html_footer())

        return "\n".join(html_parts)

    def _html_header(self) -> str:
        """Return HTML header."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Duplicate Service Cleanup Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 1px solid #ddd; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
        .summary {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
        .success {{ color: green; }}
        .warning {{ color: orange; }}
        .error {{ color: red; }}
    </style>
</head>
<body>
    <h1>Duplicate Service Cleanup Report</h1>
    <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
"""

    def _html_summary(self) -> str:
        """Return HTML summary section."""
        summary = self._get_aggregated_summary()

        status_class = "success" if summary.get("success", False) else "warning"

        return f"""    <div class="summary">
        <h2>Summary</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Services</td><td>{summary.get('total_services', 0)}</td></tr>
            <tr><td>Duplicate Groups Found</td><td>{summary.get('duplicate_groups', 0)}</td></tr>
            <tr><td>Services Selected</td><td>{summary.get('services_selected', 0)}</td></tr>
            <tr><td>Services Deleted</td><td>{summary.get('services_deleted', 0)}</td></tr>
            <tr><td>Policy Migrations</td><td>{summary.get('policy_migrations', 0)}</td></tr>
            <tr><td>Group Migrations</td><td>{summary.get('group_migrations', 0)}</td></tr>
            <tr class="{status_class}"><td>Status</td><td>{'Success' if summary.get('success', False) else 'Completed with warnings'}</td></tr>
        </table>
    </div>
"""

    def _html_details(self) -> str:
        """Return HTML details section."""
        details = []
        for report in self._reports:
            details.append(f"""    <h2>{report['type'].upper()}</h2>
    <table>
        <tr><th>Key</th><th>Value</th></tr>""")
            for key, value in report['data'].items():
                details.append(f"        <tr><td>{key}</td><td>{value}</td></tr>")
            details.append("    </table>")

        return "\n".join(details) if details else "    <p>No report details available.</p>"

    def _html_footer(self) -> str:
        """Return HTML footer."""
        return """
</body>
</html>
"""

    def _build_json_report(self) -> Dict:
        """Build JSON report content."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": self._get_aggregated_summary(),
            "details": self._reports,
            "report_id": f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        }
        return report

    def _get_aggregated_summary(self) -> Dict:
        """Get aggregated summary from all reports."""
        summary = {
            "total_services": 0,
            "duplicate_groups": 0,
            "services_selected": 0,
            "services_deleted": 0,
            "policy_migrations": 0,
            "group_migrations": 0,
            "success": False,
        }

        for report in self._reports:
            if report['type'] == 'cleanup':
                data = report['data']
                summary['total_services'] = data.get('services_collected', 0)
                summary['duplicate_groups'] = data.get('duplicate_groups_found', 0)
                summary['services_selected'] = len(data.get('winners_selected', {}))
            elif report['type'] == 'deletion':
                data = report['data']
                summary['services_deleted'] = data.get('services_deleted', 0)
            elif report['type'] == 'migration':
                data = report['data']
                summary['policy_migrations'] = data.get('policies_updated', 0)
                summary['group_migrations'] = data.get('groups_updated', 0)
                if data.get('success'):
                    summary['success'] = True

        return summary

    def clear_reports(self) -> None:
        """Clear all stored reports."""
        self._reports = []
        logger.debug("Cleared reports")


def generate_duplicate_report(services: List[Dict]) -> str:
    """
    Generate a simple duplicate services report.

    Args:
        services: List of service information dictionaries

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("DUPLICATE SERVICES REPORT")
    lines.append("=" * 60)
    lines.append("")

    for service in services:
        name = service.get('name', 'unknown')
        protocol = service.get('protocol', 'unknown')
        port = service.get('port', 'unknown')
        usage = service.get('usage', 0)

        lines.append(f"Service: {name}")
        lines.append(f"  Protocol/Port: {protocol}/{port}")
        lines.append(f"  Usage Count: {usage}")
        lines.append("")

    return "\n".join(lines)