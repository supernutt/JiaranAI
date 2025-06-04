from manim import *

class MathFunctionShapesComparison(Scene):
    def construct(self):
        # Create a coordinate system
        axes = Axes(x_range=[-2*np.pi, 2*np.pi], y_range=[0, 1.5])
        sine_graph = axes.plot(lambda x: np.sin(x), x_range=[-2*np.pi, 2*np.pi], color=BLUE)
        gaussian_graph = axes.plot(lambda x: np.exp(-x**2 / 2) / np.sqrt(2*np.pi), x_range=[-2*np.pi, 2*np.pi], color=RED)

        # Label the x-axis with key points
        labels = axes.get_axis_labels(MathTex("-2\pi"), MathTex("0.5"))
        key_points = [(-2*np.pi, 0), (-np.pi, 0), (0, 0), (np.pi, 0), (2*np.pi, 0)]
        key_labels = [MathTex("-2\pi"), MathTex("-\pi"), MathTex("0"), MathTex("\pi"), MathTex("2\pi")]

        for point, label in zip(key_points, key_labels):
            label.next_to(axes.c2p(point[0], point[1]), DOWN)
        
        # Add mathematical labels for both functions
        sine_label = MathTex("\sin(x)", color=BLUE).next_to(sine_graph, UP)
        gaussian_label = MathTex("e^{-x^2/2} / \sqrt{2\pi}", color=RED).next_to(gaussian_graph, UP)

        # Show the oscillatory nature of sine function and bell-shaped curve of Gaussian distribution
        self.play(Create(axes), Write(labels), *[Write(label) for label in key_labels])
        self.play(Create(sine_graph), Write(sine_label))
        self.wait(1)
        self.play(Transform(sine_graph, gaussian_graph), Transform(sine_label, gaussian_label))
        self.wait(1)