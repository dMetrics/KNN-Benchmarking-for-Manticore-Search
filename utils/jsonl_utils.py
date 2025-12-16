#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: xavier
"""

import bz2
import gzip
import json
import logging

logger = logging.getLogger(__name__)


def jsonl_dump_open(out_fname: str, items_name="items", mode="wb"):
    """Opens a file for dumping json items by lines.

    Supports gzip and bz2 compression.

    Returns the open file in 'wb' mode:

    ``` fp = jsonl_dump_open('tmp.json.gzip')
    fp.write('{}\\n'.format(json.dumps({'bla': 1})).encode('utf8'))
    fp.close() ```
    """
    fp = None
    try:
        if out_fname.endswith(".bz2"):
            logger.info(
                "Dumping {} to '{}' with bz2 compression".format(items_name, out_fname)
            )
            fp = bz2.open(out_fname, mode=mode)
        elif out_fname.endswith(".gz"):
            logger.info(
                "Dumping {} to '{}' with gzip compression".format(items_name, out_fname)
            )
            fp = gzip.open(out_fname, mode=mode)
        else:
            logger.info(
                "Dumping {} to '{}' with no compression".format(items_name, out_fname)
            )
            fp = open(out_fname, mode=mode)
    except Exception as e:
        logger.error(str(e))
    return fp


def jsonl_dump_item(item, line_number, file):
    """Dumps a single item to the file, as one line."""
    try:
        item_str = json.dumps(item)
    except Exception as e:
        logger.error("json line {}: {}".format(line_number + 1, e))
        item_str = "{}"
    file.write("{}\n".format(item_str).encode("utf8"))


def jsonl_dump_item_str(item_str: str, line_number, file):
    """Dumps a single item to the file, as one line."""
    file.write("{}\n".format(item_str).encode("utf8"))


def jsonl_dump(items, out_fname: str, items_name: str = "items") -> None:
    """Write items to JSON-lines file, with one item per line.

    Supports gzip and bz2 compression. These compressions are used
    when `out_fname` ends with `gzip` or `bz2` respectively.

    Parameters
    ----------
    items
      An iterable of items that must be json compatible
    out_fname
      Output file name
    items_name
      An optional name of the items (e.g. "entities") used in logging messages
    """
    fp = jsonl_dump_open(out_fname, items_name=items_name)
    if fp is not None:
        line_number = -1
        for line_number, item in enumerate(items):
            jsonl_dump_item(item, line_number, file=fp)
        fp.close()
        logger.info("Done, {} {} in dump".format(line_number + 1, items_name))
    else:
        logger.error("Error creating file '{}'".format(out_fname))


def jsonl_load(in_fname, max_items=None):
    """Loads  the items (lines) in the file.

    Returns a list of items.

    Supports compressed files in gzip and bz2 formats.
    """
    L = [item for item in jsonl_iter(in_fname, max_items=max_items)]
    return L


def jsonl_iter(in_fname, max_items=None):
    """Iterates over the items (lines) in the file, yielding the json object in
    each line.

    Parameter `max_items` iterates over the first items.

    Supports compressed files in gzip and bz2 formats.
    """
    fp = None
    try:
        if in_fname.endswith(".bz2"):
            fp = bz2.open(in_fname, mode="rb")
        elif in_fname.endswith(".gz"):
            fp = gzip.open(in_fname, mode="rb")
        else:
            fp = open(in_fname, mode="rb")
    except Exception as e:
        logger.error(str(e))
        return None

    if fp is None:
        logger.warning(f'Error opening file "{in_fname}"')
        return None

    num_item = -1
    for num_item, linebytes in enumerate(fp):
        line_str = linebytes.decode("utf-8").rstrip("\n")
        yield json.loads(line_str)
        if max_items is not None and (num_item + 1) == max_items:
            break
    fp.close()
    # msg.info('Loaded {} from \'{}\''.format(num_item + 1, in_fname))
