from explainer_studio.scene_kit import *


class Dam(NarratedScene):
    def construct(self):
        title = Text("水為什麼能推動水車？", font_size=HEADING_FONT_SIZE).to_edge(UP)
        dam = get_image("shared/assets/images/dam.png", height=4.5).next_to(title, DOWN, buff=0.5)
        with self.play_beat("water_levels") as beat:
            self.play_sound("whoosh_in")
            self.play(Write(title), run_time=beat.get_seconds_until(0.4))
            self.play(FadeIn(dam, shift=0.3 * UP))

        formula = Tex(R"E = m g h", font_size=96).set_color(YELLOW)
        label = Text("位能", font_size=LABEL_FONT_SIZE).set_color(GREY_A)
        VGroup(formula, label).arrange(DOWN, buff=0.4).move_to(3.4 * RIGHT + 0.3 * DOWN)
        with self.play_beat("potential_energy"):
            self.play(dam.animate.scale(0.7).move_to(3.3 * LEFT + 0.3 * DOWN), run_time=1.2)
            self.play(Write(formula), FadeIn(label, shift=0.2 * UP))

        with self.play_beat("listen") as beat:
            self.play(ShowCreation(get_highlight_rectangle(formula)))
            self.wait(beat.remaining_seconds)
            # the chord plays in the two-second pause the script leaves after this line
            self.play_sound("shared/assets/audio/chord.ogg")
