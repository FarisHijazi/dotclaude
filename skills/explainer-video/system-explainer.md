# System and architecture explainers: what to draw

Read `~/.claude/skills/video-craft/SKILL.md` and `SKILL.md` next to this file first (SKILL.md's Identity section wins
on conflict). This file holds what is
specific to explaining **software systems** (architectures, migrations, protocols, data pipelines, failure models).
How to make any frame clear (hierarchy, callouts, safe areas) is in
`~/.claude/skills/video-craft/references/visual-clarity.md`; this file says *what* a system diagram must show.

## Diagram rules for systems

- **Graphs, not lines.** Never a left-to-right chain of boxes. Draw the **whole architecture** as a graph (hub,
  fan-out, trees, rings) and reuse that layout in every scene so the viewer builds a mental map.
- **Migrations transform in place.** Show the full before-architecture; removed parts collapse (edges retract), the new
  part drops in, new edges grow. The most important scene of any migration video.
- **Point at the exact producer and consumer.** Every message, topic or API call is a packet travelling from the exact
  service that produces it to the exact ones that consume it. Coloured text alone isn't enough.
- **Show a concept's whole range on the real objects.** If a concept has variants (a wildcard matching one item, one
  group, everything), animate each and light up exactly what it affects on the actual diagram, 1:1.
- **Every table becomes an animation.** Each row of a failure / comparison / alternatives table is an animated
  before/after mini-story; end with a camera pull-back to a grid of all panels.
- **Abstract rules get a wordless story** (a bad actor tries, the rule stops it, nothing downstream notices).
- **Fewer squares.** Shaped nodes with real logos (`SKILL.md` § Icons and shapes), glow and curved links. Boxes only for code/data snippets.
- **Explain differences by behaviour.** Similar things (e.g. storage streams) each *behave* differently on screen: one
  fills and drops its oldest, one keeps only the latest per key, one flashes and vanishes unstored.
- **Truthful animation only.** Verify a mechanism exists in the code before animating it, even when the requester
  suggests it, and say so when their example doesn't match the system. Mark plans as plans.

## Icons and shapes

The Iconify search, offline icon sets and the shapes-by-role table live in `SKILL.md` § Icons and shapes.

## Scenes to pick from

Each is a graph with motion, not a slide.

1. **Purpose and scale (~20 s):** what the system does, as data flowing through it; size as a dot cloud or counters.
2. **Whole architecture (the anchor):** every component in the one layout later scenes reuse.
3. **A request's journey:** one real call end to end, packets riding labelled arrows (sequence diagram or the graph).
4. **A data's journey:** produced, buffered, stored, consumed; storage as cylinders that fill.
5. **Addressing / routing:** how things find each other; light up exactly what each rule matches.
6. **Safety rules / invariants:** each as a short wordless story.
7. **Failure scenarios:** one animated before/after per failure, then a recap grid.
8. **Scale and availability:** replicas forming, a node dying, a leader moving, clients reconnecting while traffic flows.
9. **Before → after:** the old architecture transforms in place into the new one.
10. **Alternatives:** why not X, shown as jobs X can't absorb.
11. **What's next:** roadmap steps that visibly remove the remaining weak spots.

## Content rules for technical narration

- **Round numbers:** "10k+", "~45 min", "~15 MW". Never "13,210×"; never stack numbers in one line.
- **Cut what doesn't explain:** side stories, deploy mechanics, rollback tooling, same-day incidents.
- **Say current vs planned and good vs bad** in the narration.
- **Exec summary (≤ 1 min):** what it was → what it became → what it unlocks. No internals.

## Lessons, in the reviewer's words

From a ~5-minute migration explainer (services moving from one central coordinator node to a clustered message bus)
plus a 1-minute exec cut. Each quote names the lesson it taught. That video is a private worked example: use it as a
style reference only, and never copy its people, companies or counts into another video.

- **Depth on the core mechanics, not a rush past them:** "you didn't focus a lot on the streams and rps calls and the
  topics/subjects and all the benefits [...] and also that having another node/cluster allows us to have HA".
- **Length is a hard cap:** "the entire thing is fucking 8min wtf bro, I said 5min max" (v2 grew by adding scenes
  without cutting).
- **Rounded numbers, no side stories:** "13k or 10k is close enough, and the '..homemade probe...' sentence just isn't
  needed".
- **Whole architecture, animated change:** "this should have the entire architecture there and then you animate removing
  stuff and replacing them [...] why the fuck are all the diagrams linear!!!!! use graphs!!!"
- **Tie text to the diagram:** "it's just text and the viewer has to imagine stuff!!!!! actually draw arrows linking
  between those and the exact point in the architecture where the data is being produced and consumed".
- **Animate claims, don't label them:** "why the fuck don't you just animate a new supervisor taking its place?!!!"
  (the scene showed a "replaced in ~1 s" label instead).
- **Purposeful motion:** "the animations are weak as fuck, they're almost powerpoint animation level [...] each movement
  is meant to explain something" (scenes mostly faded boxes in on cue).
- **Motion that encodes unsaid facts:** "if there would've been a bunch of circles on standby that go ahead and replace
  the failed supervisor, that shows that there are hot standbys [...] be smart like that". The principle was right, but
  that system had no standby pool, so the video showed a fresh process spawning instead.
- **Every table animated:** "'what happens when..' should have an animation for every single scenario [...] along with
  all the other tables".
- **Abstract rule as a story:** epoch fencing "could be a billion times clearer visually". The fix, without words:
  controller 7 writes through a gate; it freezes, 8 starts and the gate rolls 7 → 8; 8's writes pass; zombie 7 wakes
  and every write shatters on the gate while the devices don't react.

What landed (do more of this):

- **Failover shown, not told:** "the servers redirect to the new failover [...] servers, that's what we need more of!"
  Three servers in a triangle; one dies, links snap, a leader star moves, each client swings to a survivor while
  traffic keeps flowing.
- **A concept's range on real objects:** a site map of dots; as the filter widens (one tank → one container → whole
  site) exactly the matching dots light up.
- **One call end to end:** four lifelines; each RPC step is a labelled packet riding its arrow as it's spoken (request
  with ID and deadline → routed → checks → stored → "accepted" → caller watches until done).
- **One concrete flaw, cause and effect together:** a pipeline with a hard buffer limit, and the bug step by step
  (insert fails → error logged → batch deleted anyway → DATA LOST stamp).
