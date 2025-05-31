```python
from manim import *

class RedSquare(Scene):
    def construct(self):
        square = Square(color=RED)
        self.play(FadeIn(square))
        self.wait(1)
        self.play(FadeOut(square))
```