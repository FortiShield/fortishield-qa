---
name: 'Test: API'
about: Test suite for the API.
title: ''
labels: ''
assignees: ''

---

# API test

| Version | Revision | Branch |
| --- | --- | --- |
| x.y.z | rev | branch |

## Installation

- [ ] Install API in a cluster of two nodes. One of the nodes must be a custom directory install. All agents must report to the worker node.
- [ ] Check API status is running in both nodes.

## Configuration

- [ ] Custom user, password and https working.

## Calls

### Certificates and HTTPS

- [ ] Install certificates.
- [ ] Run query using HTTPS.

### Test mocha

Required tests:

- Agents.
- Decoders.
- Manager.
- Cluster.
- Rootcheck.
- Rules.
- Syscheck.
- Syscollector.

Checks:

- [ ] Master node:
    - [ ] Ubuntu 18.
    - [ ] CentOS 7.
    - [ ] CentOS 6.
