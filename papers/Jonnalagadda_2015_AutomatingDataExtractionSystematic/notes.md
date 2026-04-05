---
title: "Automating data extraction in systematic reviews: a systematic review"
authors: "Siddhartha R. Jonnalagadda; Pawan Goyal; Mark D. Huffman"
year: 2015
venue: "Systematic Reviews"
doi_url: "https://doi.org/10.1186/s13643-015-0066-7"
pages: "1-16"
---

# Automating data extraction in systematic reviews: a systematic review

## One-Sentence Summary
Jonnalagadda et al. survey the pre-2015 literature on automating systematic-review data extraction and find that published systems can often recover narrow subsets of review data elements with useful accuracy, but the field is fragmented across corpora, label schemes, and task formulations, with no unified framework that covers the full extraction workload. *(pp.1, 12-14)*

## Problem and Framing
The paper targets step 4 of the systematic review workflow: extracting structured data from included studies after screening is complete. The authors argue that this step is time-consuming, delays evidence synthesis, and is a plausible place where natural language processing could reduce reviewer effort. *(pp.1-2)*
Their framing is explicitly narrower than generic review automation. They are not reviewing citation screening, topic identification, or evidence synthesis in general; they focus on methods that identify or extract data items needed to populate a review data abstraction form. *(pp.1-2, 12)*
The motivating claim is practical rather than theoretical: if extraction can be partially automated, reviewers could speed up systematic reviews, decrease time to clinical practice, and reduce the backlog between evidence production and evidence use. *(p.1)*

## Review Protocol
The review follows Systematic Reviews Centre guidance and reports search and selection procedures in a way that is close to a formal review protocol, though the authors later note that they did not publish a protocol a priori. *(pp.2, 13)*
Search sources were PubMed, IEEE Xplore, and ACM Digital Library, limited to January 1, 2000 through January 6, 2015, with citation chasing and expert input for additional studies. The date restriction was chosen because biomedical NLP before 2000 was judged too immature to be useful for systematic-review extraction. *(p.2)*
Inclusion required two things: the paper had to describe data elements extracted or intended for extraction, and at least one entity had to be automatically extracted with an evaluation result reported for that entity. Editorials, commentaries, and papers not tied to data extraction for reviews were excluded. *(p.2)*
Two reviewers independently handled title/abstract review and full-text review, with disagreements resolved by discussion or third-reviewer adjudication. Reported agreement was very high: kappa 0.97 at abstract screening and agreement 0.97 and 1.00 on abstract and full-text screening respectively. *(pp.2, 4)*
The PRISMA-style flow shows 1,220 records from database search plus 5 from other sources, 1,190 after deduplication, 75 screened, 26 full-text reports included, and 49 full-text exclusions. No quantitative meta-analysis was attempted because the included studies differed too much in methodology and measurement. *(pp.4-5)*

## Target Data Elements and Taxonomy
A major contribution of the paper is the explicit inventory of review data elements, derived from Cochrane, CONSORT, STARD, PICO, PECODR, and PIBOSO guidance. The paper organizes these items into categories including participants, interventions, outcomes, comparisons, results, interpretation, objectives, methods, and miscellaneous review metadata. *(pp.2-4)*
The inventory contains more than 52 candidate elements. Examples include participant demographics and disease characteristics, intervention groups and intervention details sufficient for replication, outcome definitions and measurement units, sample size, adverse events, external validity, study rationale, risk-of-bias items such as sequence generation and allocation concealment, and practical items such as funding source or corresponding author. *(pp.3-4, 9)*
Table 3 is especially useful as an implementation checklist because it rewrites these elements as extraction targets grouped by Source, Eligibility, Methods, Participants, Interventions, Outcomes, Results, and Miscellaneous. That checklist is close to the shape of a data abstraction form a reviewer would actually fill out. *(p.9)*

## Evidence Landscape Covered by the Review
The included studies are heterogeneous along at least three axes. First, they target different units: some classify or locate whole sentences, others extract concepts or slot values, and others attempt richer full-text extraction. *(pp.5-8)*
Second, they work on different source material. Many studies use only abstracts, while others use full-text articles or guideline documents. That difference matters because abstract-only extraction often avoids layout and long-range context problems that appear in full text. *(pp.5-11)*
Third, they use incompatible task vocabularies. Common label sets include PICO, PECODR, and PIBOSO, but even when two papers use similar concepts they frequently use different corpora and evaluation setups, making cross-study comparison weak. *(pp.2, 5-12)*

## What Was Successfully Automated
Across the 52 potential data elements considered relevant to review extraction, the authors find published attempts for 25 elements and complete automated extraction for 14. The largest number of distinct elements extracted by any one study was 7. That is the core empirical message of the review: some automation exists, but coverage is sparse and piecemeal. *(pp.1, 12-14)*
Participant-related information is the most developed area. Sixteen studies addressed extraction of participant counts, age, sex, ethnicity, comorbidities, symptom descriptors, or related population descriptors, often with F-scores above 0.8 for narrow subproblems. Examples include participant detection from structured abstracts, demographic slot extraction from PubMed abstracts, and recovery of trial participant numbers from abstracts or full text. *(pp.5-12)*
Intervention extraction is the second most developed area, covered by thirteen studies. Systems extract intervention groups, treatment mentions, comparison groups, or PIBOSO-style intervention labels from abstracts and full text. Performance is often good enough to be useful for constrained corpora, but the papers use different tasks and datasets, so the review cannot claim a stable best method. *(pp.5-12)*
Outcome extraction is also reasonably mature relative to the rest of the field. Seven studies address outcomes or outcome-related elements, including PICO sentence classification and concept extraction for outcomes in abstracts, again often with F-scores above 0.7 on the paper's reported tasks. *(pp.5-12)*
Results-level extraction is less developed. Only four studies are identified for sample-size or result extraction from full text, though some of these still report respectable performance, such as full-text keyword-plus-sentence classifiers for patient, intervention, result, study-design, and research-goal sentences. *(pp.7, 10-12)*
Interpretation, objectives, and methods are sparsely explored. Only a few papers address external validity, study hypotheses, reference standards, study design, or risk-of-bias items. The paper treats this as a significant gap because those fields are necessary for real review workflows, not optional extras. *(pp.3-4, 8, 11-13)*

## Representative Methods in the Included Studies
The studies rely on a familiar pre-deep-learning toolbox: conditional random fields, support vector machines, naive Bayes, maximum entropy, logistic regression, manually written rules, regular expressions, linear-chain models, hidden models over parse trees, topic models, and template filling. *(pp.5-11)*
Sentence classification over abstracts is the most common setup. Representative results include CRF-based PIBOSO tagging on PubMed abstracts, PICO sentence labeling with supervised classifiers, and identification of coordinating constructs for intervention/comparison statements. These studies usually report category-level F-scores rather than end-to-end extraction success on a review form. *(pp.5-10)*
Concept extraction from full text appears in work such as ExaCT, which identifies sentences likely to contain trial characteristics and then applies extraction rules to recover eligibility criteria, sample size, intervention duration, and related trial fields from full articles. This is one of the closest papers in the review to an actual data-abstraction system rather than a sentence tagger. *(pp.8, 11)*
Risk-of-bias extraction is represented by Marshall et al., which applies a soft-margin SVM for sentence extraction and joint modeling for sequence generation, allocation concealment, blinding, and related bias items in clinical trial reports. The review treats this as evidence that review-specific methodological judgments can also be attacked with NLP, though the reported scores are weaker than for simpler population/intervention extraction tasks. *(pp.8, 10)*

## Quantitative Summary of Performance
Most reported systems evaluate a narrow output and report F-score, sometimes alongside precision and recall. The review emphasizes that many reported F-scores are above 70%, and some narrowly defined subtasks reach much higher values. *(pp.1, 5-12)*
Concrete examples include:
- Kim et al. report micro-averaged F-scores of 80.9% on structured abstracts and 66.9% on unstructured abstracts for PIBOSO sentence classification. *(p.6)*
- Huang et al. report sentence-level PICO-style extraction results around 0.91 for participants, 0.75 for interventions, and 0.88 for outcomes on structured abstracts. *(p.6)*
- Hassanzadeh et al. report a PIBOSO-related micro-averaged F-score of 91 using CRFs with discriminative features. *(p.6)*
- Kiritchenko et al. report precision 0.88, recall 0.93, and F-score 0.91 for identifying relevant sentences in full-text randomized trial reports before slot extraction. *(p.8)*
- Zhao et al. report full-text sentence classification F-scores of 0.91 for patients, 0.75 for intervention, 0.61 for result, 0.91 for study design, and 0.79 for research goal. *(p.7)*
The review is careful not to overclaim from these numbers. Accuracy is not directly comparable because corpora, labels, and evaluation protocols differ widely, and many papers optimize on easier or narrower tasks than real-world review data extraction. *(pp.4, 12-13)*

## Gaps, Failure Modes, and Methodological Weaknesses
The authors highlight the absence of gold standards shared across studies. With the exception of one PIBOSO corpus of 1,000 medical abstracts, most studies use private datasets and custom annotation schemes. That makes it impossible to compare methods cleanly or assess whether score differences are meaningful. *(p.13)*
Coverage of review data elements is poor. Twenty-seven of the 52 candidate data elements had not been explored by any study in the review, and many others were investigated by only one paper. This means the field was still in an exploratory stage rather than converging on a common abstraction architecture. *(p.13)*
The review itself is limited by possible missing studies, absence of a published protocol, and duplication of effort across search, screening, full-text review, and data extraction within the review process. The authors explicitly acknowledge possible selection and extraction bias. *(pp.13-14)*
The included primary studies also often have high risk of bias. Because many are non-randomized method papers without strong gold standards or blinded evaluation, reporting bias and selection bias are likely. The paper notes that even risk-of-bias reporting standards for NLP system papers were immature. *(p.11)*

## Conclusions and Design Implications for This Project
The paper's central conclusion is that no unified information extraction framework tailored to systematic reviews existed as of early 2015, even though many subproblems had promising partial solutions. *(pp.1, 13-14)*
For this repository, the paper is most useful as a decomposition guide. It argues that "data extraction" should not be treated as one monolithic task: the concrete targets are participant descriptors, intervention details, outcomes, results, bias items, and ancillary metadata, each with different evidence types and difficulty. This is an implementation inference from the paper's taxonomy and review tables. *(pp.3-4, 9, 12-14)*
It also supports a staged pipeline design. Many successful papers first locate relevant sentences, then classify concepts, then fill structured fields. Systems like ExaCT illustrate that sentence detection plus targeted extraction is more realistic than trying to jump directly from full text to a complete review form. This is an implementation inference from the included-study summaries. *(pp.5-11)*
Finally, the paper is a warning against trusting benchmark scores without task normalization. If this project ever compares extraction modules, it will need stable schemas, shared evaluation sets, and element-specific metrics; otherwise apparent progress will mostly reflect moving targets. This is an implementation inference from the paper's discussion of missing gold standards and incomparable corpora. *(pp.12-14)*

## Related Work Worth Reading
- Kiritchenko et al. (2010), ExaCT, for full-text extraction of clinical-trial characteristics from articles. *(pp.8, 15)*
- Marshall et al. (2014), for NLP-based extraction of risk-of-bias items from clinical trial reports. *(pp.8, 15)*
- Tsafnat et al. (2014), for a broader review of systematic-review automation tasks beyond data extraction. *(p.12, 15)*
- Thomas et al. (2011), for text-mining support across the wider systematic-review workflow. *(p.12, 15)*
- Wallace et al. (2012), for semi-automated screening and workload reduction in systematic reviews. *(p.12, 15)*
- Cohen et al. (2013), for evidence-based medicine automation from the perspective of health informatics. *(p.15)*

---

## Collection Cross-References
### Already in Collection
- (none found)

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [[Liakata_2012_AutomaticRecognitionConceptualizationZones]] - complementary sentence-level information extraction work, though Liakata targets scientific discourse roles rather than review-form fields. This is a conceptual link, not a citation match. *(pp.5-12)*

## Usefulness to This Project
High. The paper does not provide a modern model recipe, but it is a strong requirements document for any review-oriented extraction pipeline because it itemizes the field schema, shows which subfields were historically tractable, and explains why end-to-end automation remained unsolved. *(pp.3-4, 9, 12-14)*
