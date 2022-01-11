import os

from jinja2 import Template

TEMPLATE = Template(
    """
<html>
<head>
<style>
body {
  font-family: sans-serif;
}
th.rotate {
  height: 140px;
  white-space: nowrap;
}
th.rotate > div {
  transform: translate(10px, 51px) rotate(315deg);
  width: 30px;
}
tr.result > td {
  height: 30px;
  text-align: center;
}
tr.result > td.pass {
  background: lightgreen;
}
tr.result > td.fail {
  background: pink;
}
tr.result > td.xfail {
  background: orange;
}
tr.result > td.not-implemented {
  background: lightgrey;
}
</style>
</head>
<body>
<h1>SDMX web services</h1>
<p>
  This page shows the results of automatic tests run for the <a
  href="https://github.com/khaeru/sdmx"><code>sdmx1</code></a> Python package. The
  package includes built-in support for the following known SDMX REST web services.
</p>
<p>Notes:</p>
{% set run_url=env["GITHUB_REPOSITORY"] + "/actions/runs/" + env["GITHUB_RUN_ID"] %}
<ol>
  <li>
    Services where only the <code>data</code> endpoint is tested are those supporting
    SDMX-JSON only. Although the SDMX-JSON standard <em>does</em> specify formats for
    JSON structure messages, <code>sdmx1</code>—and most existing SDMX-JSON-only web
    services—support only data queries.
  </li>
  <li>
    If this run was triggered on GitHub Actions, a complete log may be <a
    href="https://github.com/{{ run_url }}">here</a>; under “Jobs”, select “services”.
  </li>
</ol>
<table>
<thead>
  <tr>
    <th>Source</td>
    {% for resource in resources %}
    <th class="rotate"><div>{{ resource.name }}</div></td>
    {% endfor %}
  </tr>
</thead>
{% for source_id, results in data.items() %}
<tr class="result">
  <td><strong>{{ source_id }}</strong></td>
  {% for resource in resources %}
  {% set result = results.get(resource) %}
  <td class="{{ result }}">{{ abbrev.get(result) }}</td>
  {% endfor %}
</tr>
{% endfor %}
</table>

<p>Table key:</p>
<table>
<tr class="result">
  <td class="pass">✔</td>
  <td style="text-align: left">Pass</td>
</tr>
<tr class="result">
  <td class="fail">✘</td>
  <td style="text-align: left">Fail</td>
</tr>
<tr class="result">
  <td class="xfail">✔</td>
  <td style="text-align: left">
    Known/expected failure; see GitHub for related issue(s).
  </td>
</tr>
<tr class="result">
  <td class="not-implemented"></td>
  <td style="text-align: left">
    Web service does not implement this endpoint; not queried.
  </td>
</tr>
<tr class="result">
  <td>—</td>
  <td style="text-align: left">No test for this endpoint</td>
</tr>
</table>
</body>
</html>
"""
)

ABBREV = {
    "not-implemented": "",
    "pass": "✔",
    "xfail": "✔",
    "fail": "✘",
    None: "—",
}


class ServiceReporter:
    def __init__(self, config):
        self.path = config.invocation_params.dir.joinpath(
            "service-endpoints", "index.html"
        )
        self.path.parent.mkdir()
        self.data = {}
        self.resources = set()

    def pytest_runtest_makereport(self, item, call):
        try:
            assert call.when == "call"
            source_id = item.cls.source_id
            endpoint = item.funcargs["endpoint"]
        except (AssertionError, AttributeError, KeyError):
            return

        self.data.setdefault(source_id, dict())

        xfail_classes = list(
            map(
                lambda m: m.kwargs["raises"],
                filter(lambda m: m.name == "xfail", item.own_markers),
            )
        )

        try:
            if call.excinfo.type is NotImplementedError:
                result = "not-implemented"
            elif xfail_classes:
                result = "xfail" if xfail_classes[0] is call.excinfo.type else "fail"
            else:
                result = str(call.excinfo.type)
        except AttributeError:
            result = "pass"

        self.resources.add(endpoint)
        self.data[source_id][endpoint] = result

    def pytest_sessionfinish(self, session, exitstatus):
        if not self.data:
            return
        with open(self.path, "w") as f:
            f.write(
                TEMPLATE.render(
                    data=self.data,
                    abbrev=ABBREV,
                    resources=sorted(self.resources),
                    env=os.environ,
                )
            )
