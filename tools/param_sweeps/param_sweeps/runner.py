# SPDX-FileCopyrightText: 2026 Tazlin
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The contract both runners implement, so one campaign driver can drive either of them.

A runner turns a [`RenderJob`][param_sweeps.spec.RenderJob] into an image and says nothing
about where the image goes: checkpointing, file naming, sidecars and the index all live in the
driver, so the local and API paths cannot drift apart in what they produce.

Critical public members:

- [`SweepRunner`][param_sweeps.runner.SweepRunner]: the abstract runner.
- [`RenderOutcome`][param_sweeps.runner.RenderOutcome]: an image plus what the runner can report
  about how it was made.
- [`FetchPlanEntry`][param_sweeps.runner.FetchPlanEntry]: one line of the pre-run fetch plan.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from PIL import Image
from pydantic import BaseModel, ConfigDict

from param_sweeps.spec import ModelSpec, RenderJob


class RenderOutcome(BaseModel):
    """Represents one rendered image and what the runner knows about its provenance."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True, protected_namespaces=())

    image: Image.Image
    model_name_used: str | None = None
    note: str | None = None


class FetchPlanEntry(BaseModel):
    """Represents one model a campaign needs, and whether it has to be fetched first."""

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    model_name: str
    approximate_size_gb: float
    already_present: bool | None
    """``None`` when the runner cannot tell, which is the honest answer for the API runner."""

    image_count: int


class SweepRunner(ABC):
    """A backend that renders sweep jobs.

    Subclass Integration:
        [`prepare`][param_sweeps.runner.SweepRunner.prepare] is called once with every job the
        campaign will run, before any rendering, and is where a runner does its setup and any
        model fetching. [`render`][param_sweeps.runner.SweepRunner.render] is called once per
        job, in order, never concurrently. [`close`][param_sweeps.runner.SweepRunner.close] is
        always called, including when the campaign fails.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the runner's name, as recorded in every sidecar it produces."""

    @abstractmethod
    def fetch_plan(self, jobs: Sequence[RenderJob], models: Sequence[ModelSpec]) -> list[FetchPlanEntry]:
        """Return what this runner would have to fetch to render these jobs."""

    @abstractmethod
    def prepare(self, jobs: Sequence[RenderJob], models: Sequence[ModelSpec]) -> None:
        """Set the backend up for this campaign, fetching whatever the jobs need."""

    @abstractmethod
    def render(self, job: RenderJob) -> RenderOutcome:
        """Render one job.

        Raises:
            RuntimeError: If the backend could not produce an image for this job.
        """

    def close(self) -> None:
        """Release whatever the runner is holding.

        The default releases nothing, because a runner that holds nothing should not have to
        say so. It is not abstract for that reason.
        """
        return
