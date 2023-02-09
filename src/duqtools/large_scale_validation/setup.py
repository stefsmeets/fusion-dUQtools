from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

import yaml
from jinja2 import Environment, FileSystemLoader

from duqtools.config import var_lookup

from ..config import Config
from ..operations import op_queue
from ..utils import no_op, read_imas_handles_from_file

if TYPE_CHECKING:
    import jinja2

    from duqtools.api import IDSMapping, ImasHandle

logger = logging.getLogger(__name__)


class SetupError(Exception):
    ...


def get_template(filename: str) -> jinja2.Template:
    """Load filename as a jinja2 template."""
    path = Path(filename)
    drc = Path(path).parent
    file_loader = FileSystemLoader(str(drc))
    environment = Environment(loader=file_loader, autoescape=True)
    return environment.get_template(path.name)


def _get_key(filename: str, *, key: str):
    """Grab key from unrendered config file."""
    with open(filename, 'rb') as f:
        for line in f:
            try:
                item = yaml.safe_load(line)
                return item[key]
            except (yaml.YAMLError, TypeError, KeyError):
                continue


def _generate_run_dir(drc: Path, cfg: str, force: bool):
    drc.mkdir(exist_ok=force, parents=True)

    with open(drc / 'duqtools.yaml', 'w') as f:
        f.write(cfg)


class ExtrasV210921:
    """Track run number to avoid overwriting existing data in sequential
    runs."""
    MAX_RUN = 9999

    def __init__(self, template_file: str):
        self.n_samples = self._get_n_samples(template_file)
        self.run_numbers: dict[tuple[str, int],
                               int] = defaultdict(lambda: 1000)

    @staticmethod
    def _get_n_samples(template_file: str) -> int:
        """Grab number of samples generated by this config, from
        `create.sampler.n_samples`."""
        n_samples = _get_key(template_file, key='n_samples')

        if not n_samples:
            raise ValueError('`create.sampler.n_samples` must be defined for '
                             'jintrac `v210921` config')

        return n_samples

    def add_system_attrs(self, handle: ImasHandle, run: SimpleNamespace):
        """Add system specific attributes to run namespace."""
        data_in_start = self.run_numbers[handle.db, handle.shot]
        data_out_start = data_in_start + self.n_samples

        self.run_numbers[handle.db,
                         handle.shot] = data_out_start + self.n_samples

        if self.run_numbers[handle.db, handle.shot] > self.MAX_RUN:
            raise ValueError(
                f'Cannot write data with run number > {self.MAX_RUN}')

        run.data_in_start = data_in_start
        run.data_out_start = data_out_start


class Variables:
    lookup = var_lookup.filter_type('IDS2jetto-variable')

    def __init__(self, *, handle: ImasHandle):
        self.handle = handle
        self._ids_cache: dict[str, IDSMapping] = {}

    def _get_ids(self, ids: str):
        """Cache ids lookups to avoid repeated data reads."""
        if ids in self._ids_cache:
            mapping = self._ids_cache[ids]
        else:
            mapping = self.handle.get(ids)
            self._ids_cache[ids] = mapping

        return mapping

    def __getattr__(self, key: str):
        try:
            spec = self.lookup[f'ids-{key}']
        except KeyError as exc:
            msg = f'Cannot find {key!r} in your variable listing (i.e. `variables.yaml`).'
            raise KeyError(msg) from exc

        value = spec.default

        for item in spec.paths:
            mapping = self._get_ids(item.ids)
            try:
                trial = mapping[item.path]
            except KeyError:
                continue

            if all(condition(trial) for condition in spec.accept_if):
                value = trial
                break

        if not value:
            raise ValueError(
                f'No value matches specifications given by: {spec}')

        return value


def setup(*, template_file, input_file, force, **kwargs):
    """Setup large scale validation runs for template."""
    cwd = Path.cwd()

    if not input_file:
        raise OSError('Input file not defined.')

    handles = read_imas_handles_from_file(input_file)

    template = get_template(template_file)

    if _get_key(template_file, key='system') == 'jetto-v210921':
        add_system_attrs = ExtrasV210921(template_file).add_system_attrs
    else:
        add_system_attrs = no_op  # default to no-op

    for name, handle in handles.items():
        run = SimpleNamespace(name=name)

        add_system_attrs(run)

        variables = Variables(handle=handle)

        cfg = template.render(run=run, variables=variables, handle=handle)

        Config.parse_raw(cfg)  # make sure config is valid

        out_drc = cwd / name

        if out_drc.exists() and not force:
            op_queue.add_no_op(description='Directory exists',
                               extra_description=name)
            op_queue.warning(description='Warning',
                             extra_description='Some targets already exist, '
                             'use --force to override')
        else:
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
