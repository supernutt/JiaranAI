from manim import *

class PlotSineCosine(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-PI, PI, PI/2],
            y_range=[-1, 1, 2],
            axis_config={"include_numbers": True},
        )

        sine_curve = axes.get_graph(
            lambda x: np.sin(x), color=BLUE
        )
        sine_curve_label = axes.get_graph_label(
            sine_curve, "\\sin(x)", x_val=1.5, direction=DOWN
        )

        cosine_curve = axes.get_graph(
            lambda x: np.cos(x), color=RED
        )
        cosine_curve_label = axes.get_graph_label(
            cosine_curve, "\\cos(x)", x_val=-0.5, direction=UP
        )

        self.play(
            Create(axes),
            Create(sine_curve),
            Write(sine_curve_label),
            run_time=2 
        )

        self.wait()

        self.play(
            Create(cosine_curve),
            Write(cosine_curve_label),
            run_time=3
        )

        self.wait()

        cosine_curve_shifted = axes.get_graph(
            lambda x: np.cos(x - PI/2), color=GREEN
        )
        cosine_curve_shifted_label = axes.get_graph_label(
            cosine_curve_shifted, "\\cos(x - \\pi/2)", x_val=-1.5, direction=UP
        )

        self.play(Transform(cosine_curve, cosine_curve_shifted),
                  ReplacementTransform(cosine_curve_label, cosine_curve_shifted_label),
                  run_time=3
        )

        self.wait()