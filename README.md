# manim-cache-demo

Animations of systems concepts using [Manim Community (ManimCE)](https://docs.manim.community/).

Scenes:

- `cache_demo.py` / `CacheDemo` — basic cache hit/miss.
- `pix_cache_aside.py` / `PixCacheAside` — Pix receipt API saturating
  Postgres at peak time and being saved by cache-aside (Redis).

## Installation

Project managed with [uv](https://docs.astral.sh/uv/), pinned to Python 3.13
(3.14 doesn't have pre-built wheels for `glcontext` yet).
FFmpeg is not required — ManimCE 0.20 uses the `av` library.

```powershell
uv sync
```

## Rendering

```powershell
uv run manim -pql pix_cache_aside.py PixCacheAside   # low quality, opens when done
uv run manim -pqh pix_cache_aside.py PixCacheAside   # high quality (1080p)
uv run manim -pql cache_demo.py CacheDemo
```

The video is written to `media/videos/cache_demo/`.

> **Note:** if Windows App Control blocks `uv run` (os error 4551 — it flags the
> unsigned launcher shims in `.venv\Scripts`), run the base interpreter directly:
>
> ```powershell
> $env:PYTHONPATH = "$PWD\.venv\Lib\site-packages"
> & "$env:APPDATA\uv\python\cpython-3.13-windows-x86_64-none\python.exe" -m manim -pqh pix_cache_aside.py PixCacheAside
> ```
