# Security policy

Please report vulnerabilities privately to the repository owner. Do not include
real CCTV frames, personal data, credentials, customer policies or site details.

The DSL is intentionally declarative: it contains no arbitrary code execution,
dynamic imports, regular expressions or user-defined functions. A production
deployment must still add authentication, tenant authorization, signed policy
packages, persistence, rate limits, audit logging and resource quotas.

