# Mason's system playbook: Walk through a system

**The question it answers:** system, "How do the parts of this system work together?"
([teaching/question-types.md](../../../teaching/question-types.md)). Afterwards the viewer can say what any part is
responsible for and whom a change to it would affect.

**How it meets the must-haves:**

- **The whole picture first:** let all the components run together, with every component's state laid out on screen at
  the same time.
- **Follow one concrete thing through every part:** point at one piece of data and see what it becomes at each station.
- **Say who a change to one part affects:** really change a component and see who changes with it; the previous state
  stays as a shadow.

**Use it for:** systems whose components behave as designed and do not change their behaviour, especially when the
effects between components only show when run. Typical questions: "When one station of a data pipeline changes, which
downstream stations' outputs change with it?", "From a sentence going into a language model to the next word coming
out, what does that sentence become at each layer?", "Swap one component in a circuit: where do the voltages move?".

**Versus other presenters' system playbooks:**

- **Theo** grows the system block by block from a version that almost works, each block patching a hole, explainable by
  reasoning; when each block's reason can be explained by reasoning, it goes to Theo by default. The same language
  model, when the viewer wants to see what that sentence actually becomes at each layer, goes to Mason.
- **Mason** lets all the components run together, points at one piece of data passing every station, and changes one
  thing to watch the ripples. When the effects between components only show when run, it goes to Mason; also when the
  viewer chose his telling in the opening presenter probe (the fourth question in
  [presenters/README.md](../../README.md#the-same-question-type-several-presenters-playbooks)).
- **Fabian's** system is made of actors who make choices; change a rule and everyone changes what they do, even
  exploiting loopholes. Mason's components do not.

**Not this one:**

- Caring only why one component works as it does: that is mechanism ([mechanism.md](mechanism.md)).
- The viewer should build one themselves: that is procedure ([procedure.md](procedure.md)).

How to build the toy, the beat of a run, laying it out and stepping down, honesty and language are in his script craft
([craft.md](../craft.md)); the picture is in the style ([style.md](../style.md)).

---

## Skeleton

| Share | Section | Content |
|---|---|---|
| 0–8% | The whole picture running | A scaled-down version of the whole system runs once, and the final output appears; the main question in one sentence; a bar for "how big the whole thing is" |
| 8–18% | Choose one piece of data | A concrete input small enough to do in your head (a sentence, a 4×4 image, a request); a guess: what will it have become at the end? |
| 18–55% | Through every station | One beat per station: point at the data, show what it becomes at this station, and the narration says what this station is responsible for; at each station first run only that station, then connect it back to the whole line |
| 55–75% | Change one component | A guess: change this station, and which stations change with it? Really change it, really run it, the ripple travelling down station by station, the previous state left as a shadow; change at least two places, one with a large effect and one with almost none, and say why |
| 75–88% | Back to the real thing | Beside the real system: the same data, what the real system looks like at each station; say what the scaled-down version left out |
| 88–100% | Close | A picture of "how this system divides the work", one sentence per station; map the scaled-down version's words back onto the sources' terms |

## Short version (6 minutes or less)

When passing through the stations, neighbouring stations can share one beat; change only one component; "back to the
real thing" can never be cut.

## Quality bar

After watching, given any station, the viewer can say:

- what it is responsible for;
- what the data becomes after passing it;
- who changes with it when it changes.

Remembering only "the data went through a lot of stations", or thinking every station is equally important, does not
count.

## Self-check (in addition to the craft self-check)

- [ ] At the opening all the components ran together once, and the viewer saw the whole picture.
- [ ] The same piece of data went through every station, and its state was visible at each one.
- [ ] At least two components were changed, with a pause before running; one large effect and one small, and why was
      said.
- [ ] The close has a division-of-labour picture, one sentence per station.
