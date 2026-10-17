# Learning Contracts (draft)

This is the **planned shared data contract** for `learning-platform` and independent content producers such as `java-learning`. Canonical source repository: `https://github.com/phuongnguyenit93/learning-contract`. The working directory `learning-platform/learning-contracts/` is linked to that repository as a Git submodule, rather than copied into the frontend's Git history.

**Status: draft only.** Nothing in this folder is wired into `npm run build`, Gradle, CI/CD, GitHub Releases, or production policy enforcement. Creating/editing a schema does not change producer outputs or frontend TypeScript interfaces automatically.

## Goals and ownership

- `learning-platform` owns the common **published wire format** and decides which contract versions it can read.
- Each producer owns its source content, technology-specific tooling, transformation logic and ability to emit a supported format.
- The contract is technology-neutral: `java`, `javascript`, `nodejs`, etc. are **dataset/programming-language identifiers**, while `vi`, `en` and future locales are **content languages**. They are independent concepts.
- Optional capabilities stay optional. A documentation-only module does not need API Docs, executable source code, Java package information or a quiz.
- Java-only `master.json`, `properties.json`, source YAML skeleton comments, Gradle tasks and frontend React component state are **not** shared contracts.

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
| `schemas/reference.schema.json` | References YAML, validated *after parsing* |
| `schemas/api-docs.schema.json` | Optional API Docs JSON |
| `schemas/manifest.schema.json` | Dataset ZIP `manifest.json` |
| `policy/compatibility.json` | Dynamic publish/read support policy (currently `DRAFT`) |
| `policy/compatibility.schema.json` | Rules for the policy document itself |

All schema files use JSON Schema **Draft 2020-12**. External `$ref` paths are relative to the schema file (`./common.schema.json`). The schemas are designed against the Java publisher's **current emitted shapes** and existing `src/types/learning.ts`; they do not intentionally introduce new required feature fields. A future integration must additionally test complete generated datasets, cross-file links, counts, unique IDs and URL restrictions; JSON Schema alone cannot guarantee all those relations.

The current JSON/YAML documents have their own wire-format values such as `version: 1` or `schemaVersion: 1`. **Do not confuse** those integers (or embedded Quiz/Interview YAML comment versions) with the shared semantic contract version `1.0.0`. A future release can add `contractVersion` to the archive manifest; it is **optional in this draft** so existing Java archives are not rejected.

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
