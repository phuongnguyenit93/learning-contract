# Learning Contracts (draft)

This is the **planned shared data contract** for `learning-platform` and independent content producers such as `java-learning`. Canonical source repository: `https://github.com/phuongnguyenit93/learning-contract`. The working directory `learning-platform/learning-contracts/` is linked to that repository as a Git submodule, rather than copied into the frontend's Git history.

**Status: draft only.** Nothing in this folder is wired into `npm run build`, Gradle, CI/CD, GitHub Releases, or production policy enforcement. Creating/editing a schema does not change producer outputs or frontend TypeScript interfaces automatically.

## Goals and ownership

- `learning-platform` owns the common **published wire format** and decides which contract versions it can read.
- Each producer owns its source content, technology-specific tooling, transformation logic and ability to emit a supported format.
- The contract is technology-neutral: `java`, `javascript`, `nodejs`, etc. are **dataset/programming-language identifiers**, while `vi`, `en` and future locales are **content languages**. They are independent concepts.
- Optional capabilities stay optional. A documentation-only module does not need API Docs, executable source code, Java package information or a quiz.
- Java-only `master.json`, `properties.json`, source YAML skeleton comments, Gradle tasks and frontend React component state are **not** shared contracts.

## Repository access and publishing ownership

**Single writer, multiple readers:** `learning-platform` is the sole project authorized to propose and publish changes to this shared contract. `java-learning` and all future language/learning consumers must **fetch, pull, or download only**. They must not edit or push to `learning-contract`, and must not automatically open write-capable credentials for this repository in their CI workflows.

The rule above describes **project ownership**, not a feature that `.gitmodules` or Git remote URLs enforce. GitHub grants push access to authenticated **users, apps, and keys** (not to a source checkout's parent repository). A developer using the same GitHub account with write access in both `learning-platform` and `java-learning` can technically push from either working directory. Git configuration, a `pre-push` hook, or `branch = main` does **not** create a security boundary.

Recommended access model:

1. Keep write permission to `learning-contract` restricted to the platform maintainer identity and, if automatic publishing is needed, a dedicated GitHub App granted **Contents: write** only for the contract repository.
2. Consumer CI uses `permissions: contents: read` on its own repository and the public GitHub contract URL without a credential (or a dedicated **read-only** GitHub App/deploy key for private contracts). Do **not** supply it with the maintainer PAT or a write-enabled deploy key.
3. Do not add consumer developers/bots as collaborators with write access to `learning-contract`. Optional GitHub branch rulesets can restrict updates and force pushes; a write restriction requires a deliberately designated bypass actor, not a repository folder name.
4. For strict technical separation even when the projects share a computer, publish via a **dedicated platform GitHub App identity** and configure repository rules to allow only that publishing identity. The owner/admin still controls the repository's security settings. This has **not** been provisioned.

For consumer checkouts, a normal HTTPS submodule URL is enough for pulling a public repository. Consumers should pin to a specific submodule commit or released contract version; they must not silently track the latest `main` in builds.

## Files

| File | Payload / purpose |
| --- | --- |
| `contract.json` | Draft semantic contract version and directory of document schemas |
| `schemas/common.schema.json` | Shared definitions such as locale, difficulty and Knowledge/API relations |
| `schemas/module-catalog.schema.json` | Producer `module-catalog.json` tree |
| `schemas/knowledge.schema.json` | Knowledge `index.json` and section links |
| `schemas/knowledge-search.schema.json` | Per-locale search indexes |
| `schemas/roadmap.schema.json` | Roadmap YAML, validated *after parsing* |
| `schemas/video-index.schema.json` | Video index and script links |
| `schemas/video-script.schema.json` | Video scenes and transitions |
| `schemas/quiz.schema.json` | Quiz YAML, validated *after parsing* |
| `schemas/interview.schema.json` | Interview YAML, validated *after parsing* |
| `schemas/summary-questions.schema.json` | Independent chapter Summary Questions YAML (`questions[]`, question/answer only) |
| `schemas/reference.schema.json` | References YAML, validated *after parsing* |
| `schemas/api-docs.schema.json` | Optional API Docs JSON |
| `schemas/manifest.schema.json` | Dataset ZIP `manifest.json` |
| `policy/compatibility.json` | Dynamic publish/read support policy (currently `DRAFT`) |
| `policy/compatibility.schema.json` | Rules for the policy document itself |

All schema files use JSON Schema **Draft 2020-12**. External `$ref` paths are relative to the schema file (`./common.schema.json`). The schemas are designed against the Java publisher's **current emitted shapes** and existing `src/types/learning.ts`; they do not intentionally introduce new required feature fields. A future integration must additionally test complete generated datasets, cross-file links, counts, unique IDs and URL restrictions; JSON Schema alone cannot guarantee all those relations.

The current JSON/YAML documents have their own wire-format values such as `version: 1` or `schemaVersion: 1`. **Do not confuse** those integers (or embedded Quiz/Interview YAML comment versions) with the shared semantic contract version `1.0.0`. A future release can add `contractVersion` to the archive manifest; it is **optional in this draft** so existing Java archives are not rejected.

## Schema-driven YAML authoring (draft)

The shared JSON Schemas are the **source of truth for the payload shape** of Quiz, Interview and Roadmap. A producer may parse a schema to generate a YAML skeleton and comments, then parse the completed YAML back into data to validate it with JSON Schema Draft 2020-12.

- Standard `type`, `required`, `enum`, `pattern`, `minItems`, `maxItems`, `contains` and `minContains`/`maxContains` are **actual validation constraints**. In particular, Quiz must contain exactly four answers and each of the four answer IDs A/B/C/D exactly once, regardless of ordering.
- Standard `description` is the canonical English explanation. `x-description: { "vi": "...", "en": "..." }`, `x-title` and `x-labels` are **custom annotations** for bilingual YAML comments, headings and labels; they do not influence JSON Schema validation.
- Standard `default` provides **authoring hints only**. A validator does not automatically fill missing fields. Values such as `question: ""`, `correctAnswerId: ""` or `answers: []` are intentional *draft placeholders* and **must be replaced before publishing**. Their defaults are not necessarily themselves valid against final constraints. Producers should create these fields explicitly rather than silently fixing submissions.
- `x-uniqueBy: "id"` is a **custom business rule marker** for producers (for example, unique Quiz question IDs and Roadmap milestone IDs). It is **not enforced by a standard JSON Schema validator**; producer-specific business validation must enforce it. Quiz answer-ID uniqueness is separately enforced with standard JSON Schema `contains` constraints.
- `x-guidance` on Roadmap preserves bilingual content-generation principles and the thinking framework from the former Java `roadmap-schema.yml`. This metadata guides authoring but does not constrain payload structure.
- Shared `readmeRelation` and `apiRelation` permit either two empty strings (no link) or two populated strings. The schemas can reject half-filled pairs, but checking whether the referenced Knowledge anchor or API method **actually exists** is business validation outside JSON Schema.
- Schema authoring enhancements are **not yet consumed by Java generators**. The original Java YAML schema resources must remain in place until a tested migration switches generation and internal validation to these JSON Schemas.

For an optional audit of the existing Java-generated Quiz, Interview and Roadmap payloads (requires Python, `jsonschema` and `PyYAML`):

```bash
python -m pip install jsonschema PyYAML
python tests/validate_java_generated.py --data-dir ../../java-learning/build/learning-data/java
```

The audit does not modify either repository or validate additional document kinds. Once Gradle/CI validation is integrated, pin the Git submodule commit and run a compatible schema snapshot against the final generated output.

## Version policy

`policy/compatibility.json` represents a **mutable policy**, separate from an immutable versioned schema archive. Its keys mean:

| Field | Meaning |
| --- | --- |
| `enforcement` | `DRAFT` is documentation only; `ENFORCED` is reserved for a future running policy checker |
| `targetVersion` | Version producers are encouraged to adopt; not necessarily the minimum accepted version |
| `versions.<version>.status` | Human-facing `ACTIVE`, `DEPRECATED`, `FORBIDDEN`, `RETIRED` |
| `allowPublish` | Whether new datasets may be published using this version |
| `allowRead` | Whether the platform may continue reading datasets with this version |
| `message` / `replacement` | Migration guidance and optional replacement version |

Suggested lifecycle:

1. **ACTIVE:** `allowPublish=true`, `allowRead=true`.
2. **DEPRECATED:** `allowPublish=true`, `allowRead=true`; warn producers to upgrade.
3. **FORBIDDEN:** `allowPublish=false`, `allowRead=true`; reject **new** publications but keep existing data working during migration.
4. **RETIRED:** `allowPublish=false`, `allowRead=false`; only after the platform can safely retire or migrate all existing data.

For example, when `1.1.0` is ready, publish a new versioned artifact and update policy's `targetVersion` to `1.1.0`, while leaving `1.0.0` as `DEPRECATED` with `allowRead=true` and `allowPublish=true`. Producers may migrate independently. A policy change **does not** rewrite or migrate any files; a compatibility adapter or generator change is still required for breaking changes.

**Safety rule:** `FORBIDDEN` for publishing must not automatically mean `RETIRED` for reading. Before changing policy, the platform must actually support the versions it marks readable. A release/build gate must fail closed when a required fresh policy check is unavailable; local checks may use cached policy and warn about staleness.

## Planned integration (NOT implemented)

1. Publish the **current** `schemas/` and `contract.json` as an immutable version-tagged GitHub Release ZIP with a checksum. The source tree continues to have just **one** current `schemas/` directory; old snapshots live in tags/Releases, not `schemas/v1.0/`, `schemas/v1.1/`, etc.
2. Producer Gradle/npm/Python build tooling pins a version, downloads/verifies/caches it, and can optionally use a local folder override for development. Checking the current policy is separate from downloading a pinned schema.
3. Each producer validates generated output against the pinned schema **locally** before publishing. CI must check current policy again immediately before publishing, rather than relying on an old local cache.
4. `learning-platform` validates downloaded datasets and uses a compatible reader/adapter for any still-readable older version before deploying them. TypeScript types may eventually be generated from this contract instead of maintained by hand.
5. Add real schema validation tests against generated Java assets before enabling any enforcement. The initial schemas are a reviewed **starting point**, not proof that all data or future producers already conform.

## Editing from learning-platform

Once `learning-platform` commits its `.gitmodules` and submodule pointer, a fresh clone should use `git clone --recurse-submodules` (or `git submodule update --init --recursive` after cloning). The submodule is a **separate repository**. To publish schema edits, run `git -C learning-contracts add .`, `git -C learning-contracts commit -m "..."` and `git -C learning-contracts push`. Then commit the updated submodule pointer in `learning-platform` if the frontend should track that revision.

**The Git repository is not yet a schema distribution channel.** A versioned Release ZIP, Gradle/npm dependency download, runtime validation and production policy enforcement remain future work. Git submodule checkout only manages source collaboration; it does not automatically fetch the latest schema on every build.
