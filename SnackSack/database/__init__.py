import json

from .package import Package
from .partner import Partner


class PackageDB:
    def __init__(self, file):
        self.file = file # "packages.json"
        self.records = []

        try:
            with open(self.file) as f:
                self.records = json.load(f)

        except Exception as e:
            raise e


    def update_file(self):
        with open(self.file, "w") as f:
            json.dump(self.records, f, indent=4)


    def checkout(self, index: int, amount: int = 1):
        try:
            assert index < len(self.records), "IndexError"

            package = Package.from_json(self.records[index])

            assert package.amount >= amount

            package.amount -= amount

            if package.amount > 0:
                self.records[index] = package.to_json()
            else:
                self.records.pop(index)

        except Exception as e:
            raise e


class PartnerDB:
    def __init__(self, file):
        self.file = file # "partners.json"
        self.records = []

        try:
            with open(self.file) as f:
                self.records = json.load(f)

        except Exception as e:
            raise e


    def update_file(self):
        with open(self.file, "w") as f:
            json.dump(self.records, f, indent=4)


    def create(self, record: Partner):
        self.records.append(record.to_json())
