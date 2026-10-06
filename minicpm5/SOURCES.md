# MiniCPM5: source, architecture and interface notes

Source snapshot checked October 2026. Separate publisher claims, local configured-run results and untested capabilities.

## Exact final checkpoints

| Model | Revision | Total parameters | Text layers |
|---|---|---:|---:|
| `openbmb/MiniCPM5-1B` | `87179e5c1f455ef22e6223592d2d61351b525bfc` | 1,080,632,832 | 24 |
| `openbmb/MiniCPM5-2B` | `f97400052a43d642bbc6e9975e2397e3ae6a6b52` | 2,516,756,480 | 42 |

[1B model card](https://huggingface.co/openbmb/MiniCPM5-1B/blob/87179e5c1f455ef22e6223592d2d61351b525bfc/README.md), [2B model card](https://huggingface.co/openbmb/MiniCPM5-2B/blob/f97400052a43d642bbc6e9975e2397e3ae6a6b52/README.md).

Both are dense text-only `LlamaForCausalLM` architectures with 16 query heads, two key/value heads and 131,072 configured context positions. That architecture name does not mean Meta trained these checkpoints. The 2B name approximately reflects its 1.982B non-embedding parameters; all weights still occupy storage. Runtime memory additionally includes cache and software overhead. These are distinct from MiniCPM-V vision releases.

Final releases include reinforcement learning and on-policy distillation after earlier training stages. Base, Midtrain and SFT checkpoints are not interchangeable with the final assistant. The 2B card describes 16 expert teachers, including five agent specialists; they are training resources, not 16 models that must run beside the final checkpoint. Its reported gains of 10.96 reasoning/general points and 6.96 agent points apply to the publisher's selected evaluations, not every task.

## Supported generation modes

[Pinned official deployment guidance](https://github.com/OpenBMB/MiniCPM/blob/316cfb1cea39f39cfa16b4f5703b77495c2340be/docs/deployment/transformers.md):

- 1B thinking: temperature 0.9, top-p 0.95.
- 1B nonthinking: temperature 0.7, top-p 0.95.
- 2B thinking: temperature 1.0, top-p 0.95; the only officially supported mode in this guidance.

Using model-recommended settings is not a comparison with every sampling parameter held identical. Record output budgets, sampled seeds, retries and truncation separately. Short synthetic checks do not establish broad accuracy or calibrated confidence.

## Native tool interface

[1B template](https://huggingface.co/openbmb/MiniCPM5-1B/blob/87179e5c1f455ef22e6223592d2d61351b525bfc/chat_template.jinja), [2B template](https://huggingface.co/openbmb/MiniCPM5-2B/blob/f97400052a43d642bbc6e9975e2397e3ae6a6b52/chat_template.jinja), [official parser](https://github.com/OpenBMB/MiniCPM/blob/316cfb1cea39f39cfa16b4f5703b77495c2340be/tool_parsers/minicpm5xml_tool_parser.py).

Pass function definitions through `tools=` using OpenAI-style function schemas. Native calls use XML function/param blocks. Preserve special tokens while decoding: the tokenizer marks function and parameter delimiters as special, so `skip_special_tokens=True` removes them. Tokenize a rendered native template with `add_special_tokens=False`, or obtain token IDs directly from the template, to avoid a duplicate beginning-of-sequence token.

Replay assistant calls with dictionary-valued `function.arguments` when using this local Jinja template. Append tool results with `role="tool"`; the template supplies its own result wrapper. Keep reasoning separate from executable calls. Validate complete calls, allowed function names, argument types and required fields before executing a tool. A model proposing a call does not execute that operation itself.

A prose prompt requiring a custom JSON object tests that prompted interface, not native tool calling. Report JSON syntax, schema agreement, semantic correctness and task completion separately. If a checker expects nested arguments that the prompt did not explicitly specify, disclose that ambiguity rather than presenting it as an unsafe action. Any native control should be versioned separately from such custom-format results.

## License and dates

The model cards expressly release code and weights under Apache 2.0; [repository license](https://github.com/OpenBMB/MiniCPM/blob/316cfb1cea39f39cfa16b4f5703b77495c2340be/LICENSE). Preserve relevant notices in redistributed code.

The [official changelog](https://github.com/OpenBMB/MiniCPM/blob/316cfb1cea39f39cfa16b4f5703b77495c2340be/README.md) lists 1B in May 2026 and 2B in September 2026. These are not new October releases. The generic linked technical report for MiniCPM4 should not be labeled a dedicated MiniCPM5 paper. A training diagram's 512K stage is not the released 128K inference configuration.
