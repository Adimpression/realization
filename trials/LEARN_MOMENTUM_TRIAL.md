# Momentum Learning Trial

The trial added [LEARN_MOMENTUM.md](LEARN_MOMENTUM.md) and tightened generic runtime selection in [main.py](main.py) so a learned `function_bit=1` artifact is preferred only when its full input contract is satisfied.

Fresh learning run:
```bash
set -a
source local.env >/dev/null 2>&1 || true
unset STATE_DB_URL STATE_DB_PORT STATE_DB_NAME STATE_DB_USER STATE_DB_PASSWORD
export LLM_PROVIDER=openai
export LLM_TIMEOUT_SECONDS=180
export STATE_SQLITE_PATH=state/momentum_learning_260323214829.sqlite3

python3 main.py markdown-learn \
  --markdown-file LEARN_MOMENTUM.md \
  --llm required \
  --max-artifacts 8 \
  --report-out reports/momentum_learning_260323214829_report.json \
  --state-out reports/momentum_learning_260323214829_state.json
```

That fresh DB is [momentum_learning_260323214829.sqlite3](state/momentum_learning_260323214829.sqlite3). The learn report is [momentum_learning_260323214829_report.json](reports/momentum_learning_260323214829_report.json). It learned 10 artifacts, including `artifact_ability-2-core-equation_35e317` with `function_bit=1`.

Validated CLI prompts on that fresh DB:
```bash
python3 main.py run --prompt 'Calculate momentum for mass=8 and velocity=12.' --llm off --max-steps 24
python3 main.py run --prompt 'Calculate momentum for mass=10 and velocity=5.' --llm off --max-steps 24
python3 main.py run --prompt 'What is the momentum when mass is 3 and velocity is 9?' --llm off --max-steps 24
```

Observed results:
- `96`
- `50`
- `27`

The saved probe states verify that the learned inline Python function was called:
- [momentum_learning_260323214829_probe_8_12_v2.json](reports/momentum_learning_260323214829_probe_8_12_v2.json)
- [momentum_learning_260323214829_probe_10_5_v2.json](reports/momentum_learning_260323214829_probe_10_5_v2.json)
- [momentum_learning_260323214829_probe_3_9_v2.json](reports/momentum_learning_260323214829_probe_3_9_v2.json)

In those state files, the evidence context shows:
- `artifact_id = artifact_ability-2-core-equation_35e317`
- `function_bit = 1`
- `cross_boundary_execution = true`

Regression check:
```bash
python3 -m unittest tests.test_markdown_learning
```
Result: `Ran 6 tests in 120.885s` and `OK`.

One limitation remains: the validated path uses `mass` and `velocity` phrasing. Broader aliasing such as `speed` is a separate robustness issue.
