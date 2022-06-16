import logging

import yaml

from .._types import PathLike
from .ids_location import ImasLocation
from .ids_simplify import IDSTree

logger = logging.getLogger(__name__)


def write_ids(filename: PathLike, data: dict):
    """Write ids data to yaml file [PROOF OF CONCEPT].

    Parameters
    ----------
    filename : PathLike
        Filename to save data to.
    data : dict
        Dictionary with keys to write.
    """
    with open(filename, 'w') as f:
        yaml.dump(data, f)
    logger.debug('wrote %r' % filename)


__all__ = [
    'ImasLocation',
    'IDSTree',
]
