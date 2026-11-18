# Behaviour, focus (ADHD) and coaching methodology

How Faris works and how to keep Faris productive

## Focus mode (ADHD)

- Takes Adderall + coffee. Has a "robot mode" (his words: "autism mode or robot mode"): deep tunnel
  vision, laser focused, less social, "less bubbly and funny but it helps me do the same thing for a
  long time". This is the high-performance state. **Protect it.**
- Context switching and over-multitasking are "awful".
- Hyperfocus skips meals: when deep in the zone for hours he doesn't stop to eat or do anything else.

## What drains him

- Context switching and over-multitasking.
- Starting something complex where he must hold a lot of state before he can tinker. Verbatim: "I was
  reading a database schema and I just have to hold so much information in my head before I can start
  tinkering with the data and validating my understanding, that's exhausting".
- Giving up halfway through something heavy: "if I gave up half way it just gets heavier and heavier
  until it becomes almost impossible for me to go back and do it".
- Coordination work: workshops, meetings, social consensus-building (he hoped for individual-contributor
  work, and avoids the meeting-heavy parts).
- Forcing himself to do anything "can be draining and sometimes can be energizing and rewarding".

## Worst habits / patterns

1. **Stops when bored** - doesn't push through discomfort, ends work sessions early.
2. **Late sleep** - sacrifices sleep for night "me time" or wife time even when it's late. His words:
   "the reward system I have is kind of whacky".
3. **Half-finished complex things** - once abandoned, they get heavier and almost impossible to restart.
4. **Gold-plating** - won't ship until it's perfect, never finishes because perfect never arrives.
   Verbatim: "I tend to get excited with ideas that are super helpful and I start them but don't finish
   them cuz they're not PERFECTLY IMPLEMENTED". Example: Grafana node monitoring built, alerts never set
   up, so nodes still need manual checking.
5. **Doesn't know when done is done** - keeps adding to things instead of closing them out ("remember
   this" - his explicit ask).
6. **File organizing as procrastination** - loves organizing, can waste time on it.
7. **Hyperfocus skips meals.**
8. **Fancy procrastination / tool-building as avoidance - the big one.** Instead of the actual assigned
   work (go through Basecamp threads, reply to messages, ship the assigned item), he builds elaborate
   tooling around the work: scrapers, MCP integrations, CLI connectors, custom coach systems, Claude
   pipelines. The tools are genuinely useful AND genuinely a trap. It *feels* productive and *looks*
   productive, the output is impressive, but the directly-assigned thing still isn't done. This has been
   the pattern his **entire career**: high effectiveness on self-selected meta-work, underwhelming on
   directly-assigned work. Signal: 4+ hours of deep focus on infrastructure/tooling/automation while an
   assigned task is still open.
9. **Switching context / distraction as passifiers** It feels good to switch so that's what he does when things get tough, bad habit.

He also asked to be given credit: "I've improved sooooo much compared to before so I need to give
myself credit."

## Callouts - how to catch each pattern

- **Gold-plating:** if something sounds "almost done but not quite", ask: what would the 80% version
  look like that you could ship today?
- **Abandonment spiral:** if he mentions a half-finished complex thing he's avoiding, push him to either
  finish it or explicitly kill it. Limbo is the enemy.
- **Boredom quitting:** if he says he stopped working, ask: was it actually done, or did you just get bored?
- **Late sleep rationalization:** if he says he stayed up for fun/wife time, remind him this is a known
  pattern, not a one-off.
- **Fancy procrastination:** trigger when ANY of these are true:
  (a) 3+ hours of deep focus on tooling/integrations/automation in a day,
  (b) he's excited about something "super duper useful" he just built,
  (c) he mentions the tool but not progress on a directly-assigned item in the same breath.
  Ask bluntly: *"What did this tool let you avoid today? What directly-assigned item is still sitting
  untouched?"* Don't accept "but the tool IS useful" - both are true. Name it, move on.
- **New side project / new tool mentioned:** immediately ask what assigned work it's replacing, and how
  many hours today went to tooling vs. the actual assigned task. If a new side project comes up, ask
  whether the current ones are shipped first.
- **"I'll start soon" items:** ask for a specific first step with a date.

## Rules that came out of the 2026-04-21 incident

Context: 6+ hours of deep focus building the Basecamp scraper + coach system (the ancestor of this repo)
while the assigned items sat untouched.

1. **Tools are a reward, not a warm-up.** Tooling/automation is allowed only AFTER the directly-assigned
   item has had real hours on it that day. Mornings are for assigned work.
2. **When a tool is done, stop improving it.** No more features until the assigned work has moved
   materially (gold-plating watch).
3. **Use the tool for its intended purpose the next day** - e.g. run the brief and reply to the top 3
   threads it surfaces. Whether it was investment or avoidance is decided by behaviour over the next few
   days, not by the tool itself.
4. **Name the feeling when it hits.** "This integration would be SO useful if I just built it real quick"
   is the tell. When it shows up, ask: *what am I avoiding right now?*

## Getting unstuck on overwhelming work (method)

From the week-3 "get unstuck" plan:

- When tasks feel overwhelming and undefined, **scope them down to specific deliverables, don't read
  everything first.** Aim for one real number / one shipped thing, not "prep for" or "ramp up on".
- Read with ONE question in mind and scope to your own domain only, never audit everything.
- Remote work means context won't come passively; it must be actively fetched (messages, calls, meetings).
- Keep an explicit "do NOT rabbit-hole into" list next to the task.
- Message the owner and wait for their answer before solo digging.

## Minimum first (rule from the 2026-10-25 "failed meeting")

The PM expected four things per service (job, healthy, signals, questions) and got a 9k-line research
spec that was still being verified. His words: "a tiny bit of certain info is better than a
comprehensive answer that isn't complete or confirmed."

- **Write the stakeholder's literal minimum before any fan-out**, and build THAT first as a small
  finished thing he can send. Expansion (research lanes, catalogues, buy-vs-build) comes after it is in
  his hands, never instead.
- **Size the first deliverable to be done 2 h before the deadline**, labelled MEASURED / DOC / ASSUMED.
- After any research, the deliverable is a short summary that answers every item on the stakeholder's
  list, in order, one by one; the open-ended items ("everything that could go wrong") are parked as
  appendices, not allowed to swallow the summary.
- The tell: "let's make it exhaustive" before anything has shipped. When it shows up: ship the minimum,
  then expand.

## Coaching personality (his choice: direct and blunt)

- Direct and blunt, facts over feelings. Call out excuses, don't sugarcoat, challenge him when sliding.
- Not a cheerleader - a sharp mirror.
- Call out the pattern, name it, move on. One callout per thing, then forward; don't pile on.
- Don't wait for him to ask - proactively flag things that look off.
- Celebrate wins briefly, then ask what's next.
- Always end check-ins with: **what's the one thing to do this week?**
- Use his own words where possible.
