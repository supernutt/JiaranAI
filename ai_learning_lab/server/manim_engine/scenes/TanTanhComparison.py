from manim import *

class TanTanhComparison(Scene):
    def construct(self):
        # Create coordinate system
        axes = Axes(
            x_range=[-3*PI, 3*PI, PI], 
            y_range=[-2, 2, 1], 
            axis_config={
                "include_numbers": True, 
                "numbers_to_include": [-2*PI, -PI, 0, PI, 2*PI]
            }
        )
        axes_labels = axes.get_axis_labels(
            x_label=MathTex("-3\pi", "-2\pi", "-\pi", "0", "\pi", "2\pi", "3\pi"), 
            y_label=MathTex("-2", "-1", "0", "1", "2")
        )

        # Plot functions
        tan_graph = axes.plot(
            lambda x: np.tan(x), 
            x_range=[-3*PI, 3*PI, 0.01], 
            color=BLUE, 
            discontinuities=[-2.5*PI, -0.5*PI, 1.5*PI]
        )
        tanh_graph = axes.plot(
            lambda x: np.tanh(x), 
            x_range=[-3*PI, 3*PI], 
            color=RED
        )

        # Add labels for both functions
        tan_label = MathTex("\\tan(x)", color=BLUE).next_to(tan_graph, UP, buff=0.1)
        tanh_label = MathTex("\\tanh(x)", color=RED).next_to(tanh_graph, UP, buff=0.1)

        # Define asymptotes for tan function
        asymptotes = VGroup(
            *[DashedLine(axes.c2p((2*i-1)*PI/2, -3), axes.c2p((2*i-1)*PI/2, 3), color=YELLOW) for i in range(-3, 4)]
        )
        asymptotes_label = MathTex("\\text{asymptotes}", color=YELLOW)

        # Define saturation limits for tanh function
        upper_limit = DashedLine(axes.c2p(-3*PI, 1), axes.c2p(3*PI, 1), color=PURPLE)
        lower_limit = DashedLine(axes.c2p(-3*PI, -1), axes.c2p(3*PI, -1), color=PURPLE)
        limits = VGroup(upper_limit, lower_limit)
        limits_label = MathTex("\\text{saturation limits}", color=PURPLE)

        # Add elements to scene
        self.add(axes, axes_labels, tan_graph, tanh_graph, tan_label, tanh_label, asymptotes, limits)
        self.add(asymptotes_label.next_to(asymptotes, UP))
        self.add(limits_label.next_to(limits, DOWN))
        self.wait(2)