from manim import *


class GreenSpectrum(Scene):
    def construct(self):
        # Create the squares of dark and light green color
        dark_square = Square(fill_color=GREEN_D, fill_opacity=1).shift(4*LEFT)
        light_square = Square(fill_color=GREEN_A, fill_opacity=1).shift(4*RIGHT)
        self.play(Create(dark_square), Create(light_square))
        
        # Add the color labels for each square
        dark_label = Tex("Dark Green", color=GREEN_D).scale(0.5).next_to(dark_square, UP)
        light_label = Tex("Light Green", color=GREEN_A).scale(0.5).next_to(light_square, UP)
        self.play(Write(dark_label), Write(light_label))

        # Animate the transition of colors gradually
        self.play(dark_square.animate.set_color(GREEN_A))
        self.play(light_square.animate.set_color(GREEN_D))
        self.wait(1)

        # Label the new colors
        self.play(FadeOut(dark_label), FadeOut(light_label))
        dark_label = Tex("Light Green", color=GREEN_A).scale(0.5).next_to(dark_square, UP)
        light_label = Tex("Dark Green", color=GREEN_D).scale(0.5).next_to(light_square, UP)
        self.play(Write(dark_label), Write(light_label))
        self.wait(1)

        # Create a color bar to show the transition
        color_bar = Line(start=[-4, -3, 0], end=[4, -3, 0]).set_color(color_gradient([GREEN_D, GREEN_A], 2))
        self.play(Create(color_bar))

        # Label the color bar endpoints
        dark_endpoint = Tex("Dark Green").scale(0.5).next_to(color_bar.get_start(), DOWN)
        light_endpoint = Tex("Light Green").scale(0.5).next_to(color_bar.get_end(), DOWN)
        self.play(Write(dark_endpoint), Write(light_endpoint))
        self.wait(1)