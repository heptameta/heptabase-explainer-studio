"""The library scene files import: `from explainer_studio.scene_kit import *`.

It gives the whole ManimGL namespace (np included), NarratedScene and CoverScene, the style constants, the automatic
check markers, media, file excerpts, credits and every component. Importing it applies the ManimGL patches.
"""

from manimlib import *

from . import patches  # noqa: F401  (applied on import)
from .components.cards import *
from .components.characters import *
from .components.charts import *
from .components.circuits import *
from .components.code_panels import *
from .components.diagrams import *
from .components.emphasis import *
from .components.history import *
from .components.maps import *
from .components.molecules import *
from .components.music_notation import *
from .components.simulation import *
from .components.tables import *
from .components.timelines import *
from .cover import *
from .credits import *
from .file_excerpts import *
from .layout_checks import *
from .media import *
from .narrated_scene import *
from .parts import *
from .style import *
