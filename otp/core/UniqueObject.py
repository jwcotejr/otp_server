class UniqueObject:

    def uniqueName(self, name):
        return name + '-' + str(id(self))
