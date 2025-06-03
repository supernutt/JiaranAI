from manim import *

class FunctionsPlot(Scene):
    def construct(self):
        axes = Axes(x_range=[-2*np.pi, 2*np.pi], y_range=[-2, 2])

        # Plot sine function
        sine_graph = axes.plot(lambda x: np.sin(x), x_range=[-2*np.pi, 2*np.pi], color=BLUE)
        sine_label = MathTex("f(x) = \\sin(x)", color=BLUE).next_to(sine_graph, UP)

        # Plot exponential function
        exponential_graph = axes.plot(lambda x: np.exp(x), x_range=[-2*np.pi, 2*np.pi], color=RED)
        exponential_label = MathTex("g(x) = e^x", color=RED).next_to(exponential_graph, UP)

        # Highlight the differences between the functions
        diff_highlight = DashedLine(axes.c2p(-2*np.pi, 1), axes.c2p(2*np.pi, 1), color=YELLOW)

        # Add text labels
        sine_text = Text("Sine Function", color=BLUE).next_to(diff_highlight, DOWN)
        exponential_text = Text("Exponential Growth", color=RED).next_to(diff_highlight, UP)

        # Show the functions and differences with smooth movements
        self.play(Create(axes), Write(sine_label))
        self.play(Create(sine_graph), Create(exponential_graph))
        self.wait(1)
        self.play(FadeOut(sine_label), FadeOut(exponential_graph), Write(exponential_label))
        self.play(Create(diff_highlight), Write(sine_text), Write(exponential_text))
        self.wait(1)