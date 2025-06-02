from manim import *
import numpy as np

class PhotosynthesisExplanation(Scene):
    def construct(self):
        # Text labels
        sunlight_text = Text("Sunlight", color=YELLOW)
        carbondioxide_text = Text("Carbon Dioxide", color=RED)
        glucose_text = Text("Glucose", color=GREEN)
        oxygen_text = Text("Oxygen", color=BLUE)
        chlorophyll_text = Text("Chlorophyll", color=GREEN_D)

        # Drawing plant as rectangle
        plant = Rectangle(height=3, width=2, color=GREEN)
        self.play(Create(plant))
        
        # Create a sun with rays representing sunlight
        sun = Circle().set_height(1).set_fill(YELLOW, opacity=1)
        sun.move_to(3*UP+4*LEFT)

        # Create simple rays manually
        rays = []
        for i in range(8):
            angle = i * PI / 4
            direction = np.array([np.cos(angle), np.sin(angle), 0])
            ray = Line(sun.get_center(), sun.get_center() + direction).set_stroke(YELLOW, 2)
            rays.append(ray)
        
        self.play(AnimationGroup(*[GrowFromCenter(ray) for ray in rays], lag_ratio=0.5))
        
        # Position labels
        sunlight_text.next_to(sun, UP)
        carbondioxide_text.to_edge(LEFT)
        glucose_text.to_edge(RIGHT)
        oxygen_text.to_edge(UP)
        chlorophyll_text.move_to(plant.get_center())
        
        # Show the process 
        self.play(Write(sunlight_text))
        self.play(plant.animate.set_fill(GREEN_A, 1), Write(chlorophyll_text))
        self.wait(1)
        self.play(Write(carbondioxide_text))

        carbondioxide_movement = carbondioxide_text.copy()
        self.play(carbondioxide_movement.animate.move_to(plant.get_center()))
        self.wait(1)

        self.play(Write(glucose_text))

        glucose_movement = glucose_text.copy()
        self.play(glucose_movement.animate.move_to(plant.get_center()))
        self.wait(1)

        self.play(Write(oxygen_text))

        oxygen_movement = oxygen_text.copy()
        self.play(oxygen_movement.animate.move_to(plant.get_center()))
        self.wait(1)