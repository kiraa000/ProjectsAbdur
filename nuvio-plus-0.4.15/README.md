# Nuvio Plus 0.4.15 source anchor

This branch is reserved for the source-only Nuvio Plus rebase.

Exact upstream base: `luqmanfadlli/NuvioMobile-Enhanced` release `0.4.15`

Pinned upstream commit: `655e8766f304f196e6c5860e16eef9cc9cdc65e9`

Verified complete Nuvio Plus patch SHA256: `72b0fa4191a49864f1d95163bf9eae3018decbfd60f635d04686dab7c26b5b4a`

The rebase preserves Enhanced 0.4.15 behavior in overlapping files while retaining Nuvio Plus persistent title settings, season-scoped pins, current-source Next Episode continuity, 85% prefetch, and actual-played-time 15% pin proof.

No APK, Gradle compile/build, installation, or GitHub Actions build was run for this rebase.

The existing `nuvio-enhanced-custom` build branch was intentionally left untouched because changes under `nuvio-build/**` on that branch trigger the Android build workflow.