class Match:

    def __init__(self, id, mode_id, linked_message_id, competitors=None):

        self.id = id
        
        self.mode_id = mode_id

        self.message_id = linked_message_id

        if competitors is None:
            raise Exception("competitiors must not be empty")

        self.competitors = competitors
        self.competitors_info = {}
    
    def assign_player_points(self, competitor, points):
        self.competitors_info[competitor] = points
        
    def get_competitor_info(self):
        return self.competitors_info

    def calculate_total_points(self, damage, stuns, goons):
        return damage + stuns*10 + goons*2