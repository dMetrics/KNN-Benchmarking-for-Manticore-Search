#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB (Knowledge Base) utility functions for fetching entity information.
"""
import urllib.request
import json
from typing import List, Dict, Optional


def fetch_kb_entities(entity_ids: List[int], kb_base_url: Optional[str] = None) -> Dict[int, Dict]:
    """
    Fetch entity information from KB API for given entity IDs.
    Extracts only: name, description, type.
    
    Args:
        entity_ids: List of entity IDs to fetch
        kb_base_url: Base URL for KB API (default: http://kb.dmetrics.internal/kb)
    
    Returns:
        Dictionary mapping entity ID to entity data with fields: name, description, type
    """
    if not entity_ids:
        return {}

    if kb_base_url is None:
        kb_base_url = "http://kb.dmetrics.internal/kb"
    
    # Create comma-separated IDs string
    ids_str = ','.join(str(eid) for eid in entity_ids)
    url = f"{kb_base_url}/entities?ids={ids_str}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        # Convert response to dictionary keyed by ID, extracting only needed fields
        entities = {}
        if isinstance(data, list):
            for entity in data:
                if 'id' in entity:
                    entities[entity['id']] = {
                        'name': entity.get('name'),
                        'description': entity.get('description'),
                        'type': entity.get('type')
                    }
        elif isinstance(data, dict):
            for entity_id, entity in data.items():
                if isinstance(entity, dict):
                    entities[entity_id] = {
                        'name': entity.get('name'),
                        'description': entity.get('description'),
                        'type': entity.get('type')
                    }
        
        return entities
    except Exception as e:
        print(f"Warning: Failed to fetch KB entities: {e}")
        return {}


def enrich_results_with_kb(results: List[Dict], kb_base_url: Optional[str] = None) -> List[Dict]:
    """
    Enrich search results with KB entity information.
    
    Args:
        results: List of search results, each containing at least an 'id' field
        kb_base_url: Base URL for KB API (optional, defaults to http://kb.dmetrics.internal/kb if None)
    
    Returns:
        List of results with 'kb_data' field added to each result
    """
    if kb_base_url is None:
        kb_base_url = "http://kb.dmetrics.internal/kb"

    if not results:
        return results
    
    # Extract IDs and fetch KB entities in one request
    entity_ids = [result['id'] for result in results]
    kb_entities = fetch_kb_entities(entity_ids, kb_base_url)
    
    # Enrich results with KB data
    for result in results:
        result['kb_data'] = kb_entities.get(result['id'])
    
    return results

