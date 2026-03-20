from __future__ import annotations

from dataclasses import dataclass


CHANNEL_TH = "th"
CHANNEL_KINGPOWER_CN = "kingpowercn"
CHANNEL_THT = "tht"


@dataclass(frozen=True)
class ChannelProfile:
    key: str
    label: str
    sales_sheet: str | None = None
    product_sheets: tuple[str, ...] = ()
    uses_bundled_site_mapping: bool = False
    site_mapping_virtual_sites: tuple[str, ...] = ()
    site_mapping_virtual_expansions: tuple[tuple[str, str], ...] = ()


_CHANNEL_ALIASES = {
    "th": CHANNEL_TH,
    "kingpowercn": CHANNEL_KINGPOWER_CN,
    "king_power_cn": CHANNEL_KINGPOWER_CN,
    "kpcn": CHANNEL_KINGPOWER_CN,
    "cn": CHANNEL_KINGPOWER_CN,
    "tht": CHANNEL_THT,
}


_CHANNEL_PROFILES = {
    CHANNEL_TH: ChannelProfile(
        key=CHANNEL_TH,
        label="TH",
        uses_bundled_site_mapping=True,
        site_mapping_virtual_sites=(
            "wh-bkk",
            "bkk-out",
            "dmk-out",
            "hkt-out",
            "cnx-out",
            "bs-hkt",
            "bs-cnx",
            "mjets-out",
        ),
    ),
    CHANNEL_KINGPOWER_CN: ChannelProfile(
        key=CHANNEL_KINGPOWER_CN,
        label="KingPowerCN",
        sales_sheet="WEB-CN",
        product_sheets=("click&collect", "HomeDelivery"),
        uses_bundled_site_mapping=True,
        site_mapping_virtual_sites=(
            "wh-bkk",
            "bkk-out",
            "dmk-out",
            "hkt-out",
            "cnx-out",
            "bs-hkt",
            "bs-cnx",
            "wh-bkk-delivery",
        ),
    ),
    CHANNEL_THT: ChannelProfile(
        key=CHANNEL_THT,
        label="THT",
        sales_sheet="CROSS-BORDER",
        product_sheets=("Cross-Border",),
        uses_bundled_site_mapping=True,
        site_mapping_virtual_sites=(
            "dmall-freezone",
            "dmall-online-wh",
            "jd-freezone",
            "jd-online-wh",
            "tht-freezone",
            "tht-online-wh",
            "wh-online-dmall",
            "wh-online-jd",
            "wh-online-tht",
            "wh-online-tiktok",
        ),
        site_mapping_virtual_expansions=(
            ("wh-online-dmall", "dmall-online-wh"),
            ("wh-online-jd", "jd-online-wh"),
        ),
    ),
}


def normalize_channel_key(value: object) -> str:
    raw = str(value or "").strip().lower().replace("-", "").replace(" ", "").replace("/", "")
    if raw not in _CHANNEL_ALIASES:
        supported = ", ".join(profile.label for profile in get_channel_profiles())
        msg = f"Unsupported channel {value!r}. Supported channels: {supported}"
        raise ValueError(msg)
    return _CHANNEL_ALIASES[raw]


def get_channel_profile(value: object) -> ChannelProfile:
    return _CHANNEL_PROFILES[normalize_channel_key(value)]


def get_channel_profiles() -> tuple[ChannelProfile, ...]:
    return tuple(_CHANNEL_PROFILES[key] for key in (CHANNEL_TH, CHANNEL_KINGPOWER_CN, CHANNEL_THT))


def get_required_upload_slots(value: object) -> tuple[str, ...]:
    profile = get_channel_profile(value)
    if profile.uses_bundled_site_mapping:
        return ("sales", "stock", "sku_live")
    return ("sales", "stock", "sku_live", "site_mapping")


def normalize_virtual_site(value: object) -> str:
    return str(value or "").strip().lower()


def get_site_mapping_virtual_sites(value: object) -> tuple[str, ...]:
    return get_channel_profile(value).site_mapping_virtual_sites


def get_site_mapping_virtual_expansions(value: object) -> tuple[tuple[str, str], ...]:
    return get_channel_profile(value).site_mapping_virtual_expansions
