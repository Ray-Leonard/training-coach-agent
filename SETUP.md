# SETUP.md — Existing Agent Installation Protocol

> ⚠️ **WORK IN PROGRESS — NOT READY FOR UNATTENDED DEPLOYMENT**
>
> This document is for the user's existing, non-Training-Coach Agent. It describes
> Phase 0 and Phase 0.5 only. Modules 3–5 may support daily use, but the full project
> remains under active development and is not medical advice.

## Scope and handoff

The existing host Agent reads this document after the user provides the repository URL.
It installs a separate Training Coach Agent Profile and then hands control to that
profile. The installed Training Coach runtime does **not** read `SETUP.md`; its runtime
rules are in `AGENTS.md`, the active profile's `SOUL.md`, and the skill needed for the
current request.

The installation phases are deliberately separate from Fitness User Onboarding:

- **Phase 0 — Agent Profile Installation:** clone the repository, create and configure
  the dedicated Agent Profile, choose the communication language, and install the
  runtime Soul.
- **Phase 0.5 — Profile Handoff & Gateway Setup:** invite the user to switch to the
  new profile and set up its gateway. Stop after this handoff.
- **Phase 1 — User Onboarding & Fitness Profile Creation:** performed later by the
  Training Coach runtime after the user has switched profiles. It creates
  `data/user/profile.json` and is documented by `AGENTS.md` and the
  `user-profile-management` skill, not by this file.

Do not perform Phase 1 during installation. In particular, do not ask for or write
body measurements, weight, body-fat, goals, TDEE, macros, diet records, or training
records.

## Phase 0 — Agent Profile Installation

### 1. Accept and clone the repository

The user supplies the repository URL. Preserve the URL exactly, confirm the intended
local destination, and clone it into a workspace that is not another project's data
folder. Verify that the clone contains `AGENTS.md`, this `SETUP.md`, the `skills/`
directory, and `coach-agent-profile/` before continuing.

Do not read or import runtime data while installing. The repository's `data/` tree is
for the installed coach's future runtime and must remain free of personal data during
this phase.

### 2. Create the dedicated Agent Profile

For Hermes, create and inspect a dedicated profile rather than modifying the user's
existing profile:

```bash
hermes profile create trainingcoach --description "Private modular fitness coach"
hermes profile show trainingcoach
```

If the profile already exists, inspect it and ask the user before reusing or changing
it. Never silently overwrite an existing profile's Soul, configuration, credentials,
or gateway settings.

### 3. Configure the profile for this repository

Find the absolute path of the clone. Do not copy the placeholder path literally:

```bash
cd /path/to/your/cloned/training-coach-agent
REPO_DIR="$(pwd)"
printf '%s\n' "$REPO_DIR"
```

In `hermes config edit`, merge the relevant settings from
`coach-agent-profile/config.reference.yaml`, replacing every path placeholder with
that actual clone path:

```yaml
terminal:
  cwd: /your/actual/clone/path/training-coach-agent

skills:
  external_dirs:
    - /your/actual/clone/path/training-coach-agent/skills
```

Keep provider credentials in the host's secure profile or environment. Never copy
passwords, API keys, tokens, or private keys into the repository.

### 4. Choose the runtime communication language

Ask the user which language the Training Coach should use for normal communication.
The runtime is language-agnostic and the user may choose any language. The repository
contains read-only examples that can guide translation:

- `coach-agent-profile/SOUL.example.md` — canonical English example;
- `coach-agent-profile/SOUL.zh-CN.example.md` — reviewed Simplified Chinese example.

These `*.example.md` files are templates only. They are never the runtime Soul and
must not be modified, overwritten, or committed with the user's language preference.

After the user confirms the language:

1. Read the complete English example as the source of truth.
2. Use a reviewed localized example as a translation aid when available.
3. Otherwise translate the complete example while preserving its safety boundaries,
   principles, language rule, and calibration examples.
4. Write the finalized selected-language Soul **directly to the new Agent Profile's
   runtime `SOUL.md`**. For a Hermes named profile, this is typically:

   ```text
   ~/.hermes/profiles/trainingcoach/SOUL.md
   ```

5. Ensure the installed Soul says that normal replies use the selected language until
   the user explicitly asks to switch.

The repository examples remain read-only. Do not create a runtime `SOUL.md` inside
`coach-agent-profile/` and do not write the user's language choice into Git.

### 5. Verify the installation

Before handoff, verify all of the following:

- the dedicated Agent Profile exists;
- its repository/workspace and external skills paths point to this clone;
- its runtime `SOUL.md` exists and contains the finalized selected-language Soul;
- the repository's `*.example.md` files are unchanged;
- `data/user/profile.json` has not been created or populated;
- no body, goal, nutrition, or training record was created;
- the existing user profile's credentials and gateway were not modified.

If the active runtime Soul is missing, stop and report incomplete Agent Profile
Installation. Do not use the repository examples as a runtime fallback after handoff.

## Phase 0.5 — Profile Handoff & Gateway Setup

Once verification passes, tell the user:

```text
The Training Coach Agent Profile is installed.

Please switch to the new `trainingcoach` profile and start a new conversation there.
Then complete gateway setup for that profile. After switching, say:
“Start my fitness onboarding.”
```

The existing host Agent must not claim that it has switched profiles or completed the
gateway setup. The user must perform or approve those actions in the appropriate host
UI/CLI. Do not begin Fitness User Onboarding in the installation session.

After the user switches to the new profile, the Training Coach runtime follows
`AGENTS.md`. It does not read this file again as part of normal operation.

## Installation boundary

At the end of Phase 0.5:

- Agent Profile Installation is complete;
- profile handoff and gateway setup have been invited or completed by the user;
- the Training Coach runtime is ready to start Phase 1;
- Fitness User Onboarding has **not** started;
- `data/user/profile.json` does **not** need to exist yet.

## Rollback and safety

If installation fails, report the exact failed step and leave the user's existing
profile untouched. Do not delete profiles, repositories, credentials, or gateway
settings as an automatic rollback. The user can remove an incomplete dedicated profile
manually after reviewing what was created.
