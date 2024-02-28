# Copyright (C) 2015-2021, Fortishield Inc.
# Created by Fortishield, Inc. <security@khulnasoft.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2
import sys
sys.path.append('/fortishield-qa/deps/fortishield_testing')
from fortishield_testing import fortishield_db

result = fortishield_db.query_wdb(sys.argv[1])
if result:
  print(result)
