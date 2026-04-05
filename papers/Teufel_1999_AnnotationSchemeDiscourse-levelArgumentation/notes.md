---
title: "An annotation scheme for discourse-level argumentation in research articles"
authors: "Simone Teufel, Jean Carletta, Marc Moens"
year: 1999
venue: "Proceedings of EACL '99"
doi_url: "https://doi.org/10.3115/977035.977051"
citation: "Teufel, Simone, Jean Carletta, and Marc Moens. 1999. An annotation scheme for discourse-level argumentation in research articles. Proceedings of EACL '99."
---

## Summary

This paper proposes a sentence-level annotation scheme for scientific articles aimed at building better training data for automatic abstracting. The key design choice is to label the local argumentative role of each sentence rather than recover a full rhetorical tree over the whole paper. The authors argue that scientific papers use relatively stable rhetorical moves and that these moves are more useful for summarization than domain-specific topical content alone. *(p.1)*

The scheme is intentionally lightweight. It distinguishes accepted background knowledge, neutral references to other work, the authors' own contribution, explicit aims, explicit textual-organization statements, contrastive statements, and statements that cite prior work as a basis or source of support. The paper then evaluates whether humans can apply the scheme reproducibly, first with trained annotators and then with minimally trained annotators. *(pp.1-3)*

## Problem And Motivation

Existing automatic abstracting methods in the 1990s relied heavily on surface features, cue phrases, or sentence extraction without enough discourse structure. Prior systems such as Brandow et al., Kupiec et al., and Rau et al. are presented as useful but limited because they do not model the argumentative role of a sentence inside a research article. The authors want a reusable training resource in which each sentence is labeled with a discourse function that is meaningful for summarization. *(p.1)*

They explicitly reject using full RST-style relational structure as the primary target. Their objection is practical rather than philosophical: whole-document rhetorical parsing is expensive, field-sensitive, and not obviously necessary for identifying summary-worthy content in scientific papers. Instead, they focus on what kind of contribution a sentence makes locally inside the paper's argument. *(pp.1-2)*

## Design Principles

The scheme is based on rhetorical moves from genre analysis, especially Swales, but is adapted from whole-paper moves to sentence-level labels. The paper emphasizes three design constraints:

- the labels should be general enough to apply across computational-linguistics papers from different subfields;
- the scheme should encode argumentative function rather than physical section placement;
- the categories should support automatic abstracting by making aim statements, claims of novelty, and relations to prior work explicit. *(pp.1-2)*

Two distinctions drive the design. First, the scheme separates textual organization from argumentative role, so a sentence about "what this section does" is not treated like a scientific claim. Second, it separates attribution: does the content belong to accepted background, prior work, or the current paper? This authorship distinction is central because abstracting systems need to know whether a proposition is a contribution, a goal, a criticism, or merely context. *(p.2)*

## Annotation Scheme

The authors define a three-way basic scheme plus four extra categories for the full scheme. *(p.2)*

### Basic Scheme

| Category | Definition |
| --- | --- |
| BACKGROUND | Sentences describing generally accepted background knowledge. |
| OTHER | Sentences describing specific prior work in a neutral way, excluding contrastive statements and basis/support relations. |
| OWN | Sentences describing the current paper's own work, except cases singled out as AIM or TEXTUAL. This includes methodology, limitations, and future work. |

### Additional Full-Scheme Categories

| Category | Definition |
| --- | --- |
| AIM | Sentences that best portray the particular research goal. |
| TEXTUAL | Explicit statements about the textual section structure of the paper. |
| CONTRAST | Sentences that contrast the present work with prior work or point out weaknesses in other research, including direct comparisons. |
| BASIS | Sentences where the current work uses another work as a basis, starting point, or source of support. |

The paper also gives a decision tree for annotation. The first question is attribution: is the sentence about the authors' own work, accepted background, or some other specific research? If it is about the current work, the annotator then asks whether it states the goal or merely the textual organization before falling back to OWN. If it is about prior work or background, the annotator asks whether the sentence is contrastive or whether it presents prior work as a basis for the current paper. This creates a simple sequence of local decisions rather than a global discourse parse. *(pp.2-3)*

## Data And Experimental Setup

The evaluation uses 48 computational-linguistics papers: 22 papers for Study I and 26 papers for Study II, drawn from the Computation and Language E-Print Archive and ACL-related sources from roughly 1994-1995. One paper initially included in the first study was later discarded because it was actually a review paper, and the scheme was not intended for review articles. *(p.3)*

Studies I and II use three highly trained annotators who are also graduate students in the area. Training included four training papers, detailed written instructions, and weekly discussions. The full scheme required substantially more documentation than the basic one: about 6 pages of instructions for the basic scheme versus 17 pages for the full scheme. Annotators were not allowed to revise earlier decisions once weekly discussions had already clarified problem cases, and annotation took roughly 20-30 minutes per paper for documents of about 380 words. *(p.3)*

Study I measures stability and reproducibility with trained annotators. Stability is intra-annotator agreement over time; reproducibility is inter-annotator agreement. Kappa is used instead of raw agreement because the category distribution is uneven and some categories are much rarer than others. *(pp.2-3)*

Study III tests how far the scheme can be used with much lighter training. Eighteen subjects, mostly with graduate training in cognitive science or related areas, received only minimal written instructions plus a decision tree. They were divided into groups, each group annotating a paper that had already been found reproducible in Study II. One group also received one fully annotated example paper. *(p.5)*

## Main Results

The core result is that trained annotators can apply the basic scheme reliably and the full scheme acceptably well. The basic three-way scheme is reported as both stable and reproducible, with pooled inter-annotator agreement around kappa 0.78. The full seven-way scheme drops to about kappa 0.71, which the authors regard as a meaningful but still workable level given the subjectivity of discourse labeling. *(p.4)*

The best-performing category is AIM. Goal statements are consistently easier to identify than OWN, BASIS, or CONTRAST, and the authors highlight this as especially important for summarization because aim sentences often belong in abstracts. TEXTUAL is also relatively reproducible. In contrast, OWN and BACKGROUND are harder to separate, and the triad of OWN, CONTRAST, and BASIS causes the largest confusion when the full scheme is used. *(pp.4-5)*

Study I also suggests that paper-level characteristics affect annotation difficulty. Papers with more self-citations are harder to annotate, likely because the difference between prior work and the current authors' own earlier work becomes blurred. Conference papers appear easier than journal papers because they are shorter, more standardized, and contain less extended descriptive material. *(pp.4-5)*

Study III shows that minimal training alone is not enough to guarantee reproducibility. The three novice groups vary widely, and the paper argues that paper-specific effects dominate: some papers are inherently easier to classify than others. The group that saw one annotated example plus a particularly reproducible paper performed close to trained annotators, but the authors do not take this as proof that the scheme can be used reliably without sustained task-specific training. *(p.5)*

## Error Modes And Diagnostics

The paper gives several concrete reasons why some categories fail more often than others:

- sentences that describe the authors' own previous work are difficult because attribution and novelty are entangled; these cases blur OWN versus OTHER and also confuse CONTRAST or BASIS decisions; *(p.4)*
- weak or implicit criticism of prior work is difficult to distinguish from neutral description, which hurts CONTRAST reliability; *(p.1, p.4)*
- OWN and BACKGROUND can blur when a paper assumes shared domain knowledge while still framing it as part of the current technical setup; *(p.2, p.4)*
- journal papers with longer descriptive stretches and less rigid structure produce more ambiguity than shorter conference papers. *(pp.4-5)*

The authors inspect confusion patterns rather than reporting only one summary number. They note that collapsing difficult distinctions improves kappa to the high-reliability range, which supports the view that the scheme is fundamentally usable but that some boundaries may need to be simplified for practical annotation pipelines. *(p.4)*

## What This Paper Contributes Methodologically

This is an early, concrete move away from purely structural discourse theory toward a task-oriented annotation scheme for scientific writing. The paper's methodology matters for implementation because it treats scientific discourse annotation as a supervised-data design problem:

- define labels in terms of downstream utility for abstracting;
- make local sentence-level decisions instead of document-level trees;
- separate contribution attribution from textual structure;
- measure both intra-annotator stability and inter-annotator reproducibility;
- analyze category confusion and paper-level difficulty, not just aggregate agreement. *(pp.1-6)*

That design directly anticipates later work on argument zoning and scientific discourse tagging. The paper is especially useful if the project needs labels that distinguish current contribution, goal, relation to prior work, and paper-organization text while staying simple enough for human annotation. *(pp.1-6)*

## Implementation-Relevant Takeaways

For this project, the strongest practical takeaways are:

1. Sentence-level local-role labels can be reproducible enough to justify building training data without full discourse parsing. *(pp.1-4)*
2. Attribution to own work versus other work is a first-class variable and should not be left implicit in the label set. *(pp.1-2)*
3. AIM is both useful and easier to annotate than several other categories, so it is a strong candidate anchor label for bootstrapping models or guidelines. *(pp.4-5)*
4. Own-work versus prior-own-work and neutral-description versus criticism are the main ambiguity zones, so any modern scheme should document these boundaries explicitly and probably include adjudication examples. *(pp.4-5)*
5. Paper genre and format matter; models trained only on short conference papers may not transfer cleanly to longer journal articles. *(pp.4-5)*

## Limitations

The evaluation corpus is small and domain-specific, confined to computational linguistics. The paper does not show downstream summarization gains from using these labels; it shows only that the labels can be learned by humans with moderate reliability. The scheme is also intentionally local, so it loses richer discourse relations such as elaboration, evidence chains, or global nucleus-satellite structure that full rhetorical models might capture. *(pp.1, 4-6)*

The novice-annotator study is suggestive rather than decisive because paper difficulty is confounded with training condition. The authors openly note that the final usefulness of the coding scheme will only become clear in downstream applications. *(pp.5-6)*

## Testable Properties

- The three-way basic scheme is more reproducible than the full seven-way scheme, with trained-annotator inter-annotator agreement reported around kappa 0.78 for the basic scheme and around 0.71 for the full scheme. *(p.4)*
- AIM sentences are the easiest category to identify reliably and are especially promising as summary-bearing material for automatic abstracting. *(pp.4-5)*
- Most reproducibility failures come from separating OWN from BASIS and CONTRAST, and from separating OWN from BACKGROUND in ambiguous cases. *(pp.4-5)*
- Papers with more self-citations are harder to annotate because the difference between the current paper and the authors' prior work becomes less clear. *(p.4)*
- Conference papers are easier to annotate reproducibly than journal papers because they are shorter and structurally more standardized. *(pp.4-5)*
- Minimal instructions without extended training do not by themselves guarantee reliable annotation; paper-specific difficulty remains a dominant factor. *(p.5)*

## Usefulness For This Collection

High usefulness. This paper is a direct precursor to later scientific-discourse annotation work and provides a concrete, experimentally tested label inventory centered on argumentative role. It is particularly valuable if the collection is being built toward implementation of research-paper discourse tagging, argument zoning, or discourse-aware summarization. *(pp.1-6)*

---

## Collection Cross-References

### Already in Collection

- (none found)

### Cited By (in Collection)

- (none found)

### Conceptual Links

- (none found)

### New Leads (Not Yet in Collection)

- Swales_1990_GenreAnalysisEnglishAcademicResearchSettings - core source for the communicative-move framing used to define the annotation scheme.
- Mann_1987_RhetoricalStructureTheory - primary contrast case for full rhetorical-structure approaches.
- Kircz_1991_RhetoricalStructureScientificArticles - direct antecedent on argumentative analysis of scientific articles.
- Kupiec_1995_TrainableDocumentSummarizer - extractive summarization baseline used in the motivation.
- Marcu_1997_DiscourseStructuresTextSummaries - discourse-based summarization comparison point.
- Thompson_1991_EvaluationReportingVerbsAcademicPapers - evidence that local linguistic cues reveal evaluative stance in research articles.
