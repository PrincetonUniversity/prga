# Here's a hack-fix for the following dependency combos to work:
#   1. protobuf 2.5 w/ Python 2.7
#   2. protobuf 3.7 w/ Python 3.7
# Note that protobuf 2.5 will not work with Python 3 because of string encoding: literal string is utf-8 encoded in
# Python 3, but protobuf expects byte-encoded string. Similarly, protobuf 3.7 will not work with Python 2.

import sys
import os

_dir = os.path.dirname(__file__)
sys.path.append(_dir)

import common_pb2 as common
import bitchain_pb2 as bitchain

sys.path.remove(_dir)
