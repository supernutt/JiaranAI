from manim import *

class SineCosinePhaseShift(Scene):
    def construct(self):
        
        # Create Axes
        axes = Axes(x_range=[-2*PI, 2*PI, PI/2], y_range=[-1, 1, 0.5],
                    x_length=10, y_length=4,
                    axis_config={"include_numbers": True,
                                 "numbers_to_include": [-2*PI, -PI, 0, PI, 2*PI]})
        
        # Create sine and cosine graph
        sine_graph = axes.plot(lambda x: np.sin(x), x_range=[-2*PI, 2*PI], color=BLUE)
        cosine_graph = axes.plot(lambda x: np.cos(x), x_range=[-2*PI, 2*PI], color=RED)

        # Create labels
        x_axis_label = axes.get_axis_labels(MathTex("x"), MathTex("y"))
        sine_label = MathTex("\\sin(x)", color=BLUE).next_to(sine_graph, UP, buff=0.2)
        cosine_label = MathTex("\\cos(x)", color=RED).next_to(cosine_graph, DOWN, buff=0.2)

        # Initial scene
        self.play(Create(axes), Write(x_axis_label), Create(sine_graph),
                  Create(cosine_graph), Write(sine_label), Write(cosine_label))

        # Highlight key points
        for i in range(-2, 3):
            dot = Dot(axes.c2p(i*PI, 0), color=YELLOW)
            self.play(GrowFromCenter(dot))

        max_min_points = [axes.c2p(i*PI/2, (-1)**(i + 1)) for i in range(-4, 5)]
        for point in max_min_points:
            dot = Dot(point, color=PINK)
            self.play(GrowFromCenter(dot))

        self.wait()

        # Show phase shift
        shifted_cosine_graph = axes.plot(lambda x: np.cos(x + PI/2),
                                        x_range=[-2*PI, 2*PI], color=RED)
        cosine_label_shifted = MathTex("\\cos(x + \\frac{\pi}{2})", color=RED).next_to(shifted_cosine_graph, DOWN, buff=0.2)

        self.play(Transform(cosine_graph, shifted_cosine_graph),
                  ReplacementTransform(cosine_label, cosine_label_shifted),
                  run_time=2)

        self.wait()