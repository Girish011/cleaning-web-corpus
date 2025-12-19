# Experiment B – Length-based quality filtering

## Objective

Study how different minimum document lengths (in words) affect:
- Number of documents kept in the corpus.
- Average document length.
- Distribution of dirt_type and cleaning_method tags.

We want to choose a threshold that balances data quantity and quality.

## Results

We ran the full pipeline with three different `MIN_WORDS` settings:

- MIN_WORDS = 200  
  - Total documents: 11  
  - Average main_text length: 1292.7 words

- MIN_WORDS = 500  
  - Total documents: 10  
  - Average main_text length: 1378.2 words

- MIN_WORDS = 1000  
  - Total documents: 7  
  - Average main_text length: 1684.6 words

## Conclusion

Raising the minimum length threshold reduces corpus size but increases average document length:

- Going from 200 → 500 words removes 1 shorter document while slightly increasing the average length.
- Going from 500 → 1000 words removes 3 more documents and significantly increases average length, favoring longer, more detailed guides.

For this domain, a threshold around 500 words appears to be a good balance between keeping enough documents and favoring richer, tutorial-style content. Higher thresholds (e.g., 1000 words) may be useful for high-quality subsets or specific downstream uses but reduce coverage more aggressively.
