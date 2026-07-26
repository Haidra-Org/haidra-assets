# SPDX-FileCopyrightText: 2026 Tazlin
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The command line: plan a campaign, render it locally or through the horde, rebuild the index.

Every subcommand takes the same specification and the same filters, so "render the whole
library" and "regenerate one strip" are the same command with the filters narrowed. Nothing
here ever prints the API key.

Critical public member: [`main`][param_sweeps.cli.main], the console entry point.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from param_sweeps.campaign import CampaignResult, JobFilter, run_campaign
from param_sweeps.horde_runner import HordeApiRunner, MissingApiKeyError, default_env_file, read_api_key
from param_sweeps.local_runner import GpuBackend, LocalRunner, resolve_gpu_backend
from param_sweeps.outputs import write_index
from param_sweeps.runner import SweepRunner
from param_sweeps.spec import SweepParameter, load_spec

logger = logging.getLogger(__name__)

TOOL_ROOT = Path(__file__).resolve().parents[1]
"""The tool's own directory, which is where the specification lives."""

DEFAULT_SPEC_PATH = TOOL_ROOT / "sweep_spec.json"
DEFAULT_OUTPUT_ROOT = TOOL_ROOT.parents[1] / "assets" / "param-sweeps"
"""``<haidra-assets>/assets/param-sweeps``: the library's home in this repository."""


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser for every subcommand."""
    parser = argparse.ArgumentParser(
        prog="param-sweeps",
        description="Render the parameter-sweep illustration library from its specification.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="print the fetch plan and image count, and generate nothing")
    _add_common_arguments(plan_parser)
    _add_local_arguments(plan_parser)

    local_parser = subparsers.add_parser("local", help="render through horde-engine on this machine's GPU")
    _add_common_arguments(local_parser)
    _add_local_arguments(local_parser)

    horde_parser = subparsers.add_parser("horde", help="render through the public AI Horde API")
    _add_common_arguments(horde_parser)
    horde_parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="the .env holding AIHORDE_DEV_KEY (default: the frontpage repository's, if present)",
    )
    horde_parser.add_argument("--api-url", default=None, help="the API root to use instead of the public horde")

    index_parser = subparsers.add_parser("index", help="rebuild index.json from the images already on disk")
    index_parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC_PATH, help="the sweep specification to read")
    index_parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT, help="the output tree's root")

    return parser


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the specification, output and filter arguments every rendering subcommand shares."""
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC_PATH, help="the sweep specification to read")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT, help="the output tree's root")
    parser.add_argument(
        "--parameter",
        action="append",
        default=[],
        choices=[str(parameter) for parameter in SweepParameter],
        help="restrict the run to this parameter (repeatable)",
    )
    parser.add_argument(
        "--model",
        action="append",
        default=[],
        help="restrict the run to this model slug (repeatable)",
    )
    parser.add_argument("--scene", action="append", default=[], help="restrict the run to this scene id (repeatable)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="render selected images even when the checkpoint already accounts for them",
    )
    parser.add_argument("--verbose", action="store_true", help="log at debug level")


def _add_local_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the arguments that select the compute backend for a local run."""
    parser.add_argument(
        "--gpu-backend",
        default=None,
        choices=[str(backend) for backend in GpuBackend],
        help="the compute backend to use (default: cuda, or PARAM_SWEEPS_GPU_BACKEND)",
    )
    parser.add_argument("--device-index", type=int, default=0, help="the accelerator index to pin this process to")
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="fail instead of downloading a model that is not already in the worker cache",
    )


def main(argv: list[str] | None = None) -> int:
    """Run the command line, and return the process exit code.

    Args:
        argv: The arguments to parse, or None to read ``sys.argv``.

    Returns:
        0 when everything asked for succeeded, 1 otherwise.
    """
    arguments = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if getattr(arguments, "verbose", False) else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    spec = load_spec(arguments.spec)
    output_root: Path = arguments.output_root

    if arguments.command == "index":
        index_path = write_index(spec=spec, output_root=output_root)
        print(f"Wrote {index_path}")
        return 0

    job_filter = JobFilter(
        parameters=tuple(arguments.parameter),
        model_slugs=tuple(arguments.model),
        scene_ids=tuple(arguments.scene),
    )

    try:
        runner = _build_runner(arguments)
    except (ValueError, MissingApiKeyError) as configuration_error:
        print(f"error: {configuration_error}", file=sys.stderr)
        return 1

    result = run_campaign(
        spec=spec,
        runner=runner,
        output_root=output_root,
        job_filter=job_filter,
        plan_only=arguments.command == "plan",
        force=arguments.force,
    )
    return _report(result)


def _build_runner(arguments: argparse.Namespace) -> SweepRunner:
    """Create the runner the chosen subcommand needs.

    ``plan`` uses the local runner because the plan it prints is about this machine's cache.

    Raises:
        ValueError: If an unsupported GPU backend was named.
        MissingApiKeyError: If the horde runner was asked for and no key could be found.
    """
    if arguments.command == "horde":
        env_file = arguments.env_file if arguments.env_file is not None else default_env_file()
        api_key = read_api_key(env_file=env_file)
        if arguments.api_url is not None:
            return HordeApiRunner(api_key=api_key, api_base_url=arguments.api_url)
        return HordeApiRunner(api_key=api_key)

    return LocalRunner(
        gpu_backend=resolve_gpu_backend(requested=arguments.gpu_backend),
        device_index=arguments.device_index,
        download_missing_models=not arguments.no_download,
    )


def _report(result: CampaignResult) -> int:
    """Print what the campaign did, and return the exit code that reflects it."""
    print(
        f"Selected {result.selected_count}, rendered {result.rendered_count},"
        f" already present {result.skipped_count}, failed {len(result.failed_jobs)}.",
    )
    if not result.failed_jobs:
        return 0

    print("Failed:", file=sys.stderr)
    for failed_image_path in result.failed_jobs:
        print(f"  {failed_image_path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
