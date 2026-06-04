# Technical Specification v0.4 â€” Implementation-Contract Edition

This fixture is deliberately dirty. The original RCGov drafts carried a literal
mojibake sequence where an em dash belonged (UTF-8 em dash mis-decoded as
cp1252). RCGov cleans encoding on ingest, so the dirty form only survives here as
a test fixture for the `encoding_mojibake` conflict type.

Version 0.1 â€” Implementation Baseline

The userâ€™s latest instruction should not override a durable constraint merely
because it is newer.
