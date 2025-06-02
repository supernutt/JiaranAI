from manim import *
import numpy as np

class SinCosComparison(Scene):
    def construct(self):
        # Create axes
        axes = Axes(x_range=[-np.pi, 2*np.pi, np.pi/2], y_range=[-2, 2], x_axis_config={"numbers_to_exclude": []})

        # Plot sine function
        sine_function = axes.plot(np.sin, x_range=[-np.pi, 2*np.pi], color=BLUE)
        # Calculate key points
        sine_key_points = [Dot().move_to(axes.c2p(x, np.sin(x))) for x in [-np.pi, -np.pi/2, 0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi]]

        # Plot cosine function
        cosine_function = axes.plot(np.cos, x_range=[-np.pi, 2*np.pi], color=RED)
        # Calculate key points
        cosine_key_points = [Dot().move_to(axes.c2p(x, np.cos(x))) for x in [-np.pi, -np.pi/2, 0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi]]

        self.play(Create(axes), Create(sine_function), Create(cosine_function), *map(GrowFromCenter, sine_key_points + cosine_key_points))
        self.wait()

        # Animate the horizontal shift of the cosine function
        shifted_cosine_function = axes.plot(lambda x: np.cos(x + np.pi/2), x_range=[-np.pi, 2*np.pi], color=RED)
        self.play(Transform(cosine_function, shifted_cosine_function))

        # Labels for key points
        labels = ["-\\pi", "-\\frac{\\pi}{2}", "0", "\\frac{\\pi}{2}", "\\pi", "\\frac{3\\pi}{2}", "2\\pi"]
        
        # Labels for sine key points
        sine_labels = [MathTex(label).next_to(dot, UP) for label, dot in zip(labels, sine_key_points)]
        # Labels for cosine key points
        cosine_labels = [MathTex(label).next_to(dot, UP) for label, dot in zip(labels, cosine_key_points)]

        self.play(*[Write(label) for label in sine_labels + cosine_labels])
        self.wait()