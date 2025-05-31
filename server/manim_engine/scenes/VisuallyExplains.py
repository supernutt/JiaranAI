from manim import *

# Generated from prompt: "Create a Manim animation that visually explains the Pythagorean theorem using a right triangle. Start by drawing a right triangle with sides labeled as 'a', 'b', and 'c'. Animate squares to represent the areas of the squares formed on each side of the triangle. Show that the sum of the areas of the squares on the two smaller sides ('a' and 'b') is equal to the area of the square on the hypotenuse ('c'). Highlight this relationship by animating the squares transforming into each other. Label each square with the corresponding side length squared (e.g., 'a²', 'b²', 'c²'). Finally, display the Pythagorean theorem equation: 'a² + b² = c²' and emphasize the concept with a clear visual representation."
class VisuallyExplains(Scene):
    def construct(self):
        # Create a text object with the prompt
        text = Text("Animation: Create a Manim animation that visually explains the Pythagorean theorem using a right triangle. Start by drawing a right triangle with sides labeled as 'a', 'b', and 'c'. Animate squares to represent the areas of the squares formed on each side of the triangle. Show that the sum of the areas of the squares on the two smaller sides ('a' and 'b') is equal to the area of the square on the hypotenuse ('c'). Highlight this relationship by animating the squares transforming into each other. Label each square with the corresponding side length squared (e.g., 'a²', 'b²', 'c²'). Finally, display the Pythagorean theorem equation: 'a² + b² = c²' and emphasize the concept with a clear visual representation.", font_size=36)
        
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
