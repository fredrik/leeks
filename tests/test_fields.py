"""The claim-field registry: arity, the merged-column derivation, the seam."""

from leeks.fields import CLAIMS, MULTI_FIELDS, merged_fields
from leeks.models import AlbumInfo, TrackInfo


def test_merged_fields_are_the_cast_carrying_claims():
    # A merged column is exactly a claim field with a cast (ADR 0025); the
    # relational and column-less fields (artist, genre, tracktotal) are absent.
    assert merged_fields("album") == {"title": str, "year": int}
    assert merged_fields("track") == {"title": str, "track": int}


def test_only_genre_is_set_valued_today():
    assert MULTI_FIELDS == ("genre",)


def test_every_claim_field_reads_a_real_model_attribute():
    # The attr seam (the genre field reads the plural `genres`) must point at a
    # field that exists, or the write path's getattr would explode (ADR 0025).
    models = {"album": AlbumInfo, "track": TrackInfo}
    for field in CLAIMS:
        assert field.model_attr in models[field.entity].model_fields, field
