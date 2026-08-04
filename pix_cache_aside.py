"""Cenário real: API de comprovantes Pix sob carga, resolvida com cache-aside.

Narrativa:
  1. App do banco consulta comprovante de Pix na API, que busca no Postgres (~45 ms).
  2. Horário de pico (dia 5, salários caindo): consultas se acumulam, o banco satura.
  3. Entra o Redis com o padrão cache-aside: miss -> busca no banco -> grava no cache.
  4. Consultas seguintes respondem direto do cache (~3 ms) e o banco respira.

Renderizar:
    uv run manim -pql pix_cache_aside.py PixCacheAside
    uv run manim -pqh pix_cache_aside.py PixCacheAside
"""

from manim import *


def service_box(label: str, color, width: float = 2.3, height: float = 1.05,
                font_size: int = 26) -> VGroup:
    box = RoundedRectangle(width=width, height=height, corner_radius=0.15, color=color)
    txt = Text(label, font_size=font_size).move_to(box)
    return VGroup(box, txt)


class PixCacheAside(Scene):
    def construct(self):
        self.caption = None
        self.latency = None
        self.cpu = None

        self.build_architecture()
        self.normal_traffic()
        self.bottleneck()
        self.cache_aside()
        self.finale()

    # ------------------------------------------------------------------ helpers

    def set_caption(self, text: str, color=WHITE, run_time: float = 0.5):
        new = Text(text, font_size=24, color=color).to_edge(DOWN)
        if self.caption is None:
            self.play(FadeIn(new), run_time=run_time)
        else:
            self.play(FadeOut(self.caption), FadeIn(new), run_time=run_time)
        self.caption = new

    def set_latency(self, value: str, color):
        new = Text(f"latência: {value}", font_size=24, color=color).to_corner(UR)
        if self.latency is None:
            self.latency = new
            self.play(FadeIn(new), run_time=0.4)
        else:
            self.play(Transform(self.latency, new), run_time=0.4)

    def set_cpu(self, value: str, color):
        new = Text(f"CPU {value}", font_size=20, color=color)
        new.next_to(self.db, DOWN, buff=0.15)
        if self.cpu is None:
            self.cpu = new
            self.play(FadeIn(new), run_time=0.4)
        else:
            self.play(Transform(self.cpu, new), run_time=0.4)

    def travel(self, points, color=GREEN, seg_time: float = 0.55, keep=False):
        """Anima um Dot passando pelos pontos dados; retorna o Dot."""
        dot = Dot(color=color, radius=0.1).move_to(points[0])
        self.add(dot)
        for p in points[1:]:
            self.play(dot.animate.move_to(p), run_time=seg_time)
        if not keep:
            self.play(FadeOut(dot), run_time=0.15)
        return dot

    # ------------------------------------------------------------------ fases

    def build_architecture(self):
        title = Text("Pix: consulta de comprovante", font_size=34).to_edge(UP)

        self.apps = VGroup(*[
            service_box("App", GREEN_B, width=1.5, height=0.7, font_size=20)
            for _ in range(3)
        ]).arrange(DOWN, buff=0.35).shift(LEFT * 5.4)

        self.api = service_box("API Pix", WHITE).shift(LEFT * 1.3)
        self.db = service_box("Postgres", BLUE).shift(RIGHT * 5)

        self.link_in = Line(self.apps.get_right() + RIGHT * 0.1,
                            self.api.get_left() + LEFT * 0.1,
                            stroke_opacity=0.35)
        self.link_db = Line(self.api.get_right() + RIGHT * 0.1,
                            self.db.get_left() + LEFT * 0.1,
                            stroke_opacity=0.35)

        self.play(Write(title))
        self.play(
            FadeIn(self.apps),
            FadeIn(self.api),
            FadeIn(self.db),
            Create(self.link_in),
            Create(self.link_db),
        )
        self.set_caption("Fez um Pix? O app busca o comprovante na API, que consulta o banco")

    def normal_traffic(self):
        self.set_latency("45 ms", GREEN)
        self.set_cpu("30%", GREEN)

        app = self.apps[1].get_center()
        api = self.api.get_center()
        db = self.db.get_center()
        self.travel([app, api, db, api, app])
        self.wait(0.4)

    def bottleneck(self):
        self.set_caption("Dia 5, salário caiu: todo mundo fazendo e conferindo Pix", YELLOW)

        dots = VGroup(*[
            Dot(color=GREEN, radius=0.09).move_to(self.apps[i % 3].get_center())
            for i in range(6)
        ])
        self.add(dots)
        self.play(LaggedStart(
            *[d.animate.move_to(self.api.get_center()) for d in dots],
            lag_ratio=0.12, run_time=1.2,
        ))

        # Requisições enfileiram esperando o banco
        queue = [self.db.get_left() + LEFT * (0.45 + 0.42 * i) for i in range(6)]
        self.play(LaggedStart(
            *[d.animate.move_to(p) for d, p in zip(dots, queue)],
            lag_ratio=0.12, run_time=1.2,
        ))

        self.set_latency("380 ms", YELLOW)
        self.set_cpu("78%", YELLOW)
        self.play(dots.animate.set_color(ORANGE), run_time=0.5)

        self.set_caption("Toda consulta vai ao banco: pool de conexões esgotado", ORANGE)
        self.set_latency("2,4 s", RED)
        self.set_cpu("97%", RED)
        self.play(
            self.db[0].animate.set_color(RED),
            dots.animate.set_color(RED),
            run_time=0.6,
        )
        self.play(Indicate(self.db, color=RED))

        self.set_caption("Usuários olhando a telinha de loading…", RED)
        self.wait(0.8)

        # Fila é processada lentamente e some
        self.play(LaggedStart(
            *[FadeOut(d, target_position=self.db.get_center()) for d in dots],
            lag_ratio=0.2, run_time=2,
        ))
        self.wait(0.3)

    def cache_aside(self):
        self.set_caption("Solução: cache-aside com Redis", WHITE)

        self.redis = service_box("Redis", YELLOW).move_to(
            (self.api.get_center() + self.db.get_center()) / 2 + UP * 1.9
        )
        self.link_cache = DashedLine(
            self.api.get_top() + UP * 0.1,
            self.redis.get_left() + LEFT * 0.1,
            stroke_opacity=0.45, color=YELLOW,
        )
        self.play(FadeIn(self.redis), Create(self.link_cache))
        self.wait(0.3)

        app = self.apps[1].get_center()
        api = self.api.get_center()
        db = self.db.get_center()
        redis = self.redis.get_center()

        # 1) consulta o cache -> MISS
        self.set_caption("1) API consulta o Redis primeiro → MISS", YELLOW)
        dot = self.travel([app, api, redis], keep=True)
        miss = Text("MISS", font_size=22, color=RED).next_to(self.redis, UP, buff=0.15)
        self.play(Indicate(self.redis, color=RED), FadeIn(miss))

        # 2) busca no banco
        self.set_caption("2) No miss, a API busca no banco (1 única vez)", WHITE)
        self.play(dot.animate.move_to(api), run_time=0.4)
        self.play(dot.animate.move_to(db), run_time=0.55)
        self.play(Indicate(self.db, color=BLUE), run_time=0.6)
        self.play(dot.animate.move_to(api), run_time=0.55)

        # 3) grava no cache
        self.set_caption('3) Grava no Redis: SET comprovante:9f3a  (TTL 10 min)', YELLOW)
        self.play(dot.animate.move_to(redis), run_time=0.55)
        entry = Text("comprovante:9f3a", font_size=18, color=YELLOW)
        entry.next_to(self.redis, UP, buff=0.15)
        self.play(FadeOut(miss), FadeIn(entry))

        # 4) responde
        self.set_caption("4) Responde ao app", GREEN)
        self.play(dot.animate.move_to(api), run_time=0.4)
        self.play(dot.animate.move_to(app), run_time=0.5)
        self.play(FadeOut(dot), run_time=0.15)

        # Consultas seguintes: HIT direto do cache
        self.set_caption("Consultas seguintes do mesmo comprovante: HIT no cache", GREEN)
        self.set_latency("3 ms", GREEN)
        hit = Text("HIT", font_size=22, color=GREEN).next_to(entry, RIGHT, buff=0.25)
        for i in range(3):
            src = self.apps[i].get_center()
            d = self.travel([src, api, redis], seg_time=0.3, keep=True)
            if i == 0:
                self.play(Indicate(self.redis, color=GREEN), FadeIn(hit), run_time=0.5)
            self.play(d.animate.move_to(api), run_time=0.3)
            self.play(d.animate.move_to(src), run_time=0.3)
            self.play(FadeOut(d), run_time=0.1)

        self.set_cpu("25%", GREEN)
        self.play(self.db[0].animate.set_color(BLUE), FadeOut(hit), run_time=0.6)

    def finale(self):
        self.set_caption(
            "Cache-aside: o banco só vê a 1ª consulta; o resto sai do Redis",
            GREEN, run_time=0.8,
        )
        stats = VGroup(
            Text("antes: 2,4 s  |  CPU 97%", font_size=22, color=RED),
            Text("depois: 3 ms  |  CPU 25%", font_size=22, color=GREEN),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).to_corner(UL).shift(DOWN * 0.9)
        self.play(FadeIn(stats))
        self.wait(2.5)
