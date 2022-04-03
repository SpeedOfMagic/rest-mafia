class Voting:
    votes: dict[str, str]

    def __init__(self, voters: list[str]):
        self.votes = {voter: None for voter in voters}

    def vote(self, voter: str, candidate: str or None):
        self.votes[voter] = candidate

    def get_winner(self):
        candidate_votes = {}
        majority = len(self.votes) // 2 + 1  # 5 -> 3, 6 -> 4, 7 -> 4, ...
        for candidate in self.votes.values():
            candidate_votes[candidate] = candidate_votes.get(candidate, 0) + 1
            if candidate_votes[candidate] >= majority:
                return candidate
        return None
