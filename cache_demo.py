"""Animação de cache hit/miss com Manim Community (ManimCE).

Renderizar:
    manim -pql cache_demo.py CacheDemo      # preview em baixa qualidade
    manim -pqh cache_demo.py CacheDemo      # alta qualidade (1080p)
"""

from manim import *


class CacheDemo(Scene):
    def construct(self):
        # --- Componentes: Client, Cache e DB ---
        client_box = RoundedRectangle(width=2.2, height=1.2, corner_radius=0.15)
        client_box.shift(LEFT * 4.5)
        cache_box = RoundedRectangle(width=2.2, height=1.2, corner_radius=0.15, color=YELLOW)
        db_box = RoundedRectangle(width=2.2, height=1.2, corner_radius=0.15, color=BLUE)
        db_box.shift(RIGHT * 4.5)

        client_label = Text("Client", font_size=28).move_to(client_box)
        cache_label = Text("Cache", font_size=28).move_to(cache_box)
        db_label = Text("DB", font_size=28).move_to(db_box)

        title = Text("Cache: miss e hit", font_size=36).to_edge(UP)

        self.play(Write(title))
        self.play(
            FadeIn(client_box, client_label),
            FadeIn(cache_box, cache_label),
            FadeIn(db_box, db_label),
        )
        self.wait(0.5)

        # --- Primeira requisição: cache MISS ---
        status = Text("GET user:42", font_size=24, color=GREEN).next_to(title, DOWN)
        self.play(FadeIn(status))

        req = Dot(color=GREEN, radius=0.12).move_to(client_box)
        self.play(req.animate.move_to(cache_box), run_time=1)

        miss = Text("MISS", font_size=24, color=RED).next_to(cache_box, DOWN)
        self.play(Indicate(cache_box, color=RED), FadeIn(miss))
        self.wait(0.3)

        # Vai até o banco e volta populando o cache
        self.play(req.animate.move_to(db_box), run_time=1)
        self.play(Indicate(db_box, color=BLUE))

        entry = Text("user:42", font_size=20, color=YELLOW).next_to(cache_box, UP)
        self.play(req.animate.move_to(cache_box), run_time=1)
        self.play(FadeIn(entry), FadeOut(miss))  # cache populado

        self.play(req.animate.move_to(client_box), run_time=1)
        self.play(FadeOut(req), FadeOut(status))
        self.wait(0.5)

        # --- Segunda requisição: cache HIT ---
        status2 = Text("GET user:42 (de novo)", font_size=24, color=GREEN).next_to(title, DOWN)
        self.play(FadeIn(status2))

        req2 = Dot(color=GREEN, radius=0.12).move_to(client_box)
        self.play(req2.animate.move_to(cache_box), run_time=1)

        hit = Text("HIT", font_size=24, color=GREEN).next_to(cache_box, DOWN)
        self.play(Indicate(cache_box, color=GREEN), FadeIn(hit))
        self.play(req2.animate.move_to(client_box), run_time=0.6)  # resposta rápida, sem ir ao DB

        conclusion = Text(
            "Sem ida ao banco: resposta direto do cache",
            font_size=24,
        ).to_edge(DOWN)
        self.play(FadeIn(conclusion))
        self.wait(2)
