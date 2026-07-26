# SPDX-FileCopyrightText: 2026 Tazlin
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Drive a campaign: filter the specification, render what is missing, keep the index current.

The driver is the only place that knows about resumption and file layout. It asks the runner
for a fetch plan and prints it before anything is generated, skips every job the checkpoint
already accounts for, and writes the checkpoint and the index as it goes, so the tree on disk
is a usable library at every point during a long run rather than only at the end.

Critical public members:

- [`run_campaign`][param_sweeps.campaign.run_campaign]: render a (possibly filtered) campaign.
- [`JobFilter`][param_sweeps.campaign.JobFilter]: which subset of the specification to run.
- [`format_fetch_plan`][param_sweeps.campaign.format_fetch_plan]: the pre-run report's text.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from param_sweeps.checkpoint import CampaignCheckpoint
from param_sweeps.outputs import save_render, write_index
from param_sweeps.runner import FetchPlanEntry, SweepRunner
from param_sweeps.spec import ModelSpec, RenderJob, SweepSpec

logger = logging.getLogger(__name__)

INDEX_REWRITE_INTERVAL = 10
"""How many images to render between index rewrites, so a long run stays consumable."""


class JobFilter(BaseModel):
    """Represents the subset of the specification a run should cover.

    An unset field matches everything, so the default filter runs the whole specification and a
    single strip is named by setting all three.
    """

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    parameters: tuple[str, ...] = ()
    model_slugs: tuple[str, ...] = ()
    scene_ids: tuple[str, ...] = ()

    def matches(self, job: RenderJob) -> bool:
        """Return whether this job is inside the filter."""
        if self.parameters and str(job.parameter) not in self.parameters:
            return False
        if self.model_slugs and job.model_slug not in self.model_slugs:
            return False
        return not (self.scene_ids and job.scene_id not in self.scene_ids)


class CampaignResult(BaseModel):
    """Represents what a campaign run did."""

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    selected_count: int
    rendered_count: int
    skipped_count: int
    failed_jobs: tuple[str, ...]


def select_jobs(*, spec: SweepSpec, job_filter: JobFilter) -> list[RenderJob]:
    """Return the specification's jobs that the filter selects, in specification order."""
    return [job for job in spec.expand_jobs() if job_filter.matches(job)]


def models_for_jobs(*, spec: SweepSpec, jobs: Sequence[RenderJob]) -> list[ModelSpec]:
    """Return the models these jobs need, in specification order."""
    needed_slugs = {job.model_slug for job in jobs}
    return [image_model for image_model in spec.models if image_model.slug in needed_slugs]


def format_fetch_plan(*, entries: Sequence[FetchPlanEntry], total_image_count: int, pending_count: int) -> str:
    """Return the human-readable fetch plan printed before any generation starts."""
    lines = ["Fetch plan:"]

    total_to_fetch_gb = 0.0
    unknown_gb = 0.0
    for entry in entries:
        if entry.already_present is None:
            presence = "presence unknown"
            unknown_gb += entry.approximate_size_gb
        elif entry.already_present:
            presence = "already on disk"
        else:
            presence = "must be downloaded"
            total_to_fetch_gb += entry.approximate_size_gb

        size_note = f"~{entry.approximate_size_gb:.1f} GB, " if entry.approximate_size_gb > 0 else ""
        lines.append(f"  {entry.model_name}: {size_note}{presence} ({entry.image_count} images)")

    download_note = f"  approximate download: {total_to_fetch_gb:.1f} GB"
    if unknown_gb > 0:
        download_note += f", plus up to {unknown_gb:.1f} GB whose presence could not be checked"
    lines.append(download_note)
    lines.append(f"Images: {total_image_count} selected, {pending_count} still to render.")
    return "\n".join(lines)


def run_campaign(
    *,
    spec: SweepSpec,
    runner: SweepRunner,
    output_root: Path,
    job_filter: JobFilter | None = None,
    plan_only: bool = False,
    force: bool = False,
) -> CampaignResult:
    """Render every selected job that is not already on disk, and keep the index current.

    Args:
        spec: The specification to render.
        runner: The backend to render with.
        output_root: The root of the output tree.
        job_filter: Which subset to run. Defaults to the whole specification.
        plan_only: Print the fetch plan and stop without preparing the runner or generating.
        force: Render selected jobs even when the checkpoint already accounts for them.

    Returns:
        What the run rendered, skipped and failed.

    Side Effects:
        Writes images, sidecars, the checkpoint and the index under ``output_root``, and on the
        local runner downloads model weights into the worker cache.
    """
    resolved_filter = job_filter if job_filter is not None else JobFilter()
    selected_jobs = select_jobs(spec=spec, job_filter=resolved_filter)
    if not selected_jobs:
        raise ValueError("the filter selected no jobs; check the parameter, model and scene names")

    checkpoint = CampaignCheckpoint(output_root=output_root)
    pending_jobs = [job for job in selected_jobs if force or not checkpoint.is_complete(job.relative_image_path)]

    needed_models = models_for_jobs(spec=spec, jobs=pending_jobs or selected_jobs)
    fetch_plan = runner.fetch_plan(pending_jobs or selected_jobs, needed_models)
    print(
        format_fetch_plan(
            entries=fetch_plan,
            total_image_count=len(selected_jobs),
            pending_count=len(pending_jobs),
        ),
    )

    skipped_count = len(selected_jobs) - len(pending_jobs)
    if plan_only:
        return CampaignResult(
            selected_count=len(selected_jobs),
            rendered_count=0,
            skipped_count=skipped_count,
            failed_jobs=(),
        )

    rendered_count = 0
    failed_jobs: list[str] = []

    try:
        runner.prepare(pending_jobs, needed_models)

        for job_number, job in enumerate(pending_jobs, start=1):
            print(f"[{job_number}/{len(pending_jobs)}] {job.relative_image_path}")
            started_at = datetime.now(UTC)
            try:
                outcome = runner.render(job)
            except RuntimeError as render_error:
                # One unlucky job should not end a campaign that resumes cleanly; the failure is
                # reported at the end and the checkpoint leaves the job pending for the next run.
                logger.error("Render failed: job=%s error=%s", job.relative_image_path, render_error)
                failed_jobs.append(job.relative_image_path)
                continue

            save_render(
                image=outcome.image,
                job=job,
                output_root=output_root,
                runner_name=runner.name,
                started_at=started_at,
                finished_at=datetime.now(UTC),
                model_name_used=outcome.model_name_used,
                worker_note=outcome.note,
            )
            checkpoint.mark_complete(
                relative_image_path=job.relative_image_path,
                runner_name=runner.name,
                seed=job.seed,
            )
            rendered_count += 1

            if rendered_count % INDEX_REWRITE_INTERVAL == 0:
                write_index(spec=spec, output_root=output_root)
    finally:
        runner.close()
        write_index(spec=spec, output_root=output_root)

    return CampaignResult(
        selected_count=len(selected_jobs),
        rendered_count=rendered_count,
        skipped_count=skipped_count,
        failed_jobs=tuple(failed_jobs),
    )
