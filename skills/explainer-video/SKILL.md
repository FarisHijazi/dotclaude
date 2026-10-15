---
name: explainer-video
description: Make an explainer / documentation video for ANY technical or software system (Remotion + OpenAI TTS + subtitles) to Faris's standard — 3Blue1Brown/Fern-level purposeful motion, whole-architecture graphs, hard length cap. Use whenever asked for an explainer, walkthrough, architecture or migration video, or "video that explains X".
---

# Explainer videos: Faris's standard

General guidelines for explaining **any technical or software system** on video: an architecture, a migration, a
protocol, a data pipeline, a failure model. This file is self-contained, so a reader with no other context should be
able to make a video Faris accepts. The rules come from his feedback on one real video (a messaging migration),
described under "Worked example", and its concrete cases are kept as examples. Use the `remotion-best-practices` skill
for Remotion APIs. This file covers **what good looks like**, **what he said**, and **how to get there**.

## Worked example: where these rules came from

- **Who:** Faris Hijazi is the engineer requesting the video. He reviews every version and reacts bluntly. Swearing in
  his quotes means frustration, not hostility. Audiences: his co-engineer (technical) and executives (the 1-minute cut).
- **What:** a ~5-minute explainer of a migration at a bitcoin-mining / grid-services site, and a < 1-minute executive
  summary.
- **The system, in one paragraph:**
  - ~3,000 miners sit on 36 electrical breakers and draw ~15 MW.
  - A grid operator sends a power target.
  - A *grid gateway* forwards it to a *fleet controller*, which splits it across 36 *supervisors* (one process per
    breaker), and they drive the miners.
  - Telemetry (readings from every device) flows into a time-series database.
- **The migration:**
  - **Before:** every service was a *Ray actor*, found by name through one central *Ray head* node, so losing that node
    lost everything. Telemetry went through *Redis Streams*, which held only ~3 minutes of buffer and silently lost
    data when the database failed.
  - **After:** everything talks over *NATS*, one message bus.
- **Glossary** (terms used in the quotes below):
  - *NATS*: a message server. Services publish messages to named **subjects** (dot-separated paths such as
    `svc.fleet.set_fleet_power.v1` or `telemetry.discovery.c03.b1.t3.miner.<serial>`). Subscribers can use
    **wildcards** (`telemetry.>` means "everything under telemetry"). It also does request/reply (RPC).
  - *JetStream*: NATS's on-disk storage. A **stream** keeps the messages of some subjects for replay, e.g. a FLEET
    telemetry stream, a STATE stream that keeps only the latest value per subject, and `live.*` samples that aren't
    stored at all.
  - **Epoch / fence**: every writer (e.g. a controller) carries a number that only goes up. A write from an older epoch
    (a "zombie" controller that came back to life) is refused before it reaches a device.
  - **HA**: high availability, meaning no single machine whose death stops everything. Here: three NATS servers in a
    cluster instead of one Ray head.
  - **Failover**: when a server dies, clients reconnect to a surviving one.
  - **Gates A/0/B/C**: phases of the migration plan. Gate 0 was the switch to NATS.
  - **Fern / 3Blue1Brown (3b1b)**: YouTube explainer channels whose animations make concepts visible through purposeful
    motion. That's the reference style.

## The bar

**YouTube-explainer level (3Blue1Brown, Fern), never PowerPoint.** Every movement must explain something. If the
viewer has to read text or imagine a mechanism, the scene failed.

- **Show, don't narrate.** The best beat teaches something the narration never says. Example: a crashed worker process
  is visibly replaced by a new one flying into its empty slot, so the viewer learns "it self-heals" without a word.
- **Graphs, not lines.** Never a left-to-right chain of boxes. Draw the **whole architecture** as a graph (hub,
  fan-out, trees, rings) and reuse the same layout from scene to scene so the viewer builds a mental map.
- **Migrations are a transformation animated in place.** Put the full before-architecture on screen. The removed parts
  collapse (their edges retract into the services), the new part drops in, and new edges grow. This is the most
  important scene of any migration video.
- **Point at the exact producer and consumer.** Every message, subject, topic or API call is a packet travelling on the
  architecture, from the exact service that produces it to the exact ones that consume it. A coloured string of text
  alone isn't enough.
- **Show a concept's whole range on the real objects.** If a concept has variants (a wildcard matching one tank, one
  container, the whole site), animate each variant and light up exactly what it affects on the actual diagram, 1:1, so
  there's no room for guessing.
- **Every table becomes an animation.** "What happens when…" failure scenarios, before/after comparisons, alternatives:
  each row is an animated before/after mini-story. Example, database down: on the left, batches are thrown into a trash
  can; on the right, messages pile up in the stream, the database recovers, and the pile drains into it. End with a
  camera pull-back to a grid of all the panels.
- **Abstract rules get a story.** See the epoch/zombie example under "In his own words".
- **Fewer squares.** Use round icon nodes with glow, curved links, cylinders for storage, dot clouds for fleets, and
  rings for process boundaries. Boxes only for code/data snippets.
- **Explain differences by behaviour.** When several things are similar (different storage streams), show each one
  *behaving* differently. One fills fast and drops its oldest messages, one keeps only the latest card per subject
  (each new card knocks the old one out), one flashes and vanishes without being stored.

## Scenes for any system explainer

Pick what fits; each one is a graph with motion, not a slide.

1. **Purpose and scale (~20 s):** what the system does, shown as data/requests flowing through it, with its size as a
   dot cloud or counters (users, nodes, msgs/s).
2. **Whole architecture (the anchor):** every component in one graph layout that later scenes reuse.
3. **A request's journey:** one real call end to end, as packets riding labelled arrows (a sequence diagram or the
   architecture graph).
4. **A data's journey:** where data is produced, buffered, stored and consumed, with storage drawn as cylinders that
   fill.
5. **Addressing / routing:** how things find each other (names, topics, URLs, keys). Show matching rules by lighting up
   exactly what matches, 1:1.
6. **Safety rules / invariants:** each one as a short wordless story (a bad actor tries, the rule stops it, nothing
   downstream notices).
7. **Failure scenarios:** one animated before/after per failure (node dies, DB down, network split, overload), with a
   recap grid.
8. **Scale and availability:** replicas forming, a node dying, a leader moving, clients reconnecting while traffic keeps
   flowing.
9. **Before → after (migrations):** the old architecture transforms in place into the new one.
10. **Alternatives:** why not X, shown as jobs that X can't absorb (they bounce off and need a second system).
11. **What's next:** a roadmap whose steps visibly remove the remaining weak spots.

## In his own words (verbatim, 2026-10-15)

Each quote has a **Context** paragraph: what was on screen and why he said it, so the lesson carries over to other
videos. Quotes are in the order he said them.

**The original ask**
> "fan out sonnet subagents read all the artifacts and code related to NATS and understand it super well please and
> then please make a remotion full 5min video that explains everything and use ~/.env OPENAI API KEY for the TTS and put
> subtitles"

Context: research comes first, with parallel agents reading the real code and docs, so every claim is grounded. Then a
5-minute Remotion video with an OpenAI text-to-speech voice and subtitles.

> "explain everything and all the scenarios and and how it does different things, comparisons of before/after
> ray->NATS [...] and what the next phases are"

Context: a migration explainer must cover how it worked before, how it works now, what happens in each failure
scenario, side-by-side comparisons, and the roadmap.

**Length**
> "yes speedup to 1.25x"

Context: the first cut was 6:41. Speeding the narration up (pitch preserved) is an acceptable way to hit the time cap.

> "I think we can get to even bellow 2min if it's a less technical one, make a version that's <1min which is like an <!-- codespell:ignore -->
> executive summary that shows what was, what has become, and how this will help us scale from 2880 miners on 15MW to
> expand to a 200MW site and also will allow digital twins and virtual power plants"

Context: also make a short business version: was → is → what it unlocks (scale, digital twins, virtual power plants),
with no internals.

> "also the entire thing is fucking 8min wtf bro, I said 5min max"

Context: version 2 grew to 7:38 because new scenes were added without cutting anything. The stated length is a hard
cap: budget the words before generating the voice.

**Content focus**
> "I still think the video needs more visuals and more diagrams and less squares, and you didn't focus a lot on the
> streams and rps calls and the topics/subjects and all the benefits like not needing DB aggregators etc etc, and also
> that having another node/cluster allows us to have HA, as apposed to ray-head having a single point of failure"

Context: version 1 rushed past the core mechanics. He wants depth on the substance: how subjects work, what an RPC call
looks like, what streams are, why live state no longer needs database aggregation queries (current values are just the
last message on a subject), and how a cluster gives HA where the old design had one fatal node. Plus more diagrams and
fewer rectangles.

> "also explain the differences between the different streams we have etc"

Context: a scene listed the storage streams (FLEET, GRID, SITE, STATE, live) without saying how they differ. Show each
one's role and behaviour.

> "why do we need to regurgitate so many numbers, I don't want exact numbers like \"x13,210 failed to lookup actor..\",
> 13k or 10k is close enough, and the \"..homemade probe...\" sentence just isn't needed bro"

Context: the narration quoted exact log figures (13,210 lookups, 46 min, 590 msg/s, 1.8 TB) and told a side story about
a health probe. Use rounded numbers and drop side stories; precision costs attention and explains nothing.

> "the image switch and \"rollback script stands by\" aren't needed" · "\"dashboard toggles refused this
> afternoon...\" isn't needed, drop it"

Context: operational details don't belong in an architecture explainer: how the deploy swapped Docker images, the
rollback tooling, a same-day incident. Keep only what explains how the system works and why it's better.

**Architecture and graphs**
> "and for the section of \"so the plan is simple remove ray\", \"one bus 4 lanes\" this should have the entire
> architecture there and then you animate removing stuff and replacing them, this is the most important part [...] and
> why the fuck are all the diagrams linear!!!!! use graphs!!! show the entire architecture!!!!"

Context: the decision scene was four rows ("lanes") of text beside a NATS box, and other diagrams were A → B → C → D
chains. He wants the real topology on screen, with the migration happening on it: the old central node collapses, its
edges retract, the new bus drops in, and new edges grow lane by lane.

> "\"every message has an address\" page is nice that they're colored, but still, it's just text and the viewer has to
> imagine stuff!!!!! actually draw arrows linking between those and the exact point in the architecture where the data
> is being produced and consumed"

Context: subject strings were built token by token, each token coloured by role (kind / service / location / method).
He liked the colours, but text alone forces imagination. Each subject must be tied by moving arrows to the exact service
that publishes it and the ones that consume it.

**Motion quality**
> "in the page \"the control loop on NATS\" it's nice, but for the replacement of the supervisor, why the fuck don't you
> just animate a new supervisor taking its place?!!! make everything clear rather than just spitting out text and leaving
> it for the viewer to imagine!!!! stop expecting imagination or deep understanding and actually fucking animate all of
> that"

Context: the scene showed a label, "wedged one replaced alone, ~1 s", instead of showing the replacement. Any claim
written as a label should be an animation.

> "i'm fine with all of the narration but the animations are weak as fuck, they're almost powerpoint animation level,
> instead I want youtube animation explanation level!!! fern level or 3b1b level explainations!!! things moving and <!-- codespell:ignore -->
> animating with a purpose, each movement is meant to explain something"

Context: the scenes mostly faded boxes and text in on cue, like PowerPoint "appear" builds. Motion must carry the
meaning: a packet travelling, a node dying, a process being replaced, a filter changing what lights up.

> "for example with the supervisor, if there would've been a bunch of circles on standby that go ahead and replace the
> failed supervisor, that shows that there are hot standbys, this is a piece of info that you didn't have to narrate,
> yet the viewer understood, be smart like that"

Context: his model of a great beat is motion that encodes extra facts the narration never says (here, that
replacements exist and take over by themselves). The principle is right. The specific mechanism was wrong for that
system: it spawns a fresh process and keeps no standby pool. So the video shows a new process being born at the
controller and flying into the empty slot. Always verify a mechanism is real before animating it, and tell him when his
example doesn't match the system.

**Tables and abstract rules**
> "\"what happens when..\" should have an animatino for every single scenario" ... "along with all the other tables"

Context: failure scenarios and the before/after comparison were static tables with ✗/✓ text. Every table row becomes its
own animated before/after mini-story.

> "also \"zombie controller from an older epoch can't move a single machine...\" definitely could be a billion times
> clearer visually, doesn't need narration explaination just the idea of it" <!-- codespell:ignore -->

Context: epoch fencing (glossary) was a cramped panel with an "epoch 7 → write refused" label. The fix was a full-screen
story told without words:

1. Controller 7 writes to the miners through a gate.
2. Controller 7 freezes, controller 8 starts, and the gate's number rolls 7 → 8.
3. Controller 8's writes pass.
4. The zombie 7 wakes up and every write it fires shatters on the gate, while the miners don't react.

**What he loved (do more of this)**
> "one head vs. a cluster is fucking awesome, especially that part where the servers redirect to the new failover NATS
> servers, that's what we need more of!"

Context: in the HA scene, three NATS servers form a triangle. One dies, its client links snap, a vote moves the leader
star to another server, and each client's link swings over and reconnects to a survivor while traffic keeps flowing. The
failover happens on screen, so the behaviour itself is the explanation and nothing has to be read.

> "the telemetry.> visualization is awesome btw" ... "the purple one"

Context: a map of the site's 18 containers × 8 tanks drawn as dots. As the narration says "one tank, one container, the
whole site", the subscription filter changes through three steps and exactly the matching dots light up purple:

1. `telemetry.discovery.c03.b1.t3.>`
2. `telemetry.discovery.c03.>`
3. `telemetry.>`

He liked it because the circles lit up and changed, explicitly showing the different combinations of the actual
concept (which wildcard matches which miners), mapped 1:1 onto the real objects with no room for guessing. Aim for this:
take a concept's range of values and show each one directly on the real thing.

> "I like the page with \"one call end to end\""

Context: a sequence diagram with four vertical lifelines (gateway, NATS, controller, STATE stream). Each step of a real
RPC is a labelled packet riding its arrow at the moment it's spoken:

1. The request goes out with an ID and a deadline.
2. NATS routes it to whoever serves the subject.
3. The controller checks the deadline and epoch.
4. A record is stored.
5. "accepted" comes back.
6. The gateway watches until done.

Every arrow is one real message.

> "the telemetry weak spot slide is great"

Context: the "before" slide for Redis showed a producer → Redis → consumer → database pipeline and a hard buffer limit
(100,000 messages ÷ 590 per second ≈ 170 s). The bug was spelled out step by step: INSERT → error logged, XACK + XDEL →
batch deleted anyway, DATA LOST stamp. One concrete flaw, with cause and consequence on screen together.

## Content rules

- **Hard length cap.** "5 min max" means ≤ 5:00 including gaps. Budget words before generating speech (≈ 170 words per
  minute raw), then speed up 1.25–1.36× with pitch preserved. Cut filler before speeding further.
- **Round numbers:** "10k+", "~45 min", "~3,000 miners", "~15 MW". Never "13,210×". Never stack many numbers in one
  line.
- **Cut sentences that don't carry the explanation:** side stories, deploy mechanics, same-day incidents.
- **Truthful animation only.** Never animate a mechanism that doesn't exist to make something clearer. Mark plans as
  plans ("can", "next", "planned").
- **Exec summary (≤ 1 min):** what it was → what it became → what it unlocks (scale, new business). No internals.
- **Narration labels state clearly** whether something is current or planned, and whether it's good or bad.

## Process that works

1. **Research first, in parallel.** One subagent per repo/area writes cited notes, "video-worthy facts" and "diagram
   ideas". Correct the brief from the code: in the worked example the agents found three wrong numbers.
2. **Narration:** a JSON file with one entry per scene, word-budgeted to the cap. Write symbols as they're spoken
   ("S V C, fleet, set fleet power, v1").
3. **Voice and captions:**
   1. OpenAI `gpt-4o-mini-tts` (voice `onyx`, calm-engineer instructions) per scene.
   2. `whisper-1` word timestamps, aligned back to the *script* words with difflib, so the subtitles show the exact
      script.
   3. Reject any clip shorter than ~250 ms per word: the API sometimes returns truncated audio.
   4. A small speed-up script makes pitch-kept ffmpeg `atempo` copies and scales the caption times.

   The API key is `OPENAI_API_KEY` in `~/.env`.
4. **Design motion beats per spoken cue before coding.** Give each scene a `useCue()("phrase")` hook that returns the
   frame where a phrase is spoken (from the caption timings) and throws if the phrase isn't in the narration. Re-point
   cues whenever the narration changes.
5. **Shared layout and motion primitives first:**
   - One architecture layout module (node positions), reused by every scene.
   - Motion primitives: a packet that rides a curved path (with an optional label, repeating as a stream), a ripple
     ("something happened here"), a countdown ring (deadlines, timeouts), a camera that pans and zooms, a shake
     (stuck/erroring), round icon nodes, curved edges that draw in and retract, and storage cylinders that fill.
6. **Fan out one fork agent per 2–3 scenes.** Each agent owns only its files and verifies with `tsc` plus 5–10 rendered
   stills it actually looks at. Then integrate, contact-sheet every scene (`magick … +append/-append`), fix overlaps,
   and render.
7. **Deliver:**
   - Burned-in subtitles plus a sidecar `.srt`.
   - A < 30 MiB copy (`-crf 27`) for in-chat upload.
   - Keep each scene its own composition so a single scene can be re-rendered.

## Traps (each hit once)

- Environment:
  - If Chrome dies during `remotion still/render`, check PATH for unreadable directories (e.g. `/root/...`) and strip
    them.
  - If `ffmpeg`/`ffprobe` aren't installed, use the bundled `node_modules/.bin/remotion ffmpeg|ffprobe` (it lacks some
    filters, e.g. `volumedetect`).
  - Make sure `npx`/`npm` are the real Node binaries, not a bun shim.
- JSX text can't contain a bare `<` (`< 1 min`); wrap it in `{"…"}`.
- A wait loop `while pgrep -f '<pattern>'` matches its own shell's command line and never exits.
- Chat uploads cap at 30 MiB.
- Stills taken during a scene's fade look washed out. That's the transparent PNG, not the video.
