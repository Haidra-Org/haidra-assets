# SPDX-FileCopyrightText: 2026 Tazlin
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render sweep jobs on this machine's GPU through horde-engine (``hordelib``).

This is the primary runner: it is the same inference stack an AI Horde worker runs, so what it
produces is what the horde produces. The GPU backend is always stated rather than guessed, and
model weights come from the standard ``AIWORKER_CACHE_HOME`` location, so an existing worker
cache is reused instead of re-downloaded.

``hordelib`` is imported inside the methods that need it. Importing it starts a ComfyUI
environment check and pulls in torch, which must not happen merely because something wanted to
read the specification or rebuild the index.

Critical public members:

- [`LocalRunner`][param_sweeps.local_runner.LocalRunner]: the runner itself.
- [`GpuBackend`][param_sweeps.local_runner.GpuBackend]: the compute backends that can be selected.
- [`resolve_gpu_backend`][param_sweeps.local_runner.resolve_gpu_backend]: the flag/environment
  resolution, with CUDA as the documented default for this machine.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, override

from pydantic import BaseModel, ConfigDict
from strenum import StrEnum

from param_sweeps.runner import FetchPlanEntry, RenderOutcome, SweepRunner
from param_sweeps.spec import ModelSpec, RenderJob

if TYPE_CHECKING:
    from PIL import Image

logger = logging.getLogger(__name__)

GPU_BACKEND_ENVIRONMENT_VARIABLE = "PARAM_SWEEPS_GPU_BACKEND"
"""Environment variable naming the compute backend, when the flag is not given."""

COMPVIS_MODEL_MANAGER = "compvis"
"""The only model manager these sweeps need: plain checkpoint image models."""


class GpuBackend(StrEnum):
    """The compute backends a local run can be pointed at.

    These mirror ``hordelib.utils.torch_memory.AcceleratorKind``. They are restated here so that
    the command line can be parsed, and an unsupported choice rejected, without importing torch.
    """

    CUDA = "cuda"
    ROCM = "rocm"
    XPU = "xpu"
    NPU = "npu"
    MLU = "mlu"
    MPS = "mps"
    DIRECTML = "directml"
    CPU = "cpu"


DEFAULT_GPU_BACKEND = GpuBackend.CUDA
"""CUDA is the documented default; every other backend has to be asked for."""


class HordelibPayload(BaseModel):
    """Represents one job in the payload shape ``hordelib`` accepts.

    ``hordelib`` takes a plain Horde-style payload mapping, so this model exists to build that
    mapping in one checked place rather than assembling a dictionary at the call site. Note the
    field names that differ from the horde API's: steps is ``ddim_steps`` and the batch size is
    ``n_iter``.
    """

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    prompt: str
    model: str
    sampler_name: str
    cfg_scale: float
    ddim_steps: int
    denoising_strength: float
    seed: int
    width: int
    height: int
    karras: bool
    tiling: bool
    hires_fix: bool
    clip_skip: int
    n_iter: int = 1
    control_type: str | None = None
    image_is_control: bool = False
    return_control_map: bool = False

    @classmethod
    def from_job(cls, job: RenderJob) -> HordelibPayload:
        """Create a payload from a render job."""
        return cls(
            prompt=job.prompt,
            model=job.horde_model_name,
            sampler_name=job.sampler_name,
            cfg_scale=job.cfg_scale,
            ddim_steps=job.steps,
            denoising_strength=job.denoising_strength,
            seed=job.seed,
            width=job.width,
            height=job.height,
            karras=job.karras,
            tiling=job.tiling,
            hires_fix=job.hires_fix,
            clip_skip=job.clip_skip,
        )

    def as_hordelib_mapping(self) -> dict[str, Any]:
        """Return the payload in the mapping form ``hordelib`` expects."""
        return self.model_dump()


def resolve_gpu_backend(*, requested: str | None) -> GpuBackend:
    """Return the compute backend to run on, from the flag, then the environment, then the default.

    Args:
        requested: The value given on the command line, or None.

    Returns:
        The selected backend.

    Raises:
        ValueError: If a backend was named that this tool does not support.
    """
    candidate = requested if requested is not None else os.environ.get(GPU_BACKEND_ENVIRONMENT_VARIABLE)
    if candidate is None or not candidate.strip():
        return DEFAULT_GPU_BACKEND

    try:
        return GpuBackend(candidate.strip().lower())
    except ValueError as lookup_error:
        supported = ", ".join(str(backend) for backend in GpuBackend)
        raise ValueError(f"unsupported GPU backend {candidate!r}; supported backends: {supported}") from lookup_error


class LocalRunner(SweepRunner):
    """Renders sweep jobs through horde-engine on a local accelerator.

    The backend and device are applied by ``hordelib.initialise`` before torch is imported, which
    is the only point at which a device mask can still take effect, so both are settled in
    [`prepare`][param_sweeps.local_runner.LocalRunner.prepare] and never changed afterwards.

    Examples:
        ```python
        runner = LocalRunner(gpu_backend=GpuBackend.CUDA, device_index=0)
        run_campaign(spec=spec, runner=runner, output_root=output_root)
        ```
    """

    def __init__(self, *, gpu_backend: GpuBackend, device_index: int, download_missing_models: bool = True) -> None:
        """Configure a local runner.

        Args:
            gpu_backend: The compute backend to pin the process to.
            device_index: The accelerator index to pin the process to.
            download_missing_models: Whether preparation may download missing model weights into
                the worker cache. False turns a missing model into an error instead.
        """
        self._gpu_backend = gpu_backend
        self._device_index = device_index
        self._download_missing_models = download_missing_models
        self._horde: Any | None = None

    @property
    @override
    def name(self) -> str:
        return f"local:{self._gpu_backend}"

    @override
    def fetch_plan(self, jobs: Sequence[RenderJob], models: Sequence[ModelSpec]) -> list[FetchPlanEntry]:
        image_counts = _image_counts_by_model(jobs)
        return [
            FetchPlanEntry(
                model_name=image_model.horde_name,
                approximate_size_gb=image_model.approximate_download_size_gb,
                already_present=self._is_model_on_disk(image_model.horde_name),
                image_count=image_counts.get(image_model.slug, 0),
            )
            for image_model in models
        ]

    @override
    def prepare(self, jobs: Sequence[RenderJob], models: Sequence[ModelSpec]) -> None:
        import hordelib
        from hordelib.horde import HordeLib
        from hordelib.shared_model_manager import SharedModelManager
        from hordelib.utils.torch_memory import AcceleratorKind

        logger.info("Initialising hordelib: backend=%s device_index=%s", self._gpu_backend, self._device_index)
        hordelib.initialise(
            setup_logging=True,
            logging_verbosity=3,
            accelerator_kind=AcceleratorKind(str(self._gpu_backend)),
            device_index=self._device_index,
        )

        SharedModelManager.load_model_managers([COMPVIS_MODEL_MANAGER])
        for image_model in models:
            self._ensure_model_present(image_model)

        self._horde = HordeLib()

    @override
    def render(self, job: RenderJob) -> RenderOutcome:
        if self._horde is None:
            raise RuntimeError("prepare() must be called before render()")

        payload = HordelibPayload.from_job(job)
        result = self._horde.basic_inference_single_image(payload.as_hordelib_mapping())

        rendered_image: Image.Image | None = result.image
        if rendered_image is None:
            raise RuntimeError(f"hordelib returned no image for {job.relative_image_path}")

        fault_note = "; ".join(str(fault) for fault in result.faults) if result.faults else None
        return RenderOutcome(image=rendered_image, model_name_used=job.horde_model_name, note=fault_note)

    @override
    def close(self) -> None:
        self._horde = None

    def _ensure_model_present(self, image_model: ModelSpec) -> None:
        """Download this model's weights if they are not already in the worker cache.

        Raises:
            RuntimeError: If the model is unknown to the reference, or the download failed.
        """
        from hordelib.shared_model_manager import SharedModelManager

        if self._is_model_on_disk(image_model.horde_name):
            logger.info("Model already in the worker cache: model=%s", image_model.horde_name)
            return

        if not self._download_missing_models:
            raise RuntimeError(f"model {image_model.horde_name} is not in the cache and downloading is disabled")

        logger.info(
            "Downloading model: model=%s approximate_size_gb=%.1f",
            image_model.horde_name,
            image_model.approximate_download_size_gb,
        )
        download_succeeded = SharedModelManager.manager.download_model(image_model.horde_name)
        if not download_succeeded:
            raise RuntimeError(f"could not download model {image_model.horde_name}")

    @staticmethod
    def _is_model_on_disk(horde_model_name: str) -> bool | None:
        """Return whether this model's weights are already present, or None if it cannot be told.

        The answer is unknown before ``hordelib`` is initialised, which is exactly the state the
        fetch plan is printed in on a first run, so it is reported as unknown rather than guessed.
        """
        try:
            from hordelib.shared_model_manager import SharedModelManager
        except ImportError:
            logger.debug("hordelib is not installed; model presence cannot be determined")
            return None

        compvis_manager = getattr(SharedModelManager.manager, COMPVIS_MODEL_MANAGER, None)
        if compvis_manager is None:
            return None

        presence: bool = compvis_manager.is_model_available(horde_model_name)
        return presence


def _image_counts_by_model(jobs: Sequence[RenderJob]) -> dict[str, int]:
    """Return how many images each model slug is responsible for."""
    counts: dict[str, int] = {}
    for job in jobs:
        counts[job.model_slug] = counts.get(job.model_slug, 0) + 1
    return counts
