"""Central place for package metadata."""

from pkg_resources import DistributionNotFound, get_distribution

# NOTE: We use __title__ instead of simply __name__ since the latter would
#       interfere with a global variable __name__ denoting object's name.
__title__ = "reservations"
__summary__ = "Open source reservation system written in Django"
__url__ = "https://github.com/UL-FRI/reservations"

try:
    # Try to get the version from git tag.
    __version__ = get_distribution(__title__).version
except DistributionNotFound:
    pass

__author__ = "Gašper Fele-Žorž and Gregor Jerše"
__email__ = "polz@aufbix.org"

__license__ = "GNU Affero General Public License (3.0)"
__copyright__ = "2000-2022, " + __author__

__all__ = (
    "__title__",
    "__summary__",
    "__url__",
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__copyright__",
)
