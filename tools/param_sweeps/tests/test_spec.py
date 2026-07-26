# SPDX-FileCopyrightText: 2026 Tazlin
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check that the checked-in specification expands the way its consumers assume it does."""

from __future__ import annotations

from pathlib import Path

import pytest

from param_sweeps.spec import RenderJob, StripPresentation, SweepParameter, SweepSpec, load_spec, value_label

SPEC_PATH = Path(__file__).resolve().parents[1] / "sweep_spec.json"


@pytest.fixture(scope="module")
def spec() -> SweepSpec:
    return load_spec(SPEC_PATH)


def test_spec_loads_and_declares_the_expected_models(spec: SweepSpec) -> None:
    assert {image_model.slug for image_model in spec.models} == {
        "deliberate",
        "albedobase-xl",
        "anything-diffusion",
    }
    assert spec.seed == 1234567890


def test_every_sweep_states_a_rationale(spec: SweepSpec) -> None:
    for sweep in spec.sweeps:
        assert sweep.rationale.strip(), f"{sweep.parameter} has no rationale"


def test_clip_skip_runs_on_all_three_models(spec: SweepSpec) -> None:
    clip_skip_strips = [strip for strip in spec.expand_strips() if strip.parameter is SweepParameter.CLIP_SKIP]
    assert {strip.image_model.slug for strip in clip_skip_strips} == {
        "deliberate",
        "albedobase-xl",
        "anything-diffusion",
    }


def test_the_anime_model_anchors_at_clip_skip_two(spec: SweepSpec) -> None:
    anime_model = spec.model_for_slug("anything-diffusion")
    assert anime_model.anchor_clip_skip == 2

    steps_grid_jobs = [
        job
        for job in spec.expand_jobs()
        if job.model_slug == "anything-diffusion" and job.parameter is SweepParameter.STEPS_CFG_GRID
    ]
    assert steps_grid_jobs
    assert all(job.clip_skip == 2 for job in steps_grid_jobs)


def test_tiling_and_hires_run_on_the_thing_scene_only(spec: SweepSpec) -> None:
    for parameter in (SweepParameter.TILING, SweepParameter.HIRES_FIX):
        scenes = {job.scene_id for job in spec.expand_jobs() if job.parameter is parameter}
        assert scenes == {"thing"}, f"{parameter} should only run on the object scene"


def test_tiling_is_presented_as_a_repeat(spec: SweepSpec) -> None:
    tiling_strips = [strip for strip in spec.expand_strips() if strip.parameter is SweepParameter.TILING]
    assert tiling_strips
    assert all(strip.presentation is StripPresentation.TILE_REPEAT_2X2 for strip in tiling_strips)


def test_hires_strip_renders_above_native_size(spec: SweepSpec) -> None:
    hires_jobs = [job for job in spec.expand_jobs() if job.parameter is SweepParameter.HIRES_FIX]
    assert hires_jobs
    for job in hires_jobs:
        native_width = spec.model_for_slug(job.model_slug).native_width
        assert job.width > native_width, "hires-fix does nothing at or below native size"
        assert job.width % 64 == 0


def test_the_grid_is_six_by_six_per_baseline(spec: SweepSpec) -> None:
    grid_strips = [strip for strip in spec.expand_strips() if strip.parameter is SweepParameter.STEPS_CFG_GRID]
    assert len(grid_strips) == 3
    for strip in grid_strips:
        assert len(strip.jobs) == 36
        assert strip.grid_steps_values == [4, 8, 12, 20, 30, 50]


def test_resolution_strip_is_sdxl_only_and_ends_at_native(spec: SweepSpec) -> None:
    resolution_jobs = [job for job in spec.expand_jobs() if job.parameter is SweepParameter.RESOLUTION]
    assert {job.model_slug for job in resolution_jobs} == {"albedobase-xl"}
    assert [job.width for job in resolution_jobs] == [128, 256, 512, 1024]


def test_every_job_holds_the_anchor_seed(spec: SweepSpec) -> None:
    assert all(job.seed == spec.seed for job in spec.expand_jobs())


def test_scenes_share_the_lighthouse_prompt_family(spec: SweepSpec) -> None:
    assert {scene.scene_id for scene in spec.scenes} == {"person", "place", "thing"}
    for scene in spec.scenes:
        assert "lighthouse" in scene.prompt or "cliffside" in scene.prompt


def test_filenames_are_unique_and_deterministic(spec: SweepSpec) -> None:
    first_expansion = spec.expand_jobs()
    second_expansion = load_spec(SPEC_PATH).expand_jobs()

    first_paths = [job.relative_image_path for job in first_expansion]
    assert first_paths == [job.relative_image_path for job in second_expansion]
    assert len(set(first_paths)) == len(first_paths)


def test_stop_indexes_restart_within_each_strip(spec: SweepSpec) -> None:
    for strip in spec.expand_strips():
        assert [job.stop_index for job in strip.jobs] == list(range(1, len(strip.jobs) + 1))


def test_paths_follow_the_documented_layout(spec: SweepSpec) -> None:
    job: RenderJob = next(job for job in spec.expand_jobs() if job.parameter is SweepParameter.CLIP_SKIP)
    assert job.relative_image_path.startswith("clip-skip/")
    assert job.relative_image_path.endswith(".webp")
    assert job.relative_sidecar_path.endswith(".json")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (4, "4"),
        (7.5, "7_5"),
        (True, "on"),
        (False, "off"),
        ("k_euler_a", "k_euler_a"),
        ("128x128", "128x128"),
        ("AlbedoBase XL (SDXL)", "albedobase-xl-sdxl"),
    ],
)
def test_value_label(value: bool | int | float | str, expected: str) -> None:
    assert value_label(value) == expected
