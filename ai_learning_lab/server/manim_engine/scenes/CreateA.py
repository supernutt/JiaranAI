from manim import *

# Generated from prompt: "Create a simple scene with a square that turns into a circle"
class CreateA(Scene):
    def construct(self):
        # Create a text object with the prompt
        text = Text("Animation: Create a simple scene with a square that turns into a circle", font_size=36)
        
        # Animate writing the text
        self.play(Write(text))
        self.wait(1)
        
        # Transform to a different position
        self.play(text.animate.to_edge(UP))
        self.wait(1)
        
        # Create a circle
        circle = Circle(radius=2, color=BLUE)
        
        # Animate drawing the circle
        self.play(Create(circle))
        self.wait(1)
        
        # Fade out
        self.play(FadeOut(text), FadeOut(circle))
        self.wait(0.5)
