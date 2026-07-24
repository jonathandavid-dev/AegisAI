import os
from app.benchmarks.benchmark_loader import BenchmarkLoader

class DatasetManager:
    """
    Scans and manages golden QA datasets in the local datasets folder.
    """
    DEFAULT_DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datasets")

    @classmethod
    def get_available_datasets(cls) -> list[str]:
        """
        Returns a list of JSON/YAML datasets discovered.
        """
        if not os.path.exists(cls.DEFAULT_DATASET_DIR):
            return []
        
        datasets = []
        for file in os.listdir(cls.DEFAULT_DATASET_DIR):
            if file.lower().endswith((".json", ".yaml", ".yml")):
                datasets.append(file)
        return datasets

    @classmethod
    def load_dataset(cls, dataset_name: str) -> list[dict]:
        """
        Loads the cases of a specific dataset name.
        """
        filepath = os.path.join(cls.DEFAULT_DATASET_DIR, dataset_name)
        return BenchmarkLoader.load_from_file(filepath)
