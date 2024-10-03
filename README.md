[![Documentation Status](https://readthedocs.org/projects/duqtools/badge/?version=latest)](https://duqtools.readthedocs.io/en/latest/?badge=latest)
[![Tests](https://github.com/duqtools/duqtools/actions/workflows/test.yaml/badge.svg)](https://github.com/duqtools/duqtools/actions/workflows/test.yaml)
[![Tests (IMAS)](https://github.com/duqtools/duqtools/actions/workflows/test_imas.yaml/badge.svg)](https://github.com/duqtools/duqtools/actions/workflows/test_imas.yaml)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/duqtools)](https://pypi.org/project/duqtools/)
[![PyPI](https://img.shields.io/pypi/v/duqtools.svg?style=flat)](https://pypi.org/project/duqtools/)
[![DOI](https://zenodo.org/badge/492734189.svg)](https://zenodo.org/badge/latestdoi/492734189)
![Coverage](https://gist.githubusercontent.com/stefsmeets/ea916a5b3c3d9bc59065a7304e4ca707/raw/covbadge.svg)


![Duqtools banner](https://raw.githubusercontent.com/duqtools/duqtools/main/src/duqtools/data/logo.png)

# Duqtools

*Duqtools* is a tool for **D**ynamic **U**ncertainty **Q**uantification for Tokamak reactor simulations modelling.

Features:

- Set up 100s of simulation runs from a single template
- Launch standard sets of sensitivity tests with minimal programming
- Batch job submission and status tracking
- Supports the Standardized Interface Data Structures (IDSs) data directory
- Compare and visualize 100s of simulations in one overview
- Display simulation results as confidence ranges and distributions

*Duqtools* is currently under active development. It runs on linux only and requires the [ITER](http://iter.org/) Integrated Modeling and Analysis Suite ([IMAS](https://confluence.iter.org/display/IMP)).

To install:

```console
pip install duqtools
```

Or to use on the gateway:

```console
module use /gss_efgw_work/work/g2vazizi/duqtools/modules
module load duqtools/3.1.1
```

The source code is available from [Github](https://github.com/duqtools/duqtools).

Suggestions, improvements, and edits are most welcome.


## Development

Check out our [Contributing Guidelines](CONTRIBUTING.md#Getting-started-with-development) to get started with development.
