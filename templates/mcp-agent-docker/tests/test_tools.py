"""Tests for {{AGENT_NAME}} tools."""

import pytest
import json


# TODO: Add your tests here

def test_example():
    """Example test - replace with real tests."""
    assert True


def test_diagnostic_format():
    """Test that diagnostic output follows the standard format."""
    # Example of expected format
    expected_keys = [
        "agent",
        "timestamp",
        "severity",
        "summary",
        "findings",
        "recommendations"
    ]

    # TODO: Call your diagnose tool and verify the format
    sample_diagnostic = {
        "agent": "{{AGENT_NAME}}",
        "timestamp": "2024-01-20T17:30:00Z",
        "severity": "normal",
        "summary": "No issues",
        "findings": [],
        "recommendations": []
    }

    for key in expected_keys:
        assert key in sample_diagnostic, f"Missing key: {key}"

    assert sample_diagnostic["severity"] in ["critical", "warning", "normal"]
