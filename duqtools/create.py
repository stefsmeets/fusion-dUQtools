import itertools
import logging
import shutil
from pathlib import Path

import numpy as np

from duqtools.config import Config as cfg

from .ids import ImasLocation
from .jetto import JettoSettings

logger = logging.getLogger(__name__)


def copy_files(source_drc: Path, target_drc: Path):
    """Copy files for jetto run to destination directory.

    Parameters
    ----------
    source_drc : Path
        Source (template) directory.
    target_drc : Path
        Target directory.
    """
    for filename in (
            # '.llcmd',
            'jetto.in',
            'rjettov',
            'utils_jetto',
            'jetto.ex',
            'jetto.sin',
            'jetto.sgrid',
            # 'jetto.jset',
    ):
        src = source_drc / filename
        dst = target_drc / filename
        shutil.copyfile(src, dst)
    logger.debug('copied files to %s' % target_drc)


def write_batchfile(target_drc: Path):
    """Write batchfile (`.llcmd`) to start jetto.

    Parameters
    ----------
    target_drc : Path
        Directory to place batch file into.
    """
    drc_name = target_drc.name
    with open(target_drc / '.llcmd', 'w') as f:
        f.write(f"""#!/bin/sh
./rjettov -S -I -p -xmpi -x64 {drc_name} v210921_gateway_imas g2fkoech
""")


def apply(operation: dict, core_profiles) -> None:
    """Apply operation to core_profiles. Data is modified in-place.

    Parameters
    ----------
    operation : dict
        Dict with ids to modify, operator to apply, and value to use.
    core_profiles : TYPE
        Core profiles IMAS object.
    """
    ids = operation['ids']
    operator = operation['operator']
    assert operator in ('add', 'multiply', 'divide', 'power', 'subtract',
                        'floor_divide', 'mod', 'remainder')

    value = operation['value']

    logger.info('Apply `%s = %s(%s, %s)`' % (ids, operator, ids, value))

    npfunc = getattr(np, operator)
    profile = getattr(core_profiles.profiles_1d[0], ids)

    logger.debug('data range before: %s - %s' % (profile.min(), profile.max()))
    npfunc(profile, value, out=profile)
    logger.debug('data range after: %s - %s' % (profile.min(), profile.max()))


def create(**kwargs):
    """Create input for jetto and IDS data structures.

    Parameters
    ----------
    **kwargs
        Unused.
    """
    options = cfg().create

    template_drc = options.template
    matrix = options.matrix

    expanded_vars = tuple(var.expand() for var in matrix)

    combinations = itertools.product(*expanded_vars)

    jset = JettoSettings.from_directory(template_drc)

    source = ImasLocation.from_jset_input(jset)
    assert source.path().exists()

    for i, combination in enumerate(combinations):
        sub_drc = f'run_{i:04d}'
        target_drc = cfg().workspace / sub_drc
        target_drc.mkdir(parents=True, exist_ok=True)

        copy_files(template_drc, target_drc)
        write_batchfile(target_drc)

        target_in = ImasLocation(db=options.data.db,
                                 shot=source.shot,
                                 run=options.data.run_in_start_at + i)
        target_out = ImasLocation(db=options.data.db,
                                  shot=source.shot,
                                  run=options.data.run_out_start_at + i)

        jset_copy = jset.set_imas_locations(inp=target_in, out=target_out)
        jset_copy.to_directory(target_drc)

        source.copy_ids_entry_to(target_in)

        core_profiles = target_in.get('core_profiles')

        for operation in combination:
            apply(operation, core_profiles)

        with target_in.open() as data_entry_target:
            logger.info('Writing data entry: %s' % target_in)
            core_profiles.put(db_entry=data_entry_target)
