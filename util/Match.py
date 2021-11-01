class Match:

    def __init__(self, id, mode_id, linked_message_id, competitors=None):

        self.id = id
        self.mode_id = mode_id
        self.message_id = linked_message_id

        if competitors is None:
            raise Exception("competitiors must not be empty")

        self.competitors = competitors
        self.competitors_points = {}
        self.competitors_info = {}
    
    def assign_player_points(self, competitor, damage, stuns, goons):
        self.competitors_info[competitor] = {
            "damage": damage,
            "stuns": stuns,
            "goons": goons,
            "points": damage + stuns*10 + goons*2
        }
        self.competitors_points[competitor] = damage + stuns*10 + goons*2
    
    def assign_elo_gain(self, competitor, elo):
        self.competitors_info[competitor]["elo"] = elo
        
    def get_competitor_info(self):
        return self.competitors_info

    def calculate_total_points(self, damage, stuns, goons):
        return damage + stuns*10 + goons*2
        
    def is_total_damage_valid(self):
        total = 0
        for player_info in self.competitors_info:
            total += self.competitors_info[player_info]["damage"]
            
        return 1500 <= total <= 1562