from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from ..utils.doctools import document
from .stat import stat


@document
class stat_identity(stat):
    """
    Identity (do nothing) statistic

    {usage}

    Parameters
    ----------
    {common_parameters}

    {aesthetics}
    """
    DEFAULT_PARAMS = {'geom': 'point', 'position': 'identity'}

    @classmethod
    def compute_panel(cls, data, scales, **params):
        return data