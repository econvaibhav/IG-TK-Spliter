# Environment

Use a separate Python 3.10-3.12 environment and an FFmpeg executable on `PATH`.

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
ffmpeg -version
```

The processors import `moviepy.editor`, which requires MoviePy 1.x. The Python
module `ffmpeg` is provided by `ffmpeg-python`; that package does not install the
FFmpeg executable. `requirements.txt` specifies direct compatibility versions,
not a complete lockfile of every transitive dependency.

Keep this environment separate from Jupyter: MoviePy 1.0.3 requires
`decorator<5`, while some IPython versions require `decorator>=5.1`.

Run commands from the repository root so the six icon templates can be found.
The batch launcher uses Linux CPU-affinity APIs and symbolic links.
