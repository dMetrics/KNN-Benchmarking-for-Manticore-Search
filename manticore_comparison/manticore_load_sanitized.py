#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import os
import time
from typing import Dict, List
import concurrent.futures

import manticoresearch
from manticoresearch import BulkResponse
from manticoresearch.rest import ApiException

logger = logging.getLogger(__name__)

LIS_DOCUMENT_SCHEMA = """
            document_id string,
            vector_dim int,
            vector float_vector  knn_type='hnsw' knn_dims='768' hnsw_similarity='COSINE'
            """

LIS_INDEX_SETTINGS = f"stopwords = 'en'  morphology='lemmatize_en_all, libstemmer_en' min_prefix_len='3' min_infix_len = '3' expand_keywords= '1'  stopwords_unstemmed = '1' index_exact_words='1' blend_chars='+,&' rt_mem_limit='512M'"


def get_manticore_config():
    host = f"http://localhost:9308"
    return manticoresearch.Configuration(host=host)


def setup_schema(index: str, schema: str, index_settings: str):
    try:
        # Establish the database connection
        configuration = get_manticore_config()
        with manticoresearch.ApiClient(configuration) as api_client:
            # Create an instance of the IndexApi API class
            conn = manticoresearch.UtilsApi(api_client)
            createIndexStatement = f"""CREATE TABLE IF NOT EXISTS {index}({schema}) {index_settings} engine='columnar'"""
            try:
                conn.sql(createIndexStatement, raw_response=True)
                conn.sql(f"""ALTER CLUSTER DMETRICS_FTS_1 ADD {index}""", raw_response=True)
                print(f"DONE: Manticore -> createIndexIfNotExists : {index}")
            except ApiException as e:
                logger.error("Exception when calling utils api: %s\n" % e)
    except Exception as e:
        logger.error(f"Error: {e}")


def _write_to_manticore(
        name: str,
        chunk: List[Dict],
        num_retries: int = 3,
        sleep_between_retries: int = 60,
):
    configuration = get_manticore_config()

    while num_retries:
        try:
            print(f"Writing {len(chunk)} to {name} records")
            with manticoresearch.ApiClient(configuration) as api_client:
                # Create an instance of the IndexApi API class
                api_instance = manticoresearch.IndexApi(api_client)
                body = "\n".join([json.dumps(doc) for doc in chunk])
                try:
                    # Bulk index operations
                    response: BulkResponse = api_instance.bulk(body)
                    # print(response)
                except ApiException as e:
                    logger.error("Exception when calling IndexApi->bulk: %s\n" % e)
                    print("Exception when calling IndexApi->bulk: %s\n" % e)
                    raise e
                except Exception as e:
                    logger.error("Exception while writing: %s\n" % e)
                    print("Exception while writing: %s\n" % e)
            print(f"Done writing {len(chunk)} to '{name}' records ")
            break
        except Exception as e:
            num_retries -= 1
            logger.warning(
                f"Write to manticore failed: {repr(e)}. {num_retries} retries left. Sleeping for {sleep_between_retries}s before next attempt..."
            )
            time.sleep(sleep_between_retries)


def _write_to_lisdocument(
        name: str,
        chunk: List[Dict]
):
    prepared_recs = [
        {
            "insert": {
                "index": f"{name}",
                "cluster": 'DMETRICS_FTS_1',
                "doc": document.get('_source'),
            }
        }
        for document in chunk
    ]

    _write_to_manticore(name, prepared_recs)


def read_json(data_file: str):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, data_file)
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return {}


def main():
    for i in range(1, 7):
        index_name = f"""lisdocument{i}"""
        setup_schema(
            index=index_name,
            schema=LIS_DOCUMENT_SCHEMA,
            index_settings=LIS_INDEX_SETTINGS,
        )

        data = read_json("data/manticore_data_new.json")

        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(_write_to_lisdocument, index_name, data) for _ in range(1000)]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Thread generated an exception: {e}")


if __name__ == "__main__":
    main()
