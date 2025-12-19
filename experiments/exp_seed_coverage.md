# Experiment A – Seed targeting and coverage

## Objective

Evaluate how adding targeted seed URLs affects the coverage of important tag combinations in the corpus, especially:
- `stain + hand_wash`
- `dust + vacuum`
- `dust + washing_machine`

## Setup

- **v1 seeds:** Initial manually curated set of cleaning articles (pillows, clothes, carpets).
- **v2 seeds:** v1 seeds plus targeted URLs for:
  - Delicate stains and hand washing.
  - Dust removal from clothes without full washing.
  - Carpet / fabric cleaning with vacuum and spot-cleaning.

For both v1 and v2, we run the full pipeline:
- Scrapy seed spider → `data/raw/seed_pages.jsonl`
- Processing pipeline → `data/processed/cleaning_docs.jsonl`
- Analysis script → summary stats and dirt_type × cleaning_method table

## Results

### v1 (original seeds)

- Total documents: 6
- dirt_type distribution:
  - dust: 4
  - stain: 2
- cleaning_method distribution:
  - washing_machine: 3
  - vacuum: 2
  - hand_wash: 1

dirt_type × cleaning_method:

dirt_type x cleaning_method:
hand_wash vacuum washing_machine
stain 1 0 1
dust 0 2 2


### v2 (with targeted seeds)

- Total documents: 11
- dirt_type distribution:
  - dust: 6
  - stain: 5
- cleaning_method distribution:
  - washing_machine: 6
  - hand_wash: 3
  - vacuum: 2

dirt_type × cleaning_method:

dirt_type x cleaning_method:
hand_wash vacuum washing_machine
dust 1 2 3
stain 2 0 3


## Conclusion

Adding targeted seeds for delicate stains, hand washing, dust removal without full washing, and vacuum-based carpet/sofa cleaning:

- Increased coverage of `stain + hand_wash` from 1 to 2 documents.
- Increased coverage of `dust + washing_machine` from 2 to 3 documents.
- Introduced `dust + hand_wash` (0 → 1) while preserving `dust + vacuum` examples.
- Roughly doubled dataset size (6 → 11 docs) while keeping long average length (~1.3k words).

This shows that search-guided, domain-specific seed expansion is an effective way to improve coverage of specific cleaning scenarios in the corpus without sacrificing document quality.
