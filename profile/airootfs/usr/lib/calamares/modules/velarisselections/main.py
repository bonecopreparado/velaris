"""Persist Velaris packagechooser selections inside the installed system."""

from __future__ import annotations

import os

import libcalamares


CHOICES = {
    "kernel": {"bore-lto", "cachyos", "lts", "arch"},
    "graphics": {"nvidia-open", "nouveau", "amd", "intel", "virtual", "universal"},
    "profile": {"balanced", "performance", "powersave"},
}


def _selection(kind: str) -> str | None:
    value = libcalamares.globalstorage.value(f"packagechooser_{kind}")
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    if isinstance(value, dict):
        value = value.get("id") or value.get("value") or value.get("selected")
    return value if isinstance(value, str) else None


def run():
    root = libcalamares.globalstorage.value("rootMountPoint")
    if not isinstance(root, str) or not root:
        return ("Velaris selection error", "The installation target is not mounted.")

    destination = os.path.join(root, "etc", "velaris", "installer")
    os.makedirs(destination, mode=0o755, exist_ok=True)

    for kind, allowed in CHOICES.items():
        value = _selection(kind)
        if value not in allowed:
            return (
                "Velaris selection error",
                f"Calamares returned an invalid {kind} selection: {value!r}",
            )

        path = os.path.join(destination, kind)
        temporary = f"{path}.tmp"
        with open(temporary, "w", encoding="utf-8") as output:
            output.write(f"{value}\n")
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)

    return None
