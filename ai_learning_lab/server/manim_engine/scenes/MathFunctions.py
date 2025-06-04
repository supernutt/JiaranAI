from manim import *

class MathFunctions(Scene):
    def construct(self):
        # Create a coordinate system
        axes = Axes(x_range=[-3*np.pi, 3*np.pi], y_range=[0, 1.5], axis_config={"include_numbers": True})
        self.play(Create(axes))

        # Plot the sine function
        sine_graph = axes.plot(lambda x: np.sin(x), x_range=[-3*np.pi, 3*np.pi])
        sine_graph.set_color(BLUE)
        sine_label = MathTex(r"\sin(x)", color=BLUE).next_to(sine_graph, UP)
        self.play(Write(sine_graph), Write(sine_label))

        # Plot the Gaussian distribution
        gaussian_graph = axes.plot(lambda x: np.exp(-0.5*x**2) / np.sqrt(2*np.pi), x_range=[-3*np.pi, 3*np.pi])
        gaussian_graph.set_color(RED)
        gaussian_label = MathTex("G(x)", color=RED).next_to(gaussian_graph, UP)
        self.play(Write(gaussian_graph), Write(gaussian_label))

        # Emphasize the difference in shapes
        self.play(sine_graph.animate.set_color(RED), gaussian_graph.animate.set_color(BLUE))

        # Highlight the periodic nature vs symmetric spread
        self.play(sine_graph.animate.scale(1.5).shift(UP), gaussian_graph.animate.scale(1.5).shift(DOWN))

        # Animate the curves moving together
        self.play(sine_graph.animate.shift(UP), gaussian_graph.animate.shift(DOWN))

        # Add a text label to clarify the difference
        text_label = Text("Difference in shapes and behaviors").scale(0.7).to_corner(UL)
        self.play(Write(text_label))

        # Highlight key points of intersection and max values
        sine_intersection = Dot(axes.c2p(np.pi, 0), color=YELLOW)
        gaussian_intersection = Dot(axes.c2p(0, np.exp(0) / np.sqrt(2*np.pi), color=YELLOW))
        self.play(Write(sine_intersection), Write(gaussian_intersection))
        self.wait(1)