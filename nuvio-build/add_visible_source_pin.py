#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()


def path(rel):
    return root / rel


def read(rel):
    return path(rel).read_text(encoding="utf-8")


def write(rel, text):
    target = path(rel)
    target.write_text(text, encoding="utf-8")


def replace_once(rel, old, new):
    text = read(rel)
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Patch anchor count for {rel} was {count}, expected 1: {old[:140]!r}")
    write(rel, text.replace(old, new, 1))


# Add a compact, explicit pin button to each source card. Nothing about stream
# selection changes: tapping the card still plays it, and the existing long press
# behavior remains available.
replace_once(
    "composeApp/src/commonMain/kotlin/com/nuvio/app/features/streams/StreamCard.kt",
    "import androidx.compose.material3.Text\n",
    "import androidx.compose.material3.Text\nimport androidx.compose.material3.TextButton\n",
)

replace_once(
    "composeApp/src/commonMain/kotlin/com/nuvio/app/features/streams/StreamCard.kt",
    "    currentLabel: String? = null,\n    statusLabel: String? = null,\n) {\n",
    "    currentLabel: String? = null,\n    statusLabel: String? = null,\n    pinActionLabel: String? = null,\n    onPinActionClick: (() -> Unit)? = null,\n) {\n",
)

replace_once(
    "composeApp/src/commonMain/kotlin/com/nuvio/app/features/streams/StreamCard.kt",
    "        if (showAddonLogo) {\n",
    "        if (!pinActionLabel.isNullOrBlank()) {\n            TextButton(\n                onClick = { onPinActionClick?.invoke() },\n                enabled = onPinActionClick != null,\n            ) {\n                Text(text = pinActionLabel.orEmpty())\n            }\n            Spacer(modifier = Modifier.width(4.dp))\n        }\n\n        if (showAddonLogo) {\n",
)

# Thread the visible action through PlayerStreamList without changing the existing
# source click or long press callbacks.
replace_once(
    "composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerStreamList.kt",
    "    statusLabelForStream: ((StreamItem) -> String?)? = null,\n    onStreamLongClick: ((StreamItem) -> Unit)? = null,\n) {\n",
    "    statusLabelForStream: ((StreamItem) -> String?)? = null,\n    pinActionLabelForStream: ((StreamItem) -> String?)? = null,\n    onPinActionClick: ((StreamItem) -> Unit)? = null,\n    onStreamLongClick: ((StreamItem) -> Unit)? = null,\n) {\n",
)

replace_once(
    "composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerStreamList.kt",
    "                        statusLabel = statusLabelForStream?.invoke(stream),\n                        onClick = { onStreamSelected(stream) },\n                        onLongClick = onStreamLongClick?.let { callback -> { callback(stream) } },\n",
    "                        statusLabel = statusLabelForStream?.invoke(stream),\n                        pinActionLabel = pinActionLabelForStream?.invoke(stream),\n                        onPinActionClick = onPinActionClick?.let { callback -> { callback(stream) } },\n                        onClick = { onStreamSelected(stream) },\n                        onLongClick = onStreamLongClick?.let { callback -> { callback(stream) } },\n",
)

# Expose Pin/Unpin directly on each source row. The underlying per-season pinning
# repository and fallback behavior are unchanged.
replace_once(
    "composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerSourcesPanel.kt",
    "                onStreamLongClick = { stream ->\n                    val season = currentSeason\n                    if (season != null) {\n                        val pinned = PersistentPlaybackRepository.toggleSeasonPin(parentMetaId, season, stream)\n                        NuvioToastController.show(\n                            if (pinned) \"Pinned for Season $season\" else \"Source unpinned for Season $season\",\n                        )\n                    }\n                },\n",
    "                pinActionLabelForStream = { stream ->\n                    val season = currentSeason\n                    when {\n                        season == null -> null\n                        seasonPin != null && stream.matchesPersistentPin(seasonPin) -> \"Unpin S$season\"\n                        else -> \"Pin S$season\"\n                    }\n                },\n                onPinActionClick = { stream ->\n                    val season = currentSeason\n                    if (season != null) {\n                        val pinned = PersistentPlaybackRepository.toggleSeasonPin(parentMetaId, season, stream)\n                        NuvioToastController.show(\n                            if (pinned) \"Pinned for Season $season\" else \"Source unpinned for Season $season\",\n                        )\n                    }\n                },\n                onStreamLongClick = { stream ->\n                    val season = currentSeason\n                    if (season != null) {\n                        val pinned = PersistentPlaybackRepository.toggleSeasonPin(parentMetaId, season, stream)\n                        NuvioToastController.show(\n                            if (pinned) \"Pinned for Season $season\" else \"Source unpinned for Season $season\",\n                        )\n                    }\n                },\n",
)

print("Added visible per-season source pin control")
