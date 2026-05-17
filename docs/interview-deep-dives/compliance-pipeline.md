# Compliance Pipeline Deep Dive

Outbound bot responses pass through a staged compliance pipeline before delivery. The main entry points are `ghl_real_estate_ai/services/jorge/response_pipeline/pipeline.py` and `factory.py`.

## What To Inspect

- Stage ordering in `create_default_pipeline()`.
- Short-circuit behavior for TCPA opt-out handling.
- FHA/RESPA checks before message delivery.
- SMS truncation after safety and language processing.
- `tests/test_response_pipeline.py`, which is part of `make verify-focused`.

## Backend Judgment Signal

The pipeline keeps independent concerns composable: language mirroring, opt-out handling, conversation repair, compliance enforcement, disclosure behavior, translation, and SMS length. This is more maintainable than burying all safety behavior inside a prompt.
