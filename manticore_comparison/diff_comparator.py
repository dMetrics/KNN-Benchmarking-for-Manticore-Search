#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import manticoresearch
from manticoresearch.rest import ApiException as ManticoreException
import queries as q
from tabulate import tabulate

servers = [
    "http://localhost:9308"
]

tables = ["lisdocument1", "lisdocument2","lisdocument3","lisdocument4","lisdocument5","lisdocument6"]  # Tables to test queries on

def sanitize_query(query: str):
    return query.replace("\n", " ").replace("\t", " ").replace("  ", " ").strip()

def perform_query(url: str, query: str):
    configuration = manticoresearch.Configuration(host=url)
    client = manticoresearch.ApiClient(configuration)
    api_instance = manticoresearch.UtilsApi(client)
    _count = 0
    try:
        result = api_instance.sql(sanitize_query(query), raw_response=True)
        rows = result[0].get('data', [])
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
    results = {table: {} for table in tables}

    for server in servers:
        for num, tasks in enumerate(q.queries):
            name = tasks.get('name')
            query = tasks.get('query')
            for table in tables:
                table_query = query.replace('lisdocument', table)
                print(f"Running server: {server} | Query ID: {name} | Table: {table}")
                result, _count = perform_query(server, table_query)
                results[table][num] = _count

    # Prepare data for pretty table
    table_data = []
    headers = ["Query Name"] + tables  # Replace servers with tables as columns
    query_ids = list(range(len(q.queries)))

    for num, tasks in enumerate(q.queries):
        row = [tasks.get('name')]
        for table in tables:
            row.append(results[table].get(num, None))
        table_data.append(row)

    # Print the results in a pretty table
    print(tabulate(table_data, headers=headers, tablefmt="pretty", colalign=("left",) + ("center",) * len(tables)))


if __name__ == "__main__":
    main()
