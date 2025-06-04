from manim import *

class TrigonometricFunctions(Scene):
    def construct(self):
        axes = Axes(x_range=[-2*np.pi, 2*np.pi], y_range=[-1, 1])

        # Plot sine and cosine functions
        sine_graph = axes.plot(lambda x: np.sin(x), x_range=[-2*np.pi, 2*np.pi], color=BLUE)
        cosine_graph = axes.plot(lambda x: np.cos(x), x_range=[-2*np.pi, 2*np.pi], color=RED)

        # Label x-axis and key points
        labels = axes.get_axis_labels(MathTex("x"), MathTex("y"))
        x_labels = VGroup(
            MathTex("-2\\pi"), MathTex("-\\pi"), MathTex("0"), MathTex("\\pi"), MathTex("2\\pi")
        )
        x_labels.arrange(RIGHT, buff=1.5)
        x_labels.next_to(axes.x_axis.get_end(), DOWN)
        x_labels.match_color(axes.x_axis)
        
        # Add mathematical labels for sine and cosine functions
        sine_label = MathTex("\\sin(x)", color=BLUE).next_to(sine_graph, UP)
        cosine_label = MathTex("\\cos(x)", color=RED).next_to(cosine_graph, UP)

        # Highlight key points
        max_min_points = [
            axes.input_to_graph_point(n * np.pi, sine_graph) for n in range(-2, 3)
        ]
        intersection_points = [
            axes.input_to_graph_point(n * np.pi / 2, sine_graph) for n in range(-3, 4)
        ]

        # Animation for moving cosine curve
        self.play(
            cosine_graph.animate.shift(axes.c2p(np.pi/2, 0) - axes.c2p(0, 0)),
            run_time=1.5
        )

        # Highlight key points on the graph
        for point in max_min_points + intersection_points:
            dot = Dot(point, color=YELLOW)
            self.play(Create(dot))

        # Show phase difference between sine and cosine functions
        phase_difference = MathTex("\\sin(x) = \\cos(x - \\frac{\\pi}{2})")
        phase_difference.next_to(cosine_label, DOWN).shift(DOWN*0.5)
        self.play(Write(phase_difference))

        self.play(
            *[FadeOut(mob) for mob in [sine_graph, cosine_graph, labels, x_labels, sine_label, cosine_label, phase_difference]],
            run_time=2
        )
        self.wait(1)