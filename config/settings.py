# Extensions to load on startup
EXTENSIONS = [
    "Competitive",
    "Matchmaking",
    "InteractionManager",
    "LeaderboardManager"
]

# MATCHMAKING
MATCH_CREATE_CHANNEL = 900296244847587368
ONGOING_MATCHES_CHANNEL = 900296281338048562
MATCH_RESULTS_CHANNEL = 900296326254837761
LEADERBOARDS_CHANNEL = 905136981615468594

MATCHMAKING_JOIN_QUEUE_CUSTOM_ID = 'enterqueue-craneduels'
MATCHMAKING_EXIT_QUEUE_CUSTOM_ID = 'exitqueue-craneduels'

MATCHMAKING_CREATE_MATCH_FREQUENCY = 5   # time in seconds to attempt to make matches
MATCHMAKING_ONGOING_CUSTOM_ID = 'ongoingmatch-craneduels'

#MODE THUMBNAILS AND COLORS
THUMBNAILS = {
    'craneduels': "https://i.imgur.com/plhYQt3.png",
}

COLORS = {
    'craneduels': 0x65a079,
}