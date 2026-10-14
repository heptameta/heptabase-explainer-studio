"""Explainer Studio's own versions: how a dev build's version is written, and which versions each episode was worked
on with (`episodes/<episode>/explainer-studio-versions.json`).

A computer has one `explainer-studio` command, so switching between a release and a dev build switches every chat at
once, including a chat in the middle of an episode that read the guide of the earlier version. Every command that
makes an episode's video records its version there (see `cli.common.open_series`); feedback, the video page and the
cost report do not, since they make nothing. When the version differs from the episode's last recorded command (for
an episode without a record, the series' last recorded command), the command tells the agent to print the guide
again and what UPGRADING.md says the series may need. A delivery records the other versions used since the previous
delivery, so a delivery made with more than one version is not taken as a clean sample of its version.
"""

from __future__ import annotations

import re

from .errors import StudioError
from .file_io import hold_lock, load_json_model, write_json_model
from .paths import EPISODE_ID_PATTERN, Series
from .schemas.explainer_studio_versions import ExplainerStudioVersions

# `git describe --tags --match 'v[0-9]*' --long --abbrev=7` of a commit: the last release tag, the commits since it
# and the commit
GIT_DESCRIPTION_PATTERN = re.compile(r"^v(\d+)\.(\d+)\.(\d+)-(\d+)-g([0-9a-f]{7,40})$")


def convert_git_description_to_dev_build_version(git_description: str) -> str:
    """A dev build's version from `git describe` of its commit: the release after the last release tag, `.dev` with
    the number of commits since that tag, and `+g` with the commit, for example v0.1.0-13-g9b0e2d4 gives
    0.1.1.dev13+g9b0e2d4. The tagged commit itself gives .dev0: a dev build is installed from a local snapshot,
    never from the release on GitHub, so it never takes the release's number.

    The `g` matters: Python reads an all-digit label as a number (+0123456 becomes +123456), and the version is
    compared as a string."""
    match = GIT_DESCRIPTION_PATTERN.match(git_description.strip())
    if match is None:
        raise StudioError(f"cannot work out a dev build version from {git_description.strip()!r}",
                          "the nearest tag must be a release tag such as v0.1.0",
                          "build from a commit that comes after a release tag")
    major, minor, patch, distance, commit = match.groups()
    return f"{major}.{minor}.{int(patch) + 1}.dev{distance}+g{commit}"


def _load_explainer_studio_versions(series: Series, episode_id: str) -> ExplainerStudioVersions | None:
    versions_file_path = series.get_episode_paths(episode_id).explainer_studio_versions_file_path
    return (load_json_model(ExplainerStudioVersions, versions_file_path, f"{episode_id}/{versions_file_path.name}")
            if versions_file_path.exists() else None)


def _find_series_last_used_version(series: Series, excluded_episode_id: str) -> str | None:
    """The version of the series' last recorded command on another episode: the record written last."""
    versions_file_paths = [series.get_episode_paths(episode_dir_path.name).explainer_studio_versions_file_path
                           for episode_dir_path in series.episodes_dir_path.iterdir()
                           if episode_dir_path.name != excluded_episode_id
                           and EPISODE_ID_PATTERN.match(episode_dir_path.name)]
    versions_file_paths = [versions_file_path for versions_file_path in versions_file_paths
                           if versions_file_path.is_file()]
    if not versions_file_paths:
        return None
    last_versions_file_path = max(versions_file_paths,
                                  key=lambda versions_file_path: versions_file_path.stat().st_mtime)
    record = _load_explainer_studio_versions(series, last_versions_file_path.parent.name)
    return record.last_used_version if record else None


def record_version_use(series: Series, episode_id: str, version: str) -> str | None:
    """Record that a command on the episode runs with `version`. Returns what to tell the agent when the episode's
    last command ran with another version, else None. An episode's first command compares with the series' last
    one, so a new episode still learns what a series made with an earlier version needs.

    An episode without a folder is left alone (nothing of it was made yet, and a mistyped id must not create one); the
    command reports its own errors about the id."""
    if not EPISODE_ID_PATTERN.match(episode_id) or not series.get_episode_paths(episode_id).root_dir_path.is_dir():
        return None

    def check_is_recorded(record: ExplainerStudioVersions | None) -> bool:
        return record is not None and record.last_used_version == version \
            and version in record.versions_since_last_delivery

    # the usual case: nothing to write, no lock
    if check_is_recorded(_load_explainer_studio_versions(series, episode_id)):
        return None
    versions_file_path = series.get_episode_paths(episode_id).explainer_studio_versions_file_path
    with hold_lock(versions_file_path):
        record = _load_explainer_studio_versions(series, episode_id)
        if check_is_recorded(record):
            return None
        previous_version = (record.last_used_version if record
                            else _find_series_last_used_version(series, episode_id))
        versions = record.versions_since_last_delivery if record else []
        write_json_model(versions_file_path, ExplainerStudioVersions(
            last_used_version=version,
            versions_since_last_delivery=versions if version in versions else [*versions, version]))
    if previous_version is None or previous_version == version:
        return None
    from .releases import format_upgrading_sections, read_upgrading_sections

    # a new episode's chat may have read the guide after the change; one in the middle of an episode has not
    notice = (f"Explainer Studio changed from {previous_version} to {version} since the last command on {episode_id}. "
              "Run `explainer-studio guide` again before continuing: the guide you read is the earlier version's."
              if record else
              f"Explainer Studio changed from {previous_version} to {version} since the last command on this "
              "series. Run `explainer-studio guide` again before continuing unless you printed it with this version.")
    sections = read_upgrading_sections(previous_version, version)
    return notice + ("\n" + format_upgrading_sections(sections) if sections else "")


def list_earlier_versions_since_last_delivery(series: Series, episode_id: str, delivering_version: str) -> list[str]:
    """The versions used on the episode since its last delivery, other than the delivering one."""
    record = _load_explainer_studio_versions(series, episode_id)
    return ([used_version for used_version in record.versions_since_last_delivery
             if used_version != delivering_version] if record else [])


def clear_versions_since_last_delivery(series: Series, episode_id: str) -> None:
    """Start counting again after a delivery. The delivering version is not kept: if the next command comes from
    another version, the delivering one was not used for the next delivery."""
    versions_file_path = series.get_episode_paths(episode_id).explainer_studio_versions_file_path
    if not versions_file_path.exists():
        return
    with hold_lock(versions_file_path):
        record = _load_explainer_studio_versions(series, episode_id)
        if record is not None and record.versions_since_last_delivery:
            write_json_model(versions_file_path, record.model_copy(update={"versions_since_last_delivery": []}))
