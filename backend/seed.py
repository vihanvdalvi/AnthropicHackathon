"""
Seed script — owned by Person C.
Run: python -m backend.seed
Populates: 50 users, 10 issues, ~200 posts.
"""

import asyncio
import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from backend.database import init_db, AsyncSessionLocal
from backend.models import User, Issue, Post, EmpathyStat
from backend import ml

# ---------------------------------------------------------------------------
# Static seed data
# ---------------------------------------------------------------------------

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

# Posts per issue: (text, intensity, sentiment)
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
        {"text": "The university made $200M in investments last year. They can afford to subsidize student housing.", "intensity": 7.8, "sentiment": -0.7},
        {"text": "Housing stipends for low-income students would go a long way. Why isn't this being discussed?", "intensity": 8.3, "sentiment": -0.8},
        {"text": "I've had to move three times this year because landlords keep raising rent mid-lease.", "intensity": 8.6, "sentiment": -0.88},
        {"text": "My commute is 90 minutes each way because I can't afford anything closer. This affects my mental health.", "intensity": 9.0, "sentiment": -0.9},
        {"text": "Some of us chose to live farther away and budget accordingly. It's manageable.", "intensity": 4.0, "sentiment": 0.35},
        {"text": "University-owned housing is often lower quality than private. The market provides better options.", "intensity": 4.5, "sentiment": 0.25},
        {"text": "More housing supply from any source — public or private — is better than less.", "intensity": 5.8, "sentiment": 0.1},
        {"text": "My parents help with rent. I know that's not everyone's situation, but I don't think the university should manage housing.", "intensity": 3.5, "sentiment": 0.15},
        {"text": "The housing market near campus reflects broader city trends. This is a city problem, not just a university problem.", "intensity": 5.0, "sentiment": 0.05},
    ],
    "Dining Hall Quality and Pricing": [
        {"text": "A meal swipe costs $14 and gives me a sad salad and a lukewarm entree. This is exploitation.", "intensity": 7.8, "sentiment": -0.82},
        {"text": "They removed the late-night dining option this semester. Students who study late have nowhere to eat on campus.", "intensity": 8.1, "sentiment": -0.78},
        {"text": "The dining hall doesn't label allergens clearly. As someone with a nut allergy, I'm genuinely scared.", "intensity": 9.3, "sentiment": -0.91},
        {"text": "They've cut vegetarian options in half. There used to be two hot vegetarian entrees. Now there's one, most days.", "intensity": 7.2, "sentiment": -0.7},
        {"text": "The dining workers are amazing — the problems are with administration, not the staff.", "intensity": 6.5, "sentiment": -0.4},
        {"text": "For the price, the food is actually decent. I've eaten worse at restaurants that cost more.", "intensity": 4.2, "sentiment": 0.4},
        {"text": "Running a large campus dining operation is genuinely hard. Costs are up everywhere.", "intensity": 5.0, "sentiment": 0.1},
        {"text": "The dining hall has improved a lot since the new vendor took over. Give them time.", "intensity": 4.8, "sentiment": 0.5},
        {"text": "You don't have to use the dining plan if you don't like it. Cook for yourself.", "intensity": 3.5, "sentiment": 0.2},
        {"text": "The dining hall is trying to accommodate more dietary needs than it ever has before. Progress takes time.", "intensity": 4.6, "sentiment": 0.3},
        {"text": "I found a cockroach in my soup last month. I reported it and heard nothing.", "intensity": 9.5, "sentiment": -0.95},
        {"text": "The mandatory meal plan for first-years is a cash grab. We should be allowed to opt out.", "intensity": 8.4, "sentiment": -0.8},
        {"text": "Dining hall hours are terrible for students with evening labs or rehearsals.", "intensity": 7.6, "sentiment": -0.73},
        {"text": "I skip meals because it's easier than dealing with the long lines and limited options.", "intensity": 8.0, "sentiment": -0.85},
        {"text": "Campus food deserts are real — some students can't afford to supplement the meal plan with off-campus food.", "intensity": 8.7, "sentiment": -0.88},
        {"text": "Some of us actually like the dining hall. It's convenient and consistent.", "intensity": 4.0, "sentiment": 0.6},
        {"text": "I've used the suggestion box three times. Things have actually changed. Feedback works.", "intensity": 3.8, "sentiment": 0.55},
        {"text": "The salad bar is fresh and well-stocked. People who complain aren't looking at the full picture.", "intensity": 3.5, "sentiment": 0.5},
        {"text": "Dining is a massive logistical challenge. Expecting gourmet food at institutional scale is unrealistic.", "intensity": 4.5, "sentiment": 0.15},
        {"text": "The new smoothie station is genuinely good. Small wins count.", "intensity": 3.0, "sentiment": 0.65},
    ],
    "Tuition Increases": [
        {"text": "Tuition went up 6% this year. My financial aid didn't. I'm taking out more loans than ever.", "intensity": 9.2, "sentiment": -0.9},
        {"text": "The university announced a new $80M athletics facility the same week they raised tuition. I can't.", "intensity": 8.7, "sentiment": -0.87},
        {"text": "Every year they cite 'rising costs' but never explain what those costs are. Where is the transparency?", "intensity": 8.0, "sentiment": -0.8},
        {"text": "I'll graduate with $45,000 in debt. That's not a degree — that's a mortgage.", "intensity": 9.4, "sentiment": -0.93},
        {"text": "First-gen students like me have no family wealth to fall back on. Every increase is existential.", "intensity": 9.6, "sentiment": -0.95},
        {"text": "Universities face real cost pressures — faculty salaries, facilities, benefits. Tuition has to cover that.", "intensity": 5.5, "sentiment": 0.05},
        {"text": "Compared to peer institutions, our tuition is actually below average.", "intensity": 4.8, "sentiment": 0.2},
        {"text": "State funding for higher education has dropped 30% in 15 years. The university has to make up that gap.", "intensity": 5.2, "sentiment": 0.0},
        {"text": "Financial aid scales with tuition for many students. The sticker price isn't what most people pay.", "intensity": 4.5, "sentiment": 0.25},
        {"text": "The cost of a degree here is still a better long-term investment than not going at all.", "intensity": 4.0, "sentiment": 0.3},
        {"text": "I work 25 hours a week to afford this. My grades are suffering and my health is worse.", "intensity": 9.0, "sentiment": -0.9},
        {"text": "Why do we pay for services we never use? Mandatory fees for things I've never touched.", "intensity": 7.5, "sentiment": -0.72},
        {"text": "Tuition hikes disproportionately hurt students of color and first-generation students. This is a equity issue.", "intensity": 8.5, "sentiment": -0.85},
        {"text": "We need a tuition freeze now. Not a study. Not a task force. An actual freeze.", "intensity": 8.8, "sentiment": -0.88},
        {"text": "The endowment is $2 billion. The university is choosing not to use it. That's a values statement.", "intensity": 9.1, "sentiment": -0.92},
        {"text": "My loans have a repayment plan I can manage. The system isn't perfect but it works for me.", "intensity": 3.8, "sentiment": 0.1},
        {"text": "Scholarships exist and are underutilized. Students should pursue every option before concluding the system is broken.", "intensity": 4.2, "sentiment": 0.15},
        {"text": "I come from a middle-income family — too much money for full aid, not enough for comfort. But I'm making it work.", "intensity": 5.0, "sentiment": 0.0},
        {"text": "I chose this school over cheaper options because of the quality. The value is still there.", "intensity": 4.6, "sentiment": 0.35},
        {"text": "The administration has made hard choices to keep cuts away from academic programs. Tuition goes there.", "intensity": 5.1, "sentiment": 0.2},
    ],
    "Campus Safety at Night": [
        {"text": "I was followed to my car at 11pm last Tuesday. Campus police took 25 minutes to respond.", "intensity": 9.7, "sentiment": -0.97},
        {"text": "The lighting on the south path to the library is completely out. Has been for weeks. Who do I tell?", "intensity": 8.2, "sentiment": -0.8},
        {"text": "More blue light emergency phones won't fix anything if response time is 20+ minutes.", "intensity": 8.5, "sentiment": -0.85},
        {"text": "As a woman, I've changed my entire schedule to avoid being on campus after 9pm. That's not okay.", "intensity": 9.3, "sentiment": -0.93},
        {"text": "The campus safety app crashes constantly. The one time I needed it, it didn't work.", "intensity": 8.8, "sentiment": -0.88},
        {"text": "I've walked this campus at all hours for 4 years without incident. It's genuinely safer than off-campus areas.", "intensity": 4.5, "sentiment": 0.3},
        {"text": "Campus police are underfunded and understaffed. Blaming them ignores the resource problem.", "intensity": 5.8, "sentiment": -0.2},
        {"text": "The escort service is free and available. Use it — that's what it's there for.", "intensity": 4.0, "sentiment": 0.4},
        {"text": "Crime statistics on campus are lower than most comparable campuses. We're actually doing okay.", "intensity": 4.7, "sentiment": 0.35},
        {"text": "Safety improvements cost money. There's a real tradeoff with other budget priorities.", "intensity": 5.0, "sentiment": 0.0},
        {"text": "Three sexual assaults were reported in the past month near the east parking structure. This is a crisis.", "intensity": 9.5, "sentiment": -0.95},
        {"text": "I don't feel safe using the library late. I've started going home earlier, which hurts my studying.", "intensity": 8.0, "sentiment": -0.82},
        {"text": "Night owls on campus are disproportionately grad students and working students. Their safety matters too.", "intensity": 7.8, "sentiment": -0.75},
        {"text": "The Safe Ride program was cancelled this year. That was one of the most used services on campus.", "intensity": 8.4, "sentiment": -0.84},
        {"text": "I've reported the broken lights four times. Nothing happens. The feedback loop is broken.", "intensity": 8.6, "sentiment": -0.86},
        {"text": "My night classes are important for my degree path. I shouldn't have to feel unsafe getting there.", "intensity": 8.9, "sentiment": -0.89},
        {"text": "Most of the safety issues are off-campus adjacent. The university can only control so much.", "intensity": 4.8, "sentiment": 0.1},
        {"text": "The safety committee meets monthly and has made real improvements. The process is slower than we'd like.", "intensity": 4.2, "sentiment": 0.2},
        {"text": "Feeling unsafe and being unsafe are different things. We should be careful not to let anxiety drive policy.", "intensity": 4.5, "sentiment": 0.05},
        {"text": "The peer safety ambassador program is genuinely helpful. More funding there would go far.", "intensity": 5.5, "sentiment": 0.3},
    ],
    "Mental Health Resources": [
        {"text": "I waited 6 weeks to see a counselor. By then my crisis had passed — barely.", "intensity": 9.4, "sentiment": -0.93},
        {"text": "The counseling center is only open M-F 9-5. Students have mental health crises at 2am too.", "intensity": 8.6, "sentiment": -0.86},
        {"text": "I was told I needed more sessions than they could provide and was referred off-campus. I don't have a car.", "intensity": 8.9, "sentiment": -0.89},
        {"text": "There are 2 psychiatrists for 30,000 students. Do the math.", "intensity": 9.1, "sentiment": -0.91},
        {"text": "The mindfulness app they promoted as a resource is not a replacement for actual therapy.", "intensity": 8.3, "sentiment": -0.83},
        {"text": "The counseling center has hired three new counselors this year. More help is coming.", "intensity": 5.0, "sentiment": 0.4},
        {"text": "Teletherapy options have expanded. It's not perfect but there are more access points than there used to be.", "intensity": 4.8, "sentiment": 0.35},
        {"text": "Mental health in college is a national crisis. This campus is doing more than many.", "intensity": 4.5, "sentiment": 0.3},
        {"text": "There are peer support groups, crisis lines, and wellness workshops. Some students just don't know about them.", "intensity": 4.3, "sentiment": 0.2},
        {"text": "Therapy isn't the only solution. Community, exercise, and sleep hygiene matter too.", "intensity": 4.0, "sentiment": 0.1},
        {"text": "I left school for a semester because I couldn't get help. I nearly didn't come back.", "intensity": 9.5, "sentiment": -0.95},
        {"text": "My friend's emergency hospitalization was followed up by... a pamphlet. That's the system we have.", "intensity": 9.2, "sentiment": -0.92},
        {"text": "International students face extra barriers — cultural stigma and language access gaps.", "intensity": 8.7, "sentiment": -0.87},
        {"text": "Athletes are told mental health concerns could affect their scholarship. That's a chilling effect on help-seeking.", "intensity": 9.0, "sentiment": -0.9},
        {"text": "The 'mental health day' policy is meaningless if there's no follow-up support when students use it.", "intensity": 7.9, "sentiment": -0.79},
        {"text": "I've used the counseling center twice and had positive experiences. It helped me get through finals.", "intensity": 4.2, "sentiment": 0.65},
        {"text": "My RA has been better than any formal resource. Peer support matters.", "intensity": 5.5, "sentiment": 0.5},
        {"text": "Group therapy sessions filled up in 2 days. That's a demand problem, but the supply is being increased.", "intensity": 4.7, "sentiment": 0.15},
        {"text": "Some of the mental health issues students face need clinical care the university genuinely can't provide.", "intensity": 5.0, "sentiment": 0.0},
        {"text": "They added a walk-in crisis hour every week. That's not enough but it's a real change.", "intensity": 4.4, "sentiment": 0.2},
    ],
    "Free Speech on Campus": [
        {"text": "A speaker was disinvited last month without any public explanation. That's not how open inquiry works.", "intensity": 8.1, "sentiment": -0.75},
        {"text": "I was told my tabling event needed special approval because of 'controversial content.' What does that mean?", "intensity": 7.8, "sentiment": -0.78},
        {"text": "The administration defines 'harassment' so broadly that legitimate debate gets chilled.", "intensity": 7.5, "sentiment": -0.7},
        {"text": "Students protesting guest speakers are also exercising free speech. Why does one side get more protection?", "intensity": 6.5, "sentiment": -0.3},
        {"text": "Academic freedom requires being challenged. Safe spaces can coexist with open discourse — but not when comfort trumps inquiry.", "intensity": 7.2, "sentiment": -0.5},
        {"text": "Some speech causes real harm to students who are already marginalized. That's not hypothetical.", "intensity": 8.2, "sentiment": -0.6},
        {"text": "Hateful rhetoric isn't free speech — it's a power tool used against specific communities.", "intensity": 8.5, "sentiment": -0.7},
        {"text": "Students shouldn't have to debate their right to exist on this campus. That's what some 'free speech' events require.", "intensity": 8.8, "sentiment": -0.85},
        {"text": "The university has a responsibility to protect students from hostile environments, not just speakers.", "intensity": 7.6, "sentiment": -0.65},
        {"text": "Real inclusion means some people feel less comfortable. The discomfort of marginalized students matters more.", "intensity": 7.9, "sentiment": -0.72},
        {"text": "The best response to bad speech is more speech, not censorship.", "intensity": 7.0, "sentiment": 0.2},
        {"text": "Universities used to be the place ideas went to be tested. Now they're managed for emotional safety.", "intensity": 7.3, "sentiment": -0.4},
        {"text": "I've heard more political uniformity in classrooms here than I expected. That concerns me.", "intensity": 6.8, "sentiment": -0.5},
        {"text": "Disinviting speakers based on student petition pressure is precedent that cuts both ways.", "intensity": 6.5, "sentiment": -0.3},
        {"text": "I want to be able to argue for my views in class without being treated as harmful for holding them.", "intensity": 7.5, "sentiment": -0.65},
        {"text": "Context matters. A hateful speaker on a campus with a history of bias incidents is different from abstract debate.", "intensity": 5.5, "sentiment": 0.0},
        {"text": "The speech policies here are clearer than most campuses I looked at. I think they thread the needle well.", "intensity": 4.5, "sentiment": 0.4},
        {"text": "I've seen both over-restriction and under-restriction on this campus. It's genuinely hard to get right.", "intensity": 5.0, "sentiment": 0.0},
        {"text": "Most of what gets called 'censorship' here is just communities declining to platform certain voices.", "intensity": 5.2, "sentiment": 0.1},
        {"text": "We've had controversial events that went fine. The sky doesn't always fall.", "intensity": 4.0, "sentiment": 0.3},
    ],
    "Sustainability and Climate Policy": [
        {"text": "The university still has $200M invested in fossil fuels. Every climate pledge they make is hollow until that changes.", "intensity": 8.9, "sentiment": -0.88},
        {"text": "Our campus emits more carbon than a small city. The 2040 'net zero' goal is too slow.", "intensity": 8.2, "sentiment": -0.82},
        {"text": "The recycling bins are consistently mislabeled. We're probably landfilling half our recyclables.", "intensity": 7.5, "sentiment": -0.73},
        {"text": "Single-use plastics are everywhere on campus — dining, events, labs. We banned plastic bags but nothing else.", "intensity": 7.8, "sentiment": -0.78},
        {"text": "The new sustainability fee we pay isn't being used transparently. I've asked and can't get an answer.", "intensity": 8.0, "sentiment": -0.8},
        {"text": "The university installed solar panels on 6 buildings this year. That's meaningful progress.", "intensity": 5.5, "sentiment": 0.5},
        {"text": "Campus emissions are down 18% since 2015. The trajectory is real, even if it's not fast enough for some.", "intensity": 5.0, "sentiment": 0.35},
        {"text": "Institutional change takes time. The sustainability office is genuinely working on this.", "intensity": 4.8, "sentiment": 0.3},
        {"text": "We've had multiple student-led initiatives funded by the green revolving fund. The system works.", "intensity": 4.5, "sentiment": 0.45},
        {"text": "Students demanding immediate fossil fuel divestment don't fully understand endowment management constraints.", "intensity": 5.2, "sentiment": 0.0},
        {"text": "My environmental science class is taught in a building that isn't even LEED certified. That's embarrassing.", "intensity": 7.0, "sentiment": -0.7},
        {"text": "We have no composting program. Food waste just goes to landfill. This isn't hard to fix.", "intensity": 7.5, "sentiment": -0.74},
        {"text": "The campus fleet is 90% gas vehicles. Why is there no electrification roadmap?", "intensity": 7.2, "sentiment": -0.71},
        {"text": "I'd pay more in fees for faster climate action. I think many students would.", "intensity": 7.8, "sentiment": -0.2},
        {"text": "Climate action on campus is also about justice — sustainability costs fall hardest on the most vulnerable.", "intensity": 8.3, "sentiment": -0.75},
        {"text": "I appreciate that climate is being taken seriously at all. Five years ago this wasn't even on the agenda.", "intensity": 4.5, "sentiment": 0.45},
        {"text": "Individual campus actions matter less than systemic policy. I focus my energy on advocacy, not composting.", "intensity": 5.0, "sentiment": 0.05},
        {"text": "The greenhouse gas inventory is publicly available. People criticizing without reading it aren't being fair.", "intensity": 4.8, "sentiment": 0.2},
        {"text": "We have a student sustainability council with real power. That's more than most universities.", "intensity": 5.2, "sentiment": 0.4},
        {"text": "Transition takes time and money. The university is balancing this with dozens of other priorities.", "intensity": 4.6, "sentiment": 0.1},
    ],
    "Diversity in Curriculum": [
        {"text": "I took 3 history courses and never read a primary source written by a woman or person of color. That's a problem.", "intensity": 8.4, "sentiment": -0.84},
        {"text": "The 'diversity requirement' is one class. One. For a four-year degree.", "intensity": 7.9, "sentiment": -0.79},
        {"text": "My department has 18 faculty members. Two are not white men. That affects what gets taught.", "intensity": 8.1, "sentiment": -0.81},
        {"text": "I've gone entire semesters without seeing my community's history or perspective in a syllabus.", "intensity": 8.6, "sentiment": -0.86},
        {"text": "Diversity in curriculum isn't about making people uncomfortable — it's about accuracy and completeness.", "intensity": 7.7, "sentiment": -0.6},
        {"text": "Curriculum change is a slow, faculty-driven process. It can't be mandated overnight.", "intensity": 5.0, "sentiment": 0.0},
        {"text": "Many departments have updated syllabi significantly in the past 5 years. Progress is happening.", "intensity": 4.7, "sentiment": 0.35},
        {"text": "Adding diverse authors is valuable, but it should be about merit and relevance, not checkboxes.", "intensity": 5.2, "sentiment": 0.1},
        {"text": "The new ethnic studies requirement passed last year. That was a major structural change.", "intensity": 4.5, "sentiment": 0.4},
        {"text": "Faculty have academic freedom. Students can advocate, but the curriculum isn't a democracy.", "intensity": 4.8, "sentiment": 0.0},
        {"text": "Decolonizing the curriculum doesn't mean removing Western thought — it means adding what was left out.", "intensity": 7.5, "sentiment": -0.4},
        {"text": "I came here specifically for the ethnic studies program. It's excellent — but it's siloed from everything else.", "intensity": 7.0, "sentiment": -0.5},
        {"text": "Disability perspectives are almost entirely absent from the curriculum across every field I've studied.", "intensity": 8.0, "sentiment": -0.8},
        {"text": "International students bring global perspectives but they're rarely centered in classroom discussions.", "intensity": 7.4, "sentiment": -0.72},
        {"text": "When the canon is only one culture, students are trained to see that culture as default. That has consequences.", "intensity": 7.8, "sentiment": -0.7},
        {"text": "I've had professors who actively sought diverse readings. It's a faculty culture question more than a policy one.", "intensity": 5.0, "sentiment": 0.15},
        {"text": "The new first-year seminar on global perspectives is exactly the right direction.", "intensity": 4.8, "sentiment": 0.5},
        {"text": "My department just launched a speaker series featuring underrepresented scholars. That matters.", "intensity": 4.5, "sentiment": 0.45},
        {"text": "We added a required course on race and power two years ago. Students initially resisted; now it's well-reviewed.", "intensity": 5.2, "sentiment": 0.3},
        {"text": "The change I want to see is being built. Slowly. But it is being built.", "intensity": 4.3, "sentiment": 0.35},
    ],
    "Greek Life and Social Culture": [
        {"text": "Greek organizations have GPA requirements but not ethics requirements. That's backwards.", "intensity": 7.2, "sentiment": -0.72},
        {"text": "Hazing is still happening. People just don't report it because they're afraid of losing their community.", "intensity": 8.5, "sentiment": -0.85},
        {"text": "Greek life controls too much of campus social life. If you're not in, you're out.", "intensity": 7.8, "sentiment": -0.78},
        {"text": "The houses get university resources and recognition but operate with almost zero accountability.", "intensity": 8.0, "sentiment": -0.8},
        {"text": "I've heard firsthand accounts of assault at Greek events that never got reported. The culture protects perpetrators.", "intensity": 9.1, "sentiment": -0.91},
        {"text": "Greek life gave me my closest friendships and professional network. It's not what the critics say.", "intensity": 6.5, "sentiment": 0.7},
        {"text": "My chapter does 200+ hours of community service a year. That story never gets told.", "intensity": 5.8, "sentiment": 0.5},
        {"text": "Not all Greek organizations are the same. Painting them all with one brush is unfair.", "intensity": 6.0, "sentiment": 0.4},
        {"text": "The social culture problems on campus exist outside Greek life too. It's not the only venue for bad behavior.", "intensity": 5.5, "sentiment": 0.1},
        {"text": "Greek houses are getting more progressive, more inclusive. Change is happening from the inside.", "intensity": 5.2, "sentiment": 0.45},
        {"text": "I transferred here specifically because the Greek scene wasn't dominant. I still feel excluded.", "intensity": 7.5, "sentiment": -0.75},
        {"text": "The alumni networks from Greek life create unequal career advantages. That's a structural issue.", "intensity": 7.0, "sentiment": -0.65},
        {"text": "Social events should be accessible to everyone, not just people who can afford membership fees.", "intensity": 7.8, "sentiment": -0.78},
        {"text": "The university's response to misconduct allegations in Greek life is consistently inadequate.", "intensity": 8.3, "sentiment": -0.83},
        {"text": "I feel invisible at this school outside of Greek life. I don't think that's intentional but it's real.", "intensity": 7.6, "sentiment": -0.76},
        {"text": "My Greek community was the first place I felt fully accepted at this school.", "intensity": 5.5, "sentiment": 0.8},
        {"text": "We have open parties that anyone can attend. The 'exclusivity' narrative is overstated.", "intensity": 4.8, "sentiment": 0.3},
        {"text": "The inter-Greek council has adopted a new accountability framework. Give it time to work.", "intensity": 4.5, "sentiment": 0.35},
        {"text": "Strong alumni oversight actually helps with accountability. We self-police more than people think.", "intensity": 5.0, "sentiment": 0.4},
        {"text": "Some of the best mental health and DEI programming on campus is run by Greek chapters.", "intensity": 5.3, "sentiment": 0.45},
    ],
    "Student Government Transparency": [
        {"text": "SGA spent $40,000 on a retreat but can't fund the food pantry expansion students voted for.", "intensity": 8.7, "sentiment": -0.87},
        {"text": "Meeting minutes are technically public but practically inaccessible. You have to know to ask.", "intensity": 7.5, "sentiment": -0.75},
        {"text": "The same 15 people run every committee. This isn't representative government.", "intensity": 7.8, "sentiment": -0.78},
        {"text": "I ran for student senate and was told my platform was 'too ambitious' before the vote. Who decides that?", "intensity": 8.2, "sentiment": -0.82},
        {"text": "The annual budget is never presented to students in a readable format. Just PDF dumps no one can parse.", "intensity": 7.4, "sentiment": -0.74},
        {"text": "SGA passed three major resolutions this semester. Two of them came from student petitions.", "intensity": 5.0, "sentiment": 0.45},
        {"text": "The president holds weekly office hours. Anyone can come. Most don't, then complain about lack of access.", "intensity": 4.8, "sentiment": 0.2},
        {"text": "Governing is harder than it looks. SGA navigates real bureaucratic constraints.", "intensity": 4.5, "sentiment": 0.1},
        {"text": "Budget decisions are made with input from elected representatives. That's how representative democracy works.", "intensity": 4.2, "sentiment": 0.15},
        {"text": "I've been on the SGA finance committee. We try. The transparency issues are real but so is our effort.", "intensity": 5.5, "sentiment": 0.1},
        {"text": "They endorsed a position on a state policy issue without any student vote or survey. That's overreach.", "intensity": 8.1, "sentiment": -0.81},
        {"text": "The recall process for underperforming senators is so complicated it's never been used. By design, I suspect.", "intensity": 7.9, "sentiment": -0.79},
        {"text": "Student fees fund SGA but students have no mechanism for direct budget approval. That's taxation without representation.", "intensity": 8.4, "sentiment": -0.84},
        {"text": "Every resolution SGA passes gets ignored by the administration anyway. Why are we pretending it matters?", "intensity": 8.0, "sentiment": -0.8},
        {"text": "I've submitted three feedback forms to SGA. Zero responses. Not even an auto-reply.", "intensity": 7.5, "sentiment": -0.75},
        {"text": "My senator is genuinely responsive and has followed through on commitments. Not all SGA is the same.", "intensity": 5.0, "sentiment": 0.6},
        {"text": "The new SGA website actually has searchable meeting minutes now. That's progress.", "intensity": 4.2, "sentiment": 0.5},
        {"text": "SGA advocacy led to extended library hours last year. Real impact, even if slow.", "intensity": 4.8, "sentiment": 0.5},
        {"text": "The structure is imperfect but it's the only formal channel we have. Better to engage than disengage.", "intensity": 5.2, "sentiment": 0.2},
        {"text": "Compared to what I've heard from friends at other schools, our SGA is actually pretty functional.", "intensity": 4.5, "sentiment": 0.4},
    ],
}


# ---------------------------------------------------------------------------
# Seed runner
# ---------------------------------------------------------------------------

async def seed():
    await init_db()

    async with AsyncSessionLocal() as db:
        # --- Users ---
        print("Seeding users...")
        user_objects: list[User] = []
        for name in ANON_NAMES:
            existing = (await db.execute(select(User).where(User.anon_name == name))).scalar_one_or_none()
            if existing:
                user_objects.append(existing)
                continue
            lean = round(random.uniform(-1.0, 1.0), 3)
            user = User(anon_name=name, lean_score=lean)
            db.add(user)
            user_objects.append(user)
        await db.commit()
        # Re-fetch to get IDs
        result = await db.execute(select(User))
        user_objects = result.scalars().all()
        print(f"  {len(user_objects)} users ready.")

        # --- Issues ---
        print("Seeding issues...")
        issue_map: dict[str, Issue] = {}
        for label in SEED_ISSUES:
            existing = (await db.execute(select(Issue).where(Issue.label == label))).scalar_one_or_none()
            if existing:
                issue_map[label] = existing
                continue
            issue = Issue(
                label=label,
                week_start=date.today(),
                post_count=0,
                sentiment_avg=0.0,
                intensity_avg=0.0,
                rank_score=0.0,
            )
            db.add(issue)
            issue_map[label] = issue
        await db.commit()
        # Re-fetch
        result = await db.execute(select(Issue))
        for i in result.scalars().all():
            issue_map[i.label] = i
        print(f"  {len(issue_map)} issues ready.")

        # --- Posts ---
        print("Seeding posts (embeddings via OpenAI — this may take a moment)...")
        total_posts = 0
        for label, posts_data in SEED_POSTS.items():
            issue = issue_map.get(label)
            if issue is None:
                continue

            existing_count = (await db.execute(
                select(Post).where(Post.issue_id == issue.id)
            )).scalars().all()
            if len(existing_count) >= len(posts_data):
                print(f"  Skipping '{label}' — already seeded.")
                continue

            sentiments, intensities = [], []
            for pd in posts_data:
                user = random.choice(user_objects)
                # Use provided scores (faster, avoids extra API calls during seed)
                sentiment = pd["sentiment"]
                intensity = pd["intensity"]

                try:
                    embedding = await ml.embed_text(pd["text"])
                except Exception as e:
                    print(f"    Embedding failed for post, using zeros: {e}")
                    embedding = [0.0] * 1536

                post = Post(
                    user_id=user.id,
                    issue_id=issue.id,
                    text=pd["text"],
                    embedding=embedding,
                    sentiment=sentiment,
                    intensity=intensity,
                    created_at=datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 168)),
                )
                db.add(post)
                sentiments.append(sentiment)
                intensities.append(intensity)
                total_posts += 1

            n = len(posts_data)
            issue.post_count = n
            issue.sentiment_avg = round(sum(sentiments) / n, 4)
            issue.intensity_avg = round(sum(intensities) / n, 4)
            issue.rank_score = ml.compute_rank_score(
                n, issue.intensity_avg,
                ml.recency_weight(datetime.now(timezone.utc))
            )
            await db.commit()
            print(f"  Seeded '{label}': {n} posts.")

        # --- Summaries ---
        print("Generating LLM summaries for all seeded issues...")
        for label, issue in issue_map.items():
            await db.refresh(issue)
            if issue.summary:
                print(f"  '{label}' already has summary, skipping.")
                continue
            posts_q = await db.execute(select(Post.text).where(Post.issue_id == issue.id))
            texts = [r[0] for r in posts_q.fetchall()]
            if not texts:
                continue
            try:
                summary_data = await ml.summarize_issue(label, texts)
                issue.summary = summary_data["summary"]
                issue.side_a_points = summary_data["side_a_points"]
                issue.side_b_points = summary_data["side_b_points"]
                issue.shared_concerns = summary_data["shared_concerns"]
                await db.commit()
                print(f"  Summary generated for '{label}'.")
            except Exception as e:
                print(f"  Summary failed for '{label}': {e}")

        print(f"\nSeed complete. {len(user_objects)} users, {len(issue_map)} issues, {total_posts} new posts.")


if __name__ == "__main__":
    asyncio.run(seed())
