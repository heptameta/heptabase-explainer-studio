from explainer_studio.scene_kit import *


class Heights(NarratedScene):
    def construct(self):
        chart = get_bar_chart([3, 5, 8], labels=["甲", "乙", "丙"], colors=[BLUE_C, TEAL, YELLOW], max_value=13,
                              width=7, height=4, y_label="高度（公尺）")
        with self.play_beat("three_levels") as beat:
            self.play(ShowCreation(chart.baseline), FadeIn(chart.labels), FadeIn(chart.y_label))
            for bar, value_label in zip(chart.bars, chart.value_labels):
                self.play(GrowFromEdge(bar, DOWN), FadeIn(value_label), run_time=beat.duration_seconds / 5)

        with self.play_beat("higher"):
            self.play(*animate_bars_to(chart, [3, 5, 12]), run_time=1.5)
            self.play(FlashAround(chart.bars[2], color=YELLOW))
