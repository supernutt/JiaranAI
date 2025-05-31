from manim import *

class PythagorasTheorem(Scene):
    def construct(self):
        # Create right triangle with squares on each side.
        triangle = Polygon(np.array([0,0,0]), np.array([4,0,0]), np.array([0,3,0]), fill_opacity=0.5)
        small_square = Square(side_length=3).next_to(triangle, LEFT, buff=0)
        medium_square = Square(side_length=4).next_to(triangle, DOWN, buff=0)
        hypotenuse_length = (3**2 + 4**2)**0.5
        big_square = Square(side_length=hypotenuse_length).rotate(np.arctan(3/4), about_point=np.array([0,0,0])).next_to(triangle, buff=0)

        triangle_label = MathTex("a=3", "b=4", "c=\sqrt{a^2 + b^2}").scale(0.7).next_to(triangle, UP)
        square_labels = MathTex("a^2=9", "b^2=16", "c=\sqrt{9 + 16}").scale(0.7).next_to(triangle_label, DOWN)

        # Add objects to the scene
        self.play(Create(triangle), Write(triangle_label), run_time=2)
        self.wait()
        self.play(Create(small_square), Write(square_labels[0]), run_time=2)
        self.wait()
        self.play(Create(medium_square), Write(square_labels[1]), run_time=2)
        self.wait()
        self.play(Create(big_square), Write(square_labels[2]), run_time=2)
        self.wait()
        
        # Transform squares into representation of the formula a^2 + b^2 = c^2
        self.play(
            ReplacementTransform(small_square, square_labels[0].copy().next_to(medium_square, UP, buff=2)),
            ReplacementTransform(medium_square, square_labels[1].copy().next_to(square_labels[0], buff=2)),
            ReplacementTransform(big_square, square_labels[2].copy().next_to(square_labels[1], buff=2)),
            run_time=3
        )
        self.wait()

        formula = MathTex('a^2', '+', 'b^2', '=', 'c^2').move_to(np.array([0,0,0]))
        self.play(
            ReplacementTransform(square_labels[0], formula[0]),
            ReplacementTransform(square_labels[1], formula[2]), 
            ReplacementTransform(square_labels[2], formula[4]),
            run_time=2
        )
        self.wait()