# Packaging Status

Packaging, signing, notarization, and installer creation are intentionally deferred. The current restructuring provides the source boundaries and build handoffs needed for that work.

Use `npm run build:screensaver` to validate the offline browser runtime only. Platform wrapper and release artifact commands remain available for the later packaging phase.