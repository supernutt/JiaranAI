from manim import *

class DemonstratePythagoreanTheorem(Scene):
    def construct(self):
        # Create the right triangle 
        triangle = Polygon(np.array([0,0,0]), np.array([3,0,0]), np.array([0,4,0]), fill_opacity=0.5)
        self.play(FadeIn(triangle))
        self.wait(1)

        # Label the sides of the triangle
        tex_a = MathTex("a").next_to(triangle, LEFT)
        tex_b = MathTex("b").next_to(triangle, DOWN)
        tex_c = MathTex("c").next_to(triangle.get_center(), RIGHT).shift(UP)

        self.play(Write(tex_a))
        self.wait(1)
        self.play(Write(tex_b))
        self.wait(1)
        self.play(Write(tex_c))
        self.wait(1)

        # Draw squares on the sides a and b
        square_a = Square(3).next_to(triangle, LEFT).shift(LEFT).set_fill(BLUE, opacity=0.5)
        square_b = Square(4).next_to(triangle, DOWN).shift(DOWN).set_fill(YELLOW, opacity=0.5)
        self.play(Create(square_a), Create(square_b))
        self.wait(1)

        # Draw a square on the side c
        square_c = Square(5).rotate(PI/4).scale(0.7).move_to(triangle.get_center()).set_fill(GREEN, opacity=0.5)
        self.play(Create(square_c))
        self.wait(1)

        # Animate the squares resizing and add the equation text
        square_a.animate.scale(0.3).shift(UP+RIGHT*3)
        square_b.animate.scale(0.3).shift(UP+RIGHT*2)

        equation_text = MathTex("a^2", "+", "b^2", "=", "c^2").next_to(triangle, RIGHT).shift(2*RIGHT)
        self.play(Write(equation_text))

        # Show the squares moving to their corresponding position in the equation
        square_a_target = square_a.copy().move_to(equation_text[0].get_center())
        square_b_target = square_b.copy().move_to(equation_text[2].get_center())
        square_c_target = square_c.copy().move_to(equation_text[4].get_center())

        self.play(Transform(square_a, square_a_target), Transform(square_b, square_b_target), Transform(square_c, square_c_target))
        self.wait(3)