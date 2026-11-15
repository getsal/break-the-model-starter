# Current State

## Active Task
ORCA-0 architecture and trust-boundary register.

## Current Status
Created `orca/ORCA-0-architecture.md` from the v2 plan and client-visible repository behavior. It separates verified client contract, documentation claims, hypotheses, and unknown internals. No external Riley or Supabase access occurred.

## Next Action
Review/commit the ORCA-0 document and continue with the separately authorized implementation tasks.

## Blockers
Track C authorization and scope are unconfirmed. Riley server internals and Supabase private schema permissions are unknown. Orca delegation was not requested for this task.

## Relevant Files
- docs/Orca Implementation Plan v2.md
- orca/ORCA-0-architecture.md
- btm.py

## Handover Note
The architecture register documents client-visible facts only. Do not treat the client contract as proof of server internals.
