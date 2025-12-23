# KNN Benchmarking for Manticore Search

This repository contains scripts for benchmarking KNN (K-Nearest Neighbors) vector search using both **FAISS** and **Manticore Search**. It provides comparators for evaluating performance, accuracy, and consistency of vector search results.

## Overview

The repository includes two main comparators:

1. **FAISSComparator** (`faiss_comparison/faiss_comparator.py`) - FAISS-based vector search implementation
2. **ManticoreComparator** (`manticore_comparison/manticore_comparator.py`) - Manticore Search-based vector search implementation

Both comparators support:
- Cosine similarity search via HNSW (Hierarchical Navigable Small World) indexes
- Vector normalization for accurate cosine similarity calculations
- KB (Knowledge Base) data enrichment for search results
- Configurable HNSW parameters (M, ef_construction, ef_search)
- Index persistence and loading

## Results

All benchmarking results are documented in [results.md](results.md)

## Setup

### 1. Manticore Cluster Setup

```bash
export CPUTYPE=amd64  # Use amd64 for Intel, arm64 for Apple Silicon
chmod +x init_manticore_cluster.sh
./init_manticore_cluster.sh
```

This sets up a Manticore Search cluster with multiple nodes (default: localhost:9308, 9318, 9328).

### 2. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### 3. Load Data to Manticore

This repo stores the dataset in Git LFS. Make sure you have it before loading:

```bash
git lfs install
git lfs pull
```

```bash
python manticore_comparison/manticore_load_sanitized.py
```

This loads vector data into Manticore Search indexes.

### 4. Run Comparison

```bash
python manticore_comparison/diff_comparator.py
```

## FAISS Comparator

### Features

- **Index Types**: Supports both HNSW (approximate) and FlatIP (exact) search
- **Index Persistence**: Saves and loads FAISS indexes to/from disk
- **Vector Normalization**: Automatically normalizes vectors for cosine similarity
- **Distance Calculation**: Converts FAISS distances to match Manticore's distance metric
- **KB Enrichment**: Optional knowledge base data enrichment for results

### Usage

```python
from faiss_comparison.faiss_comparator import FAISSComparator

# Initialize comparator
comparator = FAISSComparator(
    dimension=1024,
    use_hnsw=True,  # Use HNSW for approximate search
    ef_construction=200,
    ef_search=2000,
    hnsw_m=16
)

# Load data and build index
comparator.load_data(
    data_path="manticore_comparison/data/data.json.gz",
    max_rows=50000,
    rebuild_index=False
)

# Perform search
results = comparator.search(query_vector, k=50)

# Search with KB enrichment
results = comparator.search_with_kb(
    query_vector, 
    k=50,
    kb_base_url="<your-kb-api-url>"
)
```

### Command Line Usage

```bash
python faiss_comparison/faiss_comparator.py \
    --data-path manticore_comparison/data/data.json.gz \
    --max-rows 50000 \
    --rebuild
```

### Key Parameters

- `dimension`: Vector dimension (default: 1024)
- `use_hnsw`: Use HNSW index for approximate search (default: True)
- `hnsw_m`: Number of bi-directional links per node (default: 16, range: 16-64)
- `ef_construction`: HNSW construction parameter (default: 200)
- `ef_search`: HNSW search parameter (default: 2000)

## Manticore Comparator

### Features

- **Cluster Support**: Queries all nodes in a Manticore cluster and merges results
- **API Endpoint Logging**: Logs which API endpoints are being used
- **Per-Node Results**: Displays results from each cluster node separately
- **KB Enrichment**: Enriches results with knowledge base data
- **Index Management**: Automatic index creation and cluster management

### Usage

```python
from manticore_comparison.manticore_comparator import ManticoreComparator

# Initialize comparator
comparator = ManticoreComparator(
    dimension=1024,
    host="http://localhost:9308",
    cluster_name="FTS_1",
    hnsw_m=32,
    ef_construction=200,
    ef_search=2000,
    cluster_nodes=[
        "http://localhost:9308",
        "http://localhost:9318",
        "http://localhost:9328"
    ]
)

# Load data and setup index
comparator.load_data(
    data_path="manticore_comparison/data/data.json.gz",
    max_rows=50000,
    rebuild_index=False
)

# Perform search (queries all cluster nodes)
results = comparator.search(query_vector, k=50, filter_type=None)

# Search with KB enrichment
results = comparator.search_with_kb(
    query_vector,
    k=50,
    filter_type=None,
    kb_base_url="<your-kb-api-url>"
)
```

### Command Line Usage

```bash
python manticore_comparison/manticore_comparator.py \
    --data-path manticore_comparison/data/data.json.gz \
    --max-rows 50000 \
    --host http://localhost:9308 \
    --rebuild
```

### Key Parameters

- `dimension`: Vector dimension (default: 1024)
- `host`: Primary Manticore Search host URL (default: http://localhost:9308)
- `cluster_name`: Manticore cluster name (default: FTS_1)
- `hnsw_m`: HNSW M parameter (default: 32)
- `ef_construction`: HNSW construction parameter (default: 200)
- `ef_search`: HNSW search parameter (default: 2000)
- `cluster_nodes`: List of cluster node URLs

### API Endpoints

The Manticore comparator uses the SQL API endpoint:
- **Endpoint**: `{host}/sql` (e.g., `http://localhost:9308/sql`)
- **Method**: Uses Manticore Search `UtilsApi.sql()` method
- **Query Type**: KNN search with `knn()` function and `knn_dist()` for distance calculation

When `search()` is called, it:
1. Queries each node in the cluster separately
2. Logs the endpoint URL for each node
3. Displays results from each node
4. Merges and deduplicates results (keeping best score per document ID)
5. Returns top k results sorted by score

## Distance Calculation

Both comparators use cosine similarity with normalized vectors:

- **Manticore**: Uses `knn_dist()` which returns `1 - cosine_similarity`
- **FAISS (HNSW)**: Converts L2 distance to cosine distance: `distance = L2² / 2`
- **FAISS (FlatIP)**: Uses inner product directly: `distance = 1 - cosine_similarity`

This ensures consistent distance metrics across both implementations.

## Data Format

The expected data format is JSONL (JSON Lines) with the following structure:

```json
{"id": 123, "vector": [0.1, 0.2, ...], "type": "x"}
{"id": 456, "vector": [0.3, 0.4, ...], "type": "y"}
```

- `id`: Unique document identifier
- `vector`: List of floats (must match dimension, default: 1024)
- `type`: Optional metadata field for filtering

## Notes

- Both comparators normalize vectors for cosine similarity calculations
- Indexes are persisted to disk for faster subsequent loads
- Manticore comparator queries all cluster nodes in parallel and merges results
- Results can be enriched with KB (Knowledge Base) data for additional context
