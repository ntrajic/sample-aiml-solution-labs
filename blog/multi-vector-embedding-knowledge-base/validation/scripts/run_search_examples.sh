#!/bin/bash
"""
Example usage of the vector search test script

This script demonstrates how to use test_vector_search.py with different search modes.
"""

echo "🚀 Vector Search Examples"
echo "========================="

echo ""
echo "1️⃣  Content Similarity Search (default k=3)"
echo "Searching for documents with similar content to 'machine learning algorithms'"
python validation/scripts/test_vector_search.py --query "machine learning algorithms" --mode content_similarity --metadata "{}"

echo ""
echo "2️⃣  Metadata Similarity Search (k=3)"
echo "Searching for documents with metadata similar to 'machine learning algorithms'"
python validation/scripts/test_vector_search.py --query "machine learning algorithms" --mode metadata_similarity --metadata '{"query": "technical documentation"}' --k 3

echo ""
echo "3️⃣  Hybrid Similarity Search (k=4)"
echo "Combining content and metadata search with custom weights"
python validation/scripts/test_vector_search.py --query "machine learning algorithms" --mode hybrid_similarity --metadata '{"metadata_query": "Blogs from hyperscalers", "content_weight": 0.2, "metadata_weight": 0.8}' --k 3

echo ""
echo "4️⃣  Filter and Search (k=3)"
echo "Filtering by category then searching within results"
python validation/scripts/test_vector_search.py --query "machine learning algorithms" --mode filter_and_search --metadata '{"filter_type": "category", "filter_value": "machine learning"}' --k 3

echo ""
echo "✅ All examples completed!"