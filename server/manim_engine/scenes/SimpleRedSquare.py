from manim import *

class SimpleRedSquare(Scene):
    def construct(self):
        square = Square(color=RED)
        self.play(FadeIn(square))
        self.wait()
        self.play(FadeOut(square))