This repository contains scripts to reproduce an issue with KNN search, where loading the same data into an index produces inconsistent results across different loads.

**Results:**

All results are present in [View Results](results.md)


**Setup for data:**

1. Start the Manticore instance using Docker Compose
``` 
docker-compose up
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Run `python manticore_load_sanitized.py` to load data to indexes
4. Run `python diff_comparator.py` to get the comparison results
