from manim import *

class TanAndTanhComparison(Scene):
    def construct(self):
        # Create axes
        axes = Axes(
            x_range=[-3*PI, 3*PI],
            y_range=[-2, 2],
            axis_config={
                "include_numbers": True,
                "numbers_to_include": [-3*PI, -2*PI, 0, 2*PI, 3*PI],
            }
        )

        # Plot tan(x) and tanh(x)
        tan_graph = axes.plot(lambda x: np.tan(x), x_range=[-3*PI, 3*PI], color=BLUE)
        tanh_graph = axes.plot(lambda x: np.tanh(x), x_range=[-3*PI, 3*PI], color=RED)

        # Add labels for functions
        tan_label = MathTex(r"\tan(x)", color=BLUE).next_to(tan_graph, UP)
        tanh_label = MathTex(r"\tanh(x)", color=RED).next_to(tanh_graph, UP)

        # Add asymptotes for tan(x) at odd multiples of π/2
        for n in range(-3, 4):
            asymptote = Line(axes.c2p(n*PI/2, -2), axes.c2p(n*PI/2, 2), color=YELLOW)
            self.add(asymptote)

        # Emphasize the behavior of tanh(x) towards ±1 as x approaches ±∞
        tanh_inf_label = MathTex(r"\text{Tends towards } \pm 1").next_to(tanh_graph, DOWN)

        # Highlight the periodic behavior of tan(x) compared to tanh(x)
        periodic_label = MathTex(r"\text{Periodic behavior of } \tan(x)").next_to(tan_graph, RIGHT)
        hyperbolic_label = MathTex(r"\text{Hyperbolic shape of }\tanh(x)").next_to(tanh_graph, RIGHT)

        self.play(*[
            Create(mobject)
            for mobject in [axes, tan_graph, tanh_graph, tan_label, tanh_label, tanh_inf_label, periodic_label, hyperbolic_label]
        ])
        self.wait(1)