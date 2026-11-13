# Discovery worker tooling

This directory installs the genuine upstream `@cdxgen/cdxgen` 13.7.0 package. It
contains no vendored upstream source. Install using Node 24.22.3 (tested) or a
supported newer Node release meeting dependencies' >=24.15 requirement:

```sh
npm ci --ignore-scripts --omit=optional
npm audit --omit=optional
```

The lock pins dependency versions and hashes. `glob` 14.0.6 and `minimatch`
11.0.8 are explicit security overrides for GHSA-3g3m-2fjr-6pw4 and
GHSA-g3hv-75wg-m249. The upstream defaults resolved vulnerable transitive
versions; the patched override combination was tested with the actual adapter.
These overrides are limited in validation to this application's lockfile scan
mode; broader cdxgen capabilities are not enabled or certified by these tests.

The worker invokes Node directly, without npm/npx or shell shims. Set the
deployment environment `UAG_NODE_EXECUTABLE` to an absolute executable path if
the supported Node is not the default on PATH. This is never user-editable
integration configuration.

`UAG_SCAN_TMP_ROOT` optionally selects the staging directory. It must already
exist, be absolute and have no spaces anywhere in its path. The upstream secure
mode refuses paths with spaces and also refuses `.`. Health reports Not
configured when the selected root is unsupported. On this Windows workspace,
`D:\uag-scan-temp` was used to keep scan writes off the full C: drive; on Linux
the normal `/tmp` is suitable. This setting is deployment-controlled, never an
API parameter. Temporary scan subdirectories are removed after execution.

The accepted input has `package_json` and `package_lock` objects. Use a v3 npm
lockfile. Only registry package/version metadata is supported. Remove scripts,
workspaces and custom package configuration before submission; local/git/file
dependencies and arbitrary paths are rejected. This deliberately inventories a
lockfile without installing packages or claiming to inspect the installed tree.

The adapter stages the two files in a private temporary directory, runs with
Node filesystem permissions, denies child processes/addons, disables dependency
installation, Babel, recursion, Rust, formulation and network metadata lookup,
and supplies an environment without inherited credentials. It retains the exact
BOM text, parsed JSON, diagnostics and SHA-256 provenance. cdxgen's schema
validation remains enabled. No scan target path is accepted through the API.

Node filesystem permissions and cdxgen secure mode are defence in depth. Deploy
scanner workers with the application's CPU/memory/PID limits and network egress
restrictions. Node 24 permissions do not implement network isolation. The
upstream allowed-host setting is not a substitute for network policy.

From repository root, run the actual adapter test:

```sh
UAG_TEST_CDXGEN=1 python -m pytest tests/test_discovery_adapter.py -q
python scripts/verify_cdxgen.py
```

The CLI takes seconds, so it belongs exclusively in the background discovery
queue. It does not participate in low-latency LLM enforcement.
