from manim import *
import numpy as np

class SineTangentComparison(Scene):
    def construct(self):
        # Create axes
        axes = Axes(x_range=[-8,8,1], y_range=[-6,6,1], x_length=10, y_length=6)

        # Define sine and tangent functions
        sine_graph = axes.plot(lambda x: np.sin(x), x_range=[-8, 8], color=BLUE)
        tangent_graph = axes.plot(lambda x: np.tan(x), x_range=[-8, 8], color=RED)

        # Define labels
        sine_label = MathTex("\sin(x)", color=BLUE).next_to(sine_graph, UR)
        tangent_label = MathTex("\\tan(x)", color=RED).next_to(tangent_graph, DR)
        sine_max_label = MathTex("1").next_to(axes.c2p(np.pi/2, 1), UP)
        sine_min_label = MathTex("-1").next_to(axes.c2p(-np.pi/2, -1), DOWN)
        tangent_inf_label = MathTex("{\infty}").next_to(axes.c2p(np.pi/2, 6), UP)
        tangent_neg_inf_label = MathTex("-{\infty}").next_to(axes.c2p(-np.pi/2, -6), DOWN)

        # Highlight key points on the sine curve
        sine_peaks = [Dot().move_to(axes.c2p(x,np.sin(x))) for x in [-2*np.pi, 0, 2*np.pi]]
        sine_troughs = [Dot().move_to(axes.c2p(x,np.sin(x))) for x in [-3*np.pi/2, np.pi/2]]
        sine_zeros = [Dot().move_to(axes.c2p(x,np.sin(x))) for x in [-3*np.pi, -np.pi, np.pi, 3*np.pi]]

        # Show asymptotes on the tangent graph
        asymptotes = [DashedLine(axes.c2p(x,-6), axes.c2p(x,6), color=YELLOW)
                      for x in [-3*np.pi/2, -np.pi/2, np.pi/2, 3*np.pi/2]]

        # Display all components
        self.play(Create(axes))
        self.play(Create(sine_graph), Write(sine_label))
        self.play(*[FadeIn(dot) for dot in sine_peaks])
        self.play(Write(sine_max_label))
        self.play(*[FadeIn(dot) for dot in sine_troughs])
        self.play(Write(sine_min_label))
        self.play(*[FadeIn(dot) for dot in sine_zeros])
        self.play(Create(tangent_graph), Write(tangent_label))
        self.play(*[Create(line) for line in asymptotes])
        self.play(Write(tangent_inf_label), Write(tangent_neg_inf_label))
        self.wait()