"""Tag reading: claims into models, measurements apart, assembly on top."""

from leeks import tags
from test_harness import by_title


def materialised_tags(directory):
    return [tags.read_tags(p) for p in sorted(directory.iterdir())]


def test_read_tags_returns_claims(corpus, materialise):
    album = by_title(corpus, "Cartography for Sleepwalkers")
    directory = materialise(album)
    first = tags.read_tags(sorted(directory.iterdir())[0])
    assert first is not None
    assert first.title == "Inventory of Small Storms"
    assert first.artist == "Tin Hatch Choir"
    assert first.album == "Cartography for Sleepwalkers"
    assert first.year == 2019
    assert first.track == 1


def test_read_tags_refuses_non_audio(tmp_path):
    not_audio = tmp_path / "cover.jpg"
    not_audio.write_bytes(b"\xff\xd8\xff\xe0 not really a jpeg")
    assert tags.read_tags(not_audio) is None


def test_whitespace_only_tags_are_absent(corpus, materialise):
    from mediafile import MediaFile

    album = by_title(corpus, "Paper Lung Atlas")
    path = sorted(materialise(album).iterdir())[0]
    media = MediaFile(str(path))
    media.genre = "   "
    media.save()
    file_tags = tags.read_tags(path)
    assert file_tags is not None and file_tags.genre is None


def test_absent_tags_are_none(corpus, materialise):
    album = by_title(corpus, "Tape Hiss Archipelago")
    directory = materialise(album)
    for file_tags in materialised_tags(directory):
        assert file_tags.year is None
        assert file_tags.genre is None
        assert file_tags.tracktotal is None


def test_measure_probes_the_bytes(corpus, materialise):
    album = by_title(corpus, "Paper Lung Atlas")
    directory = materialise(album)
    # Track 1 is realised by the first tone, which is one second long.
    flac = sorted(directory.iterdir())[0]
    facts = tags.measure(flac)
    assert facts.format == "FLAC"
    assert facts.samplerate == 8000
    assert facts.channels == 1
    assert facts.duration is not None and 0.9 < facts.duration < 1.1
    assert facts.size == flac.stat().st_size


def test_assemble_clean_album(corpus, materialise):
    album = by_title(corpus, "Cartography for Sleepwalkers")
    info = tags.assemble(materialised_tags(materialise(album)))
    assert info.title == album["title"]
    assert info.artist == album["artist"]
    assert info.year == album["year"]
    assert info.genre == album["genre"]
    assert info.tracktotal == album["tracktotal"]
    assert [t.title for t in info.tracks] == [t["title"] for t in album["tracks"]]
    assert all(t.artist is None for t in info.tracks)  # nothing overrides


def test_assemble_feat_override(corpus, materialise):
    album = by_title(corpus, "Salt Meridian")
    info = tags.assemble(materialised_tags(materialise(album)))
    assert info.artist == "Tin Hatch Choir"
    overrides = {t.title: t.artist for t in info.tracks if t.artist}
    assert overrides == {"Lowland Frequencies": "Tin Hatch Choir feat. Vesna Holloway"}


def test_assemble_sparse_album(corpus, materialise):
    album = by_title(corpus, "Tape Hiss Archipelago")
    info = tags.assemble(materialised_tags(materialise(album)))
    assert info.year is None
    assert info.genre is None
    assert info.tracktotal is None
    # Track number then filename: numbered tracks first, the rest by name.
    assert [t.title for t in info.tracks] == [
        "Arcade Rain",
        "Dust on the Faders",
        "Sodium Light Study",
        "Pylon Hum",
    ]
    assert [t.track for t in info.tracks] == [1, 4, None, None]
