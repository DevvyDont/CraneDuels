class Match:

    def __init__(self, id, linked_message_id, competitors=None):

        self.id = id

        self.message_id = linked_message_id

        if competitors is None:
            raise Exception("competitiors must not be empty")
        self.competitors = competitors

