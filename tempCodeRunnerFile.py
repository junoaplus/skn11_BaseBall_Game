from game.manager import select_team, select_lineup
from game.engine import play_season

if __name__ == "__main__":
    team = select_team()
    lineup, bench, starting, bullpen = select_lineup(team)
    play_season(team, lineup, bench, starting, bullpen)