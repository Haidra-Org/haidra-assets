# SPDX-FileCopyrightText: 2026 Tazlin
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Write the rendered images, their sidecars, and the index a web app renders strips from.

Every image is written as a quality-tuned WebP with a JSON sidecar beside it recording the
exact parameters, model, seed, runner and timestamps that produced it. The index collects the
whole library into one file: a consumer that has ``index.json`` needs nothing else to draw a
scrubber strip, because each stop carries its value, caption, filename and resolved parameters.

Both on-disk shapes are declared as models rather than assembled as mappings, so the contract
this tool offers its consumers is stated in one place and checked when it is written.

Critical public members:

- [`ImageSidecar`][param_sweeps.outputs.ImageSidecar]: the per-image record.
- [`SweepIndex`][param_sweeps.outputs.SweepIndex]: the whole library's index.
- [`save_render`][param_sweeps.outputs.save_render]: write one image and its sidecar.
- [`build_index`][param_sweeps.outputs.build_index]: build the index from the specification and
  the files actually present on disk.
- [`write_index`][param_sweeps.outputs.write_index]: write that index deterministically.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field

from param_sweeps.spec import (
    GenerationParameters,
    RenderJob,
    RenderStrip,
    StripPresentation,
    SweepParameter,
    SweepSpec,
)

INDEX_FILENAME = "index.json"
"""The name of the top-level index, at the root of the output tree."""

INDEX_SCHEMA_VERSION = 1
"""The index layout consumers can expect."""

FROZEN_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid", protected_namespaces=())


class WebpEncoding:
    """The WebP encoder settings used for every image in the library.

    Quality 92 with the slowest encoder method keeps sampler noise and fine texture intact,
    which matters because several strips teach differences that live entirely in that texture.
    Lossless would roughly triple the size of the library for no visible gain at these sizes.
    """

    QUALITY = 92
    METHOD = 6


class ImageSidecar(BaseModel):
    """Represents the JSON record written beside every rendered image."""

    model_config = FROZEN_MODEL_CONFIG

    parameter: SweepParameter
    model_slug: str
    model_requested: str
    model_generated_with: str
    scene: str
    prompt: str
    stop_index: int
    stop_value: bool | int | float | str
    caption: str
    params: GenerationParameters
    runner: str
    started_at: str
    finished_at: str
    image: str
    note: str | None = None


class IndexModel(BaseModel):
    """Represents the model a strip was rendered with, as the index reports it."""

    model_config = FROZEN_MODEL_CONFIG

    slug: str
    name: str
    baseline: str
    note: str


class IndexScene(BaseModel):
    """Represents the scene a strip was rendered from, as the index reports it."""

    model_config = FROZEN_MODEL_CONFIG

    scene_id: str
    label: str
    prompt: str


class IndexStop(BaseModel):
    """Represents one stop of a strip, with everything needed to render and caption it."""

    model_config = FROZEN_MODEL_CONFIG

    value: bool | int | float | str
    label: str
    caption: str
    file: str
    sidecar: str
    params: GenerationParameters


class IndexGridAxis(BaseModel):
    """Represents one axis of a two-dimensional strip."""

    model_config = FROZEN_MODEL_CONFIG

    parameter: SweepParameter
    values: list[int | float]
    caption: str


class IndexGrid(BaseModel):
    """Represents the layout of a two-dimensional strip, in the order its stops are listed."""

    model_config = FROZEN_MODEL_CONFIG

    rows: IndexGridAxis
    columns: IndexGridAxis


class IndexStrip(BaseModel):
    """Represents one strip: a parameter swept over one model and one scene.

    ``held`` is the full parameter set of the strip's first stop and ``varying`` names the
    fields that change across it, which is how a consumer can label "everything else held at"
    without comparing stops itself.
    """

    model_config = FROZEN_MODEL_CONFIG

    strip_id: str
    parameter: SweepParameter
    presentation: StripPresentation
    caption: str
    rationale: str
    complete: bool
    image_model: IndexModel
    scene: IndexScene
    held: GenerationParameters
    varying: list[str]
    stops: list[IndexStop]
    grid: IndexGrid | None = None


class SweepIndex(BaseModel):
    """Represents the whole library: every strip a consumer can render."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: int = INDEX_SCHEMA_VERSION
    seed: int
    strips: list[IndexStrip] = Field(default_factory=list)


def save_render(
    *,
    image: Image.Image,
    job: RenderJob,
    output_root: Path,
    runner_name: str,
    started_at: datetime,
    finished_at: datetime,
    model_name_used: str | None = None,
    worker_note: str | None = None,
) -> Path:
    """Write one rendered image as WebP with its JSON sidecar, and return the image path.

    Args:
        image: The rendered image.
        job: The [`RenderJob`][param_sweeps.spec.RenderJob] that produced it.
        output_root: The root of the output tree.
        runner_name: Which runner rendered it, recorded in the sidecar.
        started_at: When the render started.
        finished_at: When the render finished.
        model_name_used: The model name the runner actually generated with, when it can report
            one (the API can hand a job to a worker running a different model than requested).
        worker_note: Any runner-specific note worth keeping, such as a fault the backend reported.

    Returns:
        The path the image was written to.

    Side Effects:
        Creates the strip's directory if it does not exist, and overwrites any existing image
        and sidecar at the job's deterministic paths.
    """
    image_path = output_root / job.relative_image_path
    sidecar_path = output_root / job.relative_sidecar_path
    image_path.parent.mkdir(parents=True, exist_ok=True)

    image.save(image_path, format="WEBP", quality=WebpEncoding.QUALITY, method=WebpEncoding.METHOD)

    sidecar = ImageSidecar(
        parameter=job.parameter,
        model_slug=job.model_slug,
        model_requested=job.horde_model_name,
        model_generated_with=model_name_used if model_name_used is not None else job.horde_model_name,
        scene=job.scene_id,
        prompt=job.prompt,
        stop_index=job.stop_index,
        stop_value=job.stop_value,
        caption=job.caption,
        params=job.generation_parameters(),
        runner=runner_name,
        started_at=started_at.isoformat(),
        finished_at=finished_at.isoformat(),
        image=image_path.name,
        note=worker_note,
    )
    sidecar_path.write_text(sidecar.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return image_path


def build_index(*, spec: SweepSpec, output_root: Path) -> SweepIndex:
    """Build the index describing every strip whose images are present on disk.

    A stop with no image on disk is left out and its strip is marked incomplete, so a partially
    rendered campaign still produces an index a consumer can use without hitting missing files.

    Args:
        spec: The specification the library was rendered from.
        output_root: The root of the output tree.

    Returns:
        The index.
    """
    index_strips: list[IndexStrip] = []

    for strip in spec.expand_strips():
        stops: list[IndexStop] = []
        missing_count = 0

        for job in strip.jobs:
            if not (output_root / job.relative_image_path).is_file():
                missing_count += 1
                continue

            stops.append(
                IndexStop(
                    value=job.stop_value,
                    label=job.stop_label,
                    caption=job.caption,
                    file=job.relative_image_path,
                    sidecar=job.relative_sidecar_path,
                    params=job.generation_parameters(),
                ),
            )

        if not stops:
            continue

        index_strips.append(
            IndexStrip(
                strip_id=strip.strip_id,
                parameter=strip.parameter,
                presentation=strip.presentation,
                caption=strip.caption,
                rationale=strip.rationale,
                complete=missing_count == 0,
                image_model=IndexModel(
                    slug=strip.image_model.slug,
                    name=strip.image_model.horde_name,
                    baseline=strip.image_model.baseline,
                    note=strip.image_model.note,
                ),
                scene=IndexScene(
                    scene_id=strip.scene.scene_id,
                    label=strip.scene.label,
                    prompt=strip.scene.prompt,
                ),
                held=strip.jobs[0].generation_parameters(),
                varying=_varying_field_names(strip),
                stops=stops,
                grid=_index_grid(strip),
            ),
        )

    return SweepIndex(seed=spec.seed, strips=index_strips)


def write_index(*, spec: SweepSpec, output_root: Path) -> Path:
    """Write the index to the root of the output tree, and return its path.

    Side Effects:
        Overwrites any existing index. The content depends only on the specification and the
        files present, so rewriting it never introduces a spurious change.
    """
    index_path = output_root / INDEX_FILENAME
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index = build_index(spec=spec, output_root=output_root)
    index_path.write_text(index.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return index_path


def _varying_field_names(strip: RenderStrip) -> list[str]:
    """Return the parameter fields that change across the strip, in declaration order."""
    if not strip.jobs:
        return []

    first_parameters = strip.jobs[0].generation_parameters()
    varying: set[str] = set()
    for job in strip.jobs[1:]:
        varying |= first_parameters.differing_field_names(job.generation_parameters())

    return [field_name for field_name in GenerationParameters.model_fields if field_name in varying]


def _index_grid(strip: RenderStrip) -> IndexGrid | None:
    """Return the strip's grid layout, or None when it is one-dimensional."""
    if not strip.grid_steps_values:
        return None

    return IndexGrid(
        rows=IndexGridAxis(
            parameter=SweepParameter.STEPS,
            values=list(strip.grid_steps_values),
            caption=strip.row_caption if strip.row_caption is not None else "",
        ),
        columns=IndexGridAxis(
            parameter=SweepParameter.CFG_SCALE,
            values=list(strip.grid_cfg_values),
            caption=strip.column_caption if strip.column_caption is not None else "",
        ),
    )
