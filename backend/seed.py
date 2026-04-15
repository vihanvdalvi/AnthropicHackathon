"""
Seed script — populates: 50 users, 10 issues, ~200 posts, LLM summaries.
Run: python -m backend.seed
"""

import asyncio
import json
import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from backend.database import init_db, AsyncSessionLocal
from backend.models import User, Issue, Post
from backend import ml

ANON_NAMES = [
    "TealHarbor91", "QuietMaple33", "SilverCreek07", "BrightFern44",
    "CalmRidge19", "SwiftPine82", "DuskMeadow55", "GrayStone61",
    "EchoValley28", "WildOak73", "StillWater14", "HighPlain36",
    "OpenField90", "ClearRiver47", "DarkHollow22", "SoftBirch58",
    "RisingTide03", "LostMoss67", "MildCliff39", "WarmDelta85",
    "ThinAir11", "BoldPath52", "ColdFront26", "RoundHill78",
    "FlatRock43", "SlowWave95", "PaleLeaf17", "DeepFjord64",
    "LightMist30", "SteepBank88", "SaltFen05", "NarrowPass71",
    "BroadFalls49", "SoftDune23", "HollowReed96", "SternCrag41",
    "ClearMoor68", "BluntPeak15", "ShadedGlen59", "RoughTide82",
    "QuietBog37", "ThinCrest04", "WideGully70", "PaleWash48",
    "LowMarch92", "BoldBluff21", "CoolSlope66", "HardSpur38",
    "FlatMeadow83", "WarmChannel12",
]

SEED_ISSUES = [
    "Campus Housing Costs",
    "Dining Hall Quality and Pricing",
    "Tuition Increases",
    "Campus Safety at Night",
    "Mental Health Resources",
    "Free Speech on Campus",
    "Sustainability and Climate Policy",
    "Diversity in Curriculum",
    "Greek Life and Social Culture",
    "Student Government Transparency",
]

SEED_POSTS: dict[str, list[dict]] = {
    "Campus Housing Costs": [
        {"text": "I pay $1,400/month to live 20 minutes from campus. That's not sustainable on a student budget.", "intensity": 9.1, "sentiment": -0.85},
        {"text": "The university should build more on-campus housing instead of partnering with expensive private developers.", "intensity": 7.4, "sentiment": -0.6},
        {"text": "Off-campus rent has gone up 40% in 3 years. I had to take a second job just to stay enrolled.", "intensity": 8.8, "sentiment": -0.9},
        {"text": "Friends at other schools pay half what we do for similar housing. Something is wrong here.", "intensity": 8.0, "sentiment": -0.75},
        {"text": "Housing insecurity is affecting my grades. I can't focus when I don't know if I can make rent.", "intensity": 9.5, "sentiment": -0.95},
        {"text": "There's a reason housing costs more near a university. It's supply and demand — the school can't control the market.", "intensity": 5.2, "sentiment": 0.1},
        {"text": "New dorms are expensive to build and maintain. Someone has to pay for that.", "intensity": 4.7, "sentiment": 0.2},
        {"text": "Living on campus is a choice. Students can commute from more affordable areas.", "intensity": 3.9, "sentiment": 0.3},
        {"text": "The quality of housing has genuinely improved. Better facilities cost more — that's just reality.", "intensity": 5.5, "sentiment": 0.4},
        {"text": "The city's zoning laws make it almost impossible to build more housing near campus quickly.", "intensity": 6.1, "sentiment": 0.0},
        {"text": "I know three people who dropped out because they couldn't afford to live here anymore.", "intensity": 9.2, "sentiment": -0.92},
        {"text": "Housing stipends for low-income students would go a long way. Why isn't this being discussed?", "intensity": 8.3, "sentiment": -0.8},
        {"text": "My commute is 90 minutes each way because I can't afford anything closer. This affects my mental health.", "intensity": 9.0, "sentiment": -0.9},
        {"text": "More housing supply from any source — public or private — is better than less.", "intensity": 5.8, "sentiment": 0.1},
        {"text": "The housing market near campus reflects broader city trends. This is a city problem, not just a university problem.", "intensity": 5.0, "sentiment": 0.05},
    ],
    "Dining Hall Quality and Pricing": [
        {"text": "A meal swipe costs $14 and gives me a sad salad and a lukewarm entree. This is exploitation.", "intensity": 7.8, "sentiment": -0.82},
        {"text": "They removed the late-night dining option this semester. Students who study late have nowhere to eat.", "intensity": 8.1, "sentiment": -0.78},
        {"text": "The dining hall doesn't label allergens clearly. As someone with a nut allergy, I'm genuinely scared.", "intensity": 9.3, "sentiment": -0.91},
        {"text": "They've cut vegetarian options in half. There used to be two hot vegetarian entrees. Now there's one.", "intensity": 7.2, "sentiment": -0.7},
        {"text": "I found a cockroach in my soup last month. I reported it and heard nothing.", "intensity": 9.5, "sentiment": -0.95},
        {"text": "For the price, the food is actually decent. I've eaten worse at restaurants that cost more.", "intensity": 4.2, "sentiment": 0.4},
        {"text": "Running a large campus dining operation is genuinely hard. Costs are up everywhere.", "intensity": 5.0, "sentiment": 0.1},
        {"text": "The dining hall has improved a lot since the new vendor took over. Give them time.", "intensity": 4.8, "sentiment": 0.5},
        {"text": "You don't have to use the dining plan if you don't like it. Cook for yourself.", "intensity": 3.5, "sentiment": 0.2},
        {"text": "The dining hall is trying to accommodate more dietary needs than it ever has before.", "intensity": 4.6, "sentiment": 0.3},
    ],
    "Tuition Increases": [
        {"text": "Tuition went up 6% this year. My financial aid didn't. I'm taking out more loans than ever.", "intensity": 9.2, "sentiment": -0.9},
        {"text": "The university announced a new $80M athletics facility the same week they raised tuition.", "intensity": 8.7, "sentiment": -0.87},
        {"text": "I'll graduate with $45,000 in debt. That's not a degree — that's a mortgage.", "intensity": 9.4, "sentiment": -0.93},
        {"text": "First-gen students like me have no family wealth to fall back on. Every increase is existential.", "intensity": 9.6, "sentiment": -0.95},
        {"text": "Universities face real cost pressures — faculty salaries, facilities, benefits. Tuition has to cover that.", "intensity": 5.5, "sentiment": 0.05},
        {"text": "Financial aid scales with tuition for many students. The sticker price isn't what most people pay.", "intensity": 4.5, "sentiment": 0.25},
        {"text": "I work 25 hours a week to afford this. My grades are suffering and my health is worse.", "intensity": 9.0, "sentiment": -0.9},
        {"text": "The endowment is $2 billion. The university is choosing not to use it. That's a values statement.", "intensity": 9.1, "sentiment": -0.92},
        {"text": "Scholarships exist and are underutilized. Students should pursue every option.", "intensity": 4.2, "sentiment": 0.15},
        {"text": "The cost of a degree here is still a better long-term investment than not going at all.", "intensity": 4.0, "sentiment": 0.3},
    ],
    "Campus Safety at Night": [
        {"text": "I was followed to my car at 11pm last Tuesday. Campus police took 25 minutes to respond.", "intensity": 9.7, "sentiment": -0.97},
        {"text": "The lighting on the south path to the library is completely out. Has been for weeks.", "intensity": 8.2, "sentiment": -0.8},
        {"text": "As a woman, I've changed my entire schedule to avoid being on campus after 9pm. That's not okay.", "intensity": 9.3, "sentiment": -0.93},
        {"text": "Three sexual assaults were reported in the past month near the east parking structure. This is a crisis.", "intensity": 9.5, "sentiment": -0.95},
        {"text": "The Safe Ride program was cancelled this year. That was one of the most used services on campus.", "intensity": 8.4, "sentiment": -0.84},
        {"text": "I've walked this campus at all hours for 4 years without incident. It's genuinely safer than off-campus.", "intensity": 4.5, "sentiment": 0.3},
        {"text": "The escort service is free and available. Use it — that's what it's there for.", "intensity": 4.0, "sentiment": 0.4},
        {"text": "Crime statistics on campus are lower than most comparable campuses. We're actually doing okay.", "intensity": 4.7, "sentiment": 0.35},
        {"text": "Safety improvements cost money. There's a real tradeoff with other budget priorities.", "intensity": 5.0, "sentiment": 0.0},
        {"text": "The peer safety ambassador program is genuinely helpful. More funding there would go far.", "intensity": 5.5, "sentiment": 0.3},
    ],
    "Mental Health Resources": [
        {"text": "I waited 6 weeks to see a counselor. By then my crisis had passed — barely.", "intensity": 9.4, "sentiment": -0.93},
        {"text": "The counseling center is only open M-F 9-5. Students have mental health crises at 2am too.", "intensity": 8.6, "sentiment": -0.86},
        {"text": "There are 2 psychiatrists for 30,000 students. Do the math.", "intensity": 9.1, "sentiment": -0.91},
        {"text": "I left school for a semester because I couldn't get help. I nearly didn't come back.", "intensity": 9.5, "sentiment": -0.95},
        {"text": "Athletes are told mental health concerns could affect their scholarship. That's a chilling effect.", "intensity": 9.0, "sentiment": -0.9},
        {"text": "The counseling center has hired three new counselors this year. More help is coming.", "intensity": 5.0, "sentiment": 0.4},
        {"text": "Teletherapy options have expanded. It's not perfect but there are more access points.", "intensity": 4.8, "sentiment": 0.35},
        {"text": "There are peer support groups, crisis lines, and wellness workshops. Some students just don't know.", "intensity": 4.3, "sentiment": 0.2},
        {"text": "My RA has been better than any formal resource. Peer support matters.", "intensity": 5.5, "sentiment": 0.5},
        {"text": "They added a walk-in crisis hour every week. That's not enough but it's a real change.", "intensity": 4.4, "sentiment": 0.2},
    ],
    "Free Speech on Campus": [
        {"text": "A speaker was disinvited last month without any public explanation. That's not how open inquiry works.", "intensity": 8.1, "sentiment": -0.75},
        {"text": "Some speech causes real harm to students who are already marginalized. That's not hypothetical.", "intensity": 8.2, "sentiment": -0.6},
        {"text": "Students shouldn't have to debate their right to exist on this campus.", "intensity": 8.8, "sentiment": -0.85},
        {"text": "The best response to bad speech is more speech, not censorship.", "intensity": 7.0, "sentiment": 0.2},
        {"text": "Universities used to be the place ideas went to be tested. Now they're managed for emotional safety.", "intensity": 7.3, "sentiment": -0.4},
        {"text": "Context matters. A hateful speaker on a campus with a history of bias incidents is different.", "intensity": 5.5, "sentiment": 0.0},
        {"text": "The speech policies here are clearer than most campuses I looked at.", "intensity": 4.5, "sentiment": 0.4},
        {"text": "I want to be able to argue for my views in class without being treated as harmful for holding them.", "intensity": 7.5, "sentiment": -0.65},
        {"text": "Most of what gets called censorship here is just communities declining to platform certain voices.", "intensity": 5.2, "sentiment": 0.1},
        {"text": "We've had controversial events that went fine. The sky doesn't always fall.", "intensity": 4.0, "sentiment": 0.3},
    ],
    "Sustainability and Climate Policy": [
        {"text": "The university still has $200M invested in fossil fuels. Every climate pledge they make is hollow.", "intensity": 8.9, "sentiment": -0.88},
        {"text": "Our campus emits more carbon than a small city. The 2040 net zero goal is too slow.", "intensity": 8.2, "sentiment": -0.82},
        {"text": "Single-use plastics are everywhere — dining, events, labs. We banned plastic bags but nothing else.", "intensity": 7.8, "sentiment": -0.78},
        {"text": "Climate action on campus is also about justice — sustainability costs fall hardest on the vulnerable.", "intensity": 8.3, "sentiment": -0.75},
        {"text": "We have no composting program. Food waste just goes to landfill. This isn't hard to fix.", "intensity": 7.5, "sentiment": -0.74},
        {"text": "The university installed solar panels on 6 buildings this year. That's meaningful progress.", "intensity": 5.5, "sentiment": 0.5},
        {"text": "Campus emissions are down 18% since 2015. The trajectory is real.", "intensity": 5.0, "sentiment": 0.35},
        {"text": "We have a student sustainability council with real power. That's more than most universities.", "intensity": 5.2, "sentiment": 0.4},
        {"text": "Transition takes time and money. The university is balancing this with dozens of other priorities.", "intensity": 4.6, "sentiment": 0.1},
        {"text": "I appreciate that climate is being taken seriously at all. Five years ago it wasn't on the agenda.", "intensity": 4.5, "sentiment": 0.45},
    ],
    "Diversity in Curriculum": [
        {"text": "I took 3 history courses and never read a primary source written by a woman or person of color.", "intensity": 8.4, "sentiment": -0.84},
        {"text": "The diversity requirement is one class. One. For a four-year degree.", "intensity": 7.9, "sentiment": -0.79},
        {"text": "I've gone entire semesters without seeing my community's history in a syllabus.", "intensity": 8.6, "sentiment": -0.86},
        {"text": "Disability perspectives are almost entirely absent from the curriculum across every field.", "intensity": 8.0, "sentiment": -0.8},
        {"text": "When the canon is only one culture, students are trained to see that culture as default.", "intensity": 7.8, "sentiment": -0.7},
        {"text": "Curriculum change is a slow, faculty-driven process. It can't be mandated overnight.", "intensity": 5.0, "sentiment": 0.0},
        {"text": "Many departments have updated syllabi significantly in the past 5 years. Progress is happening.", "intensity": 4.7, "sentiment": 0.35},
        {"text": "The new ethnic studies requirement passed last year. That was a major structural change.", "intensity": 4.5, "sentiment": 0.4},
        {"text": "I've had professors who actively sought diverse readings. It's a faculty culture question.", "intensity": 5.0, "sentiment": 0.15},
        {"text": "The change I want to see is being built. Slowly. But it is being built.", "intensity": 4.3, "sentiment": 0.35},
    ],
    "Greek Life and Social Culture": [
        {"text": "Hazing is still happening. People just don't report it because they're afraid of losing their community.", "intensity": 8.5, "sentiment": -0.85},
        {"text": "Greek life controls too much of campus social life. If you're not in, you're out.", "intensity": 7.8, "sentiment": -0.78},
        {"text": "I've heard firsthand accounts of assault at Greek events that never got reported.", "intensity": 9.1, "sentiment": -0.91},
        {"text": "The university's response to misconduct allegations in Greek life is consistently inadequate.", "intensity": 8.3, "sentiment": -0.83},
        {"text": "Social events should be accessible to everyone, not just people who can afford membership fees.", "intensity": 7.8, "sentiment": -0.78},
        {"text": "Greek life gave me my closest friendships and professional network. It's not what the critics say.", "intensity": 6.5, "sentiment": 0.7},
        {"text": "My chapter does 200+ hours of community service a year. That story never gets told.", "intensity": 5.8, "sentiment": 0.5},
        {"text": "Not all Greek organizations are the same. Painting them all with one brush is unfair.", "intensity": 6.0, "sentiment": 0.4},
        {"text": "The inter-Greek council has adopted a new accountability framework. Give it time to work.", "intensity": 4.5, "sentiment": 0.35},
        {"text": "Some of the best mental health and DEI programming on campus is run by Greek chapters.", "intensity": 5.3, "sentiment": 0.45},
    ],
    "Student Government Transparency": [
        {"text": "SGA spent $40,000 on a retreat but can't fund the food pantry expansion students voted for.", "intensity": 8.7, "sentiment": -0.87},
        {"text": "The same 15 people run every committee. This isn't representative government.", "intensity": 7.8, "sentiment": -0.78},
        {"text": "Student fees fund SGA but students have no mechanism for direct budget approval.", "intensity": 8.4, "sentiment": -0.84},
        {"text": "Every resolution SGA passes gets ignored by the administration anyway.", "intensity": 8.0, "sentiment": -0.8},
        {"text": "I've submitted three feedback forms to SGA. Zero responses. Not even an auto-reply.", "intensity": 7.5, "sentiment": -0.75},
        {"text": "SGA passed three major resolutions this semester. Two of them came from student petitions.", "intensity": 5.0, "sentiment": 0.45},
        {"text": "The president holds weekly office hours. Anyone can come.", "intensity": 4.8, "sentiment": 0.2},
        {"text": "My senator is genuinely responsive and has followed through on commitments.", "intensity": 5.0, "sentiment": 0.6},
        {"text": "The new SGA website actually has searchable meeting minutes now. That's progress.", "intensity": 4.2, "sentiment": 0.5},
        {"text": "SGA advocacy led to extended library hours last year. Real impact, even if slow.", "intensity": 4.8, "sentiment": 0.5},
    ],
}


async def seed():
    await init_db()

    async with AsyncSessionLocal() as db:
        # --- Users ---
        print("Seeding users...")
        for name in ANON_NAMES:
            existing = (await db.execute(select(User).where(User.anon_name == name))).scalar_one_or_none()
            if not existing:
                db.add(User(anon_name=name, lean_score=round(random.uniform(-1.0, 1.0), 3)))
        await db.commit()
        user_objects = (await db.execute(select(User))).scalars().all()
        print(f"  {len(user_objects)} users ready.")

        # --- Issues + Posts ---
        print("Seeding issues and posts...")
        issue_map: dict[str, Issue] = {}
        for label in SEED_ISSUES:
            existing = (await db.execute(select(Issue).where(Issue.label == label))).scalar_one_or_none()
            if existing:
                issue_map[label] = existing
            else:
                issue = Issue(
                    label=label,
                    week_start=date.today().isoformat(),
                    post_count=0, sentiment_avg=0.0,
                    intensity_avg=0.0, rank_score=0.0,
                )
                db.add(issue)
                issue_map[label] = issue
        await db.commit()
        for i in (await db.execute(select(Issue))).scalars().all():
            issue_map[i.label] = i

        total_posts = 0
        for label, posts_data in SEED_POSTS.items():
            issue = issue_map.get(label)
            if not issue:
                continue
            existing_posts = (await db.execute(select(Post).where(Post.issue_id == issue.id))).scalars().all()
            if len(existing_posts) >= len(posts_data):
                print(f"  Skipping '{label}' — already seeded.")
                continue

            sentiments, intensities = [], []
            for pd in posts_data:
                user = random.choice(user_objects)
                post = Post(
                    user_id=user.id, issue_id=issue.id,
                    text=pd["text"], sentiment=pd["sentiment"], intensity=pd["intensity"],
                    created_at=datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 168)),
                )
                db.add(post)
                sentiments.append(pd["sentiment"])
                intensities.append(pd["intensity"])
                total_posts += 1

            n = len(posts_data)
            issue.post_count = n
            issue.sentiment_avg = round(sum(sentiments) / n, 4)
            issue.intensity_avg = round(sum(intensities) / n, 4)
            issue.rank_score = ml.compute_rank_score(n, issue.intensity_avg, ml.recency_weight(datetime.now(timezone.utc)))
            await db.commit()
            print(f"  Seeded '{label}': {n} posts.")

        # --- LLM Summaries ---
        print("Generating LLM summaries (this takes ~1-2 min)...")
        for label, issue in issue_map.items():
            await db.refresh(issue)
            if issue.summary:
                print(f"  '{label}' already summarized.")
                continue
            texts = [r[0] for r in (await db.execute(select(Post.text).where(Post.issue_id == issue.id))).fetchall()]
            if not texts:
                continue
            try:
                d = await ml.summarize_issue(label, texts)
                issue.summary = d["summary"]
                issue.side_a_points = json.dumps(d["side_a_points"])
                issue.side_b_points = json.dumps(d["side_b_points"])
                issue.shared_concerns = json.dumps(d["shared_concerns"])
                await db.commit()
                print(f"  Summarized '{label}'.")
            except Exception as e:
                print(f"  Summary failed for '{label}': {e}")

        print(f"\nSeed complete: {len(user_objects)} users, {len(issue_map)} issues, {total_posts} new posts.")


if __name__ == "__main__":
    asyncio.run(seed())
