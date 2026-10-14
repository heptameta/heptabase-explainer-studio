from explainer_studio.scene_kit import *


class Cover(CoverScene):
    title = "水為什麼能\n推動水車？"

    def get_visual(self):
        return get_image("shared/assets/images/dam.png", height=4)
