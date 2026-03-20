from __future__ import annotations

from typing import Any, Mapping, MutableMapping

from channel_profiles import CHANNEL_TH, get_channel_profile, normalize_channel_key

SELECTED_CHANNEL_KEY = "selected_channel_key"
SELECTED_CHANNEL_WIDGET_KEY = "selected_channel_widget"


def ensure_selected_channel(state: MutableMapping[str, Any]) -> str:
    existing = state.get(SELECTED_CHANNEL_KEY, CHANNEL_TH)
    channel_key = normalize_channel_key(existing)
    state[SELECTED_CHANNEL_KEY] = channel_key
    return channel_key


def get_selected_channel(state: Mapping[str, Any]) -> str:
    return normalize_channel_key(state.get(SELECTED_CHANNEL_KEY, CHANNEL_TH))


def set_selected_channel(state: MutableMapping[str, Any], value: object) -> str:
    channel_key = normalize_channel_key(value)
    state[SELECTED_CHANNEL_KEY] = channel_key
    return channel_key


def sync_selected_channel_widget(state: MutableMapping[str, Any]) -> str:
    widget_value = state.get(SELECTED_CHANNEL_WIDGET_KEY)
    if widget_value is None:
        state[SELECTED_CHANNEL_WIDGET_KEY] = get_selected_channel(state)
        return get_selected_channel(state)
    channel_key = normalize_channel_key(widget_value)
    state[SELECTED_CHANNEL_KEY] = channel_key
    state[SELECTED_CHANNEL_WIDGET_KEY] = channel_key
    return channel_key


def get_selected_channel_label(state: Mapping[str, Any]) -> str:
    return get_channel_profile(get_selected_channel(state)).label
