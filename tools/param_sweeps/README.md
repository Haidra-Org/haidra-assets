# Parameter sweeps

Renders the illustration library the Learn surfaces teach generation parameters from: for each
parameter, a strip of images that differ in that parameter and nothing else, with a plain-language
caption on every stop.

One checked-in specification, [`sweep_spec.json`](sweep_spec.json), describes the whole library.
Two runners render it: **local**, through [horde-engine](https://pypi.org/project/horde-engine/)
on your own GPU, and **horde**, through the public AI Horde API. Both write the same files, so a
strip rendered one way is interchangeable with the same strip rendered the other way.

Unlike the other tools in this directory, this one is not standard-library-only: it has its own
`pyproject.toml` and is installed as a package.

## What it produces

```text
assets/param-sweeps/
  index.json                                  everything a web app needs to draw every strip
  steps/deliberate/person/001_4.webp          the image
  steps/deliberate/person/001_4.json          its sidecar: full params, model, seed, runner, timings
  ...
```

`index.json` is self-sufficient. Each strip carries its model, scene, presentation, the parameters
held constant, and its stops in order, each with a value, a filename and a caption. A consumer
that has `index.json` never has to open a sidecar or parse a filename.

Three presentations appear in the index, and a consumer is expected to honour them:

- `strip`: show the stops in order, as a scrubber.
- `grid`: lay the stops out row-major using the strip's `grid.rows` and `grid.columns` values.
- `tile_repeat_2x2`: draw each image repeated four times in a square. The tiling strip teaches
  nothing at all if the images are shown singly.

Filenames are deterministic: the same specification and seed always produce the same paths, so
re-rendering a strip overwrites it in place and never leaves an orphan behind.

## The specification

`sweep_spec.json` holds the anchor parameters every sweep holds constant, the three models, the
three scenes, and each sweep with a one-line rationale for the models it runs on. The scenes reuse
the frontpage's lighthouse-keeper tutorial world: the `person` prompt is the txt2img tutorial's
prompt verbatim, and `place` and `thing` are the same world with the keeper removed and reduced to
one object. Every image uses seed `1234567890`, as the tutorials do.

Each model renders at its own native size (512 for the SD1.5 models, 1024 for SDXL). The two
exceptions are stated in the specification: the resolution strip is the anti-example and varies
size on purpose, and the hires-fix strip renders at 1.5x native because at native size the flag
does nothing to show.

Edit the specification to change what the library contains. Nothing about the sweeps is in the
code, apart from the row-major expansion of the grid.

## Setup

```sh
cd docs/haidra-assets/tools/param_sweeps

# The tool, its tests and its linters. No GPU stack.
uv sync --group dev
```

That is everything the `horde` runner, the specification and the index need.

### The local runner, and getting the GPU backend right first

**Install the torch build for your GPU before installing `horde-engine`.** `horde-engine` depends
on torch, and if it is installed first, the default index gives you whichever build pip would pick
rather than the one your card can use. Reversing that afterwards means uninstalling torch and its
CUDA payload, so it is worth a minute up front.

CUDA is the documented default for this machine:

```sh
# 1. torch for CUDA first. Several GB.
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# 2. then horde-engine, which will keep the torch you installed
uv sync --group dev --extra local
```

For an AMD card, install a ROCm torch build in step 1 instead, and run with `--gpu-backend rocm`.
The backend is never guessed: it comes from `--gpu-backend`, then `PARAM_SWEEPS_GPU_BACKEND`, then
CUDA. Supported values are `cuda`, `rocm`, `xpu`, `npu`, `mlu`, `mps`, `directml` and `cpu`.

Model weights come from the standard worker cache, so set `AIWORKER_CACHE_HOME` to an existing
worker's cache and nothing is downloaded twice:

```sh
export AIWORKER_CACHE_HOME=/path/to/your/worker/cache
```

### The horde runner and its key

The runner reads `AIHORDE_DEV_KEY` from the environment, and failing that from the frontpage
repository's `.env` (`../../../../.env` from this directory), which is the default. Point it
somewhere else with `--env-file` or `PARAM_SWEEPS_ENV_FILE`. The key is only ever put in a request
header: it is never printed, logged or written into any output.

## Running

```sh
# What would be downloaded, and how many images, without generating anything
uv run param-sweeps plan

# The whole library on the local GPU
uv run param-sweeps local --gpu-backend cuda

# The whole library through the horde, one job at a time
uv run param-sweeps horde

# Rebuild index.json from whatever images are already on disk
uv run param-sweeps index
```

Both runners print the fetch plan (models, approximate download size, whether each is already on
disk, image counts) and the total image count before they generate anything.

By default the library is written to `assets/param-sweeps/` at the root of this repository. Send it
elsewhere with `--output-root`.

## Resuming

Every image is checkpointed the moment it is written, in `.param-sweeps-checkpoint.json` at the
root of the output tree. Interrupt a run however you like and start it again: it renders only what
is missing. A job that fails is reported at the end and left pending, so the rest of the campaign
still runs and the next invocation retries it.

An entry only counts while its image is still on disk, so **deleting an image is all it takes to
have it regenerated**. There is no bookkeeping to edit.

`index.json` is rewritten as the run goes, and always describes only images that exist. A strip
that is partly rendered appears with `"complete": false`.

## Regenerating one strip

The filters compose, and a single strip is all three of them:

```sh
# One strip: this parameter, this model, this scene
uv run param-sweeps horde --parameter clip_skip --model anything-diffusion --scene person

# Everything for one parameter, across every model and scene it runs on
uv run param-sweeps local --parameter steps

# Re-render a strip that is already complete
uv run param-sweeps local --parameter tiling --model deliberate --scene thing --force
```

Without `--force`, images already on disk are left alone. With it, the selected images are
re-rendered and overwritten in place.

## Checks

```sh
uv run ruff check .
uv run black --check .
uv run mypy
uv run pytest
```

The tests cover the specification's shape (the rules the library is supposed to obey, such as
clip-skip running on all three models and the tiling strip only ever using the object scene), the
resume behaviour, and the index. They do not generate images.
