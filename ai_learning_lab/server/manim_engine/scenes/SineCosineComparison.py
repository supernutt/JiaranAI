from manim import *
import numpy as np

class SineCosineComparison(Scene):
    def construct(self):
        axes = Axes(
            x_range = [-np.pi, 2*np.pi, np.pi/2],
            y_range = [-2, 2, 1],
            x_length = 10,
            y_length= 5,
            axis_config={"include_numbers": True},
            x_axis_config={
                "numbers_to_include": np.linspace(-np.pi, 2*np.pi, 4),
                "decimal_number_config": {
                    "num_decimal_places": 2,
                    },
            },
        )
        
        # Labels
        labels_x = [
            MathTex("-\pi").next_to(axes.c2p(-np.pi, 0), DOWN),
            MathTex("0").next_to(axes.c2p(0, 0), DOWN),
            MathTex("\pi").next_to(axes.c2p(np.pi, 0), DOWN),
            MathTex("2\pi").next_to(axes.c2p(2*np.pi, 0), DOWN),
        ]

        # Plot graphs
        sine_graph = axes.plot(np.sin, x_range=[-np.pi, 2*np.pi, np.pi/2], color = BLUE)
        cosine_graph = axes.plot(np.cos, x_range=[-np.pi, 2*np.pi, np.pi/2], color = RED)

        # Labels for the waves
        sine_label = MathTex("\sin(x)", color= BLUE).next_to(sine_graph, UP)
        cosine_label = MathTex("\cos(x)", color= RED).next_to(cosine_graph, UP)

        self.play(Create(axes), Write(labels_x), Create(sine_graph), Create(cosine_graph), Write(sine_label), Write(cosine_label), run_time=2)
        self.wait(1)

        # Phase shift animation
        cosine_graph_target = cosine_graph.copy()
        cosine_graph_target.shift(np.pi / 2 * LEFT)
        self.play(Transform(cosine_graph, cosine_graph_target), run_time=2)
        self.wait(1)