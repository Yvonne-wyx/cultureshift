from __future__ import annotations

from enum import StrEnum

from cultureshift.contracts import BrandLock


class ConfirmationErrorCode(StrEnum):
    LOCKED_FIELD_CHANGED = "locked_field_changed"
    BENEFIT_ORDER_INVALID = "benefit_order_invalid"
    LOCALIZABLE_FIELDS_INVALID = "localizable_fields_invalid"


class BrandLockConfirmationError(ValueError):
    def __init__(self, code: ConfirmationErrorCode) -> None:
        self.code = code
        super().__init__("Brand Lock confirmation is invalid")


def validate_brand_lock_confirmation(
    proposed: BrandLock,
    analyzed: BrandLock,
) -> BrandLock:
    locked_fields = (
        "logo_asset_id",
        "product_name",
        "verified_product_facts",
        "product_ui_asset_ids",
        "cta_action_meaning",
        "layout_template_asset_id",
    )
    if any(getattr(proposed, name) != getattr(analyzed, name) for name in locked_fields):
        raise BrandLockConfirmationError(ConfirmationErrorCode.LOCKED_FIELD_CHANGED)
    if len(proposed.benefit_order) != len(analyzed.benefit_order) or set(
        proposed.benefit_order
    ) != set(analyzed.benefit_order):
        raise BrandLockConfirmationError(ConfirmationErrorCode.BENEFIT_ORDER_INVALID)
    if not set(proposed.localizable_fields) <= set(analyzed.localizable_fields):
        raise BrandLockConfirmationError(ConfirmationErrorCode.LOCALIZABLE_FIELDS_INVALID)
    return proposed
