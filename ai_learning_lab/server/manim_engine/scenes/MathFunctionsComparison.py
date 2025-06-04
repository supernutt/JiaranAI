from manim import *

class MathFunctionsComparison(Scene):
    def construct(self):
        # Create axes
        axes = Axes(x_range=[-2*np.pi, 2*np.pi], y_range=[-1.5, 1.5])
        
        # Plot sine function
        sine_graph = axes.plot(lambda x: np.sin(x), x_range=[-2*np.pi, 2*np.pi], color=BLUE)
        
        # Label for sine function
        sine_label = MathTex("\\sin(x)", color=BLUE).next_to(sine_graph, UP)
        
        # Plot Gaussian function
        gaussian_graph = axes.plot(lambda x: np.exp(-x**2), x_range=[-2*np.pi, 2*np.pi], color=RED)
        
        # Label for Gaussian function
        gaussian_label = MathTex("e^{-x^2}", color=RED).next_to(gaussian_graph, UP)
        
        # Highlight the periodic nature of sine function
        sine_highlight = SurroundingRectangle(sine_graph, color=BLUE)
        
        # Highlight the symmetric, bell-shaped curve of the Gaussian function
        gaussian_highlight = SurroundingRectangle(gaussian_graph, color=RED)
        
        # Show the differences in behavior between the two functions
        self.play(Create(sine_highlight), Create(gaussian_highlight))
        self.wait(1)
        
        # Emphasize the differences in behavior with descriptive text
        properties_text = Text("Sine: Periodic, Oscillating / Gaussian: Non-periodic, Decaying").scale(0.8)
        properties_text.to_corner(UP+LEFT)
        self.play(Write(properties_text))
        self.wait(1)
        
        # Highlight the differences on the plot
        self.play(FadeOut(sine_highlight), FadeOut(gaussian_highlight))
        self.wait(0.5)
        
        # Show infinite nature of sine wave and rapid decay of Gaussian function
        self.play(sine_graph.animate.shift(4*np.pi*RIGHT), gaussian_graph.animate.shift(4*np.pi*RIGHT), run_time=4, rate_func=linear)
        
        self.wait(2)