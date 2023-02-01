import logging
from math import prod
from pathlib import Path
from string import Template

from ..config import Config
from ..operations import op_queue
from ..utils import no_op, read_imas_handles_from_file

logger = logging.getLogger(__name__)

DUMMY_VARS = {
    'TEMPLATE_USER': 'user',
    'TEMPLATE_DB': 'db',
    'TEMPLATE_SHOT': 123,
    'TEMPLATE_RUN': 456,
    'RUN_NAME': 'run_x',
    'RUN_IN_START': 10,  # v210921
    'RUN_OUT_START': 20,  # v210921
}


class SetupError(Exception):
    ...


def _generate_run_dir(drc: Path, cfg: str, force: bool):
    drc.mkdir(exist_ok=force, parents=True)

    with open(drc / 'duqtools.yaml', 'w') as f:
        f.write(cfg)


class ExtrasV210921:
    """Track run number to avoid overwriting existing data in sequential
    runs."""
    MAX_RUN = 9999

    def __init__(self, cfg: Config):
        self.n_samples = self._get_n_samples(cfg)
        self.current_run_number = 0

    @staticmethod
    def _get_n_samples(cfg: Config) -> int:
        """Grab number of samples generated by this config, from
        1. `sampler.n_samples`
        2. As a product of the number of dimensions.
        """
        if not cfg.create:
            raise SetupError('Config has no section `create`.')

        try:
            n_samples = cfg.create.sampler.n_samples
        except AttributeError:
            matrix = (model.expand() for model in cfg.create.dimensions)
            n_samples = prod([len(model) for model in matrix])

        return n_samples

    def update_mapping(self, mapping: dict):
        """Update mapping with run numbers."""
        run_in_start = self.current_run_number
        run_out_start = run_in_start + self.n_samples
        self.current_run_number = run_out_start + self.n_samples

        if self.current_run_number > self.MAX_RUN:
            raise ValueError(
                f'Cannot write data with run number > {self.MAX_RUN}')

        mapping['RUN_IN_START'] = run_in_start
        mapping['RUN_OUT_START'] = run_out_start


def setup(*, template_file, input_file, force, **kwargs):
    cwd = Path.cwd()

    if not input_file:
        raise OSError('Input file not defined.')

    handles = read_imas_handles_from_file(input_file)

    with open(template_file) as f:
        template = Template(f.read())

    dummy_cfg = Config.parse_raw(template.substitute(DUMMY_VARS))

    if (dummy_cfg.system == 'v210921'):
        extra_params = ExtrasV210921(dummy_cfg)
        update_mapping = extra_params.update_mapping
    else:
        update_mapping = no_op  # default to no-op

    for name, handle in handles.items():
        mapping = {
            'TEMPLATE_USER': handle.user,
            'TEMPLATE_DB': handle.db,
            'TEMPLATE_SHOT': handle.shot,
            'TEMPLATE_RUN': handle.run,
            'RUN_NAME': name,
        }

        update_mapping(mapping)

        cfg = template.substitute(mapping)

        Config.parse_raw(cfg)  # make sure config is valid

        out_drc = cwd / name

        op_queue.add(
            action=_generate_run_dir,
            kwargs={
                'drc': out_drc,
                'cfg': cfg,
                'force': force
            },
            description='Setup run',
            extra_description=name,
        )
