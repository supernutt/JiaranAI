from manim import *
import numpy as np

class Photosynthesis(Scene):
    def construct(self):

        # Create plant
        plant = Text("Plant", color=GREEN, font_size=50)
        self.play(Write(plant))
        self.wait()

        # Create chloroplast
        chloroplast = Circle(radius=1, color=GREEN_D, fill_opacity=0.5)
        chloroplast_label = MathTex("Chloroplast").next_to(chloroplast, UP)
        self.play(Create(chloroplast), Write(chloroplast_label))
        self.wait()

        # Show sunlight absorption
        sunlight = Arrow(start=3*UP, end=chloroplast.get_center(), color=YELLOW)
        sunlight_label = Text("Sunlight").next_to(sunlight, RIGHT)
        self.play(Create(sunlight), Write(sunlight_label))
        self.wait()

        # Illustrate water splitting
        water = Text("H2O").set_color(BLUE).next_to(chloroplast, DOWN)
        self.play(Write(water))
        self.wait()

        oxygen = Text("O2").set_color(RED).next_to(water, DOWN)
        self.play(ReplacementTransform(water, oxygen))
        self.wait()

        # Show electron transport chain
        etc = Line(chloroplast.get_bottom(), oxygen.get_top()).set_color(DARK_GRAY)
        self.play(Create(etc))
        self.wait()

        # Show ATP synthase complex
        atp_synthase = Square().set_color(PURPLE).move_to(chloroplast.get_center())
        atp_synthase_label = MathTex("ATP", "\ Synthase").next_to(atp_synthase, UP)
        self.play(Transform(chloroplast, atp_synthase), Write(atp_synthase_label))

        # Show Calvin cycle
        calvin_cycle = Circle(radius=2).set_color(BLUE)
        calvin_cycle.next_to(chloroplast, RIGHT, buff=2)
        calvin_cycle_label = MathTex("Calvin", "\ Cycle").next_to(calvin_cycle, UP)
        self.play(Create(calvin_cycle), Write(calvin_cycle_label))

        # Show fixation of carbon dioxide
        carbon_dioxide = Text("CO2").next_to(calvin_cycle, LEFT)
        self.play(Write(carbon_dioxide))
        self.wait()

        # Show production of glucose
        glucose = Text("C6H12O6").next_to(calvin_cycle, RIGHT)
        self.play(ReplacementTransform(carbon_dioxide, glucose))
        self.wait()

        # Show release of oxygen
        oxygen_release = Text("O2").next_to(oxygen, DOWN)
        self.play(ReplacementTransform(oxygen, oxygen_release))

        self.wait()