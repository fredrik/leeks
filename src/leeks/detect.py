"""Single-album detection: a validator, not a clusterer (ADR 0004).

`leek add` checks a human's claim that one directory holds one album.
Refusals name what was seen; the fix is usually `leek import`.
"""

from pathlib import Path

from leeks import tags
from leeks.tags import FileTags

# For the nested scan only; the top level asks mediafile, which is authoritative.
AUDIO_SUFFIXES = {
    ".aac",
    ".aiff",
    ".ape",
    ".dsf",
    ".flac",
    ".m4a",
    ".mp3",
    ".ogg",
    ".opus",
    ".wav",
    ".wv",
}


class NotOneAlbum(Exception):
    """The directory does not look like exactly one album."""


def _subdirectories_with_audio(directory: Path) -> list[str]:
    nested = {
        path.relative_to(directory).parts[0]
        for path in directory.rglob("*")
        if path.is_file()
        and path.suffix.lower() in AUDIO_SUFFIXES
        and path.parent != directory
    }
    return sorted(nested)


def detect(directory: Path) -> list[FileTags]:
    """Parse the directory's audio, refusing unless it looks like one album."""
    nested = _subdirectories_with_audio(directory)
    if nested:
        raise NotOneAlbum(
            f"audio in subdirectories ({', '.join(nested)}): "
            "this looks like more than one album — try `leek import`"
        )
    audio = []
    for path in sorted(directory.iterdir()):
        if path.is_file() and (parsed := tags.read_tags(path)) is not None:
            audio.append(parsed)
    if not audio:
        raise NotOneAlbum(f"no audio files in {directory}")
    albums = sorted({t.album for t in audio if t.album})
    if len(albums) > 1:
        named = "; ".join(albums)
        raise NotOneAlbum(
            f"this looks like {len(albums)} albums ({named}) — try `leek import`"
        )
    return audio
