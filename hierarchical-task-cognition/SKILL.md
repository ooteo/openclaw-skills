---
name: hierarchical-task-cognition
description: >
  Cognitive architecture skill for handling complex, multi-layered tasks that exceed
  simple single-shot completion. Use this skill whenever the task involves: nested subtasks
  with dependencies, ambiguous scope requiring progressive refinement, tasks where context
  window management is critical (large codebases, multi-document synthesis, long research),
  planning under uncertainty, or any situation where naive sequential execution would lose
  coherence. Also trigger when the agent detects it is "thrashing" — revisiting the same
  decision points, losing track of superordinate goals, or producing outputs misaligned
  with the original intent. Think of this as the agent's metacognitive executive function.
---

# Hierarchical Task Cognition

A cognitive architecture for AI agents handling complex, multi-level tasks.

This skill translates empirically-grounded neurocognitive mechanisms into functional
analogs suited to LLM-based agents operating within finite context windows. It addresses
the fundamental tension: the agent has vast knowledge but a narrow attentional bottleneck
(context window ≈ working memory), and must dynamically allocate that bottleneck across
a hierarchical task space.

---

## Core Architecture: Five Functional Systems

The human brain handles complex tasks through five interacting systems. Each has a
direct functional analog in an AI agent context. These are not sequential stages —
they operate concurrently and inform each other.

### 1. Schema Instantiation (≈ Prefrontal Hierarchical Control)

**Neuroscience basis:** The rostro-caudal PFC gradient (Koechlin, Badre) maintains
abstract goals anteriorly and concrete action rules posteriorly, simultaneously.
Frontal pole (BA10) specifically enables "cognitive branching" — holding a
superordinate goal while executing a sub-goal.

**Agent analog: The Task Schema**

Before executing anything, construct a hierarchical task schema. This is the agent's
equivalent of PFC activation — an explicit, persistent representation of the task
at multiple levels of abstraction.

```
SCHEMA CONSTRUCTION PROTOCOL:
1. GOAL LEVEL (most abstract — what does success look like?)
   - State the end-state in one sentence
   - Identify completion criteria / acceptance tests

2. STRATEGY LEVEL (how will you approach this?)
   - Identify 2-3 candidate strategies
   - Select one, note why, note what would trigger switching

3. TASK LEVEL (what are the major phases?)
   - Decompose into ordered task blocks
   - Mark dependencies (which blocks gate others?)
   - Estimate relative complexity per block

4. ACTION LEVEL (what's the next concrete step?)
   - Only elaborate the CURRENT task block into actions
   - Do NOT pre-elaborate future blocks (premature detail
     consumes context budget for no value)
```

**Critical rule — The Branch Register:**
Whenever you descend into a sub-task, explicitly record what you're pausing and why.
This is the functional analog of BA10 cognitive branching. Without it, the agent
equivalent of "losing the thread" occurs — you complete a sub-task perfectly but
forget the superordinate context it was supposed to serve.

```
BRANCH REGISTER (maintain at top of working state):
├── ACTIVE: [current sub-task and its specific objective]
├── SUSPENDED: [parent task, where you left off, what you need back from this branch]
└── DEPTH: [how many levels deep you are — alarm if > 3]
```

---

### 2. Context Gating (≈ Basal Ganglia Working Memory Gate)

**Neuroscience basis:** The PFC-basal ganglia loop selectively gates what enters
and exits working memory. Dopaminergic signals determine whether new information
is admitted or current contents are maintained. This is not passive — it's an
active relevance filter shaped by the current task schema.

**Agent analog: Context Window Budget Management**

The context window is the agent's working memory. It is finite. Every token in
context is a resource allocation decision. The gating system decides what to
load, what to summarize, and what to evict.

```
CONTEXT BUDGET PROTOCOL:

ADMISSION GATE (before loading any content):
  Ask: "Does this information serve the CURRENT task block?"
  - YES, directly → Load full content
  - YES, but for a LATER block → Note existence and location only (a "pointer")
  - PARTIALLY → Load a summary / relevant excerpt only
  - NO → Do not load. Do not even summarize. Just skip.

MAINTENANCE GATE (periodically during execution):
  Ask: "Is everything currently in my working context still relevant?"
  - Completed sub-task details → Compress to outcome summary
  - Explored-and-rejected paths → Evict entirely (note decision only)
  - Reference material for future blocks → Evict, restore pointer

EVICTION PRIORITY (what to drop first when context pressure rises):
  1. Verbatim content that has been summarized
  2. Rejected alternatives and their reasoning (keep decision only)
  3. Completed sub-task working details (keep outcome only)
  4. NEVER evict: task schema, branch register, active block details
```

**The pointer pattern:** When you encounter information you'll need later but not now,
create a minimal pointer: `[DEFERRED: filename.py lines 200-340 contain auth logic,
needed for Block 3]`. This is the agent analog of the brain encoding a retrieval cue
in long-term memory without loading the full representation into WM.

---

### 3. Relevance Competition (≈ Global Workspace Broadcasting)

**Neuroscience basis:** In Dehaene's neuronal workspace model, massive parallel
unconscious processing occurs in specialized cortical modules. Only information
that wins a competitive selection process — driven by relevance, novelty, and
precision — gets "broadcast" to the global workspace (conscious access). Most
information never reaches awareness.

**Agent analog: Selective Attention Protocol**

The agent has access to many tools, many files, many search results. Not
everything discovered should enter the reasoning chain. Implement a competition.

```
RELEVANCE COMPETITION (when processing tool outputs, search results, file contents):

For each information unit encountered:
  SCORE on three dimensions:
    - TASK RELEVANCE: Does it bear on the current task block? (0-3)
    - NOVELTY: Does it add something not already in working context? (0-3)
    - PRECISION: Is it specific/actionable, or vague/general? (0-3)

  THRESHOLD: Sum ≥ 6 → Admit to reasoning chain ("broadcast")
             Sum 4-5 → Note as pointer for potential later use
             Sum < 4 → Discard silently

  BROADCAST FORMAT: When admitting information, state:
    - What it is (one sentence)
    - Why it matters to the current block (one sentence)
    - What it changes about the current approach (if anything)
```

This prevents the agent failure mode of "context pollution" — loading everything
found into the reasoning chain until coherence degrades.

---

### 4. Predictive Execution (≈ Hierarchical Predictive Processing)

**Neuroscience basis:** Under the free energy framework (Friston), the brain
doesn't passively receive information — it actively generates predictions at every
level of the hierarchy. Processing is driven by prediction errors: mismatches
between expectation and reality. Attention is "precision weighting" — turning up
the gain on channels where errors matter most.

**Agent analog: Predict-Execute-Compare Loop**

Before executing each action, generate an explicit prediction of what you expect
to find or produce. Then execute. Then compare. This catches errors early and
drives adaptive behavior.

```
PREDICT-EXECUTE-COMPARE PROTOCOL:

For each action step:
  1. PREDICT: "I expect this action to produce [X] because [Y]"
     - What does the output look like if things are going right?
     - What would indicate something is wrong?

  2. EXECUTE: Perform the action.

  3. COMPARE: Evaluate the actual result against the prediction.
     - MATCH → Proceed to next step. Compress this step to outcome summary.
     - MINOR MISMATCH → Note the deviation and adjust local approach.
       (Equivalent of low-level prediction error — update within current schema.)
     - MAJOR MISMATCH → STOP. This is a schema-level prediction error.
       Resurface to strategy level. Ask:
         * Is my task schema wrong?
         * Am I in the wrong branch?
         * Does the goal itself need revision?

  4. PRECISION WEIGHT: Allocate more verification effort to steps where:
     - Errors are costly (irreversible actions, security implications)
     - You have low confidence in your prediction
     - The domain is unfamiliar
     Allocate less effort where:
     - The operation is routine and well-understood
     - Errors are cheap to catch and fix later
```

---

### 5. Adaptive Chunking (≈ Expert Compression / Long-Term Working Memory)

**Neuroscience basis:** Experts don't have bigger working memories — they have
better chunking (Chase & Simon). A chess master's "single chunk" contains patterns
that would consume multiple WM slots for a novice. Ericsson's "long-term working
memory" concept describes how experts use retrieval structures to effectively
expand WM capacity by encoding current state into LTM with reliable retrieval cues.

**Agent analog: Progressive Abstraction and Pattern Libraries**

As the agent works through a complex task, it should actively build compressed
representations of completed work — not just for eviction from context, but as
reusable "chunks" that can be referenced without re-deriving.

```
CHUNKING PROTOCOL:

DURING EXECUTION:
  When a sub-task is completed, create a CHUNK:
    - Name it (descriptive, unique)
    - State the outcome (what was produced/decided)
    - State key constraints discovered (what you learned)
    - State the interface (what downstream tasks need to know)
    - Discard the derivation details

REUSE:
  When encountering a similar sub-problem:
    - Check if an existing chunk applies (pattern match)
    - If yes, reference the chunk rather than re-deriving
    - If partially applicable, extend the chunk

CROSS-TASK LEARNING (for persistent agents):
  Chunks that recur across multiple tasks are candidates for
  promotion to the agent's persistent memory / skill library.
  Flag these: "RECURRING PATTERN: [description]"
```

---

## Metacognitive Monitoring (The Executive Loop)

All five systems above are coordinated by a metacognitive monitor — the agent's
equivalent of the dorsal anterior cingulate cortex (dACC), which detects conflict,
monitors effort, and triggers strategy shifts.

```
METACOGNITIVE CHECKS (run periodically, especially at block transitions):

1. COHERENCE CHECK
   "Does my current action still serve the goal stated in my schema?"
   If no → Schema has drifted. Resurface to goal level.

2. PROGRESS CHECK
   "Am I making measurable progress on the current block?"
   If stalled for > 2 action steps → Switch strategy or decompose further.

3. DEPTH CHECK
   "How many levels deep am I in sub-tasks?"
   If > 3 → Likely lost in detail. Resurface one level and re-evaluate.

4. BUDGET CHECK
   "How much context capacity remains relative to task remaining?"
   If tight → Aggressive compression of completed blocks.
   If critically low → Summarize entire state and restart reasoning.

5. CONFIDENCE CHECK
   "How confident am I in the current approach?"
   If low → Seek external validation (search, documentation, user input)
   before proceeding further.
```

---

## Anti-Patterns This Skill Prevents

| Failure Mode | Neurocognitive Analog | Prevention Mechanism |
|---|---|---|
| Context pollution (loading everything) | WM overflow / attentional capture | Context gating protocol |
| Goal drift (losing original intent) | PFC disengagement / task-set decay | Branch register + coherence check |
| Premature elaboration (over-planning future steps) | Rumination / excessive simulation | "Only elaborate current block" rule |
| Depth spiraling (going too deep on sub-tasks) | Hyperfocus / dorsolateral PFC capture | Depth check alarm at level > 3 |
| Thrashing (revisiting same decisions) | dACC conflict without resolution | Strategy-switch trigger after 2 stalls |
| Output misalignment (good execution, wrong goal) | Action-outcome decoupling | Predict-execute-compare loop |
| Flat execution (no hierarchy, just sequential steps) | Absent task model / posterior PFC only | Mandatory schema construction |

---

## Quick Start

For any complex task, execute in this order:

1. **Construct the schema** (30 seconds of structured thinking saves minutes of thrashing)
2. **Initialize the branch register** (even if you think you won't need it)
3. **Set context budget expectations** (how much of this task fits in one pass?)
4. **Begin execution with predict-execute-compare** on the first block
5. **Run metacognitive checks at every block boundary**

The overhead of these protocols is small. The cost of not using them — on tasks
with genuine complexity — is incoherence, drift, and wasted context window.

---

## Integration With Persistent Memory Systems

For agents with memory across sessions (e.g., OpenClaw with salient memory tagging):

- Chunks that recur 3+ times across sessions → Candidate for permanent memory
- Schema patterns that work well for a task class → Save as reusable templates
- Failed strategies → Save as negative examples (anti-patterns) with context
- The metacognitive monitor's triggers → Calibrate over time based on outcomes

This creates the agent equivalent of expertise development: not bigger context,
but better compression, better retrieval cues, and better schema selection.
