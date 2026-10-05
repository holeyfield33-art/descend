from descend.steward.dashboard import render_reviews


def test_model_html_is_escaped_and_unsupported_findings_are_withheld():
    page = render_reviews([{"repo": "<repo>", "sha": "123456abcdef", "status": "reviewed",
                            "review": {"findings": [{"path": "a.py", "line": 2,
                                                     "severity": "high", "reason": "<script>alert(1)</script>",
                                                     "evidence": "x < y", "verification": "check"}],
                                       "rejected": [{"index": 1, "reason": "bad evidence"}],
                                       "accounted_upper_bound_usd": 0.001}}])
    assert "<script>" not in page
    assert "&lt;repo&gt;" in page
    assert "unsupported citation(s) withheld" in page
