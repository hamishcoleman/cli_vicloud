"""
Some helper classes to store and render cloud objects, along with any
relevant metadata
"""


class Definition:
    """Encapsulate the data needed to describe the remote object"""
    def __init__(self):
        # Set defaults for the metadata
        self.datasource = None
        self.datatype = None

        # Initialise with empty data
        self.data = None

    def __repr__(self):
        return str(self.__dict__)

    def csv_fields(self):
        """Return the field names of both metadata and data"""
        d = set()
        d.add("@DataType")
        d.add("@MetaData")
        d.add("@ResourceId")

        for _id, row in self.data.items():
            d.update(row)

        return d

    def csv_rows(self):
        """Yield the contents (with metadata added)"""

        for _id, row in self.data.items():
            this = {}
            this["@DataType"] = self.datatype
            this["@MetaData"] = self.datasource.metadata()
            this["@ResourceId"] = _id
            this.update(row)
            yield this

    def canonical_data(self):
        """Return the data in our cannonical storage format"""

        for _id, row in self.data.items():
            this = {
                "datatype": self.datatype,
                "metadata": self.datasource.metadata(),
                "specifics": row,
            }
            this["metadata"]["resourceid"] = _id
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
