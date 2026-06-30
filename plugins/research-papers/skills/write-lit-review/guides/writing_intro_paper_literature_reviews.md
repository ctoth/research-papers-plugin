# Writing Top-Quality ACM or IEEE Literature Reviews: the Introduction and the Related Work Section

A practical guide for producing the two literature reviews a primary-research paper needs at ACM and IEEE venues (CHI, ASSETS, TOCHI, TACCESS, IEEE TVCG, IEEE Access, VR, ISMAR, SIGSPATIAL, and similar): the motivating review inside the **Introduction**, and the comprehensive, comparative **Related Work** section. It is the companion to `writing_full_paper_literature_reviews.md`, which covers standalone survey and PRISMA review papers. If you are writing a survey, read that guide instead.

This guide is grounded in two sources. The first is a set of six exemplar papers in this collection's `papers/`, chosen for the quality of their reviews: `feng2015investigation` (auditory map comprehension), `ZhaoPlaisantShneidermanLazar2008` (iSonic data sonification, a TOCHI article), `brock2015interactive` (interactive audio-tactile maps), `giudice2020use` (indoor navigation, a TACCESS article), `ji2022vrbubble` (social VR accessibility, an ASSETS paper), and `iachini2014does` (a cognitive-science study of spatial frames of reference). The second is the published author guidance: John Swales's CARS model, Simon Peyton Jones's *How to Write a Great Research Paper*, the IEEE Author Center and ACM CHI submission guides, and the writing-center literature on synthesis (Purdue OWL, USC, UNC, GMU, Manchester Academic Phrasebank). Full URLs are in the Sources section.

**How to use this guide.** Read **Shared Foundations** first; its principles apply to both reviews. Then go to **Part 1** to write the Introduction's review, or **Part 2** to write the Related Work section. Each part is self-contained: it has its own phrasing bank, exemplar dissection, worked example, intake questions, step-by-step protocol, and checklist. If you are a language model, collect the intake answers for the part you are writing before drafting a single sentence.

**A note on the examples (read this).** Every example in this guide, in the phrasing banks and in both worked examples, is reproduced **verbatim** from the cited paper and attributed by its bibtex key. Excerpts preserve the source's exact wording, terminology (for example "visually impaired" or "challenges"), punctuation (including any em-dashes), and original numeric citation markers (for example `[12]`). They are quotations that show you how strong authors phrase and structure a review; they are not models of house style. The rules you must follow when you write are in Shared Foundations Section 6, and they apply to your prose, not to these quotations.

---

# Shared Foundations (applies to both parts)

## 1. Synthesis, Not Summary

This is the highest-leverage skill and the most common failure mode. A reviewer can tell synthesis from summary in one paragraph.

- **Summary** restates what one source says. **Synthesis** combines several sources into a claim that none of them states alone, and shows how they relate.
- **The topic sentence states the claim; the citations support it.** Put several citations behind one claim. The mechanical tell of synthesis is multiple keys per sentence. The model in the collection is `giudice2020use`, which supports a single claim with five technologies, each cited in line:

> Accurate nonvisual route navigation through complex commercial buildings has been shown with systems using ultra-wideband (UWB) positioning [11, 12], an infrared camera to detect retro-reflective barcodes [13], a smartphone's inertial sensors [14], RFID tags [15], and inertial dead-reckoning techniques coupled with infrared sensing [16].

- **Claim, then "For example".** When a single study deserves the spotlight, lead with the synthesized claim and follow with a named example, as `ji2022vrbubble` does throughout its Related Work:

> Prior work has also used audio to identify objects within the virtual space [3, 10, 19, 42, 55, 57, 63–65]. For example, de Oliveira et al. [10] recreated a virtual stage and placed instruments in the environment that generated spacial music.

- **Pitfall.** The "citation salad," a string of `[@a] [@b] [@c]` with no claim, signals that you have not engaged with the work. A long reference list is not engagement.

## 2. Positioning and Gap-Framing Without Strawmanning

How you treat prior work is read as a signal of your judgment. Be generous and specific.

- **Be generous to the competition.** Peyton Jones names the fallacy: "to make my work look good, I have to make other people's work look bad." His counter is that credit is not like money, and giving it to others does not diminish yours. Describe what prior work achieved, then differentiate by contrast. `giudice2020use` says competing systems "have proven extremely effective" before naming what is still missing.
- **Frame the gap as a contrast, not a verdict.** Prefer neutral constructions ("focused primarily on A, rather than on B"; "less attention has been paid to B"). Avoid "prior work failed to" or "ignored," which invite the very reviewer who wrote the cited paper to reject you.
- **Make the gap specific and the contribution refutable.** A vague gap ("more work is needed") motivates nothing. State contributions concretely enough that a reader could in principle prove them wrong, and use forward references ("see Section 4") to where you deliver each one.

## 3. Citation Practices and the BibTeX Format

**Citation format (mandatory for the prose you write).** Cite using pandoc bibtex keys, inline and bracketed:

- Inline (author-prominent): `In @giudice2020use the system-aided condition improved navigation accuracy.`
- Bracketed (information-prominent): `Audio-tactile maps can outperform verbal descriptions for some spatial tasks [@Papadopoulos2018TextVSMap].`
- Multiple sources behind one claim: `[@brock2015interactive; @papadopoulos2018differences; @feng2015investigation]`

**Source of keys.** The canonical list is `Bibliography/CITATIONS.BIBTEX`. Pull every key from there and never invent one. If a paper is not in that file, flag it for the author rather than guessing. Do not invent statistics or attach a real key to a number its source does not contain.

(The quoted excerpts in this guide keep each paper's original numeric citation markers such as `[12]`, because they are verbatim. That is the publisher's rendering, not your format. You always write `@key`.)

**Density and balance.** Include the foundational works that define the area and the recent ones (roughly the last three to five years) that represent the current state. The Related Work section carries a higher citation density than the Introduction: the Introduction cites only what motivates the work and opens the gap, while Related Work cites comprehensively across every neighboring theme.

**ACM versus IEEE rendering.** The same `.bib` file drives both. ACM uses the ACM Reference Format; IEEE uses bracketed numbers in order of appearance. You do not change your keys for the venue; only the document class and bibliography style change.

**Output: the deliverable folder.** Write each finished review into its own folder, so the draft and its bibliography stay together. The folder contains exactly two files:

- the markdown draft (for example `literature_review.md`), the review prose itself; and
- `citations.bibtex`, holding the full bibtex entry for every `@key` cited in the draft, and only those keys, copied verbatim from `Bibliography/CITATIONS.BIBTEX`.

Keep the two in sync: every `@key` in the draft has a matching entry in `citations.bibtex`, and `citations.bibtex` lists nothing the draft does not cite. The pair then compiles directly with pandoc.

## 4. The Exemplars' Tone and Grammar

Both reviews should sound like the exemplars: measured, evidence-led, and concrete. Match this voice.

**Tone and register.**
- **Measured, not promotional.** Importance is asserted with facts, not adjectives. The exemplars do not call work "novel" or "groundbreaking"; they show it. `brock2015interactive` opens with a number: "Indeed, 56% of visually impaired people in France declared having problems concerning autonomous mobility."
- **Generous, then differentiating.** Describe what prior systems achieved before contrasting.
- **Concrete.** Name systems, techniques, populations, and numbers rather than gesturing at "many approaches."

**Grammar and mechanics.**
- **Verb tense.** Present for established facts ("Information visualization is a technique that enables people with normal vision to use their tremendous visual ability to explore data and discover trends." `ZhaoPlaisantShneidermanLazar2008`). Present perfect for accumulated lines of work ("There has been extensive work that assisted PVI in exploring virtual environments via audio feedback." `ji2022vrbubble`). Past for specific completed studies and for your own work ("We evaluated VRBubble with 12 participants with visual impairments..." `ji2022vrbubble`).
- **Voice.** Active for your contributions ("We aim to fill this gap by enhancing PVI's awareness of surrounding avatars in social VR." `ji2022vrbubble`). Prior work is usually active too, with the system or author as subject ("Walker and Lindsay's [79] study utilized three different audio beacons in navigation guidance." `ji2022vrbubble`).
- **Citation integration.** Two deliberate patterns: information-prominent (claim first, key at the end) for synthesis, and author-prominent (author as subject) to spotlight one study.
- **Connectives.** The dominant territory-to-niche pivot is "However,". Other observed connectives: "Indeed," "Yet," "Therefore," "As a result," "Beyond," "Similar to," "In the same vein," "For example," "For instance."

## 5. Common Pitfalls and Reviewer Complaints

1. **Missing prior work.** The reviewer who knows the uncited work will say so; CHI's guidance is blunt that inadequate references are a frequent cause of low scores.
2. **Citation salad.** Lists of keys with no synthesizing claim.
3. **Annotated bibliography.** One paragraph per source, organized by source rather than by idea.
4. **Name-dropping without integration.** Citations that do not tell the reader why the work is relevant to the gap.
5. **Strawmanning.** Overstating others' weaknesses to inflate your gap.
6. **Unsupported novelty.** "First to" or "no prior work" with no defensible basis.
7. **No clear gap or contribution.** The reader finishes unsure what is new or why it matters.
8. **Related Work that does not connect back.** A survey that never says how the cited work bears on your contribution. Every theme must end with a gap your paper addresses.
9. **Redundancy between Introduction and Related Work.** The Related Work section repeats the Introduction instead of deepening it. The Introduction names the gap; Related Work proves it across the full literature.
10. **House-rule violations.** Em-dashes, "challenge" instead of "barrier," "mapping" for a map product, person-first instead of disability-first language, or invented citation keys.

## 6. House Rules (govern your prose, not the quoted excerpts)

- **No em-dashes.** Use commas, parentheses, or rephrase. En-dashes are fine only in numeric ranges.
- **Disability-first, current terminology.** Write "blind and low-vision (BLVI)," "blind people" (not "people who are blind"), "people with disabilities (PWDs)." The older exemplars say "visually impaired people"; adopt their sentence shapes, not their dated terms.
- **"Barrier," not "challenge."**
- **"Map," not "mapping,"** when referring to a viewer or editor such as Audiom.
- **Cite with bibtex keys** from `CITATIONS.BIBTEX` only.

---

# Part 1: The Introduction's Literature Review

## 7. What the Introduction Review Is For

The literature review inside the Introduction is an argument, not a catalog. It makes three moves so that your contribution lands as the obvious next step:

1. **Motivate.** Establish that the topic matters and the problem is real.
2. **Open the gap.** Show what prior work has and has not done, and name the specific thing that is missing.
3. **Set up the contribution.** Position your paper as the thing that fills that gap.

It is selective and persuasive: it cites only what is needed to motivate the work and frame the gap, and leaves the comprehensive survey to the Related Work section (Part 2). Peyton Jones recommends stating your idea early rather than burying it behind a long related-work discussion, so the Introduction should reach your contribution quickly.

## 8. The CARS Structure (Swales)

The most reliable skeleton for an Introduction is Swales's Create-A-Research-Space model, a funnel from broad to specific:

| Move | Purpose | Length in an intro |
|------|---------|--------------------|
| **Move 1: Establish a territory** | Claim centrality; give background; review the key prior work that frames the problem | 2 to 5 sentences |
| **Move 2: Establish a niche** | Name a limitation, indicate a gap, or raise a question | 2 to 4 sentences |
| **Move 3: Occupy the niche** | State the purpose and contribution; preview findings; give a short roadmap | 3 to 6 sentences plus a contributions list |

**Test.** Label each sentence of your draft M1, M2, or M3. If you cannot find a clear M2, you have not opened a gap and a reviewer will not see why the paper is needed. If M3 has no enumerated contribution, add one.

## 9. Phrasing Bank: Introduction Moves (verbatim)

Reuse these constructions, drawn verbatim from the exemplars. Adapt the content to your paper; keep the shape. Translate any dated terminology to house standard in your own prose.

**Move 1, claiming centrality and establishing the territory**
- "Social virtual reality (VR) refers to VR platforms that allow users to socialize with each other in the form of avatars in a virtual space [41]." (`ji2022vrbubble`)
- "Information visualization is a technique that enables people with normal vision to use their tremendous visual ability to explore data and discover trends." (`ZhaoPlaisantShneidermanLazar2008`)
- "The reason that indoor navigation is often more challenging than traveling outdoors is partly due to technical limitations, as GPS-based positioning is unreliable within large buildings [1]." (`giudice2020use`)
- "While most people's interactions with digital devices are visual, there is a growing need for people to consider alternative modes of communication with devices they use every day and everywhere." (`feng2015investigation`)
- "Visually impaired people face important challenges related to orientation and mobility. Indeed, 56% of visually impaired people in France declared having problems concerning autonomous mobility [10]." (`brock2015interactive`)
- "With more than two billion people experiencing visual impairments worldwide [53], it is vital to provide PVI equal access to the emerging social VR as virtual collaboration and gathering increases, especially during the COVID-19 pandemic [50]." (`ji2022vrbubble`)
- "Traditionally, raised-line paper maps with braille text have been used. These maps have proved to be efficient for the acquisition of spatial knowledge by visually impaired people. Yet, these maps possess significant limitations [37]." (`brock2015interactive`)

**Stating prior findings as synthesis**
- "Accurate nonvisual route navigation through complex commercial buildings has been shown with systems using ultra-wideband (UWB) positioning [11, 12], an infrared camera to detect retro-reflective barcodes [13], a smartphone's inertial sensors [14], RFID tags [15], and inertial dead-reckoning techniques coupled with infrared sensing [16]." (`giudice2020use`)
- "Past work on auditory displays has focused on four distinctive techniques: auditory icons, earcons, actual (synthetic or pre-recorded) speech and spearcons [13]." (`feng2015investigation`)
- "Some research leveraged or created additional devices (e.g., PHANToM, game controller thumbsticks) to enable VR navigation by providing haptic feedback and/or audio feedback [7, 24, 30, 46, 49, 68, 85]. Others focused on software solutions, designing accessible interactions based on existing VR setups..." (`ji2022vrbubble`)

**Move 2, signaling the gap (the niche)**
- "However, prior work mainly focused on basic VR tasks such as navigation and object perception. It does not address the unique barriers caused by the dynamic and multiplayer nature of social VR." (`ji2022vrbubble`)
- "To our knowledge, no existing techniques have focused on the avatar dynamics to support accessible social VR experience for PVI." (`ji2022vrbubble`)
- "However, little has been investigated regarding whether techniques in visualizations can be translated for use in auditory data exploration without visual aids and what design implications are involved." (`ZhaoPlaisantShneidermanLazar2008`)
- "However, despite their many benefits, there is still no clear single solution for solving the vexing indoor navigation challenge for BVI travelers." (`giudice2020use`)
- "Despite these demographic trends, none of the projects on indoor navigation systems for BVI users (discussed above) included an older cohort." (`giudice2020use`)
- "Prior to our project, the usability of accessible interactive maps had never been compared to the usability of raised-line maps with braille text. Therefore, it was unknown whether interactive maps were worse or better solutions than traditional raised-line maps." (`brock2015interactive`)

**Move 3, stating purpose and contribution (occupying the niche)**
- "We aim to fill this gap by enhancing PVI's awareness of surrounding avatars in social VR." (`ji2022vrbubble`)
- "Unlike prior work that required PVI to actively explore and query information from the environment [49, 85], we focus on peripheral awareness..." (`ji2022vrbubble`)
- "Rather than focusing on technical development, our emphasis here was on investigating how use of the navigation system impacted behavioral performance." (`giudice2020use`)
- "To overcome this lack of knowledge, we conducted a systematic user study, comparing these two different map types for visually impaired people [8]." (`brock2015interactive`)
- "Our general hypothesis was that an interactive map (IM) was more usable than a tactile paper map (PM) for providing blind people with spatial knowledge about a novel environment." (`brock2015interactive`)
- Enumerated contributions: "This article first describes a research framework for designing auditory interfaces for analytical data exploration." then "Second, guided by the ADC framework, we developed a general exploratory data analysis tool for users with visual impairment, called iSonic." then "Third, we conducted an empirical evaluation of iSonic." then "Fourth, we applied the ADC framework to scatterplots..." (`ZhaoPlaisantShneidermanLazar2008`)
- Numbered roadmap: "In the remainder of this article, we (1) provide a background of accessible indoor navigation systems, (2) give an overview of the system we used to support the study, (3) discuss the relevance of our variables of interest... (4) describe an in situ study... and (5) couch the findings..." (`giudice2020use`)

## 10. How the Exemplars Open (dissection)

- **`ZhaoPlaisantShneidermanLazar2008` (iSonic, TOCHI): the textbook funnel.** Move 1 claims centrality for information visualization, then names who it excludes. Move 2 states the gap ("little has been investigated regarding whether techniques in visualizations can be translated for use in auditory data exploration"). Move 3 poses an explicit list of research questions, then four enumerated contributions.
- **`ji2022vrbubble` (social VR, ASSETS): the page-one gap.** By the bottom of page 1 the reader knows the area, why it matters (market size, the COVID-era shift), the gap ("To our knowledge, no existing techniques have focused on the avatar dynamics"), and the contribution ("We aim to fill this gap by..."). It uses "barriers," matching house style.
- **`giudice2020use` (indoor navigation, TACCESS): funnel plus roadmap.** It funnels from why indoor navigation is intrinsically hard to the behavioral question the paper answers, and closes with a numbered five-part roadmap. This is the worked example in Section 11.

## 11. Worked Example: a Real Introduction, Annotated

Reproduced verbatim from `giudice2020use` (the paper's Section 1, Introduction). The numeric citations are the paper's own. Read it, then see the annotation below.

> **1 INTRODUCTION**
>
> The reason that indoor navigation is often more challenging than traveling outdoors is partly due to technical limitations, as GPS-based positioning is unreliable within large buildings [1]. Although various technologies have been tested for supporting indoor localization (see Reference [2] for review), none have yet emerged as a widespread and widely used standard analogous to GPS-based outdoor navigation. Beyond technical limitations, the indoor navigation challenge is exacerbated by the nature of indoor spaces, as buildings are usually multi-level 3D structures with limited naming conventions for the walkable regions or addressing schemes of specific locations, i.e., the street names and building addresses that support outdoor travel [3]. As a consequence, it is more difficult to accurately represent the building structure on a real-time navigation map or to provide turn-by-turn verbal route instructions, as is available with outdoor navigation systems. These differences frequently make indoor navigation, especially when finding routes through large buildings, more frustrating and error-prone [4–6].
>
> To help mitigate these indoor navigation challenges, architects and building developers utilize a host of aids to assist indoor wayfinding, such as maps, signs, directional arrows, alpha-numeric room labels, and color-coded cues for distinguishing different spatial regions. Most of these tools for self-orientation and localization are visual in nature. As a result, anybody navigating in large, complex buildings is at a particular disadvantage if they cannot visually access this key wayfinding information, as is the case for blind or visually impaired (BVI) travelers or in situations when vision is not available (e.g., the power goes out, emergency response scenarios, etc.).
>
> This is a well-known problem and the quest for a viable solution has motivated an active research community studying technological approaches to support nonvisual indoor navigation, primarily for use by BVI travelers.
>
> Rather than focusing on technical development, our emphasis here was on investigating how use of the navigation system impacted behavioral performance. Several human factors and user interface (UI) parameters were addressed in the study, including: perception vs. memory-based information access, participant age, visual status, and collaborative navigation techniques. Results from route navigation performance (quantitative evaluation) and system usability evaluations (qualitative feedback) demonstrated that people perform best when they have access to real-time (perceptual) guidance from a navigation system and that this benefit is similarly manifested for both older and younger BVI participants and between sighted and blind users. In the remainder of this article, we (1) provide a background of accessible indoor navigation systems, (2) give an overview of the system we used to support the study, (3) discuss the relevance of our variables of interest with respect to probing how (and for whom) accessible navigation systems are generally used, (4) describe an in situ study carried out in a large university building using our system, and (5) couch the findings in terms of how they relate to existing research with navigation systems and how the current data could be used to provide guidance and best practices for improving future research in this domain.

**How it maps to CARS.**
- **Move 1 (territory), paragraphs 1 and 2.** It establishes why the problem is hard (technical limits, the 3D nature of buildings) and who it affects (BVI travelers, plus sighted people when vision is unavailable). Note the synthesis: one difficulty supported by a grouped citation `[4–6]`.
- **Move 2 (niche), paragraph 3.** A compact pivot: the problem is "well-known" and has "motivated an active research community," which credits prior work while signaling that a viable solution is still open. (The full gap is then proven across the Related Work section; see Part 2.)
- **Move 3 (occupation), paragraph 4.** "Rather than focusing on technical development, our emphasis here was on..." states the angle, previews the result, and closes with a numbered five-part roadmap.

## 12. Intake Questions for the Introduction (answer before drafting)

Do not write until you have these. If the research question, the contribution, or length is missing, ask the author rather than inventing them.

- **The paper:** the topic in one sentence; the research question or hypothesis; the core contribution (the one new thing); the method or type (system, empirical study, tool, theory, dataset); the headline result, if known.
- **The gap:** the specific gap or limitation in prior work this paper addresses; the two to five closest prior works to differentiate against; any "first to" claim and how defensible it is.
- **length:** the length budget for the Introduction; whether there is a separate Related Work section (default: yes, so the Introduction stays tight).
- **Venue:** Assume ACM or IEEE journals.
- **Sources:** must-cite seminal and recent (last three to five years) works; the source of bibtex keys (default `CITATIONS.BIBTEX`).
- **Constraints:** any work to characterize carefully (avoid strawmanning); anything to exclude.

## 13. Generation Protocol for the Introduction

1. **Collect the Section 12 intake answers.** Ask for any missing load-bearing input. Do not invent facts, numbers, or keys.
2. **Assemble candidate sources** from `CITATIONS.BIBTEX`; confirm each key exists.
3. **Draft Move 1 (territory).** Open with the need or barrier, supported by a real, cited fact. Use the Section 9 phrasing.
4. **Draft Move 2 (the gap).** Synthesize the few most relevant sources into claims with grouped citations, then name the gap with neutral contrast (Section 2).
5. **Draft Move 3 (occupation).** State the aim, then an enumerated, refutable contributions list with forward references.
6. **Match the voice** (Section 4); translate dated terminology; remove every em-dash.
7. **Write the deliverable folder** (Section 3): the markdown draft and a `citations.bibtex` holding the bibtex entry for every key you cited, copied from `CITATIONS.BIBTEX`.
8. **Self-check** against Section 14.

## 14. Checklist for the Introduction

- [ ] Section 12 intake answered: research question, contribution, venue, gap.
- [ ] A clear Move 1, Move 2, and Move 3 are all present (the CARS test).
- [ ] The contribution is stated explicitly, enumerated, and refutable, with forward references.
- [ ] Synthesis, not summary: claims carry grouped citations; no citation salad.
- [ ] The gap is framed by neutral contrast, not by disparaging prior work.
- [ ] Every citation is a pandoc `@key` that exists in `CITATIONS.BIBTEX`; no invented statistics or citations.
- [ ] Voice matches the exemplars; no em-dashes; BLVI and disability-first language; "barrier" not "challenge"; "map" not "mapping".
- [ ] Output: the review is saved to its own folder containing the markdown draft and a `citations.bibtex` whose entries are exactly the keys cited, copied from `CITATIONS.BIBTEX`.

---

# Part 2: The Related Work Section

## 15. What the Related Work Section Is For

The Related Work section (usually Section 2, sometimes after the method) is the comprehensive, comparative survey the Introduction deliberately skipped. Its job is to prove, across the full neighboring literature, the gap the Introduction asserted, and to position your contribution precisely against every relevant line of work.

| | Introduction review (Part 1) | Related Work section (Part 2) |
|---|---|---|
| Purpose | Motivate and open the gap | Survey comprehensively and compare |
| Breadth | Only what motivates the work | Every neighboring theme |
| Length | A few paragraphs | One section, often with subsections |
| Organization | CARS funnel | Thematic hierarchy |
| Citation density | Selective | High |
| Where the contribution appears | Stated up front (Move 3) | Implied per theme, restated at the end |

**The no-redundancy rule.** Related Work must deepen, not repeat, the Introduction. The Introduction names the gap in two sentences; Related Work proves it theme by theme.

## 16. How to Structure the Related Work Section

- **Use a thematic hierarchy.** An H2 section, an H3 subsection per theme, and optional H4 sub-themes for finer distinctions. `ji2022vrbubble` is the model: `2.1 Accessibility of Virtual Environments` (with `2.1.1 Audio Techniques`, itself split into Audio beacons / Object Sonification / Echolocation / User Queried Verbal Descriptions, and `2.1.2 Haptic Solutions`), then `2.2 Accessibility of the Real World` (`2.2.1`, `2.2.2`).
- **One synthesized paragraph per theme.** Open with a claim about the theme, support it with grouped citations, then give one or two named examples (the "claim, then For example" pattern from Section 1).
- **Close every theme with its gap.** End each subsection with the limitation your paper addresses. This is the device that makes the cumulative case for your contribution unavoidable.
- **Funnel within each theme.** Move from broad prior work to the specific limitation, the same shape as the CARS funnel applied at theme scale.
- **Add a comparison table when you survey systems.** A table with one row per prior system and columns for your dimensions (modality, device, evaluation, population, code/data) lets a reviewer see coverage at a glance and is the artifact downstream researchers cite.
- **End with a bridge to the contribution.** A final paragraph that gathers the per-theme gaps and states what your paper does about them.
- **Optionally declare the search.** For a systematic survey, state how the literature was found, as `brock2015interactive` does: "In order to classify existing accessible interactive maps, we performed an exhaustive search through scientific databases (ACM Digital Library, SpringerLink, IEEE Explorer, and Google Scholar). We found 43 articles that were published between 1988 and 2013 that matched our inclusion criteria."

## 17. Phrasing Bank: Related Work Moves (verbatim)

Drawn verbatim from the exemplars. Translate dated terminology to house standard in your own prose.

**Opening a theme**
- "There has been extensive work that assisted PVI in exploring virtual environments via audio feedback. We summarize different types of audio techniques in prior work below." (`ji2022vrbubble`)
- "Prior work has also enhanced the accessibility of virtual environments for PVI by generating haptic feedback or creating haptic controllers [25, 33, 66–68, 75, 76, 81, 85]." (`ji2022vrbubble`)
- "As with virtual environments, a myriad of prior work has designed audio techniques to sonify real world environments, including using audio beacons to mark waypoints [20, 84], informing users about nearby objects and landmarks through verbal descriptions [15, 66], generating auditory icons or earcons to identify points of interest [39, 58], and providing echolocation or sonar systems to enable the exploration of surrounding environments [21, 77]." (`ji2022vrbubble`)

**Labeling a sub-theme, then giving an example**
- "Audio beacons. Audio beacons have been used to convey object positions [13, 35, 36, 79]. For example, Walker and Lindsay's [79] study utilized three different audio beacons in navigation guidance." (`ji2022vrbubble`)
- "Object Sonification. Prior work has also used audio to identify objects within the virtual space [3, 10, 19, 42, 55, 57, 63–65]. For example, de Oliveira et al. [10] recreated a virtual stage and placed instruments in the environment that generated spacial music." (`ji2022vrbubble`)

**Declaring the search (systematic survey)**
- "In order to classify existing accessible interactive maps, we performed an exhaustive search through scientific databases (ACM Digital Library, SpringerLink, IEEE Explorer, and Google Scholar). We found 43 articles that were published between 1988 and 2013 that matched our inclusion criteria." (`brock2015interactive`)

**Naming a foundational contributor (narrative background)**
- "Gaver coined the term "auditory icons" in a 1986 article of the same title: "auditory icons are caricatures of naturally occurring sounds such as bumps, scrapes, or even files hitting mailboxes" [6]." (`feng2015investigation`)
- "Blattner et al. [3] developed the concept of "abstract earcons": musical "motives" that can be grouped to form "families, where earcons with similar meanings have similar sounds"." (`feng2015investigation`)

**Closing a theme with its gap**
- "However, the echolocation method was only used by a small amount of blind people." (`ji2022vrbubble`)
- "Similar to audio techniques for virtual worlds, these solutions also do not address the dynamic complexity of avatars in a social VR context." (`ji2022vrbubble`)
- "However, this work does not design for the unique challenges posed by a social context." (`ji2022vrbubble`)
- "However, despite their many benefits, there is still no clear single solution for solving the vexing indoor navigation challenge for BVI travelers." (`giudice2020use`)

**Bridging to the contribution (end of the section)**
- "Prior research on VR accessibility focuses on space navigation and object perception. However, social VR introduces additional complications with the dynamic and non-uniform avatars that present social implications. No research has addressed the accessibility of avatars in social VR. Our research aims to fill this gap by facilitating PVI's awareness of avatars in social VR via customizable audio techniques." (`ji2022vrbubble`)

## 18. How the Exemplars Structure Related Work (dissection)

- **`ji2022vrbubble`: the model thematic hierarchy.** Two top-level themes, each with sub-themes, each subsection a synthesized paragraph that ends with the gap it leaves. The pattern is reproduced in Section 19.
- **`brock2015interactive`: a taxonomy.** The related work is organized as a classification of prior maps by device class (haptic, tactile-actuator, touch-sensitive, other), introduced by an explicit exhaustive-search statement. Use this when your contribution is itself an organizing framework.
- **`giudice2020use`: synthesis plus a stacked gap.** Its `2 BACKGROUND AND RELEVANT RESEARCH` supports a singTle claim with five grouped technologies, then opens a second, demographic gap ("none of the projects on indoor navigation systems for BVI users... included an older cohort"), sharpening the contribution.
- **`feng2015investigation`: narrative background.** Its `2 BACKGROUND` walks named contributors (Gaver, Blattner, Brewster) in sequence. Readable, but use sparingly: prefer thematic synthesis over a researcher-by-researcher narrative for anything but a short background.

## 19. Worked Example: a Real Related Work Section, Annotated

Reproduced verbatim from `ji2022vrbubble` (the paper's Related Work, Section 2). This is an excerpt: subsection `2.1` and the opening of `2.2` are shown; the section continues with `2.2.1` and `2.2.2` in the same pattern. The numeric citations are the paper's own.

> **2 RELATED WORK**
>
> **2.1 Accessibility of Virtual Environments**
>
> *2.1.1 Audio Techniques for VR accessibility.* There has been extensive work that assisted PVI in exploring virtual environments via audio feedback. We summarize different types of audio techniques in prior work below.
>
> Audio beacons. Audio beacons have been used to convey object positions [13, 35, 36, 79]. For example, Walker and Lindsay's [79] study utilized three different audio beacons in navigation guidance. They observed the impacts on PVI's navigation performance as they changed various parameters, such as timbre and distance to a waypoint to trigger the audio. Maidenbaum et al. [36] provided a beeping sound based on the distance between the PVI's avatar and the virtual object in front of them to facilitate navigation in a virtual space. As the avatar got closer to the object, the beeping rose in frequency of beeps. Blind Swordsman [13] was a VR game on mobile devices, where a blind user can hear the spatial audio beacon from the enemies, physically turn to that direction, and tap the touchscreen to swing his sword in the direction he is facing.
>
> Object Sonification. Prior work has also used audio to identify objects within the virtual space [3, 10, 19, 42, 55, 57, 63–65]. For example, de Oliveira et al. [10] recreated a virtual stage and placed instruments in the environment that generated spacial music. Participants then listened to the music tracks to identify and locate instruments on the stage. Heuten et al. [19] presented a sonification interface to virtual maps for PVI. AudioDoom [63, 64] was an acoustic virtual environment designed for blind children.
>
> Echolocation. Virtual echolocation has been emulated through signals and audio reflections [2, 80, 83]. For example, Andrade et al. [2] enabled PVI to use echolocation to navigate a desktop-based virtual world, where the user's avatar can produce mouth-click or clap sounds by pressing a key on a keyboard and hear the sound reflected in the environment. However, the echolocation method was only used by a small amount of blind people.
>
> *2.1.2 Haptic Solutions for VR accessibility.* Prior work has also enhanced the accessibility of virtual environments for PVI by generating haptic feedback or creating haptic controllers [25, 33, 66–68, 75, 76, 81, 85]. For example, Jansson et al. [25] enabled PVI to use the stylus on a Phantom Premium device to "touch" a virtual space and receive force feedback to perceive different virtual surfaces and objects. In the same vein, Zhao et al. created Canetroller [85], a wearable haptic VR controller that simulated white cane interaction for blind people in virtual reality.
>
> Prior research on VR accessibility focuses on space navigation and object perception. However, social VR introduces additional complications with the dynamic and non-uniform avatars that present social implications. No research has addressed the accessibility of avatars in social VR. Our research aims to fill this gap by facilitating PVI's awareness of avatars in social VR via customizable audio techniques.
>
> **2.2 Accessibility of the Real World**
>
> As with virtual environments, a myriad of prior work has designed audio techniques to sonify real world environments, including using audio beacons to mark waypoints [20, 84], informing users about nearby objects and landmarks through verbal descriptions [15, 66], generating auditory icons or earcons to identify points of interest [39, 58], and providing echolocation or sonar systems to enable the exploration of surrounding environments [21, 77]. Similar to audio techniques for virtual worlds, these solutions also do not address the dynamic complexity of avatars in a social VR context.

**How it is built.**
- **Thematic hierarchy.** The theme (`2.1 Accessibility of Virtual Environments`) splits into sub-themes (`2.1.1 Audio Techniques`, itself split into Audio beacons / Object Sonification / Echolocation, then `2.1.2 Haptic Solutions`). Each unit is a synthesized paragraph, not a per-paper summary.
- **Claim, then "For example".** Every sub-theme opens with a claim carrying grouped citations ("Audio beacons have been used to convey object positions [13, 35, 36, 79]"), then names one or two studies.
- **Theme-closing gaps.** Echolocation ends "However, the echolocation method was only used by a small amount of blind people." The whole `2.1` theme ends with the bridge paragraph ("No research has addressed the accessibility of avatars in social VR. Our research aims to fill this gap..."), and `2.2` ends "these solutions also do not address the dynamic complexity of avatars in a social VR context."
- **Cumulative case.** Because every theme closes on the same missing capability (avatar dynamics in social VR), the contribution is inevitable by the end of the section. Build your Related Work so its gaps converge the same way.

## 20. Intake Questions for the Related Work Section

Answer the Part 1 intake (Section 12) first; it applies here too. Then add:

- Is there a separate Related Work section, or is the review folded into the Introduction? (If folded, write only Part 1.)
- What are the themes (and sub-themes) the literature splits into? Aim for two to five top-level themes.
- Which themes belong in the Introduction (briefly) versus the Related Work section (in depth)?
- Is a comparison table expected, and what are its columns (the dimensions that distinguish your work)?
- What is the page or paragraph budget for the section?
- Does the venue expect a stated search method (systematic) or an author-curated survey (narrative)?

## 21. Generation Protocol for the Related Work Section

1. **Collect intake** (Section 20, plus Section 12). Confirm there is a separate Related Work section; if not, stop and write only the Introduction.
2. **Cluster the sources into themes** from `CITATIONS.BIBTEX`, two to five top-level themes, with sub-themes where a theme is large.
3. **Per theme, write one synthesized paragraph:** a claim with grouped citations, then one or two named examples (Section 1 pattern), then the theme-closing gap (Section 2).
4. **Build the comparison table** if expected, one row per prior system, columns for your distinguishing dimensions.
5. **Write the bridge paragraph** that gathers the per-theme gaps and states the contribution.
6. **Check against the Introduction:** the section must deepen, not repeat it (Section 15).
7. **Match the voice** (Section 4); translate dated terminology; remove every em-dash.
8. **Write the deliverable folder** (Section 3): the markdown draft and a `citations.bibtex` holding the bibtex entry for every key you cited, copied from `CITATIONS.BIBTEX`.
9. **Self-check** against Section 22.

## 22. Checklist for the Related Work Section

- [ ] Section 20 intake answered; a separate Related Work section is actually wanted.
- [ ] Organized by theme (a thematic hierarchy), not one paragraph per source.
- [ ] Every theme opens with a synthesized claim carrying grouped citations.
- [ ] Every theme closes with the specific gap your paper addresses.
- [ ] A comparison table is present if the venue or topic expects one, not present by default.
- [ ] A final bridge paragraph maps the accumulated gaps to the contribution.
- [ ] The section deepens rather than repeats the Introduction.
- [ ] Every citation is a pandoc `@key` that exists in `CITATIONS.BIBTEX`; no invented statistics or citations.
- [ ] Voice matches the exemplars; no em-dashes; BLVI and disability-first language; "barrier" not "challenge"; "map" not "mapping".
- [ ] Output: the review is saved to its own folder containing the markdown draft and a `citations.bibtex` whose entries are exactly the keys cited, copied from `CITATIONS.BIBTEX`.

---

## Sources

Author guidance and writing references consulted:

- [John Swales, Create-A-Research-Space (CARS) model, USC Libraries](https://libguides.usc.edu/writingguide/CARS) and [CARS primer (PDF)](https://iuuk.mff.cuni.cz/~andrew/EAP/CaRS.pdf)
- [Simon Peyton Jones, How to Write a Great Research Paper](https://simon.peytonjones.org/great-research-paper/)
- [IEEE Author Center, Structure Your Article (journals)](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-the-text-of-your-article/structure-your-article/) and [Structure Your Paper (conferences)](https://conferences.ieeeauthorcenter.ieee.org/write-your-paper/structure-your-paper/)
- [ACM CHI Guide to a Successful Submission](https://chi2026.acm.org/guide-to-a-successful-submission/)
- [Purdue OWL, Synthesizing Sources](https://owl.purdue.edu/owl/research_and_citation/conducting_research/research_overview/synthesizing_sources.html)
- [USC Libraries, The Literature Review](https://libguides.usc.edu/writingguide/literaturereview)
- [UNC Writing Center, Literature Reviews](https://writingcenter.unc.edu/tips-and-tools/literature-reviews/)
- [GMU Writing Center, Organizing Literature Reviews](https://writingcenter.gmu.edu/writing-resources/research-based-writing/organizing-literature-reviews-the-basics)
- [Manchester Academic Phrasebank, Introducing Work](https://www.phrasebank.manchester.ac.uk/introducing-work/)

Collection exemplars, the quality bar (the verbatim excerpts above are drawn from these):

- `feng2015investigation` (`Feng_2015_InvestigationIntoComprehensionMap`): auditory map comprehension; narrative background by named contributors.
- `ZhaoPlaisantShneidermanLazar2008` (`Zhao_2008_DataSonificationUsersVisual`): iSonic, ACM TOCHI; textbook CARS funnel with enumerated contributions.
- `brock2015interactive` (`Brock_2015_InteractiveAudioTactileMaps`): interactive audio-tactile maps; taxonomic related work with an exhaustive-search statement.
- `giudice2020use` (`Giudice_2020_UseIndoorNavigationSystem`): ACM TACCESS; the worked Introduction; grouped-citation synthesis and a stacked gap.
- `ji2022vrbubble` (`Ji_2022_VRBubble`): ASSETS; the worked Related Work; thematic hierarchy with theme-closing gaps.
