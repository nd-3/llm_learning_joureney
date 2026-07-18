"""pytest共通設定。

src/main.py と evals/run_eval.py はパッケージ化されていないスクリプトのため、
それぞれのディレクトリをsys.pathに追加してテストから直接importできるようにする。
(evals/run_eval.py自身も同じ方法でsrc/main.pyをimportしている)
"""

import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)

for _subdir in ("src", "evals"):
    _path = os.path.join(PROJECT_ROOT, _subdir)
    if _path not in sys.path:
        sys.path.insert(0, _path)
