from uuid import UUID

import pytest

from cultureshift.brand_lock_confirmation import (
    BrandLockConfirmationError,
    ConfirmationErrorCode,
    validate_brand_lock_confirmation,
)
from cultureshift.contracts import BrandLock


def lock_from_payload(valid_run_payload) -> BrandLock:
    return BrandLock.model_validate(valid_run_payload["brand_lock"])


@pytest.mark.parametrize(
    ("field", "changed_value"),
    [
        ("logo_asset_id", UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")),
        ("product_name", "Changed product"),
        ("verified_product_facts", ("Changed fact",)),
        (
            "product_ui_asset_ids",
            (UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),),
        ),
        ("cta_action_meaning", "A changed action"),
        (
            "layout_template_asset_id",
            UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
        ),
    ],
)
def test_locked_fields_cannot_change(valid_run_payload, field, changed_value) -> None:
    analyzed = lock_from_payload(valid_run_payload)
    proposed = BrandLock.model_validate(
        {**analyzed.model_dump(), field: changed_value}
    )

    with pytest.raises(BrandLockConfirmationError) as caught:
        validate_brand_lock_confirmation(proposed, analyzed)

    assert caught.value.code is ConfirmationErrorCode.LOCKED_FIELD_CHANGED
    assert changed_value.__str__() not in str(caught.value)


def test_benefit_order_must_be_an_exact_permutation(valid_run_payload) -> None:
    analyzed = lock_from_payload(valid_run_payload)
    reordered = BrandLock.model_validate(
        {
            **analyzed.model_dump(),
            "benefit_order": tuple(reversed(analyzed.benefit_order)),
        }
    )
    missing = BrandLock.model_validate(
        {**analyzed.model_dump(), "benefit_order": (analyzed.benefit_order[0],)}
    )

    assert validate_brand_lock_confirmation(reordered, analyzed) == reordered
    with pytest.raises(BrandLockConfirmationError) as caught:
        validate_brand_lock_confirmation(missing, analyzed)
    assert caught.value.code is ConfirmationErrorCode.BENEFIT_ORDER_INVALID


def test_localizable_fields_must_stay_inside_analyzed_allowlist(
    valid_run_payload,
) -> None:
    base = lock_from_payload(valid_run_payload)
    analyzed = BrandLock.model_validate(
        {**base.model_dump(), "localizable_fields": ("narrative", "language")}
    )
    subset = BrandLock.model_validate(
        {**analyzed.model_dump(), "localizable_fields": ("language",)}
    )
    outside = BrandLock.model_validate(
        {
            **analyzed.model_dump(),
            "localizable_fields": ("language", "use_scenario"),
        }
    )

    assert validate_brand_lock_confirmation(subset, analyzed) == subset
    with pytest.raises(BrandLockConfirmationError) as caught:
        validate_brand_lock_confirmation(outside, analyzed)
    assert caught.value.code is ConfirmationErrorCode.LOCALIZABLE_FIELDS_INVALID
