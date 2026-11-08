# fp-control — Design advisor

How to ask "why" and offer architectural observations during a count, without distorting it. Read this at Step 1 (before asking about the boundary) and again at Step 7 (before the summary). Enhancement sessions use it too, at Step E8.

The aim is to make the user's reasoning visible and to point out what the count reveals about the design. It is not to enforce a style. The user knows their constraints; you know what function point counts tend to reveal. Offer the second as input to the first.

## The one rule: advice never changes a count

Function points measure what the user needs the system to do, from the user's point of view, regardless of technology. So:

- Count the logical requirements by the IFPUG rules, then give observations afterwards, in their own section. Never lower or raise a count because of an architecture you prefer, or because the user's chosen architecture would make something cheaper or costlier to build.
- If the user's answer to a "why" changes the *requirement* ("we don't actually need the audit log"), that is a legitimate re-count. Say so: "that removes ei-07 and eo-03, so I'll recount." If it only changes how something is built, the count stays the same.
- Never describe an observation as a counting finding. Label the section **Observations (these do not affect the FP count)**.

## Asking why (Step 1, and when a decision matters)

Ask why when the answer would change the boundary, the size, or the design; otherwise skip it. Good moments:

- **A boundary choice**: something is outside or inside and the placement is not the conventional one (skip it for an ERP the user already calls external, a payment terminal, or any system the user names as someone else's — those answer themselves) ("Is billing outside because another team owns it, or because it is a separate product?").
- **A function that looks duplicated or inflated**: several near-identical inputs, or one transaction described as three. Ask what the user needs each to do differently, not whether they are "cheating".
- **A requirement stated as a solution** ("we need a Kafka queue", "it must be microservices"): ask what problem that solves, then count the underlying functionality, not the mechanism.
- **A heavy requirement with no stated driver** (real-time sync, multi-tenant, offline mode): ask what happens if it is absent. Their answer also feeds the GSC ratings in Step 5.
- **Deferred or rejected scope**: the reason belongs in the string you save (Step 7), so ask for it once.

Ask before you rule. When the right answer depends on a fact only the user has (does each wizard step save by itself? is this table edited on its own screen?), open with that question, then explain the counting rule once you know. Do not open with a verdict ("I won't split it", "that should be one file") and then ask: the user hears a refusal first and the question second. If the user's request touches a counting rule, say what the rule is in neutral terms ("one form that saves in one commit is one elementary process") after you have the fact, and never in the first lines of the reply.

Do not quote a figure early. Until RET/FTR and DET are known, say nothing about a function's complexity or FP ("it will probably land at High", "that's worth 6 points"). The number is not yet known, and an early figure reads as a verdict or a sales pitch.

Keep it light:

- At most one "why" question per step, phrased with curiosity, not challenge. "What is driving X?" beats "Why would you do X?".
- If the user says they don't know or don't care, record it as an assumption and move on. Do not ask a second time.
- If they have already explained their reasoning, don't ask again. Restate it in a line and continue.
- Never block the count on an answer.

## Observations from the count (Step 7)

After the summary table, offer **at most three** observations, the ones most likely to matter for this system. Each must:

1. **Cite the function IDs** behind it (`ilf-02`, `ei-04`…), so the user can check it against the count.
2. **Say what the count suggests and what it does not know.** The count does not know about team size, existing infrastructure, or deadlines.
3. **End as a question or a trade-off**, not a verdict or an instruction. The test: could the user answer "no, because…" and be right? If the sentence only has one acceptable answer ("Worth a prototype first"), rewrite it with the alternative in view: "This one function carries 6 of 47 FP. Would a quick prototype of it settle the estimate, or is the design already clear enough to size from?"
4. **Leave the count as it is.** If an observation makes you want to revisit a number, you are looking at a counting question, not an observation: put it to the user as a recount, not as advice.

Signals worth looking for, with the kind of observation each supports. These are prompts for your judgment, not thresholds to apply mechanically:

| What the count shows | Worth raising |
|---|---|
| One ILF with far more DET/RET than the others, referenced by most transactions | A central entity everything depends on: would splitting it by lifecycle or ownership help, or is one table honest? |
| Several EIFs, or EI/EO crossing the boundary to the same external system | Coupling to that system: is there a stable contract, and who changes it? |
| Many near-identical EI/EO/EIQ trios over simple ILFs (maintain + list + view) | Mostly standard CRUD: generated or off-the-shelf screens may cover it, with effort better spent on the few complex functions. |
| A few High-complexity transactions carrying a large share of the UFP | Where the risk concentrates: prototype or spike those first, and re-check their FTR/DET. |
| Many EOs with calculations or derived data, few EIQs | Reporting logic in the write path: consider whether read models or a reporting store keep them separate. |
| Many ILFs with only a handful of transactions | Possibly over-modeled data, or functions still to discover: ask what reads and writes them. |
| High GSC scores (distributed processing, performance, multiple sites) | Non-functional drivers shaping the architecture: make sure they come from a real need, not a default. |
| Enhancement: a small "change" touching many CHG transactions | The change spreads through the system, a sign of tight coupling in the existing design. |

If nothing stands out, say so in one line instead of inventing observations. A short honest "this looks like a straightforward system for its size" is more useful than three forced ones.

## How it reads

Before sending the observations, check each one against this list: no imperative verbs aimed at the user ("do", "consider doing", "you should", "worth doing"), no "I won't" or "you can't", no more than two sentences, an ID in every one, and no rhetorical questions that carry their own answer ("is a 'tiny' change really 22 FP of work?"). State the fact neutrally and let the user draw the conclusion: "This one checkbox touches four functions (ilf-03, ei-05, eiq-02, eo-02). Is that spread what you expected?"

- Short, plain, in the user's language. No lecture on patterns, and no jargon the user hasn't used.
- Offer the trade-off in both directions when you can: "A single table keeps joins simple; splitting it helps if accounts and profiles will be owned by different teams."
- If the user pushes back or has a reason, accept it and don't repeat the point. Add their reason to `notes` if it is a decision worth keeping.
- Stay inside the session. Observations are shown in chat only. Do not add them to the `.fpa.yaml` file and do not put them in an HTML report; the only thing from this exchange that belongs in the file is a decision the user made (a `notes`, `deferred` or `rejected` entry).
