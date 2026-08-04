# manim-cache-demo

Animações de conceitos de sistemas usando [Manim Community (ManimCE)](https://docs.manim.community/).

Cenas:

- `cache_demo.py` / `CacheDemo` — cache hit/miss básico.
- `pix_cache_aside.py` / `PixCacheAside` — API de comprovantes Pix saturando o
  Postgres no pico e sendo salva com cache-aside (Redis).

## Instalação

Projeto gerenciado com [uv](https://docs.astral.sh/uv/), pinado no Python 3.13
(o 3.14 ainda não tem wheels pré-compilados para o `glcontext`).
FFmpeg não é necessário — o ManimCE 0.20 usa a lib `av`.

```powershell
uv sync
```

## Renderizar

```powershell
uv run manim -pql pix_cache_aside.py PixCacheAside   # baixa qualidade, abre ao terminar
uv run manim -pqh pix_cache_aside.py PixCacheAside   # alta qualidade (1080p)
uv run manim -pql cache_demo.py CacheDemo
```

O vídeo sai em `media/videos/cache_demo/`.
