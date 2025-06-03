from manim import *

class TrigonometricFunctions(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-np.pi, 2*np.pi],
            y_range=[-2, 2],
            x_length=9,
            y_length=4,
            axis_config={"include_numbers": True}
        )

        sine_graph = axes.plot(lambda x: np.sin(x), x_range=[-np.pi, 2*np.pi], color=BLUE)
        cosine_graph = axes.plot(lambda x: np.cos(x), x_range=[-np.pi, 2*np.pi], color=RED)

        labels = axes.get_axis_labels(MathTex("-\pi"), MathTex("2\pi"))
        sine_label = MathTex("\\sin(x)", color=BLUE).next_to(sine_graph, UP)
        cosine_label = MathTex("\\cos(x)", color=RED).next_to(cosine_graph, UP)

        intersection_points = [
            Dot(axes.c2p(np.pi, 0), color=YELLOW),
            Dot(axes.c2p(2*np.pi, 0), color=YELLOW),
            Dot(axes.c2p(0, 1), color=YELLOW),
            Dot(axes.c2p(np.pi, -1), color=YELLOW),
            Dot(axes.c2p(2*np.pi, 1), color=YELLOW),
            Dot(axes.c2p(2*np.pi, -1), color=YELLOW)
        ]

        max_min_points = [
            Dot(axes.c2p(np.pi/2, 1), color=YELLOW),
            Dot(axes.c2p(3*np.pi/2, -1), color=YELLOW),
            Dot(axes.c2p(np.pi, -1), color=YELLOW),
        ]

        self.play(Create(axes), Write(labels), FadeIn(sine_graph), FadeIn(cosine_graph))
        self.play(Write(sine_label), Write(cosine_label))
        self.wait(1)

        self.play(*[Create(point) for point in intersection_points])
        self.wait(1)

        self.play(*[GrowFromCenter(point) for point in max_min_points])
        self.wait(1)

        cosine_graph_phase_shifted = axes.plot(lambda x: np.cos(x + np.pi/2), x_range=[-np.pi, 2*np.pi], color=RED)

        self.play(Transform(cosine_graph, cosine_graph_phase_shifted), run_time=2)
        self.wait(1)