# agents/ — Model roles, prompts, and routing

The project is deliberately **not** built around one AI provider. Work is described
by *role*; which model fills a role is configuration, not architecture.

## Subfolders

| Folder     | Contents                                                          |
| ---------- | ----------------------------------------------------------------- |
| `roles/`   | One definition per role: purpose, inputs, outputs, quality bar     |
| `prompts/` | Versioned prompt templates, one file per prompt                    |
| `routing/` | Routing rules and fallback order                                   |

## Roles

| Role              | Purpose                                                        |
| ----------------- | -------------------------------------------------------------- |
| `BULK_RESEARCH`   | High-volume ingestion of transcripts, pages, and papers         |
| `CLASSIFICATION`  | Assign subject / topic / subtopic / question family            |
| `SUMMARIZATION`   | Condense long sources without losing provenance                 |
| `DEEP_REASONING`  | Derive methods, build recognition decision trees                |
| `CODE_GENERATION` | Write project code                                              |
| `CODE_REVIEW`     | Review code written by a different model                        |
| `VERIFICATION`    | Independently check a claim produced by another model            |
| `ARBITRATION`     | Decide between two models that disagree                         |

## Hard rules

- **The model that produced an output may never verify it.** `VERIFICATION` and
  `CODE_REVIEW` must be filled by a different provider than the author.
- `ARBITRATION` must differ from both disputing parties where a third provider is
  available; where it is not, the dispute stays `DISPUTED` and is escalated to the
  user rather than silently resolved.
- Live role→model assignments live in `config/model_routing.json`, not in code and
  not in prompts.
- Prompts are versioned files. Never edit a prompt in place once it has produced
  knowledge that is stored in the repository — add `v2` so past output stays
  explainable.
