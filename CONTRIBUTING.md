# Contributing

Use a branch and keep the app independently deployable. Run `pytest`, frontend tests/build and relevant real adapter checks. Keep mock tests isolated; never claim a mock proves upstream integration. Add source/version/licence evidence before adding an adapter. Extend typed schemas and negative tenant-isolation tests with each resource. Preserve raw outputs and clearly label normalization limits.

Do not commit secrets or confidential test artefacts. Use synthetic fixtures. Update the integration register, dependency locks, changelog and deployment documentation with meaningful changes. Public publishing and integration into Guardrail Sovereign require explicit owner authorization.
