import os
from typing import List


class BatchReviewStrategy:
    """大 PR 分批审查策略"""

    def __init__(self, repo_root: str = ".", batch_size: int = 10):
        self.repo_root = os.path.abspath(repo_root)
        self.batch_size = batch_size

    def split_batches(self, changed_files: List[str]) -> List[List[str]]:
        files_with_size = []
        for f in changed_files:
            full_path = os.path.join(self.repo_root, f)
            try:
                size = os.path.getsize(full_path)
            except OSError:
                size = 0
            files_with_size.append((f, size))

        files_with_size.sort(key=lambda x: x[1], reverse=True)

        batches: List[List[str]] = []
        current_batch: List[str] = []

        for file_path, _ in files_with_size:
            if len(current_batch) >= self.batch_size:
                batches.append(current_batch)
                current_batch = []
            current_batch.append(file_path)

        if current_batch:
            batches.append(current_batch)

        return batches
