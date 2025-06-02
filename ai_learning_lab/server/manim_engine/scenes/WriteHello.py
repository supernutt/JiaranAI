from manim import *

class WriteHello(Scene):
    def construct(self):
        # Create text object
        hello_text = Text("Hello, World!", font_size=72)
        
        # Animation sequence
        self.play(Write(hello_text))
        self.wait(1)
        
        # Transform to a different color
        colored_text = Text("Hello, World!", font_size=72, color=BLUE)
        self.play(Transform(hello_text, colored_text))
        self.wait(1)
        
        # Fade out
        self.play(FadeOut(hello_text))
        self.wait(0.5) 