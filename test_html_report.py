import pytest
from src.reqman4 import main
import respx

@pytest.mark.asyncio
@respx.mock
async def test_html_report_failed_test_context(tmp_path):
    # Create a scenario file with a failing test
    scenario_content = """
RUN:
    - GET: http://localhost:8080/test
      tests:
        - R.status == 201
"""
    scenario_file = tmp_path / "scenario.yml"
    scenario_file.write_text(scenario_content)

    # Mock the HTTP request
    respx.get("http://localhost:8080/test").respond(200, text="OK")

    # Run the scenario
    r = main.ExecutionTests([str(scenario_file)])
    o = await r.execute()

    # Generate the HTML report
    html_report = "\n".join(o.htmls)

    # Check that the title attribute is present and contains the context
    assert 'R: {&quot;status&quot;: 200,' in html_report
