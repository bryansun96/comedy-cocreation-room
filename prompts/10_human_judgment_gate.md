# Human Judgment Gate Prompt

## Purpose
Based on the feedback just generated, surface 3–4 judgment calls that must stay
with the human creative team. These are decisions the AI cannot resolve because
they depend on taste, rehearsal experience, or creative intention.

## Critical Rules
- Be specific: reference the actual premise, critique findings, or next moves
- Not generic: never write "humor is subjective" or "only creators can decide"
- Each item should name a real decision the team is facing right now
- Do not repeat problems already diagnosed — flag the judgment call, not the diagnosis

## Four Judgment Categories to Cover
1. A call only performers can make after running the material once
2. A structural or tonal choice with no objectively correct answer
3. Something that depends on the team's creative voice AI cannot read
4. Something that requires audience reaction before a decision can be made

## Output Format
Return JSON with exactly 3–4 items:
{"items": ["具体判断提醒 1", "具体判断提醒 2", "具体判断提醒 3"]}
