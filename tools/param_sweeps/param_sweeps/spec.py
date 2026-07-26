# SPDX-FileCopyrightText: 2026 Tazlin
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Parse the sweep specification and expand it into the strips and jobs a runner renders.

The specification is the single source of truth for the whole library: the anchor parameters
every sweep holds constant, the models and scenes, and each sweep's stops with the teaching
caption that belongs to the stop. Expansion is pure and deterministic, so the same
specification always produces the same strips, in the same order, with the same filenames,
whichever runner renders them.

Critical public members:

- [`SweepSpec`][param_sweeps.spec.SweepSpec]: the whole specification.
- [`RenderStrip`][param_sweeps.spec.RenderStrip]: one model/scene/parameter strip and its jobs.
- [`RenderJob`][param_sweeps.spec.RenderJob]: one fully resolved image to render.
- [`load_spec`][param_sweeps.spec.load_spec]: read and validate a specification file.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from strenum import StrEnum

# `protected_namespaces` is cleared because these models describe image-generation *models*, and
# pydantic otherwise warns about every `model_`-prefixed field name as a namespace collision.
FROZEN_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid", protected_namespaces=())

SPEC_SCHEMA_VERSION = 1
"""The specification layout this module can read."""

NON_LABEL_CHARACTERS = re.compile(r"[^a-z0-9_]+")


class SweepParameter(StrEnum):
    """The generation parameter a strip teaches."""

    STEPS = "steps"
    CFG_SCALE = "cfg_scale"
    SAMPLER = "sampler"
    CLIP_SKIP = "clip_skip"
    HIRES_FIX = "hires_fix"
    TILING = "tiling"
    STEPS_CFG_GRID = "steps_cfg_grid"
    RESOLUTION = "resolution"

    @property
    def directory_name(self) -> str:
        """Return the on-disk directory name for this parameter."""
        return str(self.value).replace("_", "-")


class StripPresentation(StrEnum):
    """How a web app should lay a strip out.

    ``TILE_REPEAT_2X2`` asks the consumer to draw each image repeated four times in a square,
    which is the only way the difference a seamless-tiling flag makes is visible at all.
    """

    STRIP = "strip"
    GRID = "grid"
    TILE_REPEAT_2X2 = "tile_repeat_2x2"


class AnchorParameters(BaseModel):
    """Represents the values every sweep holds constant unless it is the one being swept."""

    model_config = FROZEN_MODEL_CONFIG

    sampler_name: str
    cfg_scale: float
    steps: int
    karras: bool
    denoising_strength: float
    hires_fix: bool
    tiling: bool


class ModelSpec(BaseModel):
    """Represents one image model the library renders with."""

    model_config = FROZEN_MODEL_CONFIG

    slug: str
    horde_name: str
    baseline: str
    native_width: int
    native_height: int
    anchor_clip_skip: int
    approximate_download_size_gb: float
    note: str


class SceneSpec(BaseModel):
    """Represents one prompt the sweeps are rendered against."""

    model_config = FROZEN_MODEL_CONFIG

    scene_id: str
    label: str
    prompt: str
    derived_from: str


class SweepStop(BaseModel):
    """Represents one stop of a strip: the value that changes, and what it teaches.

    Every parameter field is optional and inherits the anchor (or, for ``clip_skip`` and the
    dimensions, the model) when it is unset. A stop therefore states only what it changes.
    """

    model_config = FROZEN_MODEL_CONFIG

    value: bool | int | float | str
    caption: str
    label: str | None = None
    steps: int | None = None
    cfg_scale: float | None = None
    sampler_name: str | None = None
    clip_skip: int | None = None
    hires_fix: bool | None = None
    tiling: bool | None = None
    width: int | None = None
    height: int | None = None

    @property
    def filename_label(self) -> str:
        """Return the filename-safe token identifying this stop."""
        if self.label is not None:
            return self.label
        return value_label(self.value)


class SweepBase(BaseModel):
    """Represents the fields shared by every kind of sweep."""

    model_config = FROZEN_MODEL_CONFIG

    parameter: SweepParameter
    rationale: str
    caption: str
    model_slugs: list[str]
    scene_ids: list[str]


class StripSweep(SweepBase):
    """Represents a one-dimensional sweep: a list of stops along a single parameter."""

    kind: Literal["strip"] = "strip"
    presentation: StripPresentation = StripPresentation.STRIP
    resolution_multiplier: float = 1.0
    stops: list[SweepStop]


class GridSweep(SweepBase):
    """Represents the two-dimensional steps-by-guidance sweep.

    The cells are generated rather than written out, so the axes cannot drift apart from the
    stops they describe. Rows are steps, columns are guidance, in the order declared here.
    """

    kind: Literal["grid"]
    steps_values: list[int]
    cfg_values: list[float]
    row_caption: str
    column_caption: str


Sweep = Annotated[StripSweep | GridSweep, Field(discriminator="kind")]


class GenerationParameters(BaseModel):
    """Represents the resolved generation parameters of a single image.

    This is the shape that reaches disk, in both the sidecars and the index, and the shape both
    runners translate from into their backend's own payload.
    """

    model_config = FROZEN_MODEL_CONFIG

    width: int
    height: int
    steps: int
    cfg_scale: float
    sampler_name: str
    clip_skip: int
    hires_fix: bool
    tiling: bool
    karras: bool
    denoising_strength: float
    seed: int

    def differing_field_names(self, other: GenerationParameters) -> set[str]:
        """Return the names of the fields whose values differ between these two."""
        return {
            field_name
            for field_name in type(self).model_fields
            if getattr(self, field_name) != getattr(other, field_name)
        }


class RenderJob(BaseModel):
    """Represents one fully resolved image: every parameter a runner needs, and where it lands."""

    model_config = FROZEN_MODEL_CONFIG

    parameter: SweepParameter
    model_slug: str
    horde_model_name: str
    scene_id: str
    prompt: str
    stop_index: int
    stop_label: str
    stop_value: bool | int | float | str
    caption: str
    width: int
    height: int
    steps: int
    cfg_scale: float
    sampler_name: str
    clip_skip: int
    hires_fix: bool
    tiling: bool
    karras: bool
    denoising_strength: float
    seed: int

    @property
    def relative_directory(self) -> str:
        """Return the strip's directory, relative to the output root, with forward slashes."""
        return f"{self.parameter.directory_name}/{self.model_slug}/{self.scene_id}"

    @property
    def relative_image_path(self) -> str:
        """Return the image's path relative to the output root, with forward slashes."""
        return f"{self.relative_directory}/{self.stop_index:03d}_{self.stop_label}.webp"

    @property
    def relative_sidecar_path(self) -> str:
        """Return the sidecar's path relative to the output root, with forward slashes."""
        return f"{self.relative_directory}/{self.stop_index:03d}_{self.stop_label}.json"

    def generation_parameters(self) -> GenerationParameters:
        """Return the resolved generation parameters for this job."""
        return GenerationParameters(
            width=self.width,
            height=self.height,
            steps=self.steps,
            cfg_scale=self.cfg_scale,
            sampler_name=self.sampler_name,
            clip_skip=self.clip_skip,
            hires_fix=self.hires_fix,
            tiling=self.tiling,
            karras=self.karras,
            denoising_strength=self.denoising_strength,
            seed=self.seed,
        )


class RenderStrip(BaseModel):
    """Represents one strip: a parameter swept over one model and one scene, with its jobs."""

    model_config = FROZEN_MODEL_CONFIG

    parameter: SweepParameter
    presentation: StripPresentation
    rationale: str
    caption: str
    image_model: ModelSpec
    scene: SceneSpec
    jobs: list[RenderJob]
    grid_steps_values: list[int] = Field(default_factory=list)
    grid_cfg_values: list[float] = Field(default_factory=list)
    row_caption: str | None = None
    column_caption: str | None = None

    @property
    def strip_id(self) -> str:
        """Return the stable identifier a consumer can key this strip by."""
        return f"{self.parameter.directory_name}/{self.image_model.slug}/{self.scene.scene_id}"


class SweepSpec(BaseModel):
    """Represents the whole checked-in sweep specification."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[1]
    seed: int
    anchor: AnchorParameters
    models: list[ModelSpec]
    scenes: list[SceneSpec]
    sweeps: list[Sweep]

    @model_validator(mode="after")
    def _check_references_resolve(self) -> SweepSpec:
        """Validate that identifiers are unique and every sweep reference names something."""
        known_model_slugs = {image_model.slug for image_model in self.models}
        if len(known_model_slugs) != len(self.models):
            raise ValueError("model slugs must be unique")

        known_scene_ids = {scene.scene_id for scene in self.scenes}
        if len(known_scene_ids) != len(self.scenes):
            raise ValueError("scene ids must be unique")

        for sweep in self.sweeps:
            unknown_models = set(sweep.model_slugs) - known_model_slugs
            if unknown_models:
                raise ValueError(f"sweep {sweep.parameter} names unknown models: {sorted(unknown_models)}")

            unknown_scenes = set(sweep.scene_ids) - known_scene_ids
            if unknown_scenes:
                raise ValueError(f"sweep {sweep.parameter} names unknown scenes: {sorted(unknown_scenes)}")

        return self

    def model_for_slug(self, slug: str) -> ModelSpec:
        """Return the model with this slug.

        Raises:
            KeyError: If no model in the specification carries the slug.
        """
        for image_model in self.models:
            if image_model.slug == slug:
                return image_model
        raise KeyError(f"no model with slug {slug!r}")

    def scene_for_id(self, scene_id: str) -> SceneSpec:
        """Return the scene with this identifier.

        Raises:
            KeyError: If no scene in the specification carries the identifier.
        """
        for scene in self.scenes:
            if scene.scene_id == scene_id:
                return scene
        raise KeyError(f"no scene with id {scene_id!r}")

    def expand_strips(self) -> list[RenderStrip]:
        """Return every strip the specification describes, in declaration order."""
        strips: list[RenderStrip] = []
        for sweep in self.sweeps:
            for model_slug in sweep.model_slugs:
                for scene_id in sweep.scene_ids:
                    strips.append(self._expand_one_strip(sweep, model_slug, scene_id))
        return strips

    def expand_jobs(self) -> list[RenderJob]:
        """Return every render job the specification describes, in strip order."""
        return [job for strip in self.expand_strips() for job in strip.jobs]

    def _expand_one_strip(self, sweep: StripSweep | GridSweep, model_slug: str, scene_id: str) -> RenderStrip:
        image_model = self.model_for_slug(model_slug)
        scene = self.scene_for_id(scene_id)

        if isinstance(sweep, GridSweep):
            stops = _grid_stops(sweep)
            presentation = StripPresentation.GRID
            resolution_multiplier = 1.0
        else:
            stops = sweep.stops
            presentation = sweep.presentation
            resolution_multiplier = sweep.resolution_multiplier

        jobs = [
            self._build_job(
                sweep=sweep,
                image_model=image_model,
                scene=scene,
                stop=stop,
                stop_index=stop_index,
                resolution_multiplier=resolution_multiplier,
            )
            for stop_index, stop in enumerate(stops, start=1)
        ]

        return RenderStrip(
            parameter=sweep.parameter,
            presentation=presentation,
            rationale=sweep.rationale,
            caption=sweep.caption,
            image_model=image_model,
            scene=scene,
            jobs=jobs,
            grid_steps_values=sweep.steps_values if isinstance(sweep, GridSweep) else [],
            grid_cfg_values=sweep.cfg_values if isinstance(sweep, GridSweep) else [],
            row_caption=sweep.row_caption if isinstance(sweep, GridSweep) else None,
            column_caption=sweep.column_caption if isinstance(sweep, GridSweep) else None,
        )

    def _build_job(
        self,
        *,
        sweep: StripSweep | GridSweep,
        image_model: ModelSpec,
        scene: SceneSpec,
        stop: SweepStop,
        stop_index: int,
        resolution_multiplier: float,
    ) -> RenderJob:
        width = stop.width if stop.width is not None else _scaled(image_model.native_width, resolution_multiplier)
        height = stop.height if stop.height is not None else _scaled(image_model.native_height, resolution_multiplier)

        return RenderJob(
            parameter=sweep.parameter,
            model_slug=image_model.slug,
            horde_model_name=image_model.horde_name,
            scene_id=scene.scene_id,
            prompt=scene.prompt,
            stop_index=stop_index,
            stop_label=stop.filename_label,
            stop_value=stop.value,
            caption=stop.caption,
            width=width,
            height=height,
            steps=stop.steps if stop.steps is not None else self.anchor.steps,
            cfg_scale=stop.cfg_scale if stop.cfg_scale is not None else self.anchor.cfg_scale,
            sampler_name=stop.sampler_name if stop.sampler_name is not None else self.anchor.sampler_name,
            clip_skip=stop.clip_skip if stop.clip_skip is not None else image_model.anchor_clip_skip,
            hires_fix=stop.hires_fix if stop.hires_fix is not None else self.anchor.hires_fix,
            tiling=stop.tiling if stop.tiling is not None else self.anchor.tiling,
            karras=self.anchor.karras,
            denoising_strength=self.anchor.denoising_strength,
            seed=self.seed,
        )


def value_label(value: bool | int | float | str) -> str:
    """Return a filename-safe token for a stop value.

    Booleans become ``on``/``off`` because ``true``/``false`` reads poorly in a filename, and a
    decimal point is replaced rather than kept so that the only dot in a filename is its
    extension separator.
    """
    if isinstance(value, bool):
        return "on" if value else "off"

    text = str(value).lower().replace(".", "_")
    return NON_LABEL_CHARACTERS.sub("-", text).strip("-_") or "value"


def _scaled(dimension: int, multiplier: float) -> int:
    """Return the dimension scaled and snapped down to a multiple of 64."""
    scaled = int(dimension * multiplier)
    return max(64, scaled - (scaled % 64))


def _grid_stops(sweep: GridSweep) -> list[SweepStop]:
    """Return the grid's cells in row-major order: steps outer, guidance inner."""
    stops: list[SweepStop] = []
    for steps_value in sweep.steps_values:
        for cfg_value in sweep.cfg_values:
            stops.append(
                SweepStop(
                    value=f"{steps_value}x{cfg_value:g}",
                    label=f"s{steps_value:02d}_c{value_label(cfg_value)}",
                    caption=f"{steps_value} steps at guidance {cfg_value:g}.",
                    steps=steps_value,
                    cfg_scale=cfg_value,
                ),
            )
    return stops


def load_spec(spec_path: Path) -> SweepSpec:
    """Read and validate the specification at this path.

    Args:
        spec_path: The specification file to read.

    Returns:
        The validated specification.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If the file is not valid JSON, or does not validate as a specification.
    """
    raw_text = spec_path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as decode_error:
        raise ValueError(f"{spec_path} is not valid JSON: {decode_error}") from decode_error

    return SweepSpec.model_validate(parsed)
