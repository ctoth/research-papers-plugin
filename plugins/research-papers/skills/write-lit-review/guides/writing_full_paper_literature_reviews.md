# Writing a Top-Quality ACM or IEEE Literature Review

A practical guide for producing literature reviews that survive desk review at ACM Computing Surveys (CSUR), IEEE Communications Surveys & Tutorials (COMST), ACM/IEEE topical journals (TOCHI, ASSETS, TACCESS, IEEE Access, IEEE TVCG), and venue tracks that accept survey or review papers (CHI, ASSETS, SIGSPATIAL, VR, ISMAR, etc.).

The guide is grounded in two sources: (1) published ACM/IEEE review and survey papers in this Bibliography collection (the Correa de Almeida 2023 PRISMA review at ACM SVR, the Kuriakose 2022 IETE/IEEE-style narrative review, the Morash-Macneil 2018 systematic review, the Chouvardas 2005 IEEE-supported tactile-displays survey, and the in-collection notes for these papers), and (2) the official author guidelines for ACM CSUR, IEEE COMST, the PRISMA 2020 statement, and the Kitchenham & Charters EBSE-2007-001 protocol for systematic reviews in software engineering.

---

## 1. Pick the Right Review Type First

The single most expensive mistake is writing the wrong kind of review for the venue. ACM and IEEE recognise four broadly distinct artifacts; the desk-review criteria differ.

| Type | What it does | Where it fits | Citation count typical | Distinguishing requirement |
|------|--------------|---------------|------------------------|----------------------------|
| **Narrative literature review** | Author-curated synthesis organized by themes; selection driven by author judgment | Journal "review" tracks, book chapters, IEEE Access | 50-150 | A clear thematic argument |
| **Tutorial article** | Teaches a reader who is new to the topic; introduces concepts, formalism, worked examples | IEEE COMST (tutorial type), CSUR (tutorial type), Foundations & Trends | 30-100 | Pedagogical clarity; selected references, not exhaustive |
| **Systematic literature review (SLR)** | Reproducible search + screen + extract + synthesize against a registered protocol | ACM CSUR, IEEE COMST, ASSETS, CHI (with full method), domain journals | 50-200 included; many more screened | Auditable protocol; PRISMA-style flow |
| **Comprehensive survey** | Integrates a field through an original taxonomy or analytical framework; tutorial in nature | **ACM CSUR**, IEEE COMST | **100-300+** | **Original taxonomy or analytical framework** (this is the CSUR rejection trigger; see §6) |

**Practical rule.** If you cannot answer the question "what is your original taxonomy or analytical framework?" in one sentence, you do not yet have a CSUR-class survey. You have either an SLR (in which case lean on PRISMA and a registered protocol) or a narrative review (in which case target a topical journal, not CSUR).

The Correa de Almeida 2023 paper in this collection (ACM SVR'23) is an example of a **short PRISMA-style systematic review**: 5 pages, 24 included papers, narrative synthesis, no original taxonomy. It works for a workshop venue. It would not survive CSUR.

The Kuriakose 2022 IETE Technical Review is an example of a **narrative review with taxonomic synthesis**: ~143 references, five-axis taxonomy (visual / non-visual / map-based / 3D-sound / smartphone), seven concrete design recommendations. That hybrid (taxonomy + recommendations) is the floor for a serious journal review.

---

## 2. House-Style Differences Between ACM and IEEE Review Venues

The two publishers' review tracks are similar in spirit but diverge on a few hard rules.

### ACM Computing Surveys (CSUR)

- **Hard requirement:** an original taxonomy, analytical framework, or comparison methodology. A chronological catalog of recent work is a near-automatic desk rejection.
- **Length:** typically 30-50 pages in the ACM Surveys style; long surveys must not exceed 35 pages including references in the older long-survey track. Confirm the current ceiling on the journal page.
- **References:** 100-300+ for comprehensive surveys; coverage gaps trigger revision requests.
- **Recency check:** no comparable CSUR survey on the same topic in the past 3-5 years, or a clearly articulated distinct angle.
- **Required elements:** taxonomy or framework figure in the introduction; comparison table organizing the surveyed literature; discussion identifying open problems and future directions; cover letter establishing original contribution.

### IEEE Communications Surveys & Tutorials (COMST)

- **Hard requirement:** authors must state the article category (survey vs. tutorial) in both the abstract and the introduction.
- **Length:** 30 pages max for new submissions in double-column format; less than 40 pages after revision. Excess pages incur charges.
- **Tutorial tone:** "tutorial in nature... comprehensible to readers outside the specialty." Mathematical equations should be kept to a minimum unless vital.
- **Plagiarism / dual submission:** rejection plus a 6-month submission ban.
- **References:** numbered sequentially, not alphabetically. Surveys expect liberal, authoritative citation; tutorials expect a curated selected-reference list.
- **No limits on figures or references for surveys**, but the page limit is binding.

### ACM topical journals and conferences (TOCHI, ASSETS, TACCESS, CHI, ISS, SIGSPATIAL, VR)

- Review papers are accepted but rarer; CHI and ASSETS treat literature reviews as full-paper submissions evaluated on the same criteria as empirical work (contribution, rigor, novelty).
- Page limits follow the venue's standard track (CHI: ~9-12 pages excluding refs; ASSETS: ~12-14 pages).
- A PRISMA-style figure is now expected if you describe the work as "systematic."
- Reviewer expectation: a clear claim about what the synthesis adds beyond the cited papers individually. This is the same demand CSUR makes, just under a different rubric.

### IEEE topical magazines and journals (IEEE Access, IEEE TVCG, IEEE Pervasive)

- IEEE Access is open access and accepts comprehensive reviews; rapid turnaround; high bar for clarity but moderate bar for novelty of framework. Good fit for tutorial-style reviews that would not survive CSUR's taxonomy demand.
- TVCG and Pervasive treat reviews like full papers: novel framing required.

---

## 3. The Eight Phases of a Defensible Review

These phases are common to Kitchenham & Charters' EBSE-2007-001 SLR protocol, PRISMA 2020, and the methodological guidelines for communications surveys (arXiv 2509.25828). They map onto every venue above.

### 3.1 Topic selection and research questions

Pick a scope where you can plausibly defend coverage. Write 3-6 research questions (RQs) before any searching. Examples from the Correa de Almeida ACM SVR review:

> RQ1. What is the state of the art of Spatial Audio in VR?
> RQ2. How can Spatial Audio help in the VR Experience?
> RQ3. What are the main limitations in Spatial Audio Technology?
> RQ4. How can we apply these technologies?
> RQ5. What are the next possible steps?

Each RQ should map to a section in the eventual paper. If two RQs collapse to the same extraction, merge them. If one RQ requires data your search will not surface, drop it.

**Scope test.** A CSUR-class topic typically supports 100+ relevant primary studies. If you find fewer than ~30 after a thorough search, your scope is too narrow for a comprehensive survey; pivot to a tutorial or focus the topic further.

### 3.2 Protocol registration

For systematic reviews, register the protocol before screening. Options:

- **PROSPERO** (international register; standard for health-adjacent HCI work).
- **OSF Registries** (preferred for HCI, accessibility, and software-engineering SLRs).
- **An appendix in the submitted paper.** Lower-trust but acceptable for many venues.

The protocol fixes RQs, databases, search strings, inclusion/exclusion criteria, screening procedure (single- vs multi-reviewer; inter-rater agreement target), data-extraction template, and quality-assessment rubric. Once registered, deviations must be reported with rationale.

### 3.3 Search strategy

Use multiple databases. The Correa de Almeida review used three (SCOPUS, IEEE Xplore, AES E-Library). Kuriakose used five (ACM Digital Library, IEEE Xplore, ScienceDirect, PubMed, Sensors). For ACM/IEEE-targeted topics, the minimum credible set is:

- **ACM Digital Library**
- **IEEE Xplore**
- **Scopus** or **Web of Science** (cross-publisher coverage)
- One domain-specific database (PubMed for health-adjacent work; AES E-Library for audio; arXiv for ML/AI; SpringerLink for LNCS conference proceedings)

Document the exact Boolean search string per database. A reproducible string looks like:

```
("spatial audio" OR "3D audio" OR "ambisonic" OR "binaural")
AND ("virtual reality" OR "VR" OR "head-mounted display" OR "HMD")
AND PUBYEAR > 2011
```

Run the search on a recorded date. Snowball both directions (backward via references, forward via citation tracking in Google Scholar or Scopus) on the included set; document any additions.

### 3.4 Screening

PRISMA 2020 expects a flow diagram showing identification, screening, eligibility, and inclusion counts at each stage. Reproduce the funnel as a table in the paper as well as a figure. A worked example from the Correa de Almeida review:

| Stage | Count |
|------|------|
| SCOPUS + IEEE Xplore + AES E-Library raw | 357 |
| After duplicate removal | 313 |
| Duplicates removed | 44 |
| Abstract screening — excluded | 260 |
| Abstract screening — passed | 53 |
| Full paper screening — excluded | 16 |
| Full paper screening — passed | 37 |
| No-access exclusion | 13 |
| Final included | 24 |

For credibility, two reviewers should screen independently with Cohen's kappa reported for inter-rater agreement; a third reviewer or consensus resolves disagreements. Single-reviewer screening is acceptable in narrative reviews but should be acknowledged as a limitation.

### 3.5 Quality assessment

Apply a per-study quality rubric. Common options:

- **Critical Appraisal Skills Programme (CASP)** checklists for qualitative and quantitative studies.
- **Kitchenham QA**: a short rubric with three or four items scored 0/0.5/1, then a per-study composite (e.g., "Are the aims clearly stated?", "Is the study design appropriate?", "Are findings clearly reported?", "Is the study limited?").
- Domain-specific rubrics (e.g., Joanna Briggs Institute for mixed-methods; ROBINS for non-randomized).

The Correa de Almeida review skips formal quality scoring; its own Limitations section flags this, which is the minimum honest disclosure if you also choose to skip.

### 3.6 Data extraction

Build a single spreadsheet with one row per included study and one column per RQ-driven data field. Typical columns:

- Citation key, year, venue, venue type (conference / journal / workshop)
- Population / context / setting
- Method (empirical / theoretical / tool / system)
- RQ1 extraction, RQ2 extraction, ... (one column per question)
- Outcome measures (if applicable)
- Reported limitations
- Quality score
- Notes / quotes with page numbers

Two reviewers extract independently for a sample (10-20% of included studies) to calibrate; one reviewer extracts the rest. Page-number anchors for every extracted quote let reviewers and future readers verify your claims; this collection's own `notes.md` template enforces this discipline and is a good model.

### 3.7 Taxonomy construction

This is the step that separates publishable surveys from rejected literature reviews, especially at CSUR. A taxonomy is not a list of headings. It is a structured organizing framework with:

- **Mutually exclusive and collectively exhaustive top-level categories.** Every included paper should fit one and only one cell (or have an explicit cross-classification rule).
- **Discriminating dimensions.** What property of a paper places it in one cell vs. another? The Kuriakose review uses sensing modality (visual / non-visual / map-based / 3D-sound / smartphone). A Chouvardas-style hardware survey uses actuator class (pressure-based / vibration-based / electric / thermal / electrorheological / polymeric).
- **A justification for the chosen axes.** Why these axes and not others? The argument should appear in §3 ("Taxonomy") of the paper.
- **A figure in the introduction.** A tree or matrix diagram showing the taxonomy, with the page or section where each branch is unpacked.
- **A comparison table.** One row per included paper, columns matching the taxonomy axes plus key properties (year, venue, dataset, modality, evaluation, code/data availability).

The taxonomy is constructed iteratively: a first cut is proposed during protocol design, then refined as the data extraction surfaces papers that do not fit. Document the refinements in the methodology section so reviewers see the evolution rather than guessing at it.

### 3.8 Synthesis

Two synthesis modes:

- **Narrative synthesis** is the default for HCI, accessibility, and most ACM/IEEE survey domains. Group by taxonomy cell; for each cell, summarize what the included papers found, what disagreements exist, and what remains open.
- **Meta-analytic synthesis** (effect-size pooling) is appropriate when the included studies share comparable outcome measures and designs. Rare in HCI; common in evidence-based medicine and increasingly in evaluation-of-AI literature.

For each taxonomy cell, write a paragraph or subsection answering: (a) what is known, (b) what is contested, (c) what is missing. The "what is missing" content feeds directly into §8 ("Open Problems") of the paper.

---

## 4. Canonical Structure for an ACM/IEEE Review

```
Abstract
  - Declare article category (survey | tutorial | systematic review) explicitly (COMST requires this)
  - State the original taxonomy or framework in one sentence
  - Quantify scope: N included papers, M years, K databases

1. Introduction
  - Why this topic now (timeliness)
  - Why an existing CSUR/COMST survey does not already cover it
  - Original contribution: state the taxonomy / framework explicitly
  - Research questions
  - Roadmap of the paper

2. Background
  - Core terminology
  - Foundational concepts; cite the canonical references
  - For tutorials, this section may dominate

3. Methodology
  - Review type and rationale
  - Protocol registration link (or appendix)
  - Databases queried; search strings (verbatim); search date
  - Inclusion / exclusion criteria
  - Screening procedure; PRISMA flow figure
  - Quality assessment rubric
  - Data extraction template
  - Limitations of the methodology

4. Taxonomy / Framework
  - The taxonomy figure
  - Axis-by-axis explanation
  - Cross-classification rules
  - Comparison table indexed by the taxonomy

5. State of the Art (organized by the taxonomy)
  - One subsection per top-level taxonomy branch
  - Within each subsection, organize sub-branches and salient examples
  - Use sub-tables to surface contrasts (year, technique, dataset, evaluation)

6. Cross-cutting Analysis
  - Patterns across cells: which combinations are over-studied, which are under-studied?
  - Methodological trends (datasets, evaluation methods, reproducibility, open-source release)
  - Disagreements in the literature

7. Discussion
  - Implications for researchers
  - Implications for practitioners
  - Limitations of the survey itself (scope, time window, language, database coverage, exclusion criteria)

8. Open Problems and Future Directions
  - Per-cell open problems
  - Cross-cutting open problems
  - Concrete suggested research agendas; not vague "more work is needed"

9. Conclusion
  - One-paragraph re-statement of contribution
  - The one or two findings that should reach a reader who only reads the conclusion

References
  - Numbered sequentially (IEEE); ACM style for ACM venues
  - 100-300+ for a CSUR-class survey
```

A tutorial article reorders this slightly: §2 (Background) is the largest section and contains the worked examples; §5 (State of the Art) is replaced by an exposition of the technique itself.

---

## 5. Tables, Figures, and Visualisations That Reviewers Expect

Reviewers at both ACM and IEEE survey venues actively look for these artifacts. Their absence is treated as a signal of insufficient rigor.

1. **PRISMA flow diagram** (figure) showing identification → screening → eligibility → inclusion counts. PRISMA 2020 provides a template; use the official one. Reproduce as a table for accessibility (the Bibliography collection's `notes.md` template demonstrates the pattern).
2. **Taxonomy figure** in the introduction: a tree or matrix showing the organizing framework with section / page references for each branch.
3. **Comparison table** indexed by the taxonomy with one row per included paper. Columns typically include: citation, year, venue, the taxonomy axes, dataset / corpus, evaluation method, code / data availability, key contribution. This is the table reviewers and downstream researchers actually cite.
4. **Timeline figure** showing the temporal distribution of included papers, often with overlaid technology milestones. Helpful when the field has had distinct generations of work.
5. **Per-cell summary tables** within state-of-the-art sections, repeating the comparison-table columns but filtered to one taxonomy branch. Makes the survey scannable.
6. **Open-problems table** in §8 organized by taxonomy cell, with one or two concrete research agendas per cell.

For accessibility (and for the venues this collection serves), every figure must have a text-equivalent table or full prose description. Do not put load-bearing content only in a figure.

---

## 6. The Single Most Common Rejection Trigger

For ACM CSUR specifically:

> Literature review framing without an original taxonomy, analytical framework, or comparison methodology.

A "review of the literature" alone is not a survey contribution. The contribution is the **organizing structure** you impose on the literature, defended by the synthesis. Write the taxonomy first, in one paragraph in the cover letter, then defend it in the paper.

Other common desk-rejection or major-revision triggers across ACM and IEEE survey venues:

- Reference count too low (<100 for CSUR-class; <50 for tutorial-style at IEEE Access).
- Scope overlapping a recent CSUR or COMST survey without a clearly articulated distinct angle.
- Cover letter argues "comprehensiveness" rather than "novel contribution."
- No methodology section, or a methodology section that does not show how papers were found and selected.
- Math-heavy survey at COMST (their style is tutorial; mathematics should be vital, not decorative).
- Single-reviewer screening with no acknowledged limitation.
- Dead links and missing DOIs in the reference list.
- Out-of-date final searches: if the most recent included paper is more than 18 months before submission, expect a request to refresh.

---

## 7. Writing Tone

Both ACM and IEEE survey venues expect a tutorial register: the reader is not a specialist in the cell of the taxonomy they are reading about, even if they are a specialist in the broader area.

- **Define every domain term on first use.** Cite the canonical reference for the definition.
- **Prefer prose to bullet lists** in the synthesis sections; bullets are appropriate in tables, recommendations, and open-problem catalogs.
- **Cite liberally but precisely.** Every quantitative claim ("most systems are over 5kg", "audio-only navigation produces 12% lower error rates") should carry a citation. If the claim is your synthesis across multiple studies, cite the studies that ground the claim, not a single representative.
- **Avoid editorialising adjectives.** "Sophisticated", "elegant", "groundbreaking" do not belong. Replace with quantified comparisons.
- **Treat negative results as first-class.** A survey that only reports what worked is an advertising brochure, not a survey. The Kuriakose review's blunt "all surveyed approaches fail to meet at least one of the user-centric / humanitarian criteria" is a model of the right register.
- **Disability-first language and current terminology.** For accessibility-adjacent topics, the standard is "blind and low-vision (BLVI)", "blind people" (not "people who are blind"), "people with disabilities (PWDs)". For map work, use "map" not "mapping" when describing a viewer/editor product.
- **No em-dashes.** Use commas, parentheses, or rephrase. En-dashes in numeric ranges are fine. (House rule of the XR Navigation Communications repository this guide lives in; also a common request in copy-edit at IEEE.)

---

## 8. Pre-Submission Checklist

Use this list as a final pass before submission. Each unchecked item is a likely revision request.

**Scope and contribution**
- [ ] Article type declared in abstract and introduction (COMST requirement).
- [ ] Original taxonomy or analytical framework stated in one sentence in the abstract.
- [ ] No comparable CSUR/COMST survey from the past 3-5 years on the same topic, or distinct angle clearly stated.
- [ ] Cover letter argues novel contribution, not comprehensiveness.

**Methodology**
- [ ] 3+ databases queried; exact search strings reported per database; search date recorded.
- [ ] Inclusion / exclusion criteria stated before screening.
- [ ] PRISMA flow figure and equivalent table included.
- [ ] Two-reviewer screening with Cohen's kappa, or single-reviewer with explicit limitation.
- [ ] Quality assessment rubric applied to all included studies.
- [ ] Backward and forward snowballing on the included set.
- [ ] Data-extraction template described or included in an appendix.

**Taxonomy and synthesis**
- [ ] Taxonomy figure in the introduction with axis-by-axis explanation in §4.
- [ ] Comparison table indexed by the taxonomy, one row per included paper.
- [ ] Per-cell synthesis sections in §5 covering what is known, what is contested, what is missing.
- [ ] Cross-cutting analysis in §6 surfaces patterns across cells.
- [ ] Open problems in §8 are concrete and per-cell, not vague.

**References**
- [ ] 100-300+ references for a CSUR-class survey; 50+ for a tutorial-style review.
- [ ] References numbered sequentially (IEEE) or ACM-styled.
- [ ] DOIs / arXiv IDs / URLs included.
- [ ] No dead links.
- [ ] Most recent included paper is within 18 months of submission date.

**Quality and writing**
- [ ] Tutorial register accessible to non-specialists.
- [ ] Equations minimised at COMST; load-bearing only.
- [ ] Every figure has a text-equivalent table or full prose description.
- [ ] Disability-first language used where applicable.
- [ ] No em-dashes.
- [ ] Limitations section acknowledges scope, time window, language, database coverage, and screening procedure honestly.

---

## 9. A Walkthrough Using a Collection Example

The Correa de Almeida 2023 ACM SVR paper "Spatial Audio in Virtual Reality: A systematic review" provides a worked example of the minimum credible PRISMA-style review.

| Element | What they did | Verdict |
|---------|---------------|---------|
| Type declaration | "Systematic review" in title and abstract | Good |
| Research questions | Five RQs stated upfront | Good |
| Databases | 3 (SCOPUS, IEEE Xplore, AES E-Library) | Acceptable; would want 4-5 for journal |
| Search string | Implied, not verbatim | Weak; major revision risk at CSUR |
| Inclusion / exclusion | English, 2012-2023, full-text accessible, dealing with spatial audio in VR/AR | Adequate |
| PRISMA flow | Figure 2; 357 → 24 | Good |
| Quality assessment | None | Acknowledged as a limitation; acceptable for a workshop, not for CSUR |
| Taxonomy | None; categories are descriptive (advantages / limitations / applications) | This is the gap that limits the paper to workshop venues |
| Comparison table | None | Major gap |
| Synthesis | Narrative; three-part (advantages / limitations / applications) | Adequate at the workshop scope |
| References | ~35 | Far below CSUR floor; appropriate for a 5-page workshop |
| Open problems | Implicit | Could be sharpened |

To move this paper toward a CSUR-class survey, the authors would need to: (1) expand to 100+ included papers, (2) construct an original taxonomy along axes such as `audio format × use context × hardware tier × evaluation type`, (3) add a comparison table indexed by that taxonomy, (4) apply a quality rubric, (5) sharpen open problems per taxonomy cell, and (6) commit to a 30-50 page treatment.

The Kuriakose 2022 IETE review is closer to publishable journal-survey form: ~143 references, a five-axis taxonomy, seven concrete recommendations, but it skips PRISMA-level rigour on screening and is honest about that limitation. It would be a strong fit for IEEE Access; at COMST it would need a tighter scope and a stronger framework defense; at CSUR it would need both PRISMA rigour and a more analytical taxonomy.

---

## 10. Recommended Reading

Methodology and protocol references to cite (and to actually consult) when writing the methodology section:

- **PRISMA 2020 statement** (Page et al., 2021) — 27-item checklist, abstract checklist, revised flow diagrams. The canonical reporting standard.
- **PRISMA 2020 Explanation and Elaboration** (Page et al., 2021) — exemplars for each checklist item.
- **Kitchenham & Charters, EBSE-2007-001** — "Guidelines for performing Systematic Literature Reviews in Software Engineering." The de-facto SLR protocol in computing.
- **ACM Computing Surveys Author Guidelines** — the binding rulebook for CSUR submissions, including the taxonomy requirement.
- **IEEE Communications Surveys & Tutorials Policies and Guidelines** — page limits, citation expectations, the tutorial-tone requirement.
- **From Literature to Insights: Methodological Guidelines for Survey Writing in Communications Research** (arXiv 2509.25828) — recent practical synthesis of survey-writing methodology with PRISMA, taxonomy construction, and pitfalls.

---

## Sources

Author guidelines and methodology references consulted:

- [ACM Computing Surveys Author Guidelines](https://dl.acm.org/journal/csur/author-guidelines)
- [ACM Computing Surveys Submission Guide (2026)](https://manusights.com/blog/acm-computing-surveys-submission-guide)
- [ACM Computing Surveys Editor Guidelines](https://dl.acm.org/journal/csur/associate-editor-guidelines)
- [IEEE Communications Surveys & Tutorials Policies and Guidelines](https://www.comsoc.org/publications/journals/ieee-comst/policies-guidelines)
- [IEEE Communications Surveys & Tutorials Call for Papers](https://www.comsoc.org/publications/journals/ieee-comst/call-for-papers)
- [From Literature to Insights: Methodological Guidelines for Survey Writing in Communications Research (arXiv 2509.25828)](https://arxiv.org/pdf/2509.25828)
- [The PRISMA 2020 statement (PMC8005924)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8005924/)
- [PRISMA 2020 Explanation and Elaboration (PMC8005925)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8005925/)
- [Kitchenham & Charters, Guidelines for Performing Systematic Literature Reviews in Software Engineering (EBSE-2007-001)](https://legacyfileshare.elsevier.com/promis_misc/525444systematicreviewsguide.pdf)

Collection examples consulted (in `papers/`):

- `Correa_de_Almeida_2023_SpatialAudioVirtualReality` — ACM SVR'23, PRISMA-style workshop review.
- `Kuriakose_2022_ToolsTechnologiesBlindVisually` — IETE Technical Review, narrative review with five-axis taxonomy.
- `Morash-Macneil_2018_SystematicReviewAssistiveTechnology` — SAGE systematic review.
- `Chouvardas_2005_TactileDisplays` — IEEE-supported survey, hardware taxonomy.
- `Giudice_2020_CognitiveMappingWithoutVision` — narrative review chapter.
