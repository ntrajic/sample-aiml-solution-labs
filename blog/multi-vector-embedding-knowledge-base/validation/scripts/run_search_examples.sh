#!/bin/bash
"""
Example usage of the vector search test script

This script demonstrates how to use test_vector_search.py with different search modes.
"""

echo "🚀 Vector Search Examples"
echo "Query: Find SageMaker use cases from various industry."
echo "========================="
read -p "Press Enter to continue..."

echo ""
echo "1️⃣  Content Similarity Search (default k=3)"
python scripts/test_vector_search.py --query "SageMaker use cases." --mode content_similarity --metadata "{}" --k 3
echo "------------------------------------------------"
read -p "Press Enter to continue..."

echo ""
echo "2️⃣  Metadata Similarity Search (k=3)"
python scripts/test_vector_search.py --query "SageMaker use cases." --mode metadata_similarity --metadata '{"query":"AI/ML, entertainment"}' --k 3
echo "------------------------------------------------"
read -p "Press Enter to continue..."

echo ""
echo "3️⃣  Hybrid Similarity Search (k=3)"
python scripts/test_vector_search.py --query "SageMaker use cases.s" --mode hybrid_similarity --metadata '{"query":"Analytics", "content_weight": 0.5, "metadata_weight": 0.5}' --k 3
echo "------------------------------------------------"
read -p "Press Enter to continue..."

echo ""
echo "4️⃣  Filter and Search (k=3)"
python scripts/test_vector_search.py --query "SageMaker use cases." --mode filter_and_search --metadata '{"filter_type": "industry", "filter_value": "Manufacturing"}' --k 3
echo "------------------------------------------------"
read -p "Press Enter to continue..."

echo ""
echo "✅ All examples completed!"