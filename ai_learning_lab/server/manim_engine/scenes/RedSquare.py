# Required import
from manim import *

# Define the class and methods for the animation
class RedSquare(Scene):
    def construct(self):
        # Create a square centered at origin, colored red
        square = Square(color=RED)
        
        # Animate the creation of the square
        self.play(Create(square))
        
        # Hold the frame
        self.wait()