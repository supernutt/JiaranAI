from manim import *

class PythagoreanTheorem(Scene):
    def construct(self):
        # Initialize the sizes of the sides of the triangle
        a = 3
        b = 4
        c = 5

        # Create the triangle and squares
        triangle = Polygon([0, 0, 0], [a, 0, 0], [0, b, 0], fill_opacity=0.5)
        square_c = Square(side_length=c, fill_opacity=0.5)
        square_a = Square(side_length=a, fill_opacity=0.5).rotate(PI/2).next_to(triangle, LEFT)
        square_b = Square(side_length=b, fill_opacity=0.5).next_to(triangle, DOWN)

        # Create the labels for the sides of the triangle
        side_a = MathTex("a").next_to(square_a, LEFT)
        side_b = MathTex("b").next_to(square_b, DOWN)
        side_c = MathTex("c").next_to(square_c, RIGHT)

        # Animate the growth of the squares
        self.play(Create(triangle), Create(square_a), Create(square_b), Create(square_c),
                  Write(side_a), Write(side_b), Write(side_c))
        
        # Create a group for the squares to move them together
        squares_group = VGroup(square_a, square_b)

        # Move squares to the left side of the triangle
        self.play(squares_group.to_edge, LEFT)

        # Create the theorem equation
        equation = MathTex("a^2 + b^2 = c^2").to_edge(UP)

        # Show the formula
        self.play(Write(equation), run_time=2)

        self.wait()