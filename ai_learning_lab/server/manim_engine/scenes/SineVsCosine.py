from manim import *

class SineVsCosine(Scene):
    def construct(self):
        # Set up axes
        axes = Axes(
            x_range=[-2*PI, 2*PI, PI],
            y_range=[-1.5, 1.5, 0.5],
            axis_config={
                "include_tip": True,
            },
            x_axis_config={
                "numbers_to_include": [-2*PI, -PI, 0, PI, 2*PI],
                "label_direction": DOWN,
            },
            y_axis_config={
                "include_tip": False,
            }
        )

        # Plot functions
        sine_graph = axes.plot(lambda x: np.sin(x), color=BLUE)
        cosine_graph = axes.plot(lambda x: np.cos(x), color=RED)

        # Add labels
        axes_labels = axes.get_axis_labels(x_label="x", y_label="y")
        self.add(axes_labels)
        sine_label = MathTex("\\sin(x)", color=BLUE).next_to(sine_graph, UP_RIGHT)
        cosine_label = MathTex("\\cos(x)", color=RED).next_to(cosine_graph, DOWN_RIGHT)
        self.add(sine_label, cosine_label)

        # Add starting points
        sine_dot = Dot(axes.c2p(0, np.sin(0)), color=BLUE_D)
        cosine_dot = Dot(axes.c2p(0, np.cos(0)), color=RED_D)
        self.add(sine_dot, cosine_dot)

        # Animate sine function
        self.play(sine_dot.animate.move_to(axes.c2p(PI/2, np.sin(PI/2))), run_time=2)
        self.wait(1)
        self.play(sine_dot.animate.move_to(axes.c2p(PI, np.sin(PI))), run_time=2)
        self.wait(1)
        
        # Animate cosine function
        self.play(cosine_dot.animate.move_to(axes.c2p(PI/2, np.cos(PI/2))), run_time=2)
        self.wait(1)
        self.play(cosine_dot.animate.move_to(axes.c2p(PI, np.cos(PI))), run_time=2)
        self.wait(1)
        
        # Emphasize phase shift
        phase_shift_label = MathTex("\\text{Phase shift}", color=YELLOW).next_to(axes.c2p(PI/2, 0), UP)
        phase_shift_arrow = Arrow(axes.c2p(0, 0), axes.c2p(PI/2, 0), color=YELLOW)
        self.play(Create(phase_shift_arrow), Write(phase_shift_label), run_time=2)

        self.wait()