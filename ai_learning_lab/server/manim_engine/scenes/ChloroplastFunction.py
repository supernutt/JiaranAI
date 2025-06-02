from manim import *

class ChloroplastFunction(Scene):
    def construct(self):
        plant_cell = RoundedRectangle(height=5, width=8, color=GREEN)
        chloroplast = Circle(radius=1, color=YELLOW)
        chloroplast.next_to(plant_cell, UP, buff=0.5)

        # Animation starts with a plant cell, with a chloroplast within
        self.play(Create(plant_cell), Create(chloroplast))
        self.wait(1)
        
        # Zooming into the chloroplast
        self.play(self.camera.frame.animate.scale(0.25).move_to(chloroplast))
        self.wait(1)
        
        # Drawing inner and outer membranes of chloroplast
        inner_membrane = Circle(radius=0.8, color=BLUE)
        outer_membrane = Circle(radius=0.9, color=BLUE)
        self.play(Create(inner_membrane), Create(outer_membrane))
        self.wait(1)

        # Drawing stroma and grana
        stroma = Circle(radius=0.7, color=YELLOW)
        grana = SmoothedRectangle(height=0.4, width=0.6, color=DARK_BLUE)
        grana.move_to(stroma.get_center())
        self.play(Create(stroma), Create(grana))
        
        # Showing chlorophyll on the thylakoid membranes
        chlorophyll = Dot(point=grana.get_center(), color=GREEN)
        self.play(Create(chlorophyll))
        self.wait(1)

        # Demonstrating photosynthesis
        sunlight = Arrow(start=3*UP, end=chlorophyll.get_center()+0.2*DOWN, color=YELLOW)
        self.play(Create(sunlight))
        self.wait(1)

        energy = Arrow(start=chlorophyll.get_center(), end=2*RIGHT, color=RED)
        self.play(FadeOut(sunlight), Create(energy))
        self.wait(1)

        # Highlighting glucose and oxygen production
        glucose = MathTex(r"C_6H_{12}O_6").next_to(energy, RIGHT)
        oxygen = MathTex(r"6O_2").next_to(glucose, RIGHT)
        self.play(Write(glucose), Write(oxygen))
        self.wait(2)