# SPDX-FileCopyrightText: 2026 Tazlin
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the parts a campaign depends on: resumption, output layout, and the index."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import override

import pytest
from PIL import Image

from param_sweeps.campaign import JobFilter, run_campaign
from param_sweeps.horde_runner import API_KEY_VARIABLE, MissingApiKeyError, read_api_key
from param_sweeps.local_runner import GpuBackend, HordelibPayload, resolve_gpu_backend
from param_sweeps.outputs import INDEX_FILENAME, SweepIndex, build_index
from param_sweeps.runner import FetchPlanEntry, RenderOutcome, SweepRunner
from param_sweeps.spec import ModelSpec, RenderJob, SweepParameter, SweepSpec, load_spec

SPEC_PATH = Path(__file__).resolve().parents[1] / "sweep_spec.json"

ONE_STRIP = JobFilter(parameters=("clip_skip",), model_slugs=("anything-diffusion",), scene_ids=("person",))


class CountingRunner(SweepRunner):
    """A runner that produces a solid colour, so the driver can be tested without a GPU."""

    def __init__(self, *, fail_on: str | None = None) -> None:
        """Create a runner that renders every job, except one that is asked to fail."""
        self.rendered_paths: list[str] = []
        self.prepare_count = 0
        self._fail_on = fail_on

    @property
    @override
    def name(self) -> str:
        return "test-runner"

    @override
    def fetch_plan(self, jobs: Sequence[RenderJob], models: Sequence[ModelSpec]) -> list[FetchPlanEntry]:
        return [
            FetchPlanEntry(
                model_name=image_model.horde_name,
                approximate_size_gb=image_model.approximate_download_size_gb,
                already_present=False,
                image_count=len(jobs),
            )
            for image_model in models
        ]

    @override
    def prepare(self, jobs: Sequence[RenderJob], models: Sequence[ModelSpec]) -> None:
        self.prepare_count += 1

    @override
    def render(self, job: RenderJob) -> RenderOutcome:
        if self._fail_on is not None and job.relative_image_path == self._fail_on:
            raise RuntimeError("deliberate failure")

        self.rendered_paths.append(job.relative_image_path)
        return RenderOutcome(image=Image.new("RGB", (16, 16), color=(20, 40, 60)))


@pytest.fixture(scope="module")
def spec() -> SweepSpec:
    return load_spec(SPEC_PATH)


def test_campaign_writes_images_sidecars_and_index(spec: SweepSpec, tmp_path: Path) -> None:
    runner = CountingRunner()
    result = run_campaign(spec=spec, runner=runner, output_root=tmp_path, job_filter=ONE_STRIP)

    assert result.rendered_count == 3
    assert result.failed_jobs == ()

    image_path = tmp_path / "clip-skip/anything-diffusion/person/002_2.webp"
    sidecar_path = tmp_path / "clip-skip/anything-diffusion/person/002_2.json"
    assert image_path.is_file()

    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    assert sidecar["params"]["clip_skip"] == 2
    assert sidecar["params"]["seed"] == spec.seed
    assert sidecar["runner"] == "test-runner"
    assert sidecar["model_requested"] == "Anything Diffusion"

    index = SweepIndex.model_validate_json((tmp_path / INDEX_FILENAME).read_text(encoding="utf-8"))
    assert len(index.strips) == 1
    strip = index.strips[0]
    assert strip.complete is True
    assert [stop.value for stop in strip.stops] == [1, 2, 3]
    assert strip.varying == ["clip_skip"]
    assert all(stop.caption for stop in strip.stops)


def test_a_second_run_renders_nothing_new(spec: SweepSpec, tmp_path: Path) -> None:
    first_result = run_campaign(spec=spec, runner=CountingRunner(), output_root=tmp_path, job_filter=ONE_STRIP)

    resumed_runner = CountingRunner()
    second_result = run_campaign(spec=spec, runner=resumed_runner, output_root=tmp_path, job_filter=ONE_STRIP)

    assert first_result.rendered_count == 3
    assert second_result.rendered_count == 0
    assert second_result.skipped_count == 3
    assert resumed_runner.rendered_paths == []


def test_an_interrupted_run_resumes_at_the_failed_image(spec: SweepSpec, tmp_path: Path) -> None:
    failing_path = "clip-skip/anything-diffusion/person/002_2.webp"
    first_result = run_campaign(
        spec=spec,
        runner=CountingRunner(fail_on=failing_path),
        output_root=tmp_path,
        job_filter=ONE_STRIP,
    )
    assert first_result.rendered_count == 2
    assert first_result.failed_jobs == (failing_path,)

    partial_index = SweepIndex.model_validate_json((tmp_path / INDEX_FILENAME).read_text(encoding="utf-8"))
    assert partial_index.strips[0].complete is False

    resumed_runner = CountingRunner()
    second_result = run_campaign(spec=spec, runner=resumed_runner, output_root=tmp_path, job_filter=ONE_STRIP)

    assert resumed_runner.rendered_paths == [failing_path]
    assert second_result.rendered_count == 1
    assert second_result.skipped_count == 2

    completed_index = SweepIndex.model_validate_json((tmp_path / INDEX_FILENAME).read_text(encoding="utf-8"))
    assert completed_index.strips[0].complete is True


def test_deleting_an_image_makes_the_next_run_regenerate_it(spec: SweepSpec, tmp_path: Path) -> None:
    run_campaign(spec=spec, runner=CountingRunner(), output_root=tmp_path, job_filter=ONE_STRIP)
    (tmp_path / "clip-skip/anything-diffusion/person/001_1.webp").unlink()

    resumed_runner = CountingRunner()
    run_campaign(spec=spec, runner=resumed_runner, output_root=tmp_path, job_filter=ONE_STRIP)

    assert resumed_runner.rendered_paths == ["clip-skip/anything-diffusion/person/001_1.webp"]


def test_plan_only_generates_nothing(spec: SweepSpec, tmp_path: Path) -> None:
    runner = CountingRunner()
    result = run_campaign(spec=spec, runner=runner, output_root=tmp_path, job_filter=ONE_STRIP, plan_only=True)

    assert result.rendered_count == 0
    assert runner.prepare_count == 0
    assert runner.rendered_paths == []


def test_an_empty_filter_selection_is_rejected(spec: SweepSpec, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="selected no jobs"):
        run_campaign(
            spec=spec,
            runner=CountingRunner(),
            output_root=tmp_path,
            job_filter=JobFilter(model_slugs=("no-such-model",)),
        )


def test_index_omits_strips_with_no_images(spec: SweepSpec, tmp_path: Path) -> None:
    empty_index = build_index(spec=spec, output_root=tmp_path)
    assert empty_index.strips == []


def test_hordelib_payload_renames_the_fields_hordelib_renames(spec: SweepSpec) -> None:
    job = next(job for job in spec.expand_jobs() if job.parameter is SweepParameter.STEPS)
    payload = HordelibPayload.from_job(job).as_hordelib_mapping()

    assert payload["ddim_steps"] == job.steps
    assert payload["n_iter"] == 1
    assert payload["model"] == job.horde_model_name
    assert payload["seed"] == job.seed
    assert "steps" not in payload


def test_gpu_backend_defaults_to_cuda_and_rejects_nonsense(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PARAM_SWEEPS_GPU_BACKEND", raising=False)
    assert resolve_gpu_backend(requested=None) is GpuBackend.CUDA
    assert resolve_gpu_backend(requested="rocm") is GpuBackend.ROCM

    monkeypatch.setenv("PARAM_SWEEPS_GPU_BACKEND", "xpu")
    assert resolve_gpu_backend(requested=None) is GpuBackend.XPU
    assert resolve_gpu_backend(requested="cpu") is GpuBackend.CPU

    with pytest.raises(ValueError, match="unsupported GPU backend"):
        resolve_gpu_backend(requested="quantum")


def test_api_key_is_read_from_an_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(API_KEY_VARIABLE, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(f'# a comment\n{API_KEY_VARIABLE}="secret-value"\n', encoding="utf-8")

    assert read_api_key(env_file=env_file) == "secret-value"


def test_a_missing_api_key_names_only_the_location(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(API_KEY_VARIABLE, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("SOMETHING_ELSE=1\n", encoding="utf-8")

    with pytest.raises(MissingApiKeyError) as raised:
        read_api_key(env_file=env_file)

    assert str(env_file) in str(raised.value)
