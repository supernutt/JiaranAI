from manim import *

class MathFunctionComparison(Scene):
    def construct(self):
        # Create coordinate system
        axes = Axes(x_range=[-3, 3], y_range=[-1.5, 1.5])
        x_labels = axes.get_axis_labels(MathTex("x"), MathTex("f(x)=\\tanh(x)"))
        self.play(Create(axes), Create(x_labels))

        # Plot the tanh function
        tanh_curve = axes.plot(lambda x: np.tanh(x), x_range=[-3, 3], color=BLUE)
        tanh_label = MathTex("f(x) = \\tanh(x)", color=BLUE).next_to(tanh_curve, UP)
        self.play(Create(tanh_curve), Write(tanh_label))

        # Plot the Gaussian distribution
        gaussian_curve = axes.plot(lambda x: np.exp(-x**2), x_range=[-3, 3], color=RED)
        gaussian_label = MathTex("f(x) = e^{-x^2}", color=RED).next_to(gaussian_curve, UP)
        self.play(Create(gaussian_curve), Write(gaussian_label))

        # Emphasize key features
        self.play(tanh_curve.animate.set_stroke(width=4), gaussian_curve.animate.set_stroke(width=4))

        # Show symmetry
        self.play(gaussian_curve.animate.shift(LEFT*6))
        self.wait(1)
        self.play(gaussian_curve.animate.shift(RIGHT*6))
        self.wait(1)

        # Animate comparison
        self.play(gaussian_curve.animate.shift(UP*3), run_time=3)

        # Point out differences
        self.play(Write(Text("Tanh saturates at -1 and 1", color=BLUE).to_edge(UP)))
        self.wait(1)
        self.play(Write(Text("Gaussian extends to infinity", color=RED).to_edge(UP)))
        self.wait(1)

        # Conclude with text
        conclusion = Text("Tanh is bounded, Gaussian is unbounded").scale(0.8).to_edge(DOWN)
        self.play(Create(conclusion))
        self.wait(2)

        # Fade out
        self.play(FadeOut(tanh_curve), FadeOut(tanh_label), FadeOut(gaussian_curve), FadeOut(gaussian_label), FadeOut(x_labels), FadeOut(conclusion))
        self.wait(1)