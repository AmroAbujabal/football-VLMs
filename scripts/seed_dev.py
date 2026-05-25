from database.session import engine, SessionLocal
from database.models import Base, Academy, Match, Player, PlayerMatchStats

Base.metadata.create_all(engine)
db = SessionLocal()

a = Academy(name='Al Ain FC', city='Al Ain', country='UAE', tier='pro')
db.add(a)
db.flush()

m = Match(
    academy_id=a.id,
    home_team='Al Ain',
    away_team='Al Jazira',
    processing_status='done',
    fps=25.0,
)
db.add(m)
db.flush()

p1 = Player(academy_id=a.id, name='Track 7', position='CM', jersey_number=7)
p2 = Player(academy_id=a.id, name='Track 9', position='ST', jersey_number=9)
db.add_all([p1, p2])
db.flush()

db.add(PlayerMatchStats(
    player_id=p1.id, match_id=m.id, team='home',
    distance_covered_m=9400, top_speed_ms=9.1, avg_speed_ms=5.2,
    sprint_count=6, hi_run_count=15, press_count=9,
    press_success_rate=0.67, pitch_control_contribution=0.61,
))
db.add(PlayerMatchStats(
    player_id=p2.id, match_id=m.id, team='away',
    distance_covered_m=7600, top_speed_ms=8.7, avg_speed_ms=4.5,
    sprint_count=3, hi_run_count=8, press_count=3,
    press_success_rate=0.33, pitch_control_contribution=0.39,
))
db.commit()

print('ACADEMY_ID =', a.id)
print('MATCH_ID   =', m.id)
