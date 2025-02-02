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

    def fields(self):
        """Return the field names of both metadata and data"""
        d = set()
        d.add("@DataType")
        d.add("@Profile")
        d.add("@Region")
        d.add("@ResourceId")

        for _id, row in self.data.items():
            d.update(row)

        return d

    def rows(self):
        """Yield the contents (with metadata added)"""

        for _id, row in self.data.items():
            this = {}
            this["@DataType"] = self.datatype
            this["@Profile"] = self.session.profile_name
            this["@Region"] = self.region
            this["@ResourceId"] = _id
            this.update(row)
            yield this


class DefinitionSet:
    """A list of definitions"""
    def __init__(self):
        self._list = []

    def __repr__(self):
        return str(self._list)

    def append(self, data):
        self._list.append(data)

    def fields(self):
        """Return the combined field names of all the definitions"""
        d = set()
        for data in self._list:
            d.update(data.fields())
        return d

    def rows(self):
        """Yield the contents"""
        for data in self._list:
            for row in data.rows():
                yield row
