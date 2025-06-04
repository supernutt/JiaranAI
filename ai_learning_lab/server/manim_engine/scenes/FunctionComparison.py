from manim import *

class FunctionComparison(Scene):
    def construct(self):
        # Create axes
        axes = Axes(x_range=[-2*np.pi, 2*np.pi], y_range=[-1.5, 1.5])
        
        # Plot sine function
        sine_graph = axes.plot(lambda x: np.sin(x), x_range=[-2*np.pi, 2*np.pi], color=BLUE)
        
        # Plot Gaussian function
        gaussian_graph = axes.plot(lambda x: np.exp(-0.2*x**2), x_range=[-2*np.pi, 2*np.pi], color=RED)
        
        # Add x-axis and y-axis labels
        x_labels = axes.get_axis_labels(MathTex("-2\\pi"), MathTex("-\\pi"), MathTex("0"), MathTex("\\pi"), MathTex("2\\pi"))
        y_labels = axes.get_axis_labels(MathTex("-1"), MathTex("0"), MathTex("1"))
        
        # Add mathematical labels for functions
        sine_label = MathTex("y = \\sin(x)", color=BLUE).to_edge(UP)
        gaussian_label = MathTex("y = e^{-0.2x^2}", color=RED).to_edge(UP)
        
        # Highlight the difference in behavior
        behavior_label = Text("Differences in behavior:", font_size=24).to_edge(DOWN)
        
        # Smooth transformation from sine to Gaussian
        self.play(
            ReplacementTransform(sine_graph, gaussian_graph),
            ReplacementTransform(sine_label, gaussian_label),
            run_time=2
        )
        
        # Add explanation text label
        explanation_label = Text("Sine function oscillates, Gaussian function is bell-shaped.", font_size=24).to_edge(DOWN)

        self.play(Write(explanation_label), run_time=2)
        self.wait(2)