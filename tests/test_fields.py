"""The claim-field registry: arity, the merged-column derivation, the seam."""

from leeks.fields import CLAIMS, MULTI_FIELDS, merged_fields
from leeks.models import AlbumInfo, TrackInfo


def test_merged_fields_are_the_cast_carrying_claims():
    # A merged column is exactly a claim field with a cast (ADR 0025); the
    # relational and column-less fields (artist, genre, tracktotal) are absent.
    # medium is a merged column now that `leek show` reads it (ADR 0034).
    assert merged_fields("album") == {"title": str, "year": int, "medium": str}
    assert merged_fields("track") == {"title": str, "track": int}


def test_only_genre_is_set_valued_today():
    assert MULTI_FIELDS == ("genre",)


def test_every_tagged_field_reads_a_real_model_attribute():
    # The attr seam (the genre field reads the plural `genres`) must point at a
    # field that exists, or the write path's getattr would explode (ADR 0025).
    # Untagged fields are path-only release facts with no model attribute and no
    # file_tags reading (ADR 0033), so the rule is on tagged fields alone.
    models = {"album": AlbumInfo, "track": TrackInfo}
    for field in CLAIMS:
        if field.tagged:
            assert field.model_attr in models[field.entity].model_fields, field


def test_untagged_fields_are_the_path_only_release_facts():
    # The facts only the path asserts (ADR 0033): no tag reads any of them.
    untagged = {f.name for f in CLAIMS if not f.tagged}
    assert untagged == {"medium", "region", "catalogue"}


def test_only_medium_among_the_path_facts_earns_a_column():
    # medium has a reader (`leek show`) so it casts to a merged column; region
    # and catalogue have none yet, so they stay claim-only (ADR 0034).
    casts = {f.name: f.cast for f in CLAIMS if not f.tagged}
    assert casts == {"medium": str, "region": None, "catalogue": None}
