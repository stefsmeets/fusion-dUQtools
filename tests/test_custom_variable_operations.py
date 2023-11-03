from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest
import yaml
from pytest import TEST_DATA

from duqtools.apply_model import apply_model
from duqtools.config import Config
from duqtools.ids import IDSMapping
from duqtools.schema import IDSOperation, IDSVariableModel
from duqtools.systems import get_system

EXTRA_VARS = TEST_DATA / 'config_list-vars.yaml'  # type: ignore

assert_equal = np.testing.assert_array_equal


@pytest.fixture(scope='module')
def tmpworkdir():
    with tempfile.TemporaryDirectory() as workdir:
        shutil.copytree(TEST_DATA / 'template_model',
                        Path(workdir) / 'template_model')
        yield Path(workdir)


def gen_sample_data():

    class t0:
        x = np.array((10., 20., 30.))
        x_error_upper = np.array((11., 22., 33.))
        x_error_lower = np.array((8., 16., 24.))

        y = np.array((100., 200., 300.))
        y_error_upper = np.array((110., 220., 330.))

        test = np.array((3., 3., 3.))

    class Data:
        data = [
            t0,
        ]
        time = np.array((0, ))

    return IDSMapping(Data)


def get_test_var(path):
    return IDSVariableModel(
        name='var',
        path=path,
        ids='test',
        dims=[],
    )


TEST_INPUT = (
    # custom with input variables
    # IDS only
    {
        'operator': 'custom',
        'variable': get_test_var('data/0/x'),
        'value': 2.0,
        'custom_code': 'var["test"] * value * data',  # data times 6
        'input_variables': ['test'],
    },
    # IDS with Jetto input_variables
    {
        'operator': 'custom',
        'variable': get_test_var('data/0/x'),
        'value': 2.0,
        'custom_code': 'var["test"] * var["major_radius"]',
        'input_variables': ['test', 'major_radius'],
    },
    # Jetto only
)

TEST_OUTPUT = (
    # custom with input variables
    # IDS only
    (60, 120, 180),
    # IDS with Jetto input_variables
    (918, 918, 918),
    # Jetto only
)


@pytest.mark.parametrize('model,output', zip(TEST_INPUT, TEST_OUTPUT))
def test_apply_model(model, output, tmpworkdir):
    data = gen_sample_data()
    model = IDSOperation(**model)
    with open(EXTRA_VARS) as f:
        config_dict = {'system': {'name': 'jetto'}} | yaml.safe_load(f)
    config = Config.from_dict(config_dict)
    system = get_system(cfg=config)
    apply_model(model,
                ids_mapping=data,
                system=system,
                run_dir=tmpworkdir / 'template_model')

    assert_equal(data[model.variable.path], output)
