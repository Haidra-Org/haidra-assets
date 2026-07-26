# SPDX-FileCopyrightText: 2026 Tazlin
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render sweep jobs through the public AI Horde API.

The API runner exists so the library can be produced without a local GPU, and so a strip can be
re-rendered from anywhere. It is deliberately unhurried: one job is submitted at a time and the
next is not queued until the previous image is on disk, because this is other people's hardware
being asked for a favour.

The API key is read from the frontpage repository's ``.env`` (or the environment) and is never
printed, logged, or written to any output. Nothing in this module puts the key anywhere except
the request header.

Critical public members:

- [`HordeApiRunner`][param_sweeps.horde_runner.HordeApiRunner]: the runner itself.
- [`read_api_key`][param_sweeps.horde_runner.read_api_key]: the ``.env`` and environment lookup.
- [`HordeGenerationParams`][param_sweeps.horde_runner.HordeGenerationParams]: the request body.
"""

from __future__ import annotations

import io
import logging
import os
import re
import time
from collections.abc import Sequence
from pathlib import Path
from typing import override

import requests
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field

from param_sweeps.runner import FetchPlanEntry, RenderOutcome, SweepRunner
from param_sweeps.spec import ModelSpec, RenderJob

logger = logging.getLogger(__name__)

API_KEY_VARIABLE = "AIHORDE_DEV_KEY"
"""The name of the key, both in the frontpage ``.env`` and in the environment."""

ENV_FILE_VARIABLE = "PARAM_SWEEPS_ENV_FILE"
"""Environment variable naming the ``.env`` to read the key from."""

DEFAULT_API_BASE_URL = "https://aihorde.net/api/v2"
"""The public AI Horde API."""

CLIENT_AGENT = "haidra-param-sweeps:1.0.0:https://github.com/Haidra-Org/haidra-assets"
"""Identifies this tool to the horde, as the API asks every client to do."""

ENV_ASSIGNMENT_PATTERN = re.compile(r"^\s*(?:export\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*?)\s*$")


class HordePacing:
    """How politely the runner talks to the horde.

    One job in flight at a time, a poll interval that will not add meaningful load, and a
    generous ceiling because a large or unpopular model can legitimately queue for a long while.
    """

    POLL_INTERVAL_SECONDS = 4.0
    MAX_WAIT_SECONDS = 1800.0
    PAUSE_BETWEEN_JOBS_SECONDS = 1.5
    REQUEST_TIMEOUT_SECONDS = 60.0
    MAX_ATTEMPTS_PER_JOB = 3


class HordeGenerationParams(BaseModel):
    """Represents the ``params`` object of an image generation request."""

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    sampler_name: str
    cfg_scale: float
    width: int
    height: int
    steps: int
    seed: str
    karras: bool
    hires_fix: bool
    tiling: bool
    clip_skip: int
    n: int = 1


class HordeGenerationRequest(BaseModel):
    """Represents the body of a ``POST /generate/async`` request."""

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    prompt: str
    params: HordeGenerationParams
    models: list[str]
    nsfw: bool = False
    censor_nsfw: bool = True
    r2: bool = True
    trusted_workers: bool = False
    slow_workers: bool = True

    @classmethod
    def from_job(cls, job: RenderJob) -> HordeGenerationRequest:
        """Create a request body from a render job."""
        return cls(
            prompt=job.prompt,
            models=[job.horde_model_name],
            params=HordeGenerationParams(
                sampler_name=job.sampler_name,
                cfg_scale=job.cfg_scale,
                width=job.width,
                height=job.height,
                steps=job.steps,
                seed=str(job.seed),
                karras=job.karras,
                hires_fix=job.hires_fix,
                tiling=job.tiling,
                clip_skip=job.clip_skip,
            ),
        )


class HordeGeneration(BaseModel):
    """Represents one finished generation in a status response."""

    model_config = ConfigDict(frozen=True, extra="ignore", protected_namespaces=())

    img: str = ""
    seed: str = ""
    model_used: str = Field(default="", alias="model")
    worker_name: str = ""
    censored: bool = False


class HordeAsyncRequestAccepted(BaseModel):
    """Represents the response to a submitted generation request."""

    model_config = ConfigDict(frozen=True, extra="ignore", populate_by_name=True, protected_namespaces=())

    request_id: str = Field(alias="id")
    kudos: float = 0.0


class HordeServedModel(BaseModel):
    """Represents one model the horde's workers currently serve."""

    model_config = ConfigDict(frozen=True, extra="ignore", protected_namespaces=())

    name: str = ""
    count: int = 0


class HordeStatusResponse(BaseModel):
    """Represents a ``/generate/status`` or ``/generate/check`` response."""

    model_config = ConfigDict(frozen=True, extra="ignore", protected_namespaces=())

    done: bool = False
    faulted: bool = False
    is_possible: bool = True
    queue_position: int = 0
    wait_time: int = 0
    generations: list[HordeGeneration] = Field(default_factory=list)


class MissingApiKeyError(RuntimeError):
    """The API key could not be found where it was looked for."""


def read_api_key(*, env_file: Path | None) -> str:
    """Return the AI Horde API key, from the environment or the given ``.env``.

    The environment wins, so a run can be pointed at a different key without editing a file. The
    key itself is never logged: a failure reports only where it looked.

    Args:
        env_file: The ``.env`` to read, or None to use only the environment.

    Returns:
        The key.

    Raises:
        MissingApiKeyError: If no key was found, or the one found is empty.
    """
    key_from_environment = os.environ.get(API_KEY_VARIABLE, "").strip()
    if key_from_environment:
        logger.info("Using the API key from the environment: variable=%s", API_KEY_VARIABLE)
        return key_from_environment

    if env_file is None:
        raise MissingApiKeyError(f"{API_KEY_VARIABLE} is not set and no .env was given")

    if not env_file.is_file():
        raise MissingApiKeyError(f"{API_KEY_VARIABLE} is not set and {env_file} does not exist")

    key_from_file = _read_env_value(env_file=env_file, variable_name=API_KEY_VARIABLE)
    if not key_from_file:
        raise MissingApiKeyError(f"{env_file} has no non-empty {API_KEY_VARIABLE}")

    logger.info("Using the API key from %s", env_file)
    return key_from_file


def default_env_file() -> Path | None:
    """Return the ``.env`` to read by default: the environment's, else the frontpage repository's.

    This tool lives in the ``haidra-assets`` submodule of the frontpage repository, whose ``.env``
    holds the development key. That relative position is the default and nothing more: any other
    location is given with the flag or the environment variable.
    """
    from_environment = os.environ.get(ENV_FILE_VARIABLE, "").strip()
    if from_environment:
        return Path(from_environment)

    assets_repository_root = Path(__file__).resolve().parents[3]
    frontpage_env = assets_repository_root.parent.parent / ".env"
    return frontpage_env if frontpage_env.is_file() else None


def _read_env_value(*, env_file: Path, variable_name: str) -> str:
    """Return one variable's value from a ``.env``, or the empty string when it is not there."""
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("#"):
            continue

        assignment = ENV_ASSIGNMENT_PATTERN.match(line)
        if assignment is None or assignment.group("name") != variable_name:
            continue

        return assignment.group("value").strip().strip("\"'")

    return ""


class HordeApiRunner(SweepRunner):
    """Renders sweep jobs on the public AI Horde, one job at a time.

    Network Behavior:
        Each job is one ``POST /generate/async``, then ``/generate/check`` polled until the job
        is done, then ``/generate/status`` once to collect the image URL, then the download. A
        job that faults or times out is retried a small number of times before it is reported as
        failed and left for the next run to pick up.
    """

    def __init__(
        self,
        *,
        api_key: str,
        api_base_url: str = DEFAULT_API_BASE_URL,
        session: requests.Session | None = None,
    ) -> None:
        """Configure an API runner.

        Args:
            api_key: The AI Horde API key. Held only in the session header.
            api_base_url: The API root to talk to.
            session: An existing session to use, which is how the tests substitute a transport.
        """
        self._api_base_url = api_base_url.rstrip("/")
        self._session = session if session is not None else requests.Session()
        self._session.headers.update(
            {
                "apikey": api_key,
                "Client-Agent": CLIENT_AGENT,
                "accept": "application/json",
            },
        )
        self._is_first_job = True

    @property
    @override
    def name(self) -> str:
        return "ai-horde-api"

    @override
    def fetch_plan(self, jobs: Sequence[RenderJob], models: Sequence[ModelSpec]) -> list[FetchPlanEntry]:
        image_counts: dict[str, int] = {}
        for job in jobs:
            image_counts[job.model_slug] = image_counts.get(job.model_slug, 0) + 1

        # Nothing is downloaded locally, and whether any worker currently serves a model is a
        # question about the horde's live state rather than about this machine, so presence is
        # reported as unknown rather than implied.
        return [
            FetchPlanEntry(
                model_name=image_model.horde_name,
                approximate_size_gb=0.0,
                already_present=None,
                image_count=image_counts.get(image_model.slug, 0),
            )
            for image_model in models
        ]

    @override
    def prepare(self, jobs: Sequence[RenderJob], models: Sequence[ModelSpec]) -> None:
        available_models = self._available_model_names()
        if not available_models:
            logger.warning("Could not read the horde's model list; proceeding without the availability check")
            return

        for image_model in models:
            if image_model.horde_name not in available_models:
                logger.warning(
                    "No worker currently serves this model; its jobs will queue until one does: model=%s",
                    image_model.horde_name,
                )

    @override
    def render(self, job: RenderJob) -> RenderOutcome:
        last_error = ""
        for attempt in range(1, HordePacing.MAX_ATTEMPTS_PER_JOB + 1):
            if not self._is_first_job:
                time.sleep(HordePacing.PAUSE_BETWEEN_JOBS_SECONDS)
            self._is_first_job = False

            try:
                return self._render_once(job)
            except (requests.RequestException, TimeoutError) as request_error:
                last_error = str(request_error)
                logger.warning(
                    "Horde job failed, retrying: attempt=%s/%s image=%s error=%s",
                    attempt,
                    HordePacing.MAX_ATTEMPTS_PER_JOB,
                    job.relative_image_path,
                    last_error,
                )

        raise RuntimeError(f"the horde could not render {job.relative_image_path}: {last_error}")

    @override
    def close(self) -> None:
        self._session.close()

    def _render_once(self, job: RenderJob) -> RenderOutcome:
        """Submit one job, wait for it, and return the downloaded image.

        Raises:
            RuntimeError: If the horde reported the job as faulted or impossible.
            requests.RequestException: On any transport or HTTP failure, which the caller retries.
        """
        request_body = HordeGenerationRequest.from_job(job)
        submit_response = self._session.post(
            f"{self._api_base_url}/generate/async",
            json=request_body.model_dump(),
            timeout=HordePacing.REQUEST_TIMEOUT_SECONDS,
        )
        submit_response.raise_for_status()
        accepted = HordeAsyncRequestAccepted.model_validate(submit_response.json())

        self._wait_for_completion(request_id=accepted.request_id, image_path=job.relative_image_path)

        status_response = self._session.get(
            f"{self._api_base_url}/generate/status/{accepted.request_id}",
            timeout=HordePacing.REQUEST_TIMEOUT_SECONDS,
        )
        status_response.raise_for_status()
        status = HordeStatusResponse.model_validate(status_response.json())

        if not status.generations:
            raise RuntimeError(f"the horde returned no generation for {job.relative_image_path}")

        generation = status.generations[0]
        image = self._download_image(generation.img)
        note = "censored by the horde's safety checker" if generation.censored else None
        model_used = generation.model_used if generation.model_used else job.horde_model_name

        return RenderOutcome(image=image, model_name_used=model_used, note=note)

    def _wait_for_completion(self, *, request_id: str, image_path: str) -> None:
        """Poll until the horde reports this request done.

        Raises:
            RuntimeError: If the request faulted or no worker can serve it.
            TimeoutError: If the ceiling is reached before the request completes.
        """
        deadline = time.monotonic() + HordePacing.MAX_WAIT_SECONDS

        while time.monotonic() < deadline:
            check_response = self._session.get(
                f"{self._api_base_url}/generate/check/{request_id}",
                timeout=HordePacing.REQUEST_TIMEOUT_SECONDS,
            )
            check_response.raise_for_status()
            status = HordeStatusResponse.model_validate(check_response.json())

            if status.faulted:
                raise RuntimeError(f"the horde faulted the request for {image_path}")
            if not status.is_possible:
                raise RuntimeError(f"no worker can serve the request for {image_path}")
            if status.done:
                return

            logger.debug(
                "Waiting on the horde: image=%s queue_position=%s wait_time=%s",
                image_path,
                status.queue_position,
                status.wait_time,
            )
            time.sleep(HordePacing.POLL_INTERVAL_SECONDS)

        raise TimeoutError(f"the horde did not finish {image_path} within {HordePacing.MAX_WAIT_SECONDS:.0f}s")

    def _download_image(self, image_url: str) -> Image.Image:
        """Download and decode a finished generation.

        Raises:
            RuntimeError: If the generation carries no URL.
            requests.RequestException: On any transport or HTTP failure.
        """
        if not image_url:
            raise RuntimeError("the horde returned a generation with no image URL")

        image_response = self._session.get(image_url, timeout=HordePacing.REQUEST_TIMEOUT_SECONDS)
        image_response.raise_for_status()

        with Image.open(io.BytesIO(image_response.content)) as downloaded:
            return downloaded.convert("RGB")

    def _available_model_names(self) -> set[str]:
        """Return the names of the image models workers currently serve, or an empty set."""
        try:
            models_response = self._session.get(
                f"{self._api_base_url}/status/models",
                params={"type": "image"},
                timeout=HordePacing.REQUEST_TIMEOUT_SECONDS,
            )
            models_response.raise_for_status()
        except requests.RequestException as request_error:
            logger.warning("Could not read the horde's model list: error=%s", request_error)
            return set()

        served_models = [HordeServedModel.model_validate(entry) for entry in models_response.json()]
        return {served_model.name for served_model in served_models if served_model.name}
