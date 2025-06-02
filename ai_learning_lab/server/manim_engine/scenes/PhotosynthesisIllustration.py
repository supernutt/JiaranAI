from manim import *
import numpy as np

class PhotosynthesisIllustration(Scene):
    def construct(self):
        # Set labels for chemical components and energy
        sunlight_label = Tex("Sunlight", color=YELLOW)
        water_label = Tex("H2O", color=BLUE)
        oxygen_label = Tex("O2", color=GREEN_A)
        carbon_dioxide_label = Tex("CO2", color=DARK_GRAY)
        glucose_label = Tex("C6H12O6", color=TEAL)
        atp_label = Tex("ATP", color=RED)

        # Set plant components
        root = Line(DOWN, DR, color=GREEN_D)
        stem = Line(DOWN, UP, color=GREEN_D)
        leaf = SVGMobject("Leaf", color=GREEN_B)
        chloroplast = Dot(color=DARK_BLUE)

        # Set initial positions for plant components and labels
        root.next_to(stem, DOWN)
        leaf.next_to(stem, UP)
        chloroplast.move_to(leaf.get_center())
        sunlight_label.next_to(leaf, UP)
        water_label.next_to(root, DOWN)
        oxygen_label.next_to(leaf, RIGHT)
        carbon_dioxide_label.next_to(leaf, LEFT)
        glucose_label.next_to(leaf, DOWN)
        atp_label.next_to(stem, RIGHT)

        # Animate the plant
        self.play(Create(stem), Create(root), run_time=2)
        self.play(FadeIn(leaf), run_time=1)
        self.play(FadeIn(chloroplast), run_time=1)

        # Light-dependent reactions
        self.play(Write(sunlight_label), Write(water_label), run_time=2)
        self.play(chloroplast.animate.scale(1.5), Sunset(leaf, color=YELLOW), run_time=2)
        self.play(Approach(water_label, chloroplast))
        self.wait(1)
        self.play(Write(oxygen_label), run_time=2)
        self.play(Approach(oxygen_label, LEFT))
        
        # Light-independent reactions (Calvin cycle)
        self.play(Write(carbon_dioxide_label), run_time=2)
        self.wait(1)
        self.play(Transform(carbon_dioxide_label, glucose_label), run_time=2)
        self.play(Approach(glucose_label, RIGHT), run_time=2)

        # Use of glucose
        self.play(Write(atp_label), run_time=2)
        self.play(Approach(glucose_label, atp_label), run_time=2)

        self.wait(2)