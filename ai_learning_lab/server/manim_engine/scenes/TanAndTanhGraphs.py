from manim import *

class TanAndTanhGraphs(Scene):
    def construct(self):
        axes = Axes(x_range=[-3, 3], y_range=[-1, 1])
        
        # Plot tan function in blue
        tan_graph = axes.plot(lambda x: np.tan(x), x_range=[-3, 3], color=BLUE)
        tan_label = MathTex("\\tan(x)", color=BLUE).next_to(tan_graph, UR)
        
        # Plot tanh function in red
        tanh_graph = axes.plot(lambda x: np.tanh(x), x_range=[-3, 3], color=RED)
        tanh_label = MathTex("\\tanh(x)", color=RED).next_to(tanh_graph, UL)
        
        # Highlight the asymptotic behavior of tanh
        tanh_plus_one_line = axes.plot(lambda x: 1, x_range=[-3, 3], color=RED_D)
        tanh_minus_one_line = axes.plot(lambda x: -1, x_range=[-3, 3], color=RED_D)
        
        # Key points
        key_points = {
            -np.pi: "\\pi", 
            0: "0", 
            np.pi: "\\pi"
        }
        for x_coord, label_text in key_points.items():
            key_point = Dot(axes.c2p(x_coord, 0), color=YELLOW)
            key_label = MathTex(label_text).next_to(key_point, DOWN)
            self.add(key_point, key_label)
        
        self.add(axes, tan_graph, tan_label, tanh_graph, tanh_label, tanh_plus_one_line, tanh_minus_one_line)
        self.wait(1.5)