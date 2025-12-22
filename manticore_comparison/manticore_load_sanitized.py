#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import concurrent.futures
import glob
import json
import logging
import time
from typing import Dict, List, Optional

import manticoresearch
from manticoresearch import BulkResponse
from manticoresearch.rest import ApiException
from mysql.connector import Error
from tqdm import tqdm

from utils.exec_utils import MaxQueuePool
from utils.iter_utils import chunked
from utils.jsonl_utils import jsonl_iter

logger = logging.getLogger(__name__)

INDEX_SCHEMA = """
             type string,
             `timestamp` bigint,
            vector float_vector  knn_type='hnsw' knn_dims='1024' hnsw_similarity='COSINE'
            """

LIS_INDEX_SETTINGS = f"stopwords = 'en' morphology = 'lemmatize_en_all, libstemmer_en' html_strip = '1' min_prefix_len='3' min_infix_len = '3' expand_keywords= '1'  min_stemming_len = '3' stopwords_unstemmed = '1' index_exact_words='1' blend_chars='+,&' rt_mem_limit='1024M' optimize_cutoff='1'"


def get_manticore_config(host:str = f"http://localhost:9308"):
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
                conn.sql(f"""ALTER CLUSTER FTS_1 ADD {index}""", raw_response=True)
                print(f"DONE: Manticore -> createIndexIfNotExists : {index}")
            except ApiException as e:
                logger.error("Exception when calling utils api: %s\n" % e)
    except Error as e:
        logger.error(f"Error: {e}")


def _write_to_manticore(
        name: str,
        chunk: List[Dict],
        num_retries: int = 3,
        sleep_between_retries: int = 60,
):
    configuration = get_manticore_config()

    prepared_recs = [
        {
            "replace": {
                "index": f"{name}",
                "cluster": "FTS_1",
                "id": document.pop("id"),
                "doc": document,
            }
        }
        for document in chunk
    ]

    while num_retries:
        try:
            print(f"Writing {len(prepared_recs)} to {name} records")
            with manticoresearch.ApiClient(configuration) as api_client:
                # Create an instance of the IndexApi API class
                api_instance = manticoresearch.IndexApi(api_client)
                body = "\n".join([json.dumps(doc) for doc in prepared_recs])
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


def ingest(
        name: str,
        records_json_file_path_pattern: str,
        read_batch_size: int = 10000,
        max_queue_size: int = 10,
        max_workers: int = 5,
        index_timestamp: Optional[str] = "timestamp"
):
    start_time = time.time()

    records_json_file_paths = glob.glob(records_json_file_path_pattern)
    print(
        f"Found {len(records_json_file_paths)} matching pattern "
        f"{records_json_file_path_pattern} for {name}"
    )

    def done_callback_handler(_future: concurrent.futures.Future):
        _ = _future.result()

    executor = MaxQueuePool(
        concurrent.futures.ProcessPoolExecutor, max_queue_size, max_workers=max_workers
    )
    for records_json_file_path in records_json_file_paths:
        print(f"Reading {records_json_file_path} now...")

        missing_vectors_count = 0
        for chunk in tqdm(
                chunked(jsonl_iter(records_json_file_path), read_batch_size),
                desc=f"Writing all records in batches of size {read_batch_size} at a time",
        ):
            timestamp = int(time.time())
            if index_timestamp is not None:
                for item in chunk:
                    item[index_timestamp] = timestamp

            executor.submit(_write_to_manticore, name, chunk).add_done_callback(
                done_callback_handler
            )
        print(
            f"Missing vectors for {missing_vectors_count} records in file {records_json_file_path}!"
        )

    executor.pool.shutdown(wait=True, cancel_futures=False)
    print(
        f"Writing for {name} from file(s) {records_json_file_path_pattern} "
        f"done in {time.time() - start_time:.2f}s!"
    )


def main():
    index_name = f"""index1"""
    setup_schema(
        index=index_name,
        schema=INDEX_SCHEMA,
        index_settings=LIS_INDEX_SETTINGS,
    )

    ingest(name=index_name,
           records_json_file_path_pattern="data/data.json.gz"
           )

    hosts = ["http://localhost:9308", "http://localhost:9318", "http://localhost:9328"]
    for host in hosts:
        configuration = get_manticore_config(host=host)
        with manticoresearch.ApiClient(configuration) as api_client:
            utils_api = manticoresearch.UtilsApi(api_client)
            flush_statement = f"flush ramchunk {index_name}"
            print(
                f"STARTING: flush ramchunk on {api_client.configuration.host} for {index_name}"
            )
            utils_api.sql(flush_statement, raw_response=True)
            print(
                f"DONE: flush ramchunk on {api_client.configuration.host} for {index_name}"
            )


if __name__ == "__main__":
    main()
