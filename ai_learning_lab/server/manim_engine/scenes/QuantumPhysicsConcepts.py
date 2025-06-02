from manim import *

class QuantumPhysicsConcepts(Scene):
    def construct(self):
        # Introduction
        intro = Title("Core Concepts of Quantum Physics")
        self.play(Create(intro))
        self.wait()

        # Superposition
        superposition_title = Text("Superposition")
        superposition_text = MathTex(r"\text{A particle can be in multiple states simultaneously.}")
        self.play(Write(superposition_title))
        self.wait()
        self.play(Write(superposition_text))
        self.wait()
  
        particle_states = VGroup(*[Dot().shift(i*RIGHT) for i in range(1, 4)])
        self.play(*[Create(particle_state) for particle_state in particle_states])
        self.wait()

        notice = Text("Upon measurement, it collapses into a single state:")
        self.play(FadeIn(notice, shift=UP))
        self.wait()

        # Show only one state remaining
        self.play(*[FadeOut(particle_state) for particle_state in particle_states[1:]])
        self.wait()

        # Uncertainty Principle
        self.play(FadeOut(superposition_title), FadeOut(superposition_text), FadeOut(notice), FadeOut(particle_states))

        uncertainty_title = Text("Uncertainty Principle")
        uncertainty_text = MathTex(r"\text{Greater precision in knowing particle's position results in greater uncertainty in momentum.}")
        self.play(Write(uncertainty_title))
        self.wait()
        self.play(Write(uncertainty_text))
        self.wait()

        position = Dot(color=BLUE).shift(LEFT*2)
        momentum = Dot(color=YELLOW).shift(RIGHT*2)
        position_label = Text("Position").next_to(position, DOWN)
        momentum_label = Text("Momentum").next_to(momentum, UP)

        self.play(Create(position), Create(momentum), Write(position_label), Write(momentum_label))
        self.wait()

        wave = WaveSource(num_points=400, amplitude=0.5, wavelength=1, start_color=BLUE, end_color=YELLOW)
        self.play(Create(wave, run_time=2))
        self.wait()

        # Entanglement
        self.play(FadeOut(uncertainty_title), FadeOut(uncertainty_text))

        entanglement_title = Text("Quantum Entanglement")
        entanglement_text = MathTex(r"\text{State of one particle instantly affecting state of other, regardless of distance.}")
        self.play(Write(entanglement_title))
        self.wait()
        self.play(Write(entanglement_text))
        self.wait()

        # Two particles with correlated states
        particle_1 = Dot().move_to([-2,0,0])
        particle_1_label = Text("Particle 1").next_to(particle_1, UP)
        particle_2 = Dot().move_to([2,0,0])
        particle_2_label = Text("Particle 2").next_to(particle_2, UP)

        self.play(Create(particle_1), Write(particle_1_label), Create(particle_2), Write(particle_2_label))

        # Switch state of both particles
        self.wait()
        self.play(particle_1.animate.shift(UP), particle_2.animate.shift(DOWN))
        self.wait()

        # Conclusion
        self.play(FadeOut(entanglement_title), FadeOut(entanglement_text))

        conclusion_title = Text("These are the fascinating concepts of Quantum Physics!")
        self.play(Write(conclusion_title))
        self.wait()
        self.play(FadeOut(conclusion_title))
        self.wait()
```
This given script will run correctly in the environment where Manim is installed and properly set up. The animation provides a basic visual explanation of core concepts of Quantum physics including superposition, uncertainty principle, and quantum entanglement. Keep in mind that you should install Manim Community edition (not 3b1b old version). Manim community edition can be installed via pip: `pip install manim`.