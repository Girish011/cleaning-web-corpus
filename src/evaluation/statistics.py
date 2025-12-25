"""
Legacy statistics module - kept for backward compatibility.

For comprehensive statistics, use dataset_stats.py instead.
"""

import pathlib
from src.evaluation.dataset_stats import DatasetStatistics

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "cleaning_docs.jsonl"


def main():
    """
    Legacy main function - now uses comprehensive DatasetStatistics.
    
    For full statistics, run: python -m src.evaluation.dataset_stats
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Processed file not found: {DATA_PATH}")

    # Use comprehensive statistics module
    stats = DatasetStatistics(DATA_PATH)
    stats.load_data()
    stats.compute_all()

    # Print basic summary (backward compatible output)
    basic = stats.stats['basic']
    coverage = stats.stats['coverage']

    print(f"Total documents: {basic['total_documents']}")
    print("By source_type:")
    for k, v in sorted(basic['source_type_distribution'].items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

    print("By surface_type:")
    for k, v in sorted(coverage['surface_type_distribution'].items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

    print("By dirt_type:")
    for k, v in sorted(coverage['dirt_type_distribution'].items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

    print("By cleaning_method:")
    for k, v in sorted(coverage['cleaning_method_distribution'].items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

    text_stats = stats.stats['text']
    if text_stats['word_count']:
        avg_len = text_stats['word_count']['mean']
        print(f"Average main_text length (words): {avg_len:.1f}")

    # Print dirt_type x cleaning_method matrix
    print("dirt_type x cleaning_method:")
    methods_order = sorted(coverage['cleaning_method_distribution'].keys())
    print("          " + "  ".join(f"{m:>15}" for m in methods_order))
    for dirt in sorted(coverage['dirt_type_distribution'].keys()):
        row = [f"{dirt:>10}"]
        for method in methods_order:
            count = coverage['dirt_x_method'].get(dirt, {}).get(method, 0)
            row.append(f"{count:>15}")
        print("  ".join(row))


if __name__ == "__main__":
    main()
