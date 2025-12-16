#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import manticoresearch
from manticoresearch.rest import ApiException as ManticoreException
import queries as q
import advance_queries as aq
from tabulate import tabulate

servers = [
    "http://localhost:9308","http://localhost:9318","http://localhost:9328"
]

def sanitize_query(query: str):
    return query.replace("\n", " ").replace("\t", " ").replace("  ", " ").strip()

def perform_query(url: str, query: str):
    configuration = manticoresearch.Configuration(host=url)
    client = manticoresearch.ApiClient(configuration)
    api_instance = manticoresearch.UtilsApi(client)
    _count = 0
    try:
        result = api_instance.sql(sanitize_query(query), raw_response=True)
        rows = result.actual_instance[0].get('data', [])
        if rows:
            _count = len(rows)
            if rows[0].get('total'):
                _count = rows[0].get('total')
        else:
            _count = None
    except ManticoreException as e:
        print(f"Manticore error: {e}")
        return None, None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None

    return rows, _count

def main():
    results = {table: {} for table in servers}

    for server in servers:
        for num, tasks in enumerate(q.queries):
            name = tasks.get('name')
            query = tasks.get('query')
            print(f"Running server: {server} | Query ID: {name} ")
            result, _count = perform_query(server, query)
            results[server][num] = _count

    # Prepare data for pretty table
    table_data = []
    headers = ["Query Name"] + servers  # Replace servers with tables as columns
    query_ids = list(range(len(q.queries)))

    for num, tasks in enumerate(q.queries):
        row = [tasks.get('name')]
        for server in servers:
            row.append(results[server].get(num, None))
        table_data.append(row)

    # Print the results in a pretty table
    print(tabulate(table_data, headers=headers, tablefmt="pretty", colalign=("left",) + ("center",) * len(servers)))


    advance_results = {server: {} for server in servers}
    advance_table_data = []
    advance_headers = ["Rank"] + servers

    # --- 1. Collect results for each server ---
    for server in servers:
        for task in aq.queries:
            name = task["name"]
            query = task["query"]
            print(f"Running server: {server} | Query: {name}")
            result, _count = perform_query(server, query)

            for idx, r in enumerate(result):
                advance_results[server][idx] = r

    # --- 2. Determine max number of rows ---
    max_rank = max(len(advance_results[s]) for s in servers)

    # --- 3. Build table: each rank = one row ---
    for rank in range(max_rank):
        row = [rank]  # first column = rank

        for server in servers:
            cell = advance_results[server].get(rank)

            # Convert entire result to a string to avoid precision loss
            row.append("" if cell is None else str(cell))

        advance_table_data.append(row)

    # --- 4. Print table ---
    print(tabulate(
        advance_table_data,
        headers=advance_headers,
        tablefmt="pretty",
        colalign=("center",) + ("left",) * len(servers)
    ))


if __name__ == "__main__":
    main()
