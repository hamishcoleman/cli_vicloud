"""
Some helper classes to store and render cloud objects, along with any
relevant metadata
"""


class Definition:
    """Encapsulate the data needed to describe the remote object"""
    def __init__(self):
        # Set defaults for the metadata
        self.datatype = None
        self.region = None
        self.session = None

        # Initialise with empty data
        self.data = None

    def __repr__(self):
        return str(self.__dict__)

    def csv_fields(self):
        """Return the field names of both metadata and data"""
        d = set()
        d.add("@DataType")
        d.add("@Profile")
        d.add("@Region")
        d.add("@ResourceId")

        for _id, row in self.data.items():
            d.update(row)

        return d

    def csv_rows(self):
        """Yield the contents (with metadata added)"""

        for _id, row in self.data.items():
            this = {}
            this["@DataType"] = self.datatype
            this["@Profile"] = self.session.profile_name
            this["@Region"] = self.region
            this["@ResourceId"] = _id
            this.update(row)
            yield this

    def canonical_data(self):
        """Return the data in our cannonical storage format"""

        for _id, row in self.data.items():
            this = {
                "datatype": self.datatype,
                "metadata": {
                    "profile": self.session.profile_name,
                    "region": self.region,
                    "resourceid": _id,
                },
                "specifics": row,
            }
            yield this


class DefinitionSet:
    """A list of definitions"""
    def __init__(self):
        self._list = []

    def __repr__(self):
        return str(self._list)

    def append(self, data):
        self._list.append(data)

    def csv_fields(self):
        """Return the combined field names of all the definitions"""
        d = set()
        for data in self._list:
            d.update(data.csv_fields())
        return d

    def csv_rows(self):
        """Yield the contents for csv"""
        for data in self._list:
            for row in data.csv_rows():
                yield row

    def canonical_data(self):
        """Yield the contents for storage"""
        for data in self._list:
            for row in data.canonical_data():
                yield row
