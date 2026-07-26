# SPDX-FileCopyrightText: 2026 Tazlin
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Track which images a campaign has already produced, so an interrupted run resumes.

A campaign is long and, on the API runner, is somebody else's compute being spent politely one
job at a time. The checkpoint is written after every single image, keyed by the image's
deterministic path, so stopping the run at any point and starting it again picks up at the next
unrendered image rather than at the beginning.

Critical public member: [`CampaignCheckpoint`][param_sweeps.checkpoint.CampaignCheckpoint].
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, RootModel, ValidationError

CHECKPOINT_FILENAME = ".param-sweeps-checkpoint.json"
"""The checkpoint's name, at the root of the output tree."""


class CompletedRender(BaseModel):
    """Represents one image the campaign has already produced."""

    model_config = ConfigDict(frozen=True, extra="ignore", protected_namespaces=())

    runner: str
    seed: int
    completed_at: str


class CheckpointFile(RootModel[dict[str, CompletedRender]]):
    """Represents the checkpoint on disk: completed renders keyed by their image path."""


class CampaignCheckpoint:
    """The record of what a campaign has already rendered, backed by a JSON file.

    An entry only counts when the image it names is still on disk, so deleting an image is all
    it takes to have the next run regenerate it. That keeps "regenerate one strip" a matter of
    removing files rather than editing bookkeeping.

    Thread Safety:
        Not thread-safe. Both runners render one image at a time by design.
    """

    def __init__(self, *, output_root: Path) -> None:
        """Load the checkpoint for this output tree, or start an empty one.

        Args:
            output_root: The root of the output tree the checkpoint belongs to.
        """
        self._output_root = output_root
        self._checkpoint_path = output_root / CHECKPOINT_FILENAME
        self._completed: dict[str, CompletedRender] = {}

        if self._checkpoint_path.is_file():
            self._completed = self._read_entries(self._checkpoint_path)

    @property
    def path(self) -> Path:
        """Return the checkpoint file's path."""
        return self._checkpoint_path

    @property
    def completed_count(self) -> int:
        """Return how many renders the checkpoint records."""
        return len(self._completed)

    def is_complete(self, relative_image_path: str) -> bool:
        """Return whether this image is recorded as rendered and is still on disk."""
        if relative_image_path not in self._completed:
            return False
        return (self._output_root / relative_image_path).is_file()

    def mark_complete(self, *, relative_image_path: str, runner_name: str, seed: int) -> None:
        """Record this image as rendered and write the checkpoint out immediately.

        Side Effects:
            Rewrites the checkpoint file on every call. That is one small write per image, which
            is the price of never losing more than the image in flight.
        """
        self._completed[relative_image_path] = CompletedRender(
            runner=runner_name,
            seed=seed,
            completed_at=datetime.now(UTC).isoformat(),
        )
        self._write()

    def forget(self, relative_image_path: str) -> None:
        """Drop this image's entry, so the next run renders it again."""
        self._completed.pop(relative_image_path, None)
        self._write()

    def _write(self) -> None:
        self._checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        contents = CheckpointFile(dict(sorted(self._completed.items())))
        self._checkpoint_path.write_text(contents.model_dump_json(indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _read_entries(checkpoint_path: Path) -> dict[str, CompletedRender]:
        """Return the entries in this checkpoint file.

        Raises:
            ValueError: If the file exists but cannot be read as a checkpoint. Silently starting
                over would mean re-rendering a campaign that had already been paid for.
        """
        try:
            contents = CheckpointFile.model_validate_json(checkpoint_path.read_text(encoding="utf-8"))
        except ValidationError as validation_error:
            message = f"{checkpoint_path} is not a readable checkpoint: {validation_error}"
            raise ValueError(message) from validation_error

        return dict(contents.root)
