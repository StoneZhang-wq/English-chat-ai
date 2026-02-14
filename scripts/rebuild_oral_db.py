# -*- coding: utf-8 -*-
"""
按 .cursor/rules/oral-training-db.mdc 规则（含 v1.2 难度与自然度）重新生成 oral_training_db.json。
- Simple: 4 轮（8 条），允许 1～2 句弱信息句（Sure. / Sounds good.）
- Intermediate: 8 轮（16 条），允许 2～3 句功能性废话（I see. / That makes sense.）
- Difficult: 12 轮（24 条），允许 1～2 次自然插话（To be honest, / You know,）
"""
import json
import re
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "oral_training_db.json"

# 每轮 = (A句, B句, hint_A, hint_B)，句中可用 {0} {1} … 占位
# 词汇表 = { "A": (v0, v1, ...), "B": ..., "C": ..., "Review": ..., "core_sentences": str, "core_chunks": str }

def r(*t): return t  # 一轮

# ---------- Daily Life Simple ----------
ROUNDS = {}
VOCAB = {}

# DL Simple U1: Daily Routine
ROUNDS[("Daily Life", "Simple", "U1-Daily Routine")] = [
    r("What do you do {0}?", "I {1} {2}.", "ask about routine / {0}", "I + verb + place"),
    r("Do you do that every day?", "Sure.", "ask frequency", "weak response"),
    r("What about {3}?", "I usually {4} {5}.", "ask other time / {3}", "I usually + verb"),
    r("That sounds good.", "Sounds good.", "closing", "weak response"),
]
VOCAB[("Daily Life", "Simple", "U1-Daily Routine")] = {
    "A": ("after work", "go to", "the gym", "in the evening", "watch", "TV"),
    "B": ("after school", "play", "basketball", "at night", "read", "books"),
    "C": ("in the evening", "watch", "TV", "on weekends", "run", "in the park"),
    "Review": ("at night", "read", "books", "in the morning", "drink", "coffee"),
    "core_sentences": "What do you do…? / I + verb + place / I usually + verb",
    "core_chunks": "after work / go to the gym / every day / that sounds good",
}

# DL Simple U2: Expressing Plans
ROUNDS[("Daily Life", "Simple", "U2-Expressing Plans")] = [
    r("What is your plan for {0}?", "I will {1}.", "ask plan / {0}", "I will + verb"),
    r("Who will you go with?", "I will go with {2}.", "ask who", "I will go with…"),
    r("What time?", "At {3}.", "ask time", "At + time"),
    r("Have fun.", "Sounds good.", "wish", "weak response"),
]
VOCAB[("Daily Life", "Simple", "U2-Expressing Plans")] = {
    "A": ("tomorrow", "go to the park", "my sister", "nine"),
    "B": ("Saturday", "visit my friend", "my brother", "two"),
    "C": ("next week", "see a film", "my classmate", "seven"),
    "Review": ("this Sunday", "stay home", "my family", "ten"),
    "core_sentences": "What is your plan for…? / I will + verb / I will go with…",
    "core_chunks": "plan for tomorrow / go to the park / what time",
}

# DL Simple U3: Expressing Habits
ROUNDS[("Daily Life", "Simple", "U3-Expressing Habits")] = [
    r("Do you {0} {1}?", "Sure.", "Do you + verb / {1}", "weak response"),
    r("How often?", "Every {2}.", "ask frequency", "Every + time"),
    r("What about {3}?", "Sometimes I {4} {5}.", "ask other / {3}", "Sometimes I + verb"),
    r("Good habit.", "Sounds good.", "closing", "weak response"),
]
VOCAB[("Daily Life", "Simple", "U3-Expressing Habits")] = {
    "A": ("drink coffee", "in the morning", "day", "exercise", "run", "in the park"),
    "B": ("exercise", "on weekends", "Saturday", "read", "read", "books"),
    "C": ("watch TV", "in the evening", "day", "cook", "cook", "dinner"),
    "Review": ("get up early", "at seven", "day", "walk", "walk", "to work"),
    "core_sentences": "Do you + verb…? / Yes, I do / I usually + verb",
    "core_chunks": "every day / in the morning / what about / that sounds good",
}

# DL Simple U4: Expressing Feelings
ROUNDS[("Daily Life", "Simple", "U4-Expressing Feelings")] = [
    r("How do you feel {0}?", "I feel {1}.", "ask feeling / {0}", "I feel + adjective"),
    r("Why?", "Because I {2}.", "ask reason", "Because I…"),
    r("What do you do when you feel {1}?", "I {3}.", "ask coping", "I + verb"),
    r("Take care.", "Sounds good. You too.", "closing", "weak response / you too"),
]
VOCAB[("Daily Life", "Simple", "U4-Expressing Feelings")] = {
    "A": ("today", "happy", "got good news", "smile"),
    "B": ("now", "tired", "worked late", "rest"),
    "C": ("after class", "relaxed", "finished my work", "listen to music"),
    "Review": ("today", "good", "slept well", "exercise"),
    "core_sentences": "How do you feel…? / I feel + adjective / Because I…",
    "core_chunks": "feel happy / how do you feel / take care",
}

# ---------- Daily Life Intermediate ----------
ROUNDS[("Daily Life", "Intermediate", "U1-Weekend Plans")] = [
    r("What will you do {0}?", "I think I will {1} because I {2}.", "future plan / {0}", "I think I will… / because I…"),
    r("Who will you go with? What time?", "I will go with {3}. At {4}.", "ask who / time", "I will + go with / at…"),
    r("I see.", "Yeah, maybe.", "filler", "filler"),
    r("Do you need to prepare?", "Yes, I need to {5}.", "ask prepare", "Yes, I need to…"),
    r("What if it rains?", "If it rains, I will {6}.", "if + condition", "If…, I will…"),
    r("That makes sense.", "I think so too.", "filler", "I think so too"),
    r("Have a good time.", "Thank you. You too.", "wish", "thank you"),
    r("See you next week.", "See you.", "closing", "see you"),
]
VOCAB[("Daily Life", "Intermediate", "U1-Weekend Plans")] = {
    "A": ("this weekend", "stay home", "need rest", "my family", "nine", "pack clothes", "stay in"),
    "B": ("on Saturday", "go hiking", "like nature", "my friend", "eight", "buy snacks", "go to a café"),
    "C": ("next Sunday", "visit the museum", "want to see the exhibition", "my brother", "ten", "book tickets", "go to the library"),
    "Review": ("this weekend", "stay home", "need rest", "my sister", "nine", "rest", "watch a film"),
    "core_sentences": "I think I will… / because I… / What will you…? / If…, I will…",
    "core_chunks": "this weekend / stay home / because / need rest / if it rains",
}

ROUNDS[("Daily Life", "Intermediate", "U2-Reasons for Choices")] = [
    r("Why did you choose {0}?", "Because I think that {1}.", "ask reason", "because I think that…"),
    r("When did you buy it?", "I have had it since {2}.", "ask when", "I have had… since…"),
    r("Do you like it?", "Yes, I think that it is {3}.", "ask opinion", "I think that…"),
    r("Would you recommend it?", "Yes, because it {4}.", "ask recommend", "because it…"),
    r("What about {5}?", "I think that one is {6} too.", "ask other", "I think that…"),
    r("Thanks for telling me.", "You are welcome.", "thanks", "you are welcome"),
    r("I might get one.", "Good idea.", "closing", "good idea"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Daily Life", "Intermediate", "U2-Reasons for Choices")] = {
    "A": ("this bag", "it is useful", "last month", "good", "saves time", "the blue one", "nice"),
    "B": ("this phone", "it works well", "last year", "reliable", "lasts long", "the other model", "fine"),
    "C": ("this book", "it is interesting", "last week", "helpful", "helps me relax", "the new one", "great"),
    "Review": ("this one", "it is useful", "last month", "good", "saves time", "that one", "good"),
    "core_sentences": "because I think that… / I have had… since… / I think that…",
    "core_chunks": "think of / useful / have had / recommend",
}

ROUNDS[("Daily Life", "Intermediate", "U3-Conditional Plans")] = [
    r("What will you do {0}?", "If the weather is good, I will {1}.", "ask plan", "If…, I will…"),
    r("What if it is bad?", "If it rains, I will {2} instead.", "if + condition", "If…, I will…"),
    r("Do you have a backup plan?", "Yes, I think that I will {3}.", "ask backup", "I think that I will…"),
    r("When will you decide?", "I will decide when I {4}.", "ask when", "when I…"),
    r("That makes sense.", "I think so too.", "agree", "I think so too"),
    r("Good luck.", "Thanks. You too.", "wish", "thanks"),
    r("See you then.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Daily Life", "Intermediate", "U3-Conditional Plans")] = {
    "A": ("tomorrow", "go to the park", "stay home", "see the forecast", "check the weather"),
    "B": ("on Sunday", "play tennis", "read at home", "wake up", "see the sky"),
    "C": ("next week", "visit the beach", "go to the gym", "get up", "see the news"),
    "Review": ("this weekend", "go out", "stay in", "wake up", "check"),
    "core_sentences": "If…, I will… / I think that I will… / when I…",
    "core_chunks": "if the weather is good / backup plan / decide",
}

ROUNDS[("Daily Life", "Intermediate", "U4-Opinion and Experience")] = [
    r("Have you tried {0}?", "Yes, I have tried it. I think that it is {1}.", "ask experience", "I have tried… / I think that…"),
    r("When did you try it?", "I tried it when I {2}.", "ask when", "when I…"),
    r("Why do you like it?", "Because I think that it {3}.", "ask reason", "because I think that…"),
    r("Would you try it again?", "Yes, if I have time I will {4}.", "ask again", "if I… I will…"),
    r("What else have you tried?", "I have also tried {5}. That was {6} too.", "ask more", "I have tried…"),
    r("Thanks for sharing.", "You are welcome.", "thanks", "you are welcome"),
    r("I might try it.", "Good idea.", "closing", "good idea"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Daily Life", "Intermediate", "U4-Opinion and Experience")] = {
    "A": ("this café", "is cozy", "was in town", "saves time", "go again", "the other one", "nice"),
    "B": ("this app", "is useful", "had a project", "helps a lot", "use it again", "that game", "fun"),
    "C": ("this restaurant", "is great", "celebrated my birthday", "tastes good", "visit again", "the new place", "good"),
    "Review": ("this place", "is good", "was free", "is convenient", "come again", "that one", "fine"),
    "core_sentences": "I have tried… / I think that… / because I think that…",
    "core_chunks": "think of / useful / have tried",
}

# ---------- Daily Life Difficult ----------
ROUNDS[("Daily Life", "Difficult", "U1-Work Stress Reflection")] = [
    r("Why have you been {0} lately?", "To be honest, although I {1}, I feel {2} because {3}.", "present perfect continuous / ask reason", "To be honest, / although + clause / because + reason"),
    r("How long has this been going on?", "It has been {4} since it started.", "ask duration", "It has been… since…"),
    r("What do you do when you feel that way?", "If I had more time, I would {5}.", "ask coping", "if + past, I would…"),
    r("Do you think it will get better?", "I think that it will if {6}.", "I think that… / if", "I think that… if…"),
    r("What helped you before?", "When I {7}, I felt better.", "ask past experience", "When I…, I…"),
    r("Would you try that again?", "Although it was hard, I would try because {8}.", "although / would try because", "although / would because"),
    r("Is there anything else?", "Sometimes I {9}. That helps.", "ask more", "Sometimes I…"),
    r("How does your family feel?", "They think that I need to {10}.", "they think that…", "they think that…"),
    r("Do you agree with them?", "I think that they are right because {11}.", "agree / because", "I think that… because…"),
    r("What will you do next?", "If I have time, I will {12}.", "if + present, I will", "If…, I will…"),
    r("Good luck with that.", "Thank you. I will try.", "wish", "thank you"),
    r("Take care of yourself.", "You too. Bye.", "closing", "you too"),
]
VOCAB[("Daily Life", "Difficult", "U1-Work Stress Reflection")] = {
    "A": ("stressed", "enjoy my job", "overwhelmed", "the workload has increased", "weeks", "take a break", "I rest more", "took a holiday", "it helps", "go for a walk", "rest more", "they see it", "see a doctor"),
    "B": ("tired", "like my work", "exhausted", "the deadline is tight", "months", "sleep earlier", "I exercised", "had a day off", "it works", "read a book", "sleep more", "they notice", "take a break"),
    "C": ("busy", "value my team", "pressed", "there is too much to do", "a month", "say no sometimes", "I talked to my boss", "delegated tasks", "it helps", "listen to music", "prioritise", "they know me", "talk to someone"),
    "Review": ("stressed", "enjoy my job", "overwhelmed", "work has increased", "weeks", "rest", "I rested", "took leave", "it helped", "walk", "rest", "they see it", "try"),
    "core_sentences": "Although I…, I feel… because… / It has been… since… / if + past, I would… / I think that…",
    "core_chunks": "feeling stressed / workload / overwhelmed / although",
}

ROUNDS[("Daily Life", "Difficult", "U2-Hypothetical Advice")] = [
    r("What would you do if {0}?", "You know, although it is hard, I would {1} if I had the chance because {2}.", "ask hypothetical", "You know, / although / I would… if… because…"),
    r("Have you ever been in that situation?", "Yes. When I {3}, I felt {4}.", "ask experience", "When I…, I…"),
    r("What did you do then?", "I think that I {5}. It was {6}.", "ask past", "I think that I…"),
    r("Would you do the same again?", "If I could go back, I would {7} because {8}.", "if + past, would", "If I could…, I would… because…"),
    r("What would you tell someone else?", "Although everyone is different, I would say that {9}.", "although / would say that", "I would say that…"),
    r("Do you think that helps?", "I think that it does if {10}.", "I think that… if", "I think that… if…"),
    r("Thanks for the advice.", "You are welcome.", "thanks", "you are welcome"),
    r("I will think about it.", "Good. Take care.", "closing", "take care"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Good luck.", "Thanks. You too.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
]
VOCAB[("Daily Life", "Difficult", "U2-Hypothetical Advice")] = {
    "A": ("you lost your job", "retrain", "I need new skills", "was young", "scared", "looked for help", "the right choice", "ask for support", "it was important", "they should stay calm", "they try", "you are welcome", "bye"),
    "B": ("you had to move", "find a new place", "I like change", "moved last year", "nervous", "made a list", "helpful", "take more time", "I was rushed", "they should plan ahead", "they plan", "no problem", "bye"),
    "C": ("you had to start again", "take small steps", "I believe in progress", "changed career", "uncertain", "talked to friends", "worth it", "learn more first", "knowledge helps", "they should not give up", "they persist", "any time", "bye"),
    "Review": ("that happened", "try again", "it matters", "tried", "worried", "asked for help", "good", "try harder", "it helped", "they try", "they do", "welcome", "bye"),
    "core_sentences": "Although…, I would… if… because… / If I could…, I would… / I think that…",
    "core_chunks": "although / would / if I had / because",
}

ROUNDS[("Daily Life", "Difficult", "U3-Reflection on Change")] = [
    r("How has {0} changed for you?", "The thing is, although I used to {1}, I now think that {2} because {3}.", "ask change", "The thing is, / although I used to… / I now think that… because…"),
    r("When did you notice the change?", "It has been {4} since I {5}.", "ask when", "It has been… since I…"),
    r("Do you prefer the way things are now?", "I think that it is {6} now. If I could, I would {7}.", "I think that… / if I could, would", "I think that… / I would…"),
    r("What would you tell your past self?", "Although it was hard, I would say that {8}.", "although / would say that", "I would say that…"),
    r("Has your family noticed?", "They think that I have {9}.", "they think that…", "they think that…"),
    r("Do you agree?", "I think that they are right because {10}.", "agree / because", "I think that… because…"),
    r("What will you do next?", "If I have time, I will {11}.", "if + present, I will", "If…, I will…"),
    r("That sounds good.", "Thank you. You too.", "closing", "thank you"),
    r("Good luck.", "Thanks. Bye.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Daily Life", "Difficult", "U3-Reflection on Change")] = {
    "A": ("work", "work late", "balance is important", "I was tired", "months", "changed", "better", "keep trying", "it gets easier", "changed", "they see it", "reflect more", "bye"),
    "B": ("life", "stay in every night", "going out helps", "I felt lonely", "a year", "joined a club", "happier", "do it sooner", "you learn", "noticed", "they are right", "try new things", "bye"),
    "C": ("your routine", "skip exercise", "health comes first", "I was stressed", "weeks", "started running", "healthier", "not worry so much", "things work out", "changed", "they are right", "keep it up", "bye"),
    "Review": ("things", "rush", "slow is good", "I was busy", "months", "stopped", "better", "relax", "it helps", "noticed", "right", "continue", "bye"),
    "core_sentences": "Although I used to…, I now think that… because… / It has been… since I… / I think that…",
    "core_chunks": "although / used to / I now think that / reflection",
}

# ---------- Eating Out Simple ----------
ROUNDS[("Eating Out", "Simple", "U1-Ordering Food")] = [
    r("What do you want to {0}?", "I want {1}.", "ask want / {0}", "I want + food"),
    r("Anything to drink?", "I want {2}.", "ask drink", "I want + drink"),
    r("Is that all?", "Sure.", "confirm", "weak response"),
    r("I will bring it soon.", "Sounds good. Thanks.", "closing", "weak response"),
]
VOCAB[("Eating Out", "Simple", "U1-Ordering Food")] = {
    "A": ("eat", "noodles", "tea"),
    "B": ("drink", "orange juice", "water"),
    "C": ("have for lunch", "a salad", "coffee"),
    "Review": ("order", "rice and chicken", "juice"),
    "core_sentences": "What do you want to…? / I want + food",
    "core_chunks": "want to eat / noodles / anything to drink",
}

ROUNDS[("Eating Out", "Simple", "U2-Asking for Things")] = [
    r("Can I have the {0}?", "Here you are.", "Can I have / request", "Here you are"),
    r("Can I have some {1}?", "Sure. Wait a moment.", "Can I have / request", "weak response"),
    r("Thank you.", "You are welcome.", "thanks", "you are welcome"),
    r("The bill, please.", "Here it is.", "ask bill", "Here it is"),
]
VOCAB[("Eating Out", "Simple", "U2-Asking for Things")] = {
    "A": ("menu", "water"),
    "B": ("bill", "napkins"),
    "C": ("menu", "salt"),
    "Review": ("menu", "tea"),
    "core_sentences": "Can I have…? / Here you are",
    "core_chunks": "the menu / here you are / the bill",
}

# ---------- Eating Out Intermediate ----------
ROUNDS[("Eating Out", "Intermediate", "U1-Reasons for Choice")] = [
    r("Why did you choose {0}?", "I chose it because I think that {1}.", "ask reason", "because I think that…"),
    r("Have you tried it before?", "Yes, I have tried it when I {2}.", "ask experience", "I have tried… when…"),
    r("What do you think of it?", "I think that it is {3}.", "ask opinion", "I think that…"),
    r("Would you order it again?", "Yes, because it {4}.", "ask again", "because it…"),
    r("What about {5}?", "I think that one is {6} too.", "ask other", "I think that…"),
    r("Thanks for the tip.", "You are welcome.", "thanks", "you are welcome"),
    r("I will try it.", "Good idea.", "closing", "good idea"),
    r("Enjoy your meal.", "You too.", "closing", "you too"),
]
VOCAB[("Eating Out", "Intermediate", "U1-Reasons for Choice")] = {
    "A": ("the fish", "it is fresh", "was here last week", "very good", "tastes great", "the chicken", "nice"),
    "B": ("this dish", "it is healthy", "came with my friend", "delicious", "is light", "the soup", "good"),
    "C": ("the pasta", "it is tasty", "had dinner here", "excellent", "fills me up", "the salad", "fine"),
    "Review": ("this", "it is good", "was here", "good", "is nice", "that", "good"),
    "core_sentences": "because I think that… / I have tried… when… / I think that…",
    "core_chunks": "chose / think that / have tried / because",
}

# ---------- Eating Out Difficult ----------
ROUNDS[("Eating Out", "Difficult", "U1-Preference and Condition")] = [
    r("Would you prefer {0} or {1}?", "To be honest, although I like both, I would choose {0} if I had to because {2}.", "ask preference", "To be honest, / although / I would… if… because…"),
    r("Have you had both before?", "Yes. When I {3}, I thought that {4}.", "ask experience", "When I…, I thought that…"),
    r("What if they are out of {0}?", "If that happened, I would {5} because {6}.", "if + past, would", "If…, I would… because…"),
    r("Do you come here often?", "I have been coming here since {7}.", "ask frequency", "I have been… since…"),
    r("Why do you like this place?", "I think that the {8} is {9}.", "I think that…", "I think that…"),
    r("Would you recommend it?", "Although it is busy, I would recommend it because {10}.", "although / would recommend because", "although / would because…"),
    r("Thanks for the advice.", "You are welcome.", "thanks", "you are welcome"),
    r("I will try it next time.", "Good. Enjoy.", "closing", "enjoy"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("Take care.", "You too.", "closing", "you too"),
    r("Goodbye.", "Goodbye.", "closing", "goodbye"),
]
VOCAB[("Eating Out", "Difficult", "U1-Preference and Condition")] = {
    "A": ("fish", "chicken", "it is lighter", "tried the fish", "it was good", "take the chicken", "I prefer it", "last year", "service", "excellent", "the food is worth it", "bye"),
    "B": ("pasta", "salad", "it is more filling", "had the pasta", "it was tasty", "order the salad", "it is fresh", "last month", "atmosphere", "nice", "the staff are friendly", "bye"),
    "C": ("steak", "soup", "it is more satisfying", "ate the steak", "it was great", "have the soup", "it is warm", "last summer", "menu", "varied", "the price is fair", "bye"),
    "Review": ("this", "that", "it is good", "tried it", "good", "that", "fine", "last year", "place", "good", "it is good", "bye"),
    "core_sentences": "Although…, I would… if… because… / When I…, I thought that… / I have been… since…",
    "core_chunks": "although / would choose / if I had to / because",
}

# ---------- Shopping Simple ----------
ROUNDS[("Shopping", "Simple", "U1-Asking Price")] = [
    r("How much is this {0}?", "It is {1}.", "How much / ask price", "It is + price"),
    r("How much are these {2}?", "They are {3}.", "How much / ask price", "They are + price"),
    r("I will take the {0}.", "Sure. Here you are.", "decide", "weak response / Here you are"),
    r("Thank you.", "Sounds good.", "thanks", "weak response"),
]
VOCAB[("Shopping", "Simple", "U1-Asking Price")] = {
    "A": ("shirt", "twenty dollars", "socks", "ten dollars"),
    "B": ("bag", "fifty yuan", "shoes", "ninety yuan"),
    "C": ("book", "fifteen pounds", "pens", "five pounds"),
    "Review": ("item", "thirty pounds", "ones", "twenty pounds"),
    "core_sentences": "How much is…? / It is + price / They are + price",
    "core_chunks": "this shirt / twenty dollars / how much",
}

ROUNDS[("Shopping", "Simple", "U2-Buying or Not")] = [
    r("Do you like this {0}?", "Sure. I will take it.", "Do you like / choice", "weak response / I will take it"),
    r("Do you like that {1}?", "No, I do not want it.", "Do you like / choice", "I do not want it"),
    r("Which one do you want?", "I want this {0}.", "ask which", "I want this…"),
    r("Here you are.", "Sounds good. Thanks.", "closing", "weak response"),
]
VOCAB[("Shopping", "Simple", "U2-Buying or Not")] = {
    "A": ("one", "one"),
    "B": ("bag", "shirt"),
    "C": ("book", "pen"),
    "Review": ("item", "one"),
    "core_sentences": "Do you like…? / I will take it / I do not want it",
    "core_chunks": "do you like / take it / which one",
}

# ---------- Shopping Intermediate ----------
ROUNDS[("Shopping", "Intermediate", "U1-Reason for Purchase")] = [
    r("Why did you buy {0}?", "I bought it because I think that {1}.", "ask reason", "because I think that…"),
    r("When did you buy it?", "I have had it since {2}.", "ask when", "I have had… since…"),
    r("Do you use it often?", "Yes, I think that it is {3}.", "ask use", "I think that…"),
    r("Would you buy it again?", "Yes, because it {4}.", "ask again", "because it…"),
    r("What about {5}?", "I think that one is {6} too.", "ask other", "I think that…"),
    r("Thanks.", "You are welcome.", "thanks", "you are welcome"),
    r("I might get one.", "Good idea.", "closing", "good idea"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Shopping", "Intermediate", "U1-Reason for Purchase")] = {
    "A": ("this bag", "it is useful", "last month", "very handy", "saves time", "the blue one", "nice"),
    "B": ("this phone", "it works well", "last year", "reliable", "lasts long", "the other model", "good"),
    "C": ("this book", "it is interesting", "last week", "helpful", "helps me relax", "the new one", "great"),
    "Review": ("this", "it is good", "last month", "good", "helps", "that", "fine"),
    "core_sentences": "because I think that… / I have had… since… / I think that…",
    "core_chunks": "bought / think that / have had / because",
}

# ---------- Shopping Difficult ----------
ROUNDS[("Shopping", "Difficult", "U1-Regret or Satisfaction")] = [
    r("Do you regret buying {0}?", "To be honest, although I spent a lot, I would buy it again if I had the choice because {1}.", "ask regret", "To be honest, / although + clause / if + past, I would… / because…"),
    r("How long have you had it?", "It has been {2} since I bought it.", "ask duration", "It has been… since…"),
    r("What do you like most?", "I think that the {3} is {4}.", "ask preference", "I think that…"),
    r("Would you recommend it?", "Although it is expensive, I would recommend it because {5}.", "although / would recommend because", "although / would because…"),
    r("What if you could change one thing?", "If I could, I would {6} because {7}.", "if I could, would", "If I could…, I would… because…"),
    r("Has it met your expectations?", "I think that it has because {8}.", "I think that… because", "I think that… because…"),
    r("Thanks for your opinion.", "You are welcome.", "thanks", "you are welcome"),
    r("I will think about it.", "Good. Take your time.", "closing", "take your time"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("Good luck with your purchase.", "Thanks. You too.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
]
VOCAB[("Shopping", "Difficult", "U1-Regret or Satisfaction")] = {
    "A": ("it", "the quality is worth it", "months", "quality", "excellent", "the service is good", "choose a different colour", "I like variety", "it works well", "bye"),
    "B": ("this", "the staff were helpful", "a year", "design", "nice", "it lasts long", "buy it sooner", "I waited too long", "it was a good deal", "bye"),
    "C": ("that", "the price was fair", "weeks", "material", "good", "it is durable", "try more sizes", "fit matters", "it does the job", "bye"),
    "Review": ("it", "it is worth it", "months", "quality", "good", "it is good", "change it", "it helps", "it has", "bye"),
    "core_sentences": "Although I…, I would… if… because… / I think that… / It has been… since…",
    "core_chunks": "regret buying / although / would buy again / worth it",
}

# ---------- 新增场景：全新对话内容（不得复用已有场景）---------
# Travel
ROUNDS[("Travel", "Simple", "U1-Booking and Plans")] = [
    r("When will you go to {0}?", "I will go {1}.", "ask when / {0}", "I will go + time"),
    r("Who will you go with?", "I will go with {2}.", "ask who", "I will go with…"),
    r("How long will you stay?", "For {3}.", "ask duration", "For + time"),
    r("Have a good trip.", "Thanks. Sounds good.", "wish", "weak response"),
]
VOCAB[("Travel", "Simple", "U1-Booking and Plans")] = {
    "A": ("London", "next month", "my friend", "a week"),
    "B": ("Paris", "in June", "my family", "five days"),
    "C": ("Tokyo", "this summer", "my sister", "ten days"),
    "Review": ("Beijing", "next year", "my brother", "two weeks"),
    "core_sentences": "When will you go…? / I will go with… / For + time",
    "core_chunks": "have a good trip / how long / will you go",
}
ROUNDS[("Travel", "Simple", "U2-Asking Directions")] = [
    r("Where is the {0}?", "Go {1}.", "ask place / {0}", "Go + direction"),
    r("How far is it?", "About {2} minutes.", "ask distance", "About + time"),
    r("Can I take a bus?", "Sure.", "ask transport", "weak response"),
    r("Thank you.", "Sounds good. Bye.", "thanks", "weak response"),
]
VOCAB[("Travel", "Simple", "U2-Asking Directions")] = {
    "A": ("station", "straight", "five"),
    "B": ("museum", "left", "ten"),
    "C": ("hotel", "right", "three"),
    "Review": ("park", "straight", "seven"),
    "core_sentences": "Where is…? / Go + direction / About + time",
    "core_chunks": "how far / take a bus / thank you",
}
ROUNDS[("Travel", "Simple", "U3-Sightseeing")] = [
    r("What did you see {0}?", "I saw {1}.", "ask what / {0}", "I saw + place"),
    r("Do you like it?", "Sure. It was {2}.", "ask opinion", "weak response / It was…"),
    r("Will you go again?", "Yes. Next {3}.", "ask again", "Yes. Next + time"),
    r("Have fun.", "Sounds good.", "wish", "weak response"),
]
VOCAB[("Travel", "Simple", "U3-Sightseeing")] = {
    "A": ("today", "the tower", "nice", "year"),
    "B": ("yesterday", "the temple", "great", "month"),
    "C": ("this morning", "the garden", "beautiful", "week"),
    "Review": ("there", "the lake", "good", "time"),
    "core_sentences": "What did you see…? / I saw… / It was…",
    "core_chunks": "do you like it / will you go again",
}
ROUNDS[("Travel", "Intermediate", "U1-Reasons for Travel")] = [
    r("Why did you choose {0}?", "I chose it because I think that {1}.", "ask reason", "because I think that…"),
    r("Have you been there before?", "Yes, I have been there when I {2}.", "ask experience", "I have been… when…"),
    r("What do you want to see?", "I think that I will see {3}.", "ask plan", "I think that I will…"),
    r("What if it rains?", "If it rains, I will {4}.", "if + condition", "If…, I will…"),
    r("That makes sense.", "I think so too.", "filler", "I think so too"),
    r("When do you leave?", "I leave on {5}.", "ask when", "I leave on…"),
    r("Have a safe trip.", "Thank you. You too.", "wish", "thank you"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Travel", "Intermediate", "U1-Reasons for Travel")] = {
    "A": ("Japan", "it is safe", "was young", "the temples", "stay indoors", "Monday"),
    "B": ("Italy", "the food is good", "had a break", "the museums", "go to a café", "Friday"),
    "C": ("Spain", "I like the culture", "studied there", "the beaches", "visit a gallery", "Sunday"),
    "Review": ("there", "it is nice", "went there", "the city", "rest", "Saturday"),
    "core_sentences": "because I think that… / I have been… when… / If…, I will…",
    "core_chunks": "why did you choose / have a safe trip",
}
ROUNDS[("Travel", "Intermediate", "U2-Recommendations")] = [
    r("What is good to see in {0}?", "I think that {1} is worth it because it is {2}.", "ask recommend", "I think that… because…"),
    r("How long do I need?", "I think that {3} days is enough.", "ask duration", "I think that…"),
    r("Where should I stay?", "If you like {4}, stay near {5}.", "if + suggestion", "If you…, stay…"),
    r("I see.", "Yeah, maybe.", "filler", "filler"),
    r("What about food?", "I have tried {6}. It was {7}.", "ask food", "I have tried…"),
    r("Thanks for the tips.", "You are welcome.", "thanks", "you are welcome"),
    r("I will book soon.", "Good idea.", "closing", "good idea"),
    r("See you.", "See you.", "closing", "see you"),
]
VOCAB[("Travel", "Intermediate", "U2-Recommendations")] = {
    "A": ("London", "the museum", "free", "three", "quiet", "the park", "the pie", "good"),
    "B": ("Paris", "the tower", "famous", "five", "centre", "the river", "the bread", "nice"),
    "C": ("Rome", "the square", "old", "four", "art", "the gallery", "the pasta", "great"),
    "Review": ("there", "the centre", "good", "three", "it", "there", "that", "fine"),
    "core_sentences": "I think that… because… / If you…, stay… / I have tried…",
    "core_chunks": "worth it / how long / thanks for the tips",
}
ROUNDS[("Travel", "Intermediate", "U3-Travel Experiences")] = [
    r("How was your trip to {0}?", "I think that it was {1} because I {2}.", "ask experience", "I think that… because…"),
    r("What did you do there?", "I have been to {3} and {4}.", "ask what", "I have been to…"),
    r("Did you like the food?", "Yes, because it was {5}.", "ask food", "because it was…"),
    r("Would you go again?", "If I have time, I will {6}.", "if + future", "If I…, I will…"),
    r("That makes sense.", "I think so too.", "filler", "I think so too"),
    r("Any tips for me?", "I think that you should {7}.", "ask tips", "I think that you should…"),
    r("Thanks a lot.", "You are welcome.", "thanks", "you are welcome"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Travel", "Intermediate", "U3-Travel Experiences")] = {
    "A": ("Paris", "great", "saw a lot", "the Louvre", "the tower", "fresh", "go again", "book early"),
    "B": ("Tokyo", "good", "ate a lot", "the temple", "the market", "tasty", "return next year", "get a pass"),
    "C": ("Berlin", "nice", "met friends", "the museum", "the park", "cheap", "visit again", "learn some words"),
    "Review": ("there", "fine", "enjoyed it", "the centre", "the town", "good", "go back", "plan ahead"),
    "core_sentences": "I think that… because… / I have been to… / If I…, I will…",
    "core_chunks": "how was your trip / would you go again",
}
ROUNDS[("Travel", "Difficult", "U1-Travel Preferences")] = [
    r("Do you prefer {0} or {1} when you travel?", "To be honest, although I like both, I would choose {0} if I had to because {2}.", "ask preference", "To be honest, / although / I would… if… because…"),
    r("Have you done both?", "Yes. When I {3}, I thought that {4}.", "ask experience", "When I…, I thought that…"),
    r("What if you had only one week?", "If that happened, I would {5} because {6}.", "if + past, would", "If…, I would… because…"),
    r("How long have you been travelling?", "I have been travelling since {7}.", "ask duration", "I have been… since…"),
    r("Why do you like it?", "I think that it {8}.", "I think that…", "I think that…"),
    r("Would you recommend it?", "Although it is tiring, I would recommend it because {9}.", "although / would because", "although / would because…"),
    r("Thanks for sharing.", "You are welcome.", "thanks", "you are welcome"),
    r("I will think about it.", "Good. Take care.", "closing", "take care"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("Good luck with your next trip.", "Thanks. You too.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
]
VOCAB[("Travel", "Difficult", "U1-Travel Preferences")] = {
    "A": ("cities", "beaches", "I like culture", "went to Rome", "it was great", "pick one city", "time is short", "last year", "opens my mind", "you learn a lot", "bye"),
    "B": ("trains", "planes", "trains are calm", "took a train", "it was nice", "take the train", "I get tired flying", "two years ago", "is relaxing", "you see more", "bye"),
    "C": ("solo", "group", "I like freedom", "travelled alone", "it was good", "go alone", "I need space", "last summer", "helps me think", "you meet people", "bye"),
    "Review": ("this", "that", "it is good", "tried", "good", "choose one", "it helps", "then", "is good", "it helps", "bye"),
    "core_sentences": "Although…, I would… if… because… / When I…, I thought that… / I have been… since…",
    "core_chunks": "to be honest / although / would recommend",
}
ROUNDS[("Travel", "Difficult", "U2-Culture and Places")] = [
    r("How has {0} changed the way you see things?", "The thing is, although I used to {1}, I now think that {2} because {3}.", "ask change", "The thing is, / although I used to… / I now think that… because…"),
    r("When did you notice that?", "It has been {4} since I {5}.", "ask when", "It has been… since I…"),
    r("Do you prefer the way you see it now?", "I think that it is {6}. If I could, I would {7}.", "I think that… / if I could", "I think that… / I would…"),
    r("What would you tell someone who has never been?", "Although it is hard to say, I would say that {8}.", "although / would say that", "I would say that…"),
    r("Has your family noticed a change?", "They think that I have {9}.", "they think that…", "they think that…"),
    r("Do you agree?", "I think that they are right because {10}.", "agree / because", "I think that… because…"),
    r("What will you do next?", "If I have time, I will {11}.", "if + present, I will", "If…, I will…"),
    r("Thanks for the talk.", "You are welcome.", "thanks", "you are welcome"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("Take care.", "You too.", "closing", "you too"),
    r("Goodbye.", "Goodbye.", "closing", "goodbye"),
]
VOCAB[("Travel", "Difficult", "U2-Culture and Places")] = {
    "A": ("travelling", "stay home", "the world is big", "I want to see more", "years", "went to Asia", "better", "travel more", "go and see", "changed", "they see it", "book again", "bye"),
    "B": ("living abroad", "think only of my country", "people are the same", "we share similar hopes", "a year", "moved to Berlin", "clearer", "try again", "visit first", "grown", "they are right", "plan a trip", "bye"),
    "C": ("visiting temples", "skip culture", "history matters", "it connects us", "months", "visited Kyoto", "richer", "go back", "read and go", "learned", "they notice", "explore more", "bye"),
    "Review": ("it", "ignore it", "it helps", "I learned", "time", "tried", "good", "continue", "try", "changed", "right", "do more", "bye"),
    "core_sentences": "Although I used to…, I now think that… because… / It has been… since I… / I think that…",
    "core_chunks": "the thing is / although / used to / reflection",
}
ROUNDS[("Travel", "Difficult", "U3-Reflection on Trips")] = [
    r("What would you do differently if you could {0} again?", "You know, although it was good, I would {1} if I could because {2}.", "ask hypothetical", "You know, / although / I would… if… because…"),
    r("Have you ever regretted a trip?", "Yes. When I {3}, I felt {4}.", "ask experience", "When I…, I…"),
    r("What did you do then?", "I think that I {5}. It was {6}.", "ask past", "I think that I…"),
    r("Would you do the same again?", "If I could go back, I would {7} because {8}.", "if + past, would", "If I could…, I would… because…"),
    r("What would you tell a friend?", "Although everyone is different, I would say that {9}.", "although / would say that", "I would say that…"),
    r("Do you think that helps?", "I think that it does if {10}.", "I think that… if", "I think that… if…"),
    r("Thanks for the advice.", "You are welcome.", "thanks", "you are welcome"),
    r("I will think about it.", "Good. Take care.", "closing", "take care"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Good luck.", "Thanks. You too.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
]
VOCAB[("Travel", "Difficult", "U3-Reflection on Trips")] = {
    "A": ("plan that", "book earlier", "prices were high", "rushed", "tired", "changed my plan", "okay", "take more days", "I needed rest", "plan ahead", "they listen", "bye"),
    "B": ("take that", "pack less", "I had too much", "travelled alone", "lonely", "called a friend", "fine", "go with someone", "company helps", "try both", "they try", "bye"),
    "C": ("do that", "learn the language", "it was hard to ask", "went in summer", "too hot", "stayed indoors", "good", "go in spring", "weather was better", "go when it is cool", "they plan", "bye"),
    "Review": ("do it", "plan better", "it helped", "went", "mixed", "adapted", "okay", "try again", "it helps", "plan", "they do", "bye"),
    "core_sentences": "Although…, I would… if… because… / If I could…, I would… / I think that…",
    "core_chunks": "you know / although / would do differently",
}

# Health
ROUNDS[("Health", "Simple", "U1-At the Doctor")] = [
    r("What is wrong?", "I have a {0}.", "ask problem", "I have a + symptom"),
    r("How long?", "For {1} days.", "ask duration", "For + time"),
    r("Do you take medicine?", "Yes. {2}.", "ask medicine", "Yes. + medicine"),
    r("Get well soon.", "Thanks. Sounds good.", "wish", "weak response"),
]
VOCAB[("Health", "Simple", "U1-At the Doctor")] = {
    "A": ("cold", "three", "Twice a day"),
    "B": ("headache", "two", "Once in the morning"),
    "C": ("cough", "five", "After meals"),
    "Review": ("fever", "one", "When I need it"),
    "core_sentences": "What is wrong? / I have a… / For + time",
    "core_chunks": "get well soon / take medicine",
}
ROUNDS[("Health", "Simple", "U2-Medicine and Advice")] = [
    r("Can I take {0}?", "Yes. Take it {1}.", "ask medicine / {0}", "Yes. Take it + when"),
    r("How many a day?", "{2}.", "ask frequency", "number"),
    r("Any other advice?", "Rest and drink {3}.", "ask advice", "Rest and drink…"),
    r("Thank you.", "Sounds good. Bye.", "thanks", "weak response"),
]
VOCAB[("Health", "Simple", "U2-Medicine and Advice")] = {
    "A": ("this pill", "after food", "Two", "water"),
    "B": ("this syrup", "before bed", "Three", "juice"),
    "C": ("this tablet", "in the morning", "One", "tea"),
    "Review": ("it", "with water", "Two", "water"),
    "core_sentences": "Can I take…? / Take it… / Rest and drink…",
    "core_chunks": "how many a day / any other advice",
}
ROUNDS[("Health", "Simple", "U3-Healthy Habits")] = [
    r("Do you {0} every day?", "Sure. I {1}.", "ask habit / {0}", "weak response / I + verb"),
    r("What do you eat?", "I eat {2}.", "ask food", "I eat…"),
    r("Do you sleep well?", "Yes. About {3} hours.", "ask sleep", "Yes. About + time"),
    r("That is good.", "Sounds good.", "closing", "weak response"),
]
VOCAB[("Health", "Simple", "U3-Healthy Habits")] = {
    "A": ("exercise", "run", "fruit", "seven"),
    "B": ("walk", "walk to work", "vegetables", "eight"),
    "C": ("swim", "swim on weekends", "salad", "six"),
    "Review": ("move", "go to the gym", "healthy food", "seven"),
    "core_sentences": "Do you… every day? / I eat… / About + time",
    "core_chunks": "healthy habits / sleep well",
}
ROUNDS[("Health", "Intermediate", "U1-Symptoms and Feelings")] = [
    r("How have you been feeling {0}?", "I think that I have been {1} because I {2}.", "ask feeling", "I think that… because…"),
    r("When did it start?", "I think that it started when I {3}.", "ask when", "I think that it started when…"),
    r("Have you taken anything?", "Yes, I have tried {4}.", "ask medicine", "I have tried…"),
    r("Did it help?", "I think that it {5}.", "ask result", "I think that it…"),
    r("That makes sense.", "Yeah, maybe.", "filler", "filler"),
    r("What will you do next?", "If it gets worse, I will {6}.", "if + condition", "If…, I will…"),
    r("Take care of yourself.", "Thank you. You too.", "wish", "thank you"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Health", "Intermediate", "U1-Symptoms and Feelings")] = {
    "A": ("lately", "tired", "work too much", "had a cold", "rest", "helped a bit", "see a doctor"),
    "B": ("this week", "stressed", "slept badly", "changed jobs", "tea", "calmed me down", "take a break"),
    "C": ("recently", "dizzy", "skipped meals", "was busy", "vitamins", "did not help much", "go to the clinic"),
    "Review": ("lately", "off", "was busy", "started", "something", "helped", "rest"),
    "core_sentences": "I think that… because… / I have tried… / If…, I will…",
    "core_chunks": "how have you been / take care",
}
ROUNDS[("Health", "Intermediate", "U2-Advice and Lifestyle")] = [
    r("What do you do to stay {0}?", "I think that {1} helps because it {2}.", "ask habit", "I think that… because…"),
    r("How often do you do that?", "I have been doing it since {3}.", "ask frequency", "I have been… since…"),
    r("Do you eat well?", "Yes, I think that I eat {4}.", "ask diet", "I think that I…"),
    r("What about sleep?", "If I can, I {5}.", "ask sleep", "If I can, I…"),
    r("I see.", "That makes sense.", "filler", "that makes sense"),
    r("Would you recommend it?", "Yes, because I feel {6}.", "ask recommend", "because I feel…"),
    r("Thanks for the tips.", "You are welcome.", "thanks", "you are welcome"),
    r("See you.", "See you.", "closing", "see you"),
]
VOCAB[("Health", "Intermediate", "U2-Advice and Lifestyle")] = {
    "A": ("healthy", "running", "clears my head", "last year", "enough fruit", "sleep eight hours", "better"),
    "B": ("fit", "yoga", "relaxes me", "last spring", "less sugar", "go to bed early", "calmer"),
    "C": ("well", "cycling", "saves time", "last month", "more vegetables", "rest at weekends", "stronger"),
    "Review": ("good", "exercise", "helps", "then", "well", "rest", "good"),
    "core_sentences": "I think that… because… / I have been… since… / If I can, I…",
    "core_chunks": "stay healthy / how often / would you recommend",
}
ROUNDS[("Health", "Intermediate", "U3-Health Choices")] = [
    r("Why did you choose to {0}?", "I chose it because I think that {1}.", "ask reason", "because I think that…"),
    r("Have you tried it before?", "Yes, I have tried it when I {2}.", "ask experience", "I have tried… when…"),
    r("What do you think of it?", "I think that it is {3}.", "ask opinion", "I think that…"),
    r("Would you do it again?", "Yes, because it {4}.", "ask again", "because it…"),
    r("What about {5}?", "I think that one is {6} too.", "ask other", "I think that…"),
    r("Thanks for sharing.", "You are welcome.", "thanks", "you are welcome"),
    r("I might try it.", "Good idea.", "closing", "good idea"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Health", "Intermediate", "U3-Health Choices")] = {
    "A": ("go to the gym", "it saves time", "was stressed", "useful", "helps me sleep", "yoga", "good"),
    "B": ("change my diet", "I feel lighter", "had a check-up", "worth it", "gives me energy", "running", "fine"),
    "C": ("see a therapist", "it helps me think", "felt low", "helpful", "clears my mind", "meditation", "nice"),
    "Review": ("try that", "it helps", "needed it", "good", "works", "that", "good"),
    "core_sentences": "because I think that… / I have tried… when… / I think that…",
    "core_chunks": "why did you choose / would you do it again",
}
ROUNDS[("Health", "Difficult", "U1-Health Concerns")] = [
    r("Why have you been {0} about your health lately?", "To be honest, although I {1}, I feel {2} because {3}.", "ask concern", "To be honest, / although / I feel… because…"),
    r("How long has this been on your mind?", "It has been {4} since I {5}.", "ask duration", "It has been… since I…"),
    r("What do you do when you worry?", "If I had more information, I would {6}.", "ask coping", "if + past, I would…"),
    r("Do you think it will get better?", "I think that it will if {7}.", "I think that… if", "I think that… if…"),
    r("What helped you before?", "When I {8}, I felt better.", "ask past", "When I…, I…"),
    r("Would you try that again?", "Although it was hard, I would try because {9}.", "although / would because", "although / would because"),
    r("Is there anything else?", "Sometimes I {10}. That helps.", "ask more", "Sometimes I…"),
    r("How does your family feel?", "They think that I need to {11}.", "they think that…", "they think that…"),
    r("Do you agree?", "I think that they are right because {12}.", "agree / because", "I think that… because…"),
    r("What will you do next?", "If I have time, I will {13}.", "if + present, I will", "If…, I will…"),
    r("Take care of yourself.", "Thank you. I will.", "wish", "thank you"),
    r("Goodbye.", "Goodbye.", "closing", "goodbye"),
]
VOCAB[("Health", "Difficult", "U1-Health Concerns")] = {
    "A": ("worried", "exercise", "uncertain", "I do not sleep well", "weeks", "read about it", "ask my doctor", "I get results", "talked to a friend", "it helped", "write it down", "rest more", "they are right", "book a check-up", "bye"),
    "B": ("anxious", "eat well", "stressed", "my routine changed", "months", "see a specialist", "I get advice", "I rest more", "saw a therapist", "it worked", "go for a walk", "sleep earlier", "they care", "get a second opinion", "bye"),
    "C": ("concerned", "take vitamins", "tired", "I had a scare", "a month", "do more tests", "I know more", "I changed my diet", "joined a group", "it supported me", "read", "exercise", "they understand", "follow up", "bye"),
    "Review": ("worried", "try", "unsure", "something happened", "time", "ask", "I learn", "I asked", "helped", "talk", "rest", "they say", "right", "try", "bye"),
    "core_sentences": "Although I…, I feel… because… / It has been… since I… / if + past, I would…",
    "core_chunks": "to be honest / although / take care",
}
ROUNDS[("Health", "Difficult", "U2-Prevention and Change")] = [
    r("What would you do if you wanted to {0}?", "You know, although it is hard, I would {1} if I had the chance because {2}.", "ask hypothetical", "You know, / although / I would… if… because…"),
    r("Have you ever tried?", "Yes. When I {3}, I felt {4}.", "ask experience", "When I…, I…"),
    r("What did you do then?", "I think that I {5}. It was {6}.", "ask past", "I think that I…"),
    r("Would you do the same again?", "If I could go back, I would {7} because {8}.", "if + past, would", "If I could…, I would… because…"),
    r("What would you tell someone else?", "Although everyone is different, I would say that {9}.", "although / would say that", "I would say that…"),
    r("Do you think that works?", "I think that it does if {10}.", "I think that… if", "I think that… if…"),
    r("Thanks for the advice.", "You are welcome.", "thanks", "you are welcome"),
    r("I will think about it.", "Good. Take care.", "closing", "take care"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Good luck.", "Thanks. You too.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
]
VOCAB[("Health", "Difficult", "U2-Prevention and Change")] = {
    "A": ("prevent back pain", "stretch more", "sitting hurts", "started yoga", "better", "stuck to it", "helpful", "start sooner", "I waited too long", "move every hour", "they try", "bye"),
    "B": ("sleep better", "cut caffeine", "I was restless", "changed my routine", "calmer", "slept earlier", "good", "do it earlier", "nights were bad", "avoid screens at night", "they listen", "bye"),
    "C": ("reduce stress", "meditate", "work was heavy", "tried meditation", "lighter", "practised daily", "worth it", "keep it up", "I stopped too soon", "take short breaks", "they do it", "bye"),
    "Review": ("improve", "try", "it helped", "tried", "good", "did it", "good", "continue", "it helped", "try", "they do", "bye"),
    "core_sentences": "Although…, I would… if… because… / If I could…, I would… / I think that…",
    "core_chunks": "you know / although / prevention",
}
ROUNDS[("Health", "Difficult", "U3-Long-term Goals")] = [
    r("How has your view on {0} changed?", "The thing is, although I used to {1}, I now think that {2} because {3}.", "ask change", "The thing is, / although I used to… / I now think that… because…"),
    r("When did you notice the change?", "It has been {4} since I {5}.", "ask when", "It has been… since I…"),
    r("Do you prefer how you see it now?", "I think that it is {6}. If I could, I would {7}.", "I think that… / if I could", "I think that… / I would…"),
    r("What would you tell your past self?", "Although it was hard, I would say that {8}.", "although / would say that", "I would say that…"),
    r("Has your family noticed?", "They think that I have {9}.", "they think that…", "they think that…"),
    r("Do you agree?", "I think that they are right because {10}.", "agree / because", "I think that… because…"),
    r("What will you do next?", "If I have time, I will {11}.", "if + present, I will", "If…, I will…"),
    r("That sounds good.", "Thank you. You too.", "closing", "thank you"),
    r("Good luck.", "Thanks. Bye.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Health", "Difficult", "U3-Long-term Goals")] = {
    "A": ("fitness", "skip the gym", "consistency matters", "I got older", "years", "joined a club", "better", "start earlier", "it takes time", "changed", "they see it", "keep going", "bye"),
    "B": ("diet", "eat anything", "balance is key", "I read more", "months", "cooked at home", "clearer", "worry less", "small steps work", "noticed", "they are right", "stick to it", "bye"),
    "C": ("mental health", "ignore my mood", "talking helps", "I hit a low", "a year", "asked for help", "healthier", "reach out sooner", "support matters", "grown", "they are right", "continue", "bye"),
    "Review": ("health", "ignore it", "it matters", "I learned", "time", "tried", "better", "continue", "it helps", "changed", "right", "try", "bye"),
    "core_sentences": "Although I used to…, I now think that… because… / It has been… since I… / I think that…",
    "core_chunks": "the thing is / although / long-term",
}

# Transport
ROUNDS[("Transport", "Simple", "U1-Asking the Way")] = [
    r("Where is the {0}?", "Go {1}.", "ask place", "Go + direction"),
    r("Is it far?", "About {2} minutes.", "ask distance", "About + time"),
    r("Can I walk?", "Sure.", "ask walk", "weak response"),
    r("Thank you.", "Sounds good.", "thanks", "weak response"),
]
VOCAB[("Transport", "Simple", "U1-Asking the Way")] = {
    "A": ("bus stop", "straight", "five"), "B": ("station", "left", "ten"), "C": ("taxi rank", "right", "three"), "Review": ("park", "straight", "seven"),
    "core_sentences": "Where is…? / Go… / About + time", "core_chunks": "is it far / thank you",
}
ROUNDS[("Transport", "Simple", "U2-Buying Tickets")] = [
    r("One ticket to {0}, please.", "Here you are. {1}.", "buy ticket", "Here you are"),
    r("When does it leave?", "At {2}.", "ask time", "At + time"),
    r("Which platform?", "Platform {3}.", "ask platform", "Platform + number"),
    r("Thanks.", "Sounds good.", "thanks", "weak response"),
]
VOCAB[("Transport", "Simple", "U2-Buying Tickets")] = {
    "A": ("London", "Ten pounds", "nine", "two"), "B": ("Manchester", "Fifteen pounds", "eleven", "five"), "C": ("Birmingham", "Twenty pounds", "three", "one"), "Review": ("there", "Five pounds", "two", "four"),
    "core_sentences": "One ticket to… / At + time / Platform + number", "core_chunks": "here you are / when does it leave",
}
ROUNDS[("Transport", "Simple", "U3-On the Bus or Train")] = [
    r("Is this seat free?", "Sure. Sit here.", "ask seat", "weak response"),
    r("When do we arrive?", "At {0}.", "ask arrival", "At + time"),
    r("Which stop is {1}?", "The next one.", "ask stop", "The next one"),
    r("Thank you.", "Sounds good.", "thanks", "weak response"),
]
VOCAB[("Transport", "Simple", "U3-On the Bus or Train")] = {
    "A": ("ten", "the museum"), "B": ("twelve", "the centre"), "C": ("five", "the station"), "Review": ("nine", "the park"),
    "core_sentences": "Is this seat free? / At + time / The next one", "core_chunks": "when do we arrive / which stop",
}
ROUNDS[("Transport", "Intermediate", "U1-Comparing Options")] = [
    r("How do you get to {0}?", "I think that I usually take the {1} because it is {2}.", "ask transport", "I think that… because…"),
    r("How long does it take?", "I think that it takes about {3}.", "ask time", "I think that it takes…"),
    r("What about the {4}?", "I have tried it when I {5}. It was {6}.", "ask other", "I have tried… when…"),
    r("That makes sense.", "Yeah, maybe.", "filler", "filler"),
    r("Do you need to change?", "If you take the {1}, you {7}.", "if + condition", "If you…, you…"),
    r("Thanks for the info.", "You are welcome.", "thanks", "you are welcome"),
    r("I will try it.", "Good idea.", "closing", "good idea"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Transport", "Intermediate", "U1-Comparing Options")] = {
    "A": ("work", "train", "fast", "thirty minutes", "bus", "was in a rush", "slower", "change once"),
    "B": ("town", "bus", "cheap", "twenty minutes", "train", "had luggage", "dearer", "do not change"),
    "C": ("the airport", "coach", "direct", "an hour", "train", "missed it", "okay", "change twice"),
    "Review": ("there", "train", "good", "forty minutes", "bus", "tried", "fine", "change"),
    "core_sentences": "I think that… because… / I have tried… when… / If you…, you…", "core_chunks": "how do you get / thanks for the info",
}
ROUNDS[("Transport", "Intermediate", "U2-Delays and Changes")] = [
    r("Why is the {0} late?", "I think that it is late because {1}.", "ask reason", "I think that… because…"),
    r("When will it leave?", "I have heard that it will leave at {2}.", "ask when", "I have heard that…"),
    r("Can I get a refund?", "If you ask at the desk, they will {3}.", "if + condition", "If you…, they will…"),
    r("I see.", "That makes sense.", "filler", "that makes sense"),
    r("What should I do?", "I think that you should {4}.", "ask advice", "I think that you should…"),
    r("Thanks for the help.", "You are welcome.", "thanks", "you are welcome"),
    r("I will go and ask.", "Good idea.", "closing", "good idea"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Transport", "Intermediate", "U2-Delays and Changes")] = {
    "A": ("train", "there is a signal fault", "four", "help you", "wait here"),
    "B": ("bus", "the traffic is bad", "five", "give a voucher", "try the next one"),
    "C": ("flight", "the weather is bad", "six", "rebook you", "check the screen"),
    "Review": ("train", "something happened", "soon", "help", "ask"),
    "core_sentences": "I think that… because… / I have heard that… / If you…, they will…", "core_chunks": "why is it late / get a refund",
}
ROUNDS[("Transport", "Intermediate", "U3-Travel Tips")] = [
    r("What is the best way to {0}?", "I think that {1} is best because it {2}.", "ask best way", "I think that… because…"),
    r("Have you done it before?", "Yes, I have done it when I {3}.", "ask experience", "I have done it when…"),
    r("Any tips?", "If you go early, you will {4}.", "if + advice", "If you…, you will…"),
    r("That makes sense.", "I think so too.", "filler", "I think so too"),
    r("What about tickets?", "I think that you should {5}.", "ask tickets", "I think that you should…"),
    r("Thanks a lot.", "You are welcome.", "thanks", "you are welcome"),
    r("I will remember that.", "Good.", "closing", "good"),
    r("See you.", "See you.", "closing", "see you"),
]
VOCAB[("Transport", "Intermediate", "U3-Travel Tips")] = {
    "A": ("get to the airport", "the train", "is quick", "flew last year", "find a seat", "book online"),
    "B": ("avoid rush hour", "leaving early", "saves time", "commuted daily", "miss the crowd", "check times"),
    "C": ("save money", "the bus", "is cheaper", "travelled a lot", "get a discount", "buy in advance"),
    "Review": ("go there", "that", "helps", "went", "succeed", "try that"),
    "core_sentences": "I think that… because… / I have done it when… / If you…, you will…", "core_chunks": "best way / any tips",
}
ROUNDS[("Transport", "Difficult", "U1-Commute Discussion")] = [
    r("How has your {0} been lately?", "To be honest, although I {1}, I feel {2} because {3}.", "ask commute", "To be honest, / although / I feel… because…"),
    r("How long has it been like this?", "It has been {4} since they {5}.", "ask duration", "It has been… since…"),
    r("What would you do if you could change it?", "If I had a choice, I would {6}.", "if + past, would", "If I had…, I would…"),
    r("Do you think it will get better?", "I think that it will if {7}.", "I think that… if", "I think that… if…"),
    r("What do you do to pass the time?", "When I {8}, I feel better.", "ask coping", "When I…, I…"),
    r("Would you recommend that?", "Although it is not ideal, I would try it because {9}.", "although / would because", "although / would because"),
    r("Thanks for sharing.", "You are welcome.", "thanks", "you are welcome"),
    r("I will try that.", "Good. Take care.", "closing", "take care"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Good luck.", "Thanks. You too.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
]
VOCAB[("Transport", "Difficult", "U1-Commute Discussion")] = {
    "A": ("commute", "like my job", "tired", "the trains are full", "months", "changed the timetable", "work from home", "they add more trains", "read", "it helps", "bye"),
    "B": ("journey", "live nearby", "stressed", "the road is busy", "weeks", "closed the lane", "cycle instead", "they fix the road", "listen to music", "time flies", "bye"),
    "C": ("travel", "need the job", "frustrated", "delays are common", "a year", "cut the service", "move closer", "they improve it", "podcasts", "you learn", "bye"),
    "Review": ("trip", "try", "mixed", "things changed", "time", "changed", "try", "they do", "read", "it helps", "bye"),
    "core_sentences": "Although I…, I feel… because… / It has been… since… / If I had…, I would…", "core_chunks": "to be honest / although / commute",
}
ROUNDS[("Transport", "Difficult", "U2-Transport Problems")] = [
    r("What would you do if {0}?", "You know, although it is annoying, I would {1} if I had to because {2}.", "ask hypothetical", "You know, / although / I would… if… because…"),
    r("Have you been in that situation?", "Yes. When I {3}, I felt {4}.", "ask experience", "When I…, I…"),
    r("What did you do?", "I think that I {5}. It was {6}.", "ask past", "I think that I…"),
    r("Would you do the same again?", "If I could go back, I would {7} because {8}.", "if + past, would", "If I could…, I would… because…"),
    r("What would you tell a friend?", "Although everyone is different, I would say that {9}.", "although / would say that", "I would say that…"),
    r("Do you think that helps?", "I think that it does if {10}.", "I think that… if", "I think that… if…"),
    r("Thanks for the advice.", "You are welcome.", "thanks", "you are welcome"),
    r("I will remember that.", "Good. Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("Take care.", "You too.", "closing", "you too"),
    r("Goodbye.", "Goodbye.", "closing", "goodbye"),
]
VOCAB[("Transport", "Difficult", "U2-Transport Problems")] = {
    "A": ("your train was cancelled", "take the next one", "I had no choice", "it happened", "stuck", "waited", "okay", "check the app first", "I was unprepared", "check before you go", "they do it early", "bye"),
    "B": ("you missed your bus", "call a taxi", "I was in a rush", "I missed it", "annoyed", "ran", "fine", "leave earlier", "I was late", "leave ten minutes early", "they plan", "bye"),
    "C": ("you lost your ticket", "go to the office", "they can help", "I lost it", "worried", "explained", "good", "keep it on your phone", "paper gets lost", "use the app", "they listen", "bye"),
    "Review": ("that happened", "try", "it helped", "it did", "bad", "asked", "okay", "try again", "it helped", "ask", "they do", "bye"),
    "core_sentences": "Although…, I would… if… because… / If I could…, I would… / I think that…", "core_chunks": "you know / although / transport problems",
}
ROUNDS[("Transport", "Difficult", "U3-Sustainable Transport")] = [
    r("How has your view on {0} changed?", "The thing is, although I used to {1}, I now think that {2} because {3}.", "ask change", "The thing is, / although I used to… / I now think that… because…"),
    r("When did that change?", "It has been {4} since I {5}.", "ask when", "It has been… since I…"),
    r("Do you prefer the way you think now?", "I think that it is {6}. If I could, I would {7}.", "I think that… / if I could", "I think that… / I would…"),
    r("What would you tell others?", "Although it is not easy, I would say that {8}.", "although / would say that", "I would say that…"),
    r("Has your family changed too?", "They think that I have {9}.", "they think that…", "they think that…"),
    r("Do you agree?", "I think that they are right because {10}.", "agree / because", "I think that… because…"),
    r("What will you do next?", "If I have time, I will {11}.", "if + present, I will", "If…, I will…"),
    r("That sounds good.", "Thank you.", "closing", "thank you"),
    r("Good luck.", "Thanks. Bye.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Transport", "Difficult", "U3-Sustainable Transport")] = {
    "A": ("driving", "drive everywhere", "public transport is better", "I read the news", "years", "sold my car", "better", "cycle more", "the city is cleaner", "try the bus", "changed", "they see it", "use the train", "bye"),
    "B": ("flying", "fly a lot", "we should fly less", "I saw a film", "months", "cut down", "clearer", "take the train", "the planet matters", "choose trains", "grown", "they are right", "avoid short flights", "bye"),
    "C": ("cycling", "avoid cycling", "cycling is healthy", "I moved city", "a year", "bought a bike", "healthier", "cycle daily", "it saves money", "give it a go", "noticed", "they agree", "cycle to work", "bye"),
    "Review": ("transport", "ignore it", "it matters", "I learned", "time", "changed", "good", "try", "it helps", "try", "right", "continue", "bye"),
    "core_sentences": "Although I used to…, I now think that… because… / It has been… since I… / I think that…", "core_chunks": "the thing is / although / sustainable",
}

# Work (Simple ×3, Intermediate ×3, Difficult ×3 — abbreviated for space; same structure)
ROUNDS[("Work", "Simple", "U1-Job and Schedule")] = [
    r("What do you do?", "I work at {0}.", "ask job", "I work at…"),
    r("When do you start?", "At {1}.", "ask time", "At + time"),
    r("Do you like it?", "Sure. It is {2}.", "ask opinion", "weak response / It is…"),
    r("That sounds good.", "Sounds good.", "closing", "weak response"),
]
VOCAB[("Work", "Simple", "U1-Job and Schedule")] = {"A": ("a school", "eight", "nice"), "B": ("a bank", "nine", "good"), "C": ("a shop", "seven", "fine"), "Review": ("an office", "eight", "okay"), "core_sentences": "What do you do? / I work at… / At + time", "core_chunks": "do you like it / that sounds good"}
ROUNDS[("Work", "Simple", "U2-Daily Tasks")] = [
    r("What do you do at work?", "I {0} and {1}.", "ask tasks", "I + verb and verb"),
    r("Do you have meetings?", "Yes. On {2}.", "ask meetings", "Yes. On + day"),
    r("When do you finish?", "At {3}.", "ask time", "At + time"),
    r("Thank you.", "Sounds good.", "thanks", "weak response"),
]
VOCAB[("Work", "Simple", "U2-Daily Tasks")] = {"A": ("write emails", "call people", "Mondays", "five"), "B": ("read reports", "go to meetings", "Fridays", "six"), "C": ("help customers", "check orders", "Wednesdays", "four"), "Review": ("answer calls", "send files", "Tuesdays", "five"), "core_sentences": "What do you do? / I… and… / On + day", "core_chunks": "at work / when do you finish"}
ROUNDS[("Work", "Simple", "U3-Colleagues")] = [
    r("Who do you work with?", "I work with {0}.", "ask who", "I work with…"),
    r("Do you have lunch together?", "Sometimes. We eat at {1}.", "ask lunch", "Sometimes. We eat at…"),
    r("Is your boss nice?", "Sure. He is {2}.", "ask boss", "weak response / He is…"),
    r("That is good.", "Sounds good.", "closing", "weak response"),
]
VOCAB[("Work", "Simple", "U3-Colleagues")] = {"A": ("my team", "one", "friendly"), "B": ("five people", "the café", "busy"), "C": ("my manager", "twelve", "fair"), "Review": ("them", "one", "good"), "core_sentences": "Who do you work with? / We eat at… / He is…", "core_chunks": "have lunch together / your boss"}
ROUNDS[("Work", "Intermediate", "U1-Reasons for Job")] = [
    r("Why did you choose this job?", "I chose it because I think that {0}.", "ask reason", "because I think that…"),
    r("How long have you been here?", "I have been here since {1}.", "ask duration", "I have been… since…"),
    r("Do you like the team?", "Yes, I think that they are {2}.", "ask opinion", "I think that…"),
    r("What if you get a better offer?", "If I get one, I will {3}.", "if + condition", "If I…, I will…"),
    r("That makes sense.", "I think so too.", "filler", "I think so too"),
    r("What do you want to do next?", "I think that I want to {4}.", "ask plan", "I think that I want to…"),
    r("Good luck with that.", "Thank you. You too.", "wish", "thank you"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Work", "Intermediate", "U1-Reasons for Job")] = {
    "A": ("it is stable", "last year", "friendly", "think about it", "learn more"),
    "B": ("I like the work", "two years ago", "helpful", "consider it", "get promoted"),
    "C": ("the pay is good", "last March", "nice", "talk to my boss", "change role"),
    "Review": ("it fits", "then", "good", "decide", "grow"),
    "core_sentences": "because I think that… / I have been… since… / If I…, I will…", "core_chunks": "why did you choose / good luck",
}
ROUNDS[("Work", "Intermediate", "U2-Challenges")] = [
    r("What is the hardest part of your job?", "I think that {0} is hard because {1}.", "ask challenge", "I think that… because…"),
    r("Have you always found it hard?", "No, I think that it got hard when I {2}.", "ask when", "I think that it got hard when…"),
    r("What do you do to cope?", "If I feel stressed, I {3}.", "if + coping", "If I feel…, I…"),
    r("I see.", "Yeah, maybe.", "filler", "filler"),
    r("Would you recommend this job?", "I think that it is {4} for people who {5}.", "ask recommend", "I think that it is… for people who…"),
    r("Thanks for sharing.", "You are welcome.", "thanks", "you are welcome"),
    r("I will think about it.", "Good idea.", "closing", "good idea"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Work", "Intermediate", "U2-Challenges")] = {
    "A": ("deadlines", "there is a lot to do", "took more projects", "take a break", "good", "like pressure"),
    "B": ("meetings", "they take time", "got promoted", "go for a walk", "okay", "are organised"),
    "C": ("customers", "they can be difficult", "joined this team", "talk to a friend", "fine", "like people"),
    "Review": ("it", "it is busy", "changed", "rest", "good", "try"),
    "core_sentences": "I think that… because… / I think that it got hard when… / If I feel…, I…", "core_chunks": "hardest part / would you recommend",
}
ROUNDS[("Work", "Intermediate", "U3-Career Plans")] = [
    r("Where do you see yourself in {0}?", "I think that I will {1} because I want to {2}.", "ask future", "I think that I will… because…"),
    r("Have you always wanted that?", "No, I have wanted it since I {3}.", "ask when", "I have wanted it since…"),
    r("What do you need to do?", "If I want to get there, I need to {4}.", "if + plan", "If I want to…, I need to…"),
    r("That makes sense.", "I think so too.", "filler", "I think so too"),
    r("What about your boss?", "I think that they {5}.", "ask boss", "I think that they…"),
    r("Thanks for the chat.", "You are welcome.", "thanks", "you are welcome"),
    r("I will work on it.", "Good.", "closing", "good"),
    r("See you.", "See you.", "closing", "see you"),
]
VOCAB[("Work", "Intermediate", "U3-Career Plans")] = {
    "A": ("five years", "be a manager", "lead a team", "joined", "learn more", "support me"),
    "B": ("three years", "change company", "see something new", "graduated", "get experience", "are okay with it"),
    "C": ("ten years", "start my own business", "be my own boss", "was young", "save money", "think it is possible"),
    "Review": ("then", "grow", "progress", "started", "try", "help"),
    "core_sentences": "I think that I will… because… / I have wanted it since… / If I want to…, I need to…", "core_chunks": "where do you see yourself / career plans",
}
ROUNDS[("Work", "Difficult", "U1-Work-Life Balance")] = [
    r("How do you balance {0} and {1}?", "To be honest, although I {2}, I feel {3} because {4}.", "ask balance", "To be honest, / although / I feel… because…"),
    r("How long has it been like this?", "It has been {5} since I {6}.", "ask duration", "It has been… since I…"),
    r("What would you do if you had more time?", "If I had more time, I would {7}.", "if + past, would", "If I had…, I would…"),
    r("Do you think it will change?", "I think that it will if {8}.", "I think that… if", "I think that… if…"),
    r("What do you do to relax?", "When I {9}, I feel better.", "ask coping", "When I…, I…"),
    r("Would you recommend that?", "Although it is not easy, I would try it because {10}.", "although / would because", "although / would because"),
    r("Thanks for the advice.", "You are welcome.", "thanks", "you are welcome"),
    r("I will try.", "Good. Take care.", "closing", "take care"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Good luck.", "Thanks. You too.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
]
VOCAB[("Work", "Difficult", "U1-Work-Life Balance")] = {
    "A": ("work", "life", "try hard", "tired", "hours are long", "months", "started this job", "exercise more", "they promote flexibility", "go for a walk", "it helps", "bye"),
    "B": ("meetings", "free time", "say no sometimes", "stressed", "there is too much", "weeks", "took the role", "sleep more", "I set boundaries", "read", "it calms me", "bye"),
    "C": ("deadlines", "family", "work from home sometimes", "pressed", "expectations are high", "a year", "had a child", "take holidays", "we talk about it", "cook", "it switches my mind", "bye"),
    "Review": ("job", "rest", "try", "mixed", "it is hard", "time", "changed", "rest", "I try", "relax", "it helps", "bye"),
    "core_sentences": "Although I…, I feel… because… / It has been… since I… / If I had…, I would…", "core_chunks": "to be honest / work-life balance",
}
ROUNDS[("Work", "Difficult", "U2-Change and Adaptation")] = [
    r("What would you do if your {0} changed?", "You know, although it would be hard, I would {1} if I had to because {2}.", "ask hypothetical", "You know, / although / I would… if… because…"),
    r("Have you been through that?", "Yes. When I {3}, I felt {4}.", "ask experience", "When I…, I…"),
    r("What did you do?", "I think that I {5}. It was {6}.", "ask past", "I think that I…"),
    r("Would you do the same again?", "If I could go back, I would {7} because {8}.", "if + past, would", "If I could…, I would… because…"),
    r("What would you tell a colleague?", "Although everyone is different, I would say that {9}.", "although / would say that", "I would say that…"),
    r("Do you think that works?", "I think that it does if {10}.", "I think that… if", "I think that… if…"),
    r("Thanks.", "You are welcome.", "thanks", "you are welcome"),
    r("I will keep that in mind.", "Good. Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("Take care.", "You too.", "closing", "you too"),
    r("Goodbye.", "Goodbye.", "closing", "goodbye"),
]
VOCAB[("Work", "Difficult", "U2-Change and Adaptation")] = {
    "A": ("role", "adapt", "I like learning", "changed jobs", "nervous", "asked for help", "okay", "take more time", "I rushed", "communicate early", "they listen", "bye"),
    "B": ("company", "move", "I need growth", "was made redundant", "worried", "updated my CV", "fine", "upskill first", "I was unprepared", "stay calm", "they try", "bye"),
    "C": ("team", "stay", "I value them", "lost my manager", "sad", "took on more", "good", "speak up more", "I was quiet", "ask questions", "they adapt", "bye"),
    "Review": ("job", "try", "it helps", "changed", "mixed", "adapted", "okay", "try", "it helped", "communicate", "they do", "bye"),
    "core_sentences": "Although…, I would… if… because… / If I could…, I would… / I think that…", "core_chunks": "you know / change and adaptation",
}
ROUNDS[("Work", "Difficult", "U3-Goals and Reflection")] = [
    r("How has your view on {0} changed?", "The thing is, although I used to {1}, I now think that {2} because {3}.", "ask change", "The thing is, / although I used to… / I now think that… because…"),
    r("When did that change?", "It has been {4} since I {5}.", "ask when", "It has been… since I…"),
    r("Do you prefer your view now?", "I think that it is {6}. If I could, I would {7}.", "I think that… / if I could", "I think that… / I would…"),
    r("What would you tell your past self?", "Although it was hard, I would say that {8}.", "although / would say that", "I would say that…"),
    r("Has your family noticed?", "They think that I have {9}.", "they think that…", "they think that…"),
    r("Do you agree?", "I think that they are right because {10}.", "agree / because", "I think that… because…"),
    r("What will you do next?", "If I have time, I will {11}.", "if + present, I will", "If…, I will…"),
    r("That sounds good.", "Thank you. You too.", "closing", "thank you"),
    r("Good luck.", "Thanks. Bye.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Work", "Difficult", "U3-Goals and Reflection")] = {
    "A": ("career", "only care about pay", "purpose matters too", "I got older", "years", "had a burnout", "better", "choose balance", "health comes first", "slow down", "changed", "they see it", "set boundaries", "bye"),
    "B": ("success", "chase titles", "growth matters more", "I failed once", "months", "reflected", "clearer", "learn from it", "failure teaches", "keep going", "grown", "they are right", "keep learning", "bye"),
    "C": ("teamwork", "work alone", "others help", "I joined a big team", "a year", "asked for feedback", "richer", "listen more", "ideas multiply", "trust them", "noticed", "they agree", "collaborate more", "bye"),
    "Review": ("work", "rush", "balance matters", "I learned", "time", "changed", "good", "try", "it helps", "reflect", "right", "continue", "bye"),
    "core_sentences": "Although I used to…, I now think that… because… / It has been… since I… / I think that…", "core_chunks": "the thing is / goals and reflection",
}

# Education (abbreviated: 9 units, same pattern)
ROUNDS[("Education", "Simple", "U1-Classes and Subjects")] = [
    r("What do you study?", "I study {0}.", "ask subject", "I study…"),
    r("Do you like it?", "Sure. It is {1}.", "ask opinion", "weak response / It is…"),
    r("When are your classes?", "On {2}.", "ask when", "On + days"),
    r("That sounds good.", "Sounds good.", "closing", "weak response"),
]
VOCAB[("Education", "Simple", "U1-Classes and Subjects")] = {"A": ("English", "useful", "Mondays"), "B": ("maths", "hard", "Tuesdays"), "C": ("science", "interesting", "Fridays"), "Review": ("history", "good", "Wednesdays"), "core_sentences": "What do you study? / I study… / On + days", "core_chunks": "do you like it / your classes"}
ROUNDS[("Education", "Simple", "U2-Homework")] = [
    r("Do you have {0} today?", "Yes. I have {1}.", "ask homework", "Yes. I have…"),
    r("When do you do it?", "I do it {2}.", "ask when", "I do it…"),
    r("Is it hard?", "Sometimes. I need {3}.", "ask difficulty", "Sometimes. I need…"),
    r("Good luck.", "Thanks. Sounds good.", "wish", "weak response"),
]
VOCAB[("Education", "Simple", "U2-Homework")] = {"A": ("homework", "maths", "at night", "help"), "B": ("any work", "reading", "after school", "time"), "C": ("an essay", "science", "on Sundays", "a book"), "Review": ("work", "English", "before dinner", "quiet"), "core_sentences": "Do you have…? / I have… / I do it…", "core_chunks": "when do you do it / good luck"}
ROUNDS[("Education", "Simple", "U3-Exams and Results")] = [
    r("When is your {0} exam?", "Next {1}.", "ask exam", "Next + time"),
    r("Are you ready?", "I think so. I {2}.", "ask ready", "I think so. I…"),
    r("What did you get last time?", "I got {3}.", "ask result", "I got…"),
    r("Well done.", "Thanks. Sounds good.", "praise", "weak response"),
]
VOCAB[("Education", "Simple", "U3-Exams and Results")] = {"A": ("maths", "week", "study every day", "a B"), "B": ("English", "month", "read a lot", "an A"), "C": ("science", "term", "practise", "a C"), "Review": ("exam", "week", "revise", "good"), "core_sentences": "When is…? / I think so. I… / I got…", "core_chunks": "are you ready / well done"}
ROUNDS[("Education", "Intermediate", "U1-Study Methods")] = [
    r("How do you study for {0}?", "I think that {1} works because it {2}.", "ask method", "I think that… because…"),
    r("Have you always done that?", "No, I have done it since I {3}.", "ask when", "I have done it since…"),
    r("What about when you are tired?", "If I am tired, I {4}.", "if + condition", "If I am…, I…"),
    r("That makes sense.", "I think so too.", "filler", "I think so too"),
    r("Would you recommend it?", "Yes, because I get {5}.", "ask recommend", "because I get…"),
    r("Thanks for the tip.", "You are welcome.", "thanks", "you are welcome"),
    r("I will try it.", "Good idea.", "closing", "good idea"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Education", "Intermediate", "U1-Study Methods")] = {
    "A": ("exams", "reading aloud", "helps me remember", "was fifteen", "take a break", "better grades"),
    "B": ("tests", "making notes", "organises my mind", "started college", "stop for ten minutes", "clearer ideas"),
    "C": ("essays", "discussing with friends", "deepens understanding", "joined the group", "go for a walk", "good results"),
    "Review": ("it", "this", "helps", "then", "rest", "results"),
    "core_sentences": "I think that… because… / I have done it since… / If I am…, I…", "core_chunks": "how do you study / would you recommend",
}
ROUNDS[("Education", "Intermediate", "U2-Choices and Reasons")] = [
    r("Why did you choose {0}?", "I chose it because I think that {1}.", "ask reason", "because I think that…"),
    r("How long have you been studying it?", "I have been studying it since {2}.", "ask duration", "I have been… since…"),
    r("Do you enjoy it?", "Yes, I think that it is {3}.", "ask opinion", "I think that…"),
    r("What if you could change?", "If I could change, I would {4}.", "if + could, would", "If I could…, I would…"),
    r("I see.", "That makes sense.", "filler", "that makes sense"),
    r("What do you want to do after?", "I think that I want to {5}.", "ask future", "I think that I want to…"),
    r("Good luck.", "Thank you. You too.", "wish", "thank you"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Education", "Intermediate", "U2-Choices and Reasons")] = {
    "A": ("this course", "it is useful", "last year", "interesting", "take more maths", "teach"),
    "B": ("this subject", "I like it", "two years ago", "challenging", "add languages", "research"),
    "C": ("this degree", "it opens doors", "last September", "rewarding", "start earlier", "work abroad"),
    "Review": ("it", "it fits", "then", "good", "try", "continue"),
    "core_sentences": "because I think that… / I have been… since… / I think that…", "core_chunks": "why did you choose / good luck",
}
ROUNDS[("Education", "Intermediate", "U3-Learning Experience")] = [
    r("What have you learned from {0}?", "I think that I have learned {1} because we {2}.", "ask learning", "I think that… because…"),
    r("Has it changed you?", "Yes, I think that I have {3} since I started.", "ask change", "I think that I have… since…"),
    r("What was the hardest part?", "I think that {4} was hard.", "ask hard", "I think that…"),
    r("Would you do it again?", "If I had to choose again, I would {5}.", "if + past, would", "If I had to…, I would…"),
    r("That makes sense.", "Yeah, maybe.", "filler", "filler"),
    r("What will you do next?", "I think that I will {6}.", "ask future", "I think that I will…"),
    r("Thanks for sharing.", "You are welcome.", "thanks", "you are welcome"),
    r("See you.", "See you.", "closing", "see you"),
]
VOCAB[("Education", "Intermediate", "U3-Learning Experience")] = {
    "A": ("this year", "to plan", "do projects", "become more organised", "exams", "do it again"),
    "B": ("this course", "to think critically", "debate", "grown", "the essay", "choose the same"),
    "C": ("university", "to work in a team", "had group work", "changed", "presentations", "take more courses"),
    "Review": ("it", "a lot", "did it", "improved", "that", "continue"),
    "core_sentences": "I think that… because… / I think that I have… since… / If I had to…, I would…", "core_chunks": "what have you learned / would you do it again",
}
ROUNDS[("Education", "Difficult", "U1-Learning Goals")] = [
    r("Why have you been {0} about your studies lately?", "To be honest, although I {1}, I feel {2} because {3}.", "ask concern", "To be honest, / although / I feel… because…"),
    r("How long has this been on your mind?", "It has been {4} since I {5}.", "ask duration", "It has been… since I…"),
    r("What would you do if you had more support?", "If I had more support, I would {6}.", "if + past, would", "If I had…, I would…"),
    r("Do you think it will get better?", "I think that it will if {7}.", "I think that… if", "I think that… if…"),
    r("What helped you before?", "When I {8}, I felt better.", "ask past", "When I…, I…"),
    r("Would you try that again?", "Although it was hard, I would try because {9}.", "although / would because", "although / would because"),
    r("Thanks for sharing.", "You are welcome.", "thanks", "you are welcome"),
    r("I will try that.", "Good. Take care.", "closing", "take care"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Good luck.", "Thanks. You too.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
]
VOCAB[("Education", "Difficult", "U1-Learning Goals")] = {
    "A": ("worried", "try hard", "uncertain", "the workload is heavy", "months", "failed a test", "ask for a tutor", "I get help", "joined a study group", "it helped", "bye"),
    "B": ("stressed", "care", "pressed", "exams are near", "weeks", "fell behind", "plan my time", "I manage", "talked to my teacher", "it worked", "bye"),
    "C": ("anxious", "want to do well", "nervous", "everyone is ahead", "a term", "missed classes", "focus on one subject", "I prioritise", "sought advice", "it supported me", "bye"),
    "Review": ("concerned", "try", "mixed", "it is hard", "time", "struggled", "get help", "I learn", "asked", "it helped", "bye"),
    "core_sentences": "Although I…, I feel… because… / It has been… since I… / If I had…, I would…", "core_chunks": "to be honest / learning goals",
}
ROUNDS[("Education", "Difficult", "U2-Challenges")] = [
    r("What would you do if you {0} again?", "You know, although it was hard, I would {1} if I could because {2}.", "ask hypothetical", "You know, / although / I would… if… because…"),
    r("Have you been in that situation?", "Yes. When I {3}, I felt {4}.", "ask experience", "When I…, I…"),
    r("What did you do?", "I think that I {5}. It was {6}.", "ask past", "I think that I…"),
    r("Would you do the same again?", "If I could go back, I would {7} because {8}.", "if + past, would", "If I could…, I would… because…"),
    r("What would you tell a friend?", "Although everyone is different, I would say that {9}.", "although / would say that", "I would say that…"),
    r("Do you think that helps?", "I think that it does if {10}.", "I think that… if", "I think that… if…"),
    r("Thanks for the advice.", "You are welcome.", "thanks", "you are welcome"),
    r("I will remember that.", "Good. Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("Take care.", "You too.", "closing", "you too"),
    r("Goodbye.", "Goodbye.", "closing", "goodbye"),
]
VOCAB[("Education", "Difficult", "U2-Challenges")] = {
    "A": ("failed that exam", "study differently", "I know better now", "it happened", "bad", "retook it", "okay", "start earlier", "I left it late", "ask for help early", "they do", "bye"),
    "B": ("missed that deadline", "plan better", "I learned to prioritise", "I missed one", "stressed", "asked for extension", "fine", "use a calendar", "I was disorganised", "break it into steps", "they try", "bye"),
    "C": ("chose the wrong course", "research more", "I know what I want", "I chose wrong", "lost", "switched", "good", "talk to more people", "I rushed", "follow your interest", "they listen", "bye"),
    "Review": ("had that", "try again", "it helped", "did", "mixed", "adapted", "okay", "try", "it helped", "try", "they do", "bye"),
    "core_sentences": "Although…, I would… if… because… / If I could…, I would… / I think that…", "core_chunks": "you know / challenges",
}
ROUNDS[("Education", "Difficult", "U3-Future and Reflection")] = [
    r("How has your view on {0} changed?", "The thing is, although I used to {1}, I now think that {2} because {3}.", "ask change", "The thing is, / although I used to… / I now think that… because…"),
    r("When did that change?", "It has been {4} since I {5}.", "ask when", "It has been… since I…"),
    r("Do you prefer your view now?", "I think that it is {6}. If I could, I would {7}.", "I think that… / if I could", "I think that… / I would…"),
    r("What would you tell your past self?", "Although it was hard, I would say that {8}.", "although / would say that", "I would say that…"),
    r("Has your family noticed?", "They think that I have {9}.", "they think that…", "they think that…"),
    r("Do you agree?", "I think that they are right because {10}.", "agree / because", "I think that… because…"),
    r("What will you do next?", "If I have time, I will {11}.", "if + present, I will", "If…, I will…"),
    r("That sounds good.", "Thank you. You too.", "closing", "thank you"),
    r("Good luck.", "Thanks. Bye.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Education", "Difficult", "U3-Future and Reflection")] = {
    "A": ("learning", "hate exams", "learning never stops", "I left school", "years", "started working", "better", "enjoy the process", "results are not everything", "keep going", "changed", "they see it", "keep learning", "bye"),
    "B": ("grades", "only care about A's", "effort matters more", "I failed once", "months", "reflected", "clearer", "try again", "failure teaches", "do your best", "grown", "they are right", "focus on growth", "bye"),
    "C": ("university", "want to leave early", "it shapes you", "I graduated", "a year", "looked back", "richer", "take more courses", "time there was valuable", "stay curious", "noticed", "they agree", "keep studying", "bye"),
    "Review": ("education", "rush", "it matters", "I learned", "time", "changed", "good", "continue", "it helps", "try", "right", "continue", "bye"),
    "core_sentences": "Although I used to…, I now think that… because… / It has been… since I… / I think that…",     "core_chunks": "the thing is / future and reflection",
}

# Weather, Hobbies, Family, Technology, Entertainment (每场景 9 个 Unit，全新对话)
ROUNDS[("Weather", "Simple", "U1-Today's Weather")] = [
    r("What is the weather like {0}?", "It is {1}.", "ask weather", "It is…"),
    r("Will it rain?", "Maybe. I think {2}.", "ask rain", "Maybe. I think…"),
    r("Do you need a coat?", "Sure. It is {3}.", "ask coat", "weak response / It is…"),
    r("Thanks.", "Sounds good.", "thanks", "weak response"),
]
VOCAB[("Weather", "Simple", "U1-Today's Weather")] = {"A": ("today", "cold", "so"), "B": ("now", "hot", "yes"), "C": ("outside", "windy", "maybe"), "Review": ("there", "nice", "no"), "core_sentences": "What is the weather like…? / It is… / Maybe. I think…", "core_chunks": "will it rain / thanks"}
ROUNDS[("Weather", "Simple", "U2-Planning by Weather")] = [
    r("What will you do {0}?", "If it is nice, I will {1}.", "ask plan", "If it is…, I will…"),
    r("What if it rains?", "I will {2}.", "if rain", "I will…"),
    r("When will you go?", "At {3}.", "ask when", "At + time"),
    r("Have fun.", "Thanks. Sounds good.", "wish", "weak response"),
]
VOCAB[("Weather", "Simple", "U2-Planning by Weather")] = {"A": ("tomorrow", "go out", "stay home", "ten"), "B": ("on Sunday", "go to the park", "take an umbrella", "two"), "C": ("this weekend", "play sport", "watch TV", "nine"), "Review": ("then", "go out", "rest", "noon"), "core_sentences": "If it is…, I will… / I will… / At + time", "core_chunks": "what if it rains / have fun"}
ROUNDS[("Weather", "Simple", "U3-Seasons")] = [
    r("What is your favourite {0}?", "I like {1}.", "ask season", "I like…"),
    r("Why?", "Because it is {2}.", "ask reason", "Because it is…"),
    r("What do you do then?", "I {3}.", "ask activity", "I…"),
    r("That sounds good.", "Sounds good.", "closing", "weak response"),
]
VOCAB[("Weather", "Simple", "U3-Seasons")] = {"A": ("season", "summer", "warm", "swim"), "B": ("time of year", "autumn", "cool", "walk"), "C": ("season", "winter", "cold", "ski"), "Review": ("one", "spring", "nice", "garden"), "core_sentences": "What is your favourite…? / I like… / Because it is…", "core_chunks": "what do you do / that sounds good"}
ROUNDS[("Weather", "Intermediate", "U1-Weather and Plans")] = [
    r("How does the weather affect your {0}?", "I think that if it is {1}, I {2} because it {3}.", "ask effect", "I think that if…, I… because…"),
    r("Have you had to change plans because of weather?", "Yes, I have changed plans when it {4}.", "ask experience", "I have changed… when…"),
    r("What do you do when it is bad?", "If the weather is bad, I will {5}.", "if + condition", "If…, I will…"),
    r("That makes sense.", "I think so too.", "filler", "I think so too"),
    r("Do you check the forecast?", "I think that I check it {6}.", "ask habit", "I think that I…"),
    r("Thanks for the tip.", "You are welcome.", "thanks", "you are welcome"),
    r("I will do that.", "Good idea.", "closing", "good idea"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Weather", "Intermediate", "U1-Weather and Plans")] = {
    "A": ("plans", "rainy", "stay in", "is wet", "rained", "read at home", "every morning"),
    "B": ("weekend", "sunny", "go out", "is nice", "was hot", "go to the beach", "before I go out"),
    "C": ("commute", "snowy", "work from home", "is cold", "snowed", "leave earlier", "the night before"),
    "Review": ("day", "bad", "adapt", "changes", "did", "adjust", "often"),
    "core_sentences": "I think that if…, I… because… / I have changed… when… / If…, I will…", "core_chunks": "how does the weather affect / check the forecast",
}
ROUNDS[("Weather", "Intermediate", "U2-Preferences")] = [
    r("Do you prefer {0} or {1} weather?", "I think that I prefer {0} because it is {2}.", "ask preference", "I think that I prefer… because…"),
    r("How long have you felt that way?", "I have preferred it since I {3}.", "ask when", "I have preferred it since…"),
    r("What about extreme weather?", "If it is too extreme, I feel {4}.", "if + feeling", "If it is…, I feel…"),
    r("I see.", "That makes sense.", "filler", "that makes sense"),
    r("Would you ever move for the weather?", "I think that I would if {5}.", "ask move", "I think that I would if…"),
    r("Thanks for sharing.", "You are welcome.", "thanks", "you are welcome"),
    r("I will think about it.", "Good.", "closing", "good"),
    r("See you.", "See you.", "closing", "see you"),
]
VOCAB[("Weather", "Intermediate", "U2-Preferences")] = {
    "A": ("hot", "cold", "easier to go out", "was a child", "uneasy", "I had to"),
    "B": ("cold", "hot", "cosy indoors", "moved here", "worried", "the job was right"),
    "C": ("dry", "wet", "better for my mood", "tried both", "stressed", "my family agreed"),
    "Review": ("warm", "cool", "nice", "remember", "mixed", "needed"),
    "core_sentences": "I think that I prefer… because… / I have preferred it since… / If it is…, I feel…", "core_chunks": "do you prefer / would you ever move",
}
ROUNDS[("Weather", "Intermediate", "U3-Weather Experiences")] = [
    r("What was the worst weather you have seen?", "I think that it was when {0} because {1}.", "ask experience", "I think that it was when… because…"),
    r("Where were you?", "I have been there when I {2}.", "ask where", "I have been there when…"),
    r("What did you do?", "If we could not go out, we {3}.", "if + past", "If we could not…, we…"),
    r("That makes sense.", "Yeah, maybe.", "filler", "filler"),
    r("Has the weather changed where you live?", "I think that it has got {4}.", "ask change", "I think that it has…"),
    r("Thanks for the chat.", "You are welcome.", "thanks", "you are welcome"),
    r("I will be careful.", "Good idea.", "closing", "good idea"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Weather", "Intermediate", "U3-Weather Experiences")] = {
    "A": ("it snowed a lot", "the roads were closed", "was on holiday", "stayed in", "wetter"),
    "B": ("there was a storm", "trees fell", "visited my family", "played games", "hotter"),
    "C": ("the heat was bad", "we had no AC", "lived abroad", "drank cold water", "more extreme"),
    "Review": ("something happened", "it was bad", "was there", "adapted", "different"),
    "core_sentences": "I think that it was when… because… / I have been there when… / If we could not…, we…", "core_chunks": "worst weather / has the weather changed",
}
ROUNDS[("Weather", "Difficult", "U1-Weather and Mood")] = [
    r("How does {0} affect your mood?", "To be honest, although I {1}, I feel {2} when it is {3} because {4}.", "ask effect", "To be honest, / although / I feel… when… because…"),
    r("How long have you noticed that?", "It has been {5} since I {6}.", "ask duration", "It has been… since I…"),
    r("What would you do if you could control the weather?", "If I could, I would {7}.", "if + could, would", "If I could…, I would…"),
    r("Do you think that will ever happen?", "I think that it will if {8}.", "I think that… if", "I think that… if…"),
    r("What do you do on bad days?", "When I {9}, I feel better.", "ask coping", "When I…, I…"),
    r("Would you recommend that?", "Although it is not for everyone, I would try it because {10}.", "although / would because", "although / would because"),
    r("Thanks for sharing.", "You are welcome.", "thanks", "you are welcome"),
    r("I will try that.", "Good. Take care.", "closing", "take care"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Good luck.", "Thanks. You too.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
]
VOCAB[("Weather", "Difficult", "U1-Weather and Mood")] = {
    "A": ("the weather", "like sun", "down", "grey", "I need light", "years", "moved north", "have more sun", "science finds a way", "light a lamp", "it helps", "bye"),
    "B": ("rain", "don't mind it", "calm", "wet", "it helps me focus", "months", "worked from home", "have less rain", "we adapt", "listen to music", "it works", "bye"),
    "C": ("cold", "prefer warmth", "sluggish", "freezing", "I slow down", "a year", "noticed the pattern", "live somewhere warm", "we get used to it", "exercise", "it wakes me up", "bye"),
    "Review": ("it", "try", "different", "bad", "it affects me", "time", "saw it", "change", "we see", "cope", "it helps", "bye"),
    "core_sentences": "Although I…, I feel… when… because… / It has been… since I… / If I could…, I would…", "core_chunks": "to be honest / weather and mood",
}
ROUNDS[("Weather", "Difficult", "U2-Climate and Change")] = [
    r("How has your view on {0} changed?", "The thing is, although I used to {1}, I now think that {2} because {3}.", "ask change", "The thing is, / although I used to… / I now think that… because…"),
    r("When did that change?", "It has been {4} since I {5}.", "ask when", "It has been… since I…"),
    r("Do you prefer your view now?", "I think that it is {6}. If I could, I would {7}.", "I think that… / if I could", "I think that… / I would…"),
    r("What would you tell others?", "Although it is hard to accept, I would say that {8}.", "although / would say that", "I would say that…"),
    r("Has your family changed too?", "They think that I have {9}.", "they think that…", "they think that…"),
    r("Do you agree?", "I think that they are right because {10}.", "agree / because", "I think that… because…"),
    r("What will you do next?", "If I have time, I will {11}.", "if + present, I will", "If…, I will…"),
    r("That sounds good.", "Thank you. You too.", "closing", "thank you"),
    r("Good luck.", "Thanks. Bye.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Weather", "Difficult", "U2-Climate and Change")] = {
    "A": ("climate", "ignore it", "we need to act", "I saw the news", "years", "read the reports", "better", "reduce my impact", "everyone has a role", "changed", "they see it", "recycle more", "bye"),
    "B": ("the environment", "not care much", "it affects us all", "I had a child", "months", "joined a group", "clearer", "vote for change", "policies matter", "grown", "they are right", "use less plastic", "bye"),
    "C": ("extreme weather", "think it was rare", "it is more common", "my town flooded", "a year", "researched", "richer", "support green projects", "we can help", "noticed", "they agree", "spread the word", "bye"),
    "Review": ("it", "ignore", "it matters", "I learned", "time", "changed", "good", "try", "it helps", "changed", "right", "continue", "bye"),
    "core_sentences": "Although I used to…, I now think that… because… / It has been… since I… / I think that…", "core_chunks": "the thing is / climate and change",
}
ROUNDS[("Weather", "Difficult", "U3-Discussion")] = [
    r("What would you do if {0} became more common?", "You know, although it is scary, I would {1} if I had to because {2}.", "ask hypothetical", "You know, / although / I would… if… because…"),
    r("Have you experienced that?", "Yes. When I {3}, I felt {4}.", "ask experience", "When I…, I…"),
    r("What did you do?", "I think that I {5}. It was {6}.", "ask past", "I think that I…"),
    r("Would you do the same again?", "If I could go back, I would {7} because {8}.", "if + past, would", "If I could…, I would… because…"),
    r("What would you tell people?", "Although everyone is different, I would say that {9}.", "although / would say that", "I would say that…"),
    r("Do you think that helps?", "I think that it does if {10}.", "I think that… if", "I think that… if…"),
    r("Thanks for the advice.", "You are welcome.", "thanks", "you are welcome"),
    r("I will remember that.", "Good. Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("Take care.", "You too.", "closing", "you too"),
    r("Goodbye.", "Goodbye.", "closing", "goodbye"),
]
VOCAB[("Weather", "Difficult", "U3-Discussion")] = {
    "A": ("flooding", "prepare better", "safety first", "it happened", "scared", "evacuated", "necessary", "stock supplies", "I was unprepared", "have a plan", "they listen", "bye"),
    "B": ("heatwaves", "stay indoors", "health matters", "we had one", "tired", "drank water", "good", "install AC", "we had none", "rest in the shade", "they do it", "bye"),
    "C": ("storms", "check the forecast", "knowledge helps", "one hit us", "anxious", "stayed inside", "fine", "have a kit", "we were lucky", "stay informed", "they prepare", "bye"),
    "Review": ("that", "adapt", "it helped", "did", "mixed", "coped", "okay", "try", "it helped", "prepare", "they do", "bye"),
    "core_sentences": "Although…, I would… if… because… / If I could…, I would… / I think that…", "core_chunks": "you know / weather discussion",
}

# Hobbies (Simple ×3)
ROUNDS[("Hobbies", "Simple", "U1-What You Like")] = [
    r("What do you do in your {0} time?", "I {1}.", "ask free time", "I + verb"),
    r("Do you like it?", "Sure. It is {2}.", "ask opinion", "weak response / It is…"),
    r("How often?", "Every {3}.", "ask frequency", "Every + time"),
    r("That sounds good.", "Sounds good.", "closing", "weak response"),
]
VOCAB[("Hobbies", "Simple", "U1-What You Like")] = {"A": ("free", "read", "relaxing"), "B": ("spare", "run", "healthy"), "C": ("free", "cook", "fun"), "Review": ("free", "draw", "nice"), "core_sentences": "What do you do…? / I… / Every + time", "core_chunks": "do you like it / that sounds good"}
ROUNDS[("Hobbies", "Simple", "U2-When You Do It")] = [
    r("When do you {0}?", "I do it {1}.", "ask when", "I do it…"),
    r("Where?", "At {2}.", "ask where", "At + place"),
    r("Who with?", "With {3}.", "ask who", "With…"),
    r("Have fun.", "Thanks. Sounds good.", "wish", "weak response"),
]
VOCAB[("Hobbies", "Simple", "U2-When You Do It")] = {"A": ("practise", "on Saturdays", "home", "my friend"), "B": ("play", "after work", "the park", "my brother"), "C": ("go", "on Sundays", "the club", "my sister"), "Review": ("do it", "at night", "there", "them"), "core_sentences": "When do you…? / I do it… / At + place", "core_chunks": "who with / have fun"}
ROUNDS[("Hobbies", "Simple", "U3-Inviting Someone")] = [
    r("Do you want to {0} with me?", "Sure. When?", "invite", "weak response / When?"),
    r("How about {1}?", "Sounds good. Where?", "suggest time", "weak response / Where?"),
    r("At {2}.", "Okay. See you.", "suggest place", "Okay. See you."),
    r("See you.", "See you.", "closing", "see you"),
]
VOCAB[("Hobbies", "Simple", "U3-Inviting Someone")] = {"A": ("go running", "Saturday", "the park"), "B": ("play football", "Sunday", "the pitch"), "C": ("watch a film", "Friday", "the cinema"), "Review": ("come", "then", "there"), "core_sentences": "Do you want to…? / How about…? / At + place", "core_chunks": "sounds good / see you"}
ROUNDS[("Hobbies", "Intermediate", "U1-Reasons for Hobbies")] = [
    r("Why do you like {0}?", "I think that I like it because it {1}.", "ask reason", "I think that I like it because…"),
    r("How long have you done it?", "I have done it since I {2}.", "ask duration", "I have done it since…"),
    r("What do you get from it?", "I think that I get {3}.", "ask benefit", "I think that I get…"),
    r("What if you had no time?", "If I had no time, I would {4}.", "if + past, would", "If I had…, I would…"),
    r("That makes sense.", "I think so too.", "filler", "I think so too"),
    r("Would you recommend it?", "Yes, because it is {5}.", "ask recommend", "because it is…"),
    r("Thanks. I might try it.", "Good idea.", "thanks", "good idea"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Hobbies", "Intermediate", "U1-Reasons for Hobbies")] = {
    "A": ("reading", "relaxes me", "was young", "new ideas", "miss it", "worth it"),
    "B": ("running", "keeps me fit", "left school", "energy", "try to make time", "good for you"),
    "C": ("cooking", "is creative", "had my own place", "satisfaction", "cook at weekends", "fun"),
    "Review": ("it", "helps", "started", "something", "adapt", "good"),
    "core_sentences": "I think that I like it because… / I have done it since… / If I had…, I would…", "core_chunks": "why do you like / would you recommend",
}
ROUNDS[("Hobbies", "Intermediate", "U2-Recommendations")] = [
    r("What hobby would you recommend for someone who likes {0}?", "I think that {1} is good because it {2}.", "ask recommend", "I think that… because…"),
    r("Have you tried it yourself?", "Yes, I have tried it when I {3}.", "ask experience", "I have tried it when…"),
    r("How do you find the time?", "If I plan well, I {4}.", "if + condition", "If I plan…, I…"),
    r("I see.", "That makes sense.", "filler", "that makes sense"),
    r("What about cost?", "I think that it is {5}.", "ask cost", "I think that it is…"),
    r("Thanks for the suggestion.", "You are welcome.", "thanks", "you are welcome"),
    r("I will look into it.", "Good.", "closing", "good"),
    r("See you.", "See you.", "closing", "see you"),
]
VOCAB[("Hobbies", "Intermediate", "U2-Recommendations")] = {
    "A": ("quiet", "yoga", "calms the mind", "was stressed", "find an hour", "cheap"),
    "B": ("sport", "swimming", "uses the whole body", "had back pain", "go early", "reasonable"),
    "C": ("creativity", "painting", "lets you express yourself", "had a break", "use weekends", "depends"),
    "Review": ("something", "that", "helps", "tried", "manage", "okay"),
    "core_sentences": "I think that… because… / I have tried it when… / If I plan…, I…", "core_chunks": "what hobby would you recommend / find the time",
}
ROUNDS[("Hobbies", "Intermediate", "U3-Experiences")] = [
    r("What is the best thing about your hobby?", "I think that the best thing is {0} because {1}.", "ask best", "I think that… because…"),
    r("Have you ever wanted to give up?", "Yes, when I {2}. But I think that {3}.", "ask give up", "when I… / I think that…"),
    r("What kept you going?", "If I had stopped, I would have {4}.", "if + past perfect, would have", "If I had…, I would have…"),
    r("That makes sense.", "Yeah, maybe.", "filler", "filler"),
    r("Would you do it professionally?", "I think that I would if {5}.", "ask professional", "I think that I would if…"),
    r("Thanks for sharing.", "You are welcome.", "thanks", "you are welcome"),
    r("I will give it a go.", "Good idea.", "closing", "good idea"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Hobbies", "Intermediate", "U3-Experiences")] = {
    "A": ("meeting people", "I am shy", "was busy", "it was worth it", "missed out", "the pay was good"),
    "B": ("learning new skills", "I get bored easily", "had no time", "I would regret it", "stopped growing", "I had the chance"),
    "C": ("the peace", "life is noisy", "was tired", "it helps me relax", "lost that", "it did not feel like work"),
    "Review": ("it", "it helps", "struggled", "good", "missed", "possible"),
    "core_sentences": "I think that… because… / when I… / I think that… / If I had…, I would have…", "core_chunks": "best thing / would you do it professionally",
}
ROUNDS[("Hobbies", "Difficult", "U1-Passion and Time")] = [
    r("How do you balance {0} and your hobby?", "To be honest, although I {1}, I feel {2} because {3}.", "ask balance", "To be honest, / although / I feel… because…"),
    r("How long has it been like this?", "It has been {4} since I {5}.", "ask duration", "It has been… since I…"),
    r("What would you do if you had more time?", "If I had more time, I would {6}.", "if + past, would", "If I had…, I would…"),
    r("Do you think that will happen?", "I think that it will if {7}.", "I think that… if", "I think that… if…"),
    r("What do you do to make time?", "When I {8}, I feel better.", "ask coping", "When I…, I…"),
    r("Would you recommend that?", "Although it is not easy, I would try it because {9}.", "although / would because", "although / would because"),
    r("Thanks for the advice.", "You are welcome.", "thanks", "you are welcome"),
    r("I will try.", "Good. Take care.", "closing", "take care"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Good luck.", "Thanks. You too.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
]
VOCAB[("Hobbies", "Difficult", "U1-Passion and Time")] = {
    "A": ("work", "work long hours", "guilty", "I love it", "months", "cut other things", "practise more", "I retire", "schedule it", "it is worth it", "bye"),
    "B": ("family", "have kids", "torn", "both matter", "years", "had children", "include them", "they grow up", "wake early", "you need it", "bye"),
    "C": ("study", "have exams", "stressed", "it helps me relax", "a term", "started university", "do it at weekends", "exams end", "use lunch breaks", "balance matters", "bye"),
    "Review": ("life", "try", "mixed", "it matters", "time", "changed", "try", "things change", "try", "it helps", "bye"),
    "core_sentences": "Although I…, I feel… because… / It has been… since I… / If I had…, I would…", "core_chunks": "to be honest / passion and time",
}
ROUNDS[("Hobbies", "Difficult", "U2-New Hobbies")] = [
    r("What would you do if you had to pick a new hobby?", "You know, although it is hard to choose, I would {0} if I had to because {1}.", "ask hypothetical", "You know, / although / I would… if… because…"),
    r("Have you ever started a new one?", "Yes. When I {2}, I felt {3}.", "ask experience", "When I…, I…"),
    r("What did you do?", "I think that I {4}. It was {5}.", "ask past", "I think that I…"),
    r("Would you do the same again?", "If I could go back, I would {6} because {7}.", "if + past, would", "If I could…, I would… because…"),
    r("What would you tell someone who is hesitant?", "Although everyone is different, I would say that {8}.", "although / would say that", "I would say that…"),
    r("Do you think that works?", "I think that it does if {9}.", "I think that… if", "I think that… if…"),
    r("Thanks.", "You are welcome.", "thanks", "you are welcome"),
    r("I will think about it.", "Good. Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("Take care.", "You too.", "closing", "you too"),
    r("Goodbye.", "Goodbye.", "closing", "goodbye"),
]
VOCAB[("Hobbies", "Difficult", "U2-New Hobbies")] = {
    "A": ("try painting", "I like colours", "started", "excited", "joined a class", "good", "start sooner", "I waited too long", "just start", "they try", "bye"),
    "B": ("learn an instrument", "music relaxes me", "tried guitar", "nervous", "practised daily", "okay", "get a teacher", "I was self-taught", "practise little and often", "they do", "bye"),
    "C": ("take up climbing", "I need challenge", "went once", "alive", "went again", "fine", "go with a friend", "it was scary alone", "take small steps", "they listen", "bye"),
    "Review": ("try something", "it helps", "did", "good", "tried", "okay", "continue", "it helped", "try", "they do", "bye"),
    "core_sentences": "Although…, I would… if… because… / If I could…, I would… / I think that…", "core_chunks": "you know / new hobbies",
}
ROUNDS[("Hobbies", "Difficult", "U3-Balance and Reflection")] = [
    r("How has your view on {0} changed?", "The thing is, although I used to {1}, I now think that {2} because {3}.", "ask change", "The thing is, / although I used to… / I now think that… because…"),
    r("When did that change?", "It has been {4} since I {5}.", "ask when", "It has been… since I…"),
    r("Do you prefer your view now?", "I think that it is {6}. If I could, I would {7}.", "I think that… / if I could", "I think that… / I would…"),
    r("What would you tell your past self?", "Although it was hard, I would say that {8}.", "although / would say that", "I would say that…"),
    r("Has your family noticed?", "They think that I have {9}.", "they think that…", "they think that…"),
    r("Do you agree?", "I think that they are right because {10}.", "agree / because", "I think that… because…"),
    r("What will you do next?", "If I have time, I will {11}.", "if + present, I will", "If…, I will…"),
    r("That sounds good.", "Thank you. You too.", "closing", "thank you"),
    r("Good luck.", "Thanks. Bye.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Hobbies", "Difficult", "U3-Balance and Reflection")] = {
    "A": ("free time", "work all the time", "rest matters", "I got ill", "years", "slowed down", "better", "protect it", "you need to recharge", "prioritise", "changed", "they see it", "say no more", "bye"),
    "B": ("hobbies", "skip them", "they make me me", "I had a crisis", "months", "picked one up", "clearer", "start small", "little is better than none", "make time", "grown", "they are right", "keep one hobby", "bye"),
    "C": ("fun", "feel guilty", "joy is productive", "I read a book", "a year", "scheduled play", "richer", "do it weekly", "life is short", "enjoy it", "noticed", "they agree", "protect my hobbies", "bye"),
    "Review": ("it", "ignore it", "it matters", "I learned", "time", "changed", "good", "try", "it helps", "try", "right", "continue", "bye"),
    "core_sentences": "Although I used to…, I now think that… because… / It has been… since I… / I think that…", "core_chunks": "the thing is / balance and reflection",
}

# Family（全新对话）
ROUNDS[("Family", "Simple", "U1-Family Members")] = [
    r("How many people are in your {0}?", "There are {1}.", "ask family", "There are…"),
    r("Do you live together?", "Sure. We live in {2}.", "ask live", "weak response / We live in…"),
    r("Do you see them often?", "Yes. Every {3}.", "ask frequency", "Yes. Every…"),
    r("That is nice.", "Sounds good.", "closing", "weak response"),
]
VOCAB[("Family", "Simple", "U1-Family Members")] = {"A": ("family", "four", "London"), "B": ("house", "five", "Manchester"), "C": ("flat", "three", "Birmingham"), "Review": ("home", "four", "town"), "core_sentences": "How many…? / There are… / We live in…", "core_chunks": "do you see them often / that is nice"}
ROUNDS[("Family", "Simple", "U2-Activities Together")] = [
    r("What do you do with your {0}?", "We {1} together.", "ask activity", "We… together."),
    r("When?", "Usually on {2}.", "ask when", "Usually on…"),
    r("Do you enjoy it?", "Sure. It is {3}.", "ask opinion", "weak response / It is…"),
    r("That sounds good.", "Sounds good.", "closing", "weak response"),
]
VOCAB[("Family", "Simple", "U2-Activities Together")] = {"A": ("family", "eat", "Sundays", "fun"), "B": ("parents", "watch TV", "Saturdays", "nice"), "C": ("sister", "go out", "Fridays", "good"), "Review": ("them", "talk", "weekends", "great"), "core_sentences": "What do you do with…? / We… together. / Usually on…", "core_chunks": "do you enjoy it / that sounds good"}
ROUNDS[("Family", "Simple", "U3-Weekend Plans")] = [
    r("What is your plan for the {0}?", "I will {1} with my family.", "ask plan", "I will… with my family."),
    r("Where will you go?", "We will go to {2}.", "ask where", "We will go to…"),
    r("What time?", "At {3}.", "ask time", "At + time"),
    r("Have fun.", "Thanks. Sounds good.", "wish", "weak response"),
]
VOCAB[("Family", "Simple", "U3-Weekend Plans")] = {"A": ("weekend", "have lunch", "the park"), "B": ("Sunday", "visit", "the beach"), "C": ("Saturday", "stay", "home"), "Review": ("weekend", "meet", "town"), "core_sentences": "What is your plan for…? / I will… with my family. / We will go to…", "core_chunks": "what time / have fun"}
ROUNDS[("Family", "Intermediate", "U1-Family Life")] = [
    r("How is your {0} life?", "I think that it is {1} because we {2}.", "ask family life", "I think that… because…"),
    r("Do you spend a lot of time together?", "I have spent more time with them since I {3}.", "ask time", "I have spent… since I…"),
    r("What do you do when you disagree?", "If we disagree, we {4}.", "if + condition", "If we…, we…"),
    r("That makes sense.", "I think so too.", "filler", "I think so too"),
    r("Would you change anything?", "I think that I would {5} if I could.", "ask change", "I think that I would… if…"),
    r("Thanks for sharing.", "You are welcome.", "thanks", "you are welcome"),
    r("I will call my family.", "Good idea.", "closing", "good idea"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Family", "Intermediate", "U1-Family Life")] = {
    "A": ("family", "good", "talk a lot", "moved back", "try to listen", "visit more"),
    "B": ("home", "busy", "eat together", "had kids", "take a break", "call more"),
    "C": ("family", "close", "help each other", "got older", "sit down and talk", "be more patient"),
    "Review": ("family", "fine", "get on", "changed", "talk", "try"),
    "core_sentences": "I think that… because… / I have spent… since I… / If we…, we…", "core_chunks": "how is your family life / would you change anything",
}
ROUNDS[("Family", "Intermediate", "U2-Advice and Support")] = [
    r("Do you ask your family for {0}?", "I think that I do when I {1}.", "ask advice", "I think that I do when…"),
    r("What do they usually say?", "They think that I should {2}.", "ask what", "They think that I should…"),
    r("Do you follow their advice?", "Sometimes. I think that it {3}.", "ask follow", "I think that it…"),
    r("What if you disagree?", "If I disagree, I {4}.", "if + condition", "If I…, I…"),
    r("I see.", "That makes sense.", "filler", "that makes sense"),
    r("Would you do the same for your kids?", "I think that I would if {5}.", "ask same", "I think that I would if…"),
    r("Thanks for the chat.", "You are welcome.", "thanks", "you are welcome"),
    r("See you.", "See you.", "closing", "see you"),
]
VOCAB[("Family", "Intermediate", "U2-Advice and Support")] = {
    "A": ("advice", "have a problem", "take a break", "helps", "explain my view", "they asked"),
    "B": ("help", "feel stuck", "talk to someone", "works", "listen first", "they needed it"),
    "C": ("opinions", "make big decisions", "think it over", "depends", "say thanks", "I had kids"),
    "Review": ("support", "need it", "try", "helps", "listen", "possible"),
    "core_sentences": "I think that I do when… / They think that I should… / If I…, I…", "core_chunks": "do you ask your family / would you do the same",
}
ROUNDS[("Family", "Intermediate", "U3-Changes")] = [
    r("How has your family {0} over the years?", "I think that we have {1} because {2}.", "ask change", "I think that we have… because…"),
    r("When did you notice the change?", "I have noticed it since I {3}.", "ask when", "I have noticed it since…"),
    r("Do you prefer how things are now?", "I think that it is {4}.", "ask prefer", "I think that it is…"),
    r("What if someone moved away?", "If someone moved away, we would {5}.", "if + condition", "If…, we would…"),
    r("That makes sense.", "Yeah, maybe.", "filler", "filler"),
    r("What will you do to stay close?", "I think that we will {6}.", "ask future", "I think that we will…"),
    r("Thanks for sharing.", "You are welcome.", "thanks", "you are welcome"),
    r("I will stay in touch with mine.", "Good.", "closing", "good"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Family", "Intermediate", "U3-Changes")] = {
    "A": ("changed", "grown closer", "we talk more", "had children", "better", "video call", "meet more"),
    "B": ("evolved", "become busier", "life got busy", "started work", "okay", "visit when we can", "plan holidays"),
    "C": ("grown", "learnt to listen", "we had a crisis", "left home", "healthier", "send messages", "have a reunion"),
    "Review": ("changed", "adapted", "things happened", "grew", "good", "keep in touch", "try"),
    "core_sentences": "I think that we have… because… / I have noticed it since… / If…, we would…", "core_chunks": "how has your family changed / stay close",
}
ROUNDS[("Family", "Difficult", "U1-Family and Work")] = [
    r("How do you balance {0} and {1}?", "To be honest, although I {2}, I feel {3} because {4}.", "ask balance", "To be honest, / although / I feel… because…"),
    r("How long has it been like this?", "It has been {5} since I {6}.", "ask duration", "It has been… since I…"),
    r("What would you do if you had more time at home?", "If I had more time, I would {7}.", "if + past, would", "If I had…, I would…"),
    r("Do you think that will change?", "I think that it will if {8}.", "I think that… if", "I think that… if…"),
    r("What do your family say?", "They think that I need to {9}.", "they think that…", "they think that…"),
    r("Do you agree?", "I think that they are right because {10}.", "agree / because", "I think that… because…"),
    r("Thanks for the advice.", "You are welcome.", "thanks", "you are welcome"),
    r("I will try to balance better.", "Good. Take care.", "closing", "take care"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Good luck.", "Thanks. You too.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
]
VOCAB[("Family", "Difficult", "U1-Family and Work")] = {
    "A": ("family", "work", "try hard", "torn", "both matter", "years", "took this job", "be home more", "they promote flexibility", "set boundaries", "they see it", "bye"),
    "B": ("children", "career", "love both", "guilty", "I miss them", "months", "had kids", "work part-time", "I get promoted", "leave on time", "they are right", "bye"),
    "C": ("parents", "job", "care for them", "stressed", "they are old", "a year", "moved closer", "visit every week", "we hire help", "call daily", "they agree", "bye"),
    "Review": ("home", "work", "try", "mixed", "it is hard", "time", "changed", "try", "things change", "balance", "right", "bye"),
    "core_sentences": "Although I…, I feel… because… / It has been… since I… / If I had…, I would…", "core_chunks": "to be honest / family and work",
}
ROUNDS[("Family", "Difficult", "U2-Values and Priorities")] = [
    r("What would you do if your family needed you during {0}?", "You know, although it is hard, I would {1} if I had to because {2}.", "ask hypothetical", "You know, / although / I would… if… because…"),
    r("Have you been in that situation?", "Yes. When I {3}, I felt {4}.", "ask experience", "When I…, I…"),
    r("What did you do?", "I think that I {5}. It was {6}.", "ask past", "I think that I…"),
    r("Would you do the same again?", "If I could go back, I would {7} because {8}.", "if + past, would", "If I could…, I would… because…"),
    r("What would you tell a friend?", "Although everyone is different, I would say that {9}.", "although / would say that", "I would say that…"),
    r("Do you think that helps?", "I think that it does if {10}.", "I think that… if", "I think that… if…"),
    r("Thanks.", "You are welcome.", "thanks", "you are welcome"),
    r("I will remember that.", "Good. Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("Take care.", "You too.", "closing", "you too"),
    r("Goodbye.", "Goodbye.", "closing", "goodbye"),
]
VOCAB[("Family", "Difficult", "U2-Values and Priorities")] = {
    "A": ("work", "go home", "family comes first", "it happened", "torn", "took leave", "right", "do it again", "they needed me", "put family first", "they understand", "bye"),
    "B": ("a meeting", "cancel it", "they rely on me", "my mum was ill", "worried", "left early", "hard", "call more", "I was away", "be there when it matters", "they try", "bye"),
    "C": ("a trip", "postpone", "I owe them", "dad had surgery", "stressed", "stayed", "good", "plan better", "they had no one", "show up", "they listen", "bye"),
    "Review": ("that", "choose them", "it matters", "did", "mixed", "chose", "okay", "try", "it helped", "prioritise", "they do", "bye"),
    "core_sentences": "Although…, I would… if… because… / If I could…, I would… / I think that…", "core_chunks": "you know / values and priorities",
}
ROUNDS[("Family", "Difficult", "U3-Reflection")] = [
    r("How has your view on {0} changed?", "The thing is, although I used to {1}, I now think that {2} because {3}.", "ask change", "The thing is, / although I used to… / I now think that… because…"),
    r("When did that change?", "It has been {4} since I {5}.", "ask when", "It has been… since I…"),
    r("Do you prefer your view now?", "I think that it is {6}. If I could, I would {7}.", "I think that… / if I could", "I think that… / I would…"),
    r("What would you tell your past self?", "Although it was hard, I would say that {8}.", "although / would say that", "I would say that…"),
    r("Has your family noticed?", "They think that I have {9}.", "they think that…", "they think that…"),
    r("Do you agree?", "I think that they are right because {10}.", "agree / because", "I think that… because…"),
    r("What will you do next?", "If I have time, I will {11}.", "if + present, I will", "If…, I will…"),
    r("That sounds good.", "Thank you. You too.", "closing", "thank you"),
    r("Good luck.", "Thanks. Bye.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Family", "Difficult", "U3-Reflection")] = {
    "A": ("family", "take them for granted", "time with them matters", "I had a scare", "years", "became a parent", "better", "call more", "you never regret it", "appreciate", "changed", "they see it", "visit more", "bye"),
    "B": ("parenting", "follow my parents' way", "every child is different", "I had my own", "months", "read and reflected", "clearer", "listen more", "flexibility helps", "adapted", "grown", "they are right", "keep learning", "bye"),
    "C": ("home", "want to leave", "roots matter", "I lived abroad", "a year", "came back", "richer", "stay connected", "distance teaches", "value it", "noticed", "they agree", "go home more", "bye"),
    "Review": ("family", "ignore it", "it matters", "I learned", "time", "changed", "good", "try", "it helps", "changed", "right", "continue", "bye"),
    "core_sentences": "Although I used to…, I now think that… because… / It has been… since I… / I think that…", "core_chunks": "the thing is / family reflection",
}

# Technology（全新对话）
ROUNDS[("Technology", "Simple", "U1-Using Apps")] = [
    r("Do you use {0}?", "Yes. I use it {1}.", "ask app", "Yes. I use it…"),
    r("What for?", "I use it to {2}.", "ask purpose", "I use it to…"),
    r("Is it easy?", "Sure. It is {3}.", "ask easy", "weak response / It is…"),
    r("I will try it.", "Sounds good.", "closing", "weak response"),
]
VOCAB[("Technology", "Simple", "U1-Using Apps")] = {"A": ("this app", "every day", "chat"), "B": ("that app", "at work", "send files"), "C": ("the map app", "when I travel", "find places"), "Review": ("it", "often", "learn"), "core_sentences": "Do you use…? / I use it to… / It is…", "core_chunks": "what for / I will try it"}
ROUNDS[("Technology", "Simple", "U2-Devices")] = [
    r("What {0} do you have?", "I have a {1}.", "ask device", "I have a…"),
    r("Do you like it?", "Sure. It is {2}.", "ask opinion", "weak response / It is…"),
    r("How long have you had it?", "For {3}.", "ask duration", "For…"),
    r("That sounds good.", "Sounds good.", "closing", "weak response"),
]
VOCAB[("Technology", "Simple", "U2-Devices")] = {"A": ("phone", "smartphone", "fast"), "B": ("computer", "laptop", "good"), "C": ("tablet", "iPad", "useful"), "Review": ("device", "phone", "fine"), "core_sentences": "What… do you have? / I have a… / For…", "core_chunks": "how long have you had it / that sounds good"}
ROUNDS[("Technology", "Simple", "U3-Getting Help")] = [
    r("My {0} does not work.", "What is wrong?", "say problem", "ask what"),
    r("It will not {1}.", "Try {2}.", "explain", "suggest"),
    r("I tried. It still does not work.", "Sure. Take it to {3}.", "say tried", "weak response / Take it to…"),
    r("Thank you.", "Sounds good.", "thanks", "weak response"),
]
VOCAB[("Technology", "Simple", "U3-Getting Help")] = {"A": ("phone", "turn on", "restarting it", "the shop"), "B": ("laptop", "connect", "checking the cable", "a repair shop"), "C": ("tablet", "open", "updating it", "the centre"), "Review": ("device", "work", "that", "them"), "core_sentences": "What is wrong? / Try… / Take it to…", "core_chunks": "does not work / thank you"}
ROUNDS[("Technology", "Intermediate", "U1-Preferences and Reasons")] = [
    r("Why do you prefer {0} over {1}?", "I think that I prefer it because it {2}.", "ask reason", "I think that I prefer it because…"),
    r("How long have you used it?", "I have used it since {3}.", "ask duration", "I have used it since…"),
    r("What do you use it for?", "I think that I use it for {4}.", "ask use", "I think that I use it for…"),
    r("What if they changed it?", "If they changed it, I would {5}.", "if + condition", "If they…, I would…"),
    r("That makes sense.", "I think so too.", "filler", "I think so too"),
    r("Would you recommend it?", "Yes, because it is {6}.", "ask recommend", "because it is…"),
    r("Thanks. I will try it.", "Good idea.", "thanks", "good idea"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Technology", "Intermediate", "U1-Preferences and Reasons")] = {
    "A": ("Android", "iPhone", "is cheaper", "last year", "work and play", "look for another", "reliable"),
    "B": ("Mac", "PC", "suits my work", "two years ago", "editing and design", "switch", "fast"),
    "C": ("this app", "that one", "has better features", "last month", "organising", "try something else", "simple"),
    "Review": ("this", "that", "fits me", "then", "things", "adapt", "good"),
    "core_sentences": "I think that I prefer it because… / I have used it since… / If they…, I would…", "core_chunks": "why do you prefer / would you recommend",
}
ROUNDS[("Technology", "Intermediate", "U2-Recommendations")] = [
    r("What {0} would you recommend?", "I think that {1} is good because it {2}.", "ask recommend", "I think that… because…"),
    r("Have you tried others?", "Yes, I have tried {3} when I {4}.", "ask tried", "I have tried… when…"),
    r("What about for {5}?", "I think that {6} works well.", "ask other use", "I think that…"),
    r("I see.", "That makes sense.", "filler", "that makes sense"),
    r("Do you pay for it?", "If I need {7}, I pay.", "if + condition", "If I need…, I…"),
    r("Thanks for the tip.", "You are welcome.", "thanks", "you are welcome"),
    r("I will check it out.", "Good.", "closing", "good"),
    r("See you.", "See you.", "closing", "see you"),
]
VOCAB[("Technology", "Intermediate", "U2-Recommendations")] = {
    "A": ("app", "this one", "is easy to use", "others", "was looking", "work", "that one", "more features"),
    "B": ("device", "this laptop", "lasts long", "a few", "needed an upgrade", "gaming", "that model", "speed"),
    "C": ("tool", "this software", "saves time", "several", "started the project", "teams", "that program", "support"),
    "Review": ("one", "this", "helps", "some", "wanted", "that", "it", "it"),
    "core_sentences": "I think that… because… / I have tried… when… / If I need…, I…", "core_chunks": "would you recommend / thanks for the tip",
}
ROUNDS[("Technology", "Intermediate", "U3-Problems and Fixes")] = [
    r("My {0} keeps {1}. What should I do?", "I think that you should {2} because {3}.", "ask problem", "I think that you should… because…"),
    r("Have you had that before?", "Yes, I have had it when I {4}.", "ask experience", "I have had it when…"),
    r("Did it work?", "I think that it {5}.", "ask result", "I think that it…"),
    r("What if that does not work?", "If that does not work, I would {6}.", "if + condition", "If…, I would…"),
    r("That makes sense.", "Yeah, maybe.", "filler", "filler"),
    r("Thanks for the help.", "You are welcome.", "thanks", "you are welcome"),
    r("I will try that.", "Good idea.", "closing", "good idea"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Technology", "Intermediate", "U3-Problems and Fixes")] = {
    "A": ("phone", "crashing", "restart it", "it clears the cache", "updated it", "helped", "contact support"),
    "B": ("computer", "freezing", "close apps", "it frees memory", "had too many open", "worked", "take it to a shop"),
    "C": ("WiFi", "dropping", "reset the router", "it often fixes it", "moved house", "did", "call the provider"),
    "Review": ("device", "playing up", "try that", "it helps", "did that", "helped", "ask someone"),
    "core_sentences": "I think that you should… because… / I have had it when… / If…, I would…", "core_chunks": "what should I do / thanks for the help",
}
ROUNDS[("Technology", "Difficult", "U1-Tech and Life")] = [
    r("How has {0} changed your life?", "To be honest, although I {1}, I feel {2} because {3}.", "ask change", "To be honest, / although / I feel… because…"),
    r("How long have you felt that way?", "It has been {4} since I {5}.", "ask duration", "It has been… since I…"),
    r("What would you do if you had to give it up?", "If I had to give it up, I would {6}.", "if + past, would", "If I had to…, I would…"),
    r("Do you think that will happen?", "I think that it will if {7}.", "I think that… if", "I think that… if…"),
    r("What do you do to switch off?", "When I {8}, I feel better.", "ask coping", "When I…, I…"),
    r("Would you recommend that?", "Although it is not easy, I would try it because {9}.", "although / would because", "although / would because"),
    r("Thanks for sharing.", "You are welcome.", "thanks", "you are welcome"),
    r("I will try.", "Good. Take care.", "closing", "take care"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Good luck.", "Thanks. You too.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
]
VOCAB[("Technology", "Difficult", "U1-Tech and Life")] = {
    "A": ("technology", "was hesitant", "more connected", "it saves time", "years", "got a smartphone", "miss face-to-face", "we lose touch", "leave my phone at home", "balance matters", "bye"),
    "B": ("the internet", "avoided it", "informed", "I can learn anything", "months", "started working online", "read more books", "we depend too much", "go for a walk", "you need breaks", "bye"),
    "C": ("social media", "loved it", "torn", "it connects and distracts", "a year", "noticed my mood", "use it less", "we get addicted", "set limits", "awareness helps", "bye"),
    "Review": ("tech", "tried", "mixed", "it changed things", "time", "changed", "adapt", "we see", "unplug", "it helps", "bye"),
    "core_sentences": "Although I…, I feel… because… / It has been… since I… / If I had to…, I would…", "core_chunks": "to be honest / tech and life",
}
ROUNDS[("Technology", "Difficult", "U2-Change and Adaptation")] = [
    r("What would you do if {0} changed overnight?", "You know, although it would be hard, I would {1} if I had to because {2}.", "ask hypothetical", "You know, / although / I would… if… because…"),
    r("Have you been through a big tech change?", "Yes. When I {3}, I felt {4}.", "ask experience", "When I…, I…"),
    r("What did you do?", "I think that I {5}. It was {6}.", "ask past", "I think that I…"),
    r("Would you do the same again?", "If I could go back, I would {7} because {8}.", "if + past, would", "If I could…, I would… because…"),
    r("What would you tell others?", "Although everyone is different, I would say that {9}.", "although / would say that", "I would say that…"),
    r("Do you think that helps?", "I think that it does if {10}.", "I think that… if", "I think that… if…"),
    r("Thanks.", "You are welcome.", "thanks", "you are welcome"),
    r("I will keep that in mind.", "Good. Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("Take care.", "You too.", "closing", "you too"),
    r("Goodbye.", "Goodbye.", "closing", "goodbye"),
]
VOCAB[("Technology", "Difficult", "U2-Change and Adaptation")] = {
    "A": ("your phone", "adapt", "I need it for work", "my company switched", "lost", "learnt the new system", "okay", "ask for training", "I was slow", "give it time", "they try", "bye"),
    "B": ("the platform", "move on", "others will too", "they updated the app", "frustrated", "found an alternative", "fine", "back up data first", "I lost files", "stay flexible", "they do", "bye"),
    "C": ("privacy rules", "read the terms", "it affects my data", "the law changed", "confused", "sought advice", "good", "ask an expert", "I ignored it", "understand your rights", "they listen", "bye"),
    "Review": ("it", "try", "it helped", "changed", "mixed", "adapted", "okay", "try", "it helped", "adapt", "they do", "bye"),
    "core_sentences": "Although…, I would… if… because… / If I could…, I would… / I think that…", "core_chunks": "you know / change and adaptation",
}
ROUNDS[("Technology", "Difficult", "U3-Ethics and Discussion")] = [
    r("How has your view on {0} changed?", "The thing is, although I used to {1}, I now think that {2} because {3}.", "ask change", "The thing is, / although I used to… / I now think that… because…"),
    r("When did that change?", "It has been {4} since I {5}.", "ask when", "It has been… since I…"),
    r("Do you prefer your view now?", "I think that it is {6}. If I could, I would {7}.", "I think that… / if I could", "I think that… / I would…"),
    r("What would you tell policymakers?", "Although it is complex, I would say that {8}.", "although / would say that", "I would say that…"),
    r("Has your family changed their view?", "They think that I have {9}.", "they think that…", "they think that…"),
    r("Do you agree?", "I think that they are right because {10}.", "agree / because", "I think that… because…"),
    r("What will you do next?", "If I have time, I will {11}.", "if + present, I will", "If…, I will…"),
    r("That sounds good.", "Thank you. You too.", "closing", "thank you"),
    r("Good luck.", "Thanks. Bye.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Technology", "Difficult", "U3-Ethics and Discussion")] = {
    "A": ("data privacy", "not care much", "we should protect it", "I read the news", "years", "had a breach", "better", "use less apps", "companies profit from it", "regulated", "changed", "they see it", "review my settings", "bye"),
    "B": ("AI", "be excited only", "we need rules", "I saw what it can do", "months", "tried ChatGPT", "clearer", "support regulation", "it can harm too", "evolved", "grown", "they are right", "stay informed", "bye"),
    "C": ("screen time", "use it freely", "balance matters", "I felt tired", "a year", "tracked my use", "richer", "set limits", "it affects sleep", "noticed", "they agree", "reduce it", "bye"),
    "Review": ("tech", "ignore it", "it matters", "I learned", "time", "changed", "good", "try", "it helps", "changed", "right", "continue", "bye"),
    "core_sentences": "Although I used to…, I now think that… because… / It has been… since I… / I think that…", "core_chunks": "the thing is / ethics and discussion",
}

# Entertainment（全新对话）
ROUNDS[("Entertainment", "Simple", "U1-Movies and Shows")] = [
    r("Do you watch {0}?", "Yes. I watch {1}.", "ask watch", "Yes. I watch…"),
    r("What is your favourite?", "I like {2}.", "ask favourite", "I like…"),
    r("When do you watch?", "I watch {3}.", "ask when", "I watch…"),
    r("That sounds good.", "Sounds good.", "closing", "weak response"),
]
VOCAB[("Entertainment", "Simple", "U1-Movies and Shows")] = {"A": ("films", "a lot", "comedies"), "B": ("TV", "every day", "dramas"), "C": ("shows", "at night", "sport"), "Review": ("anything", "often", "that"), "core_sentences": "Do you watch…? / I like… / I watch…", "core_chunks": "what is your favourite / that sounds good"}
ROUNDS[("Entertainment", "Simple", "U2-Going Out")] = [
    r("Do you go to the {0}?", "Sometimes. I go {1}.", "ask go out", "Sometimes. I go…"),
    r("What do you see?", "I see {2}.", "ask what", "I see…"),
    r("Do you like it?", "Sure. It is {3}.", "ask opinion", "weak response / It is…"),
    r("Have fun.", "Thanks. Sounds good.", "wish", "weak response"),
]
VOCAB[("Entertainment", "Simple", "U2-Going Out")] = {"A": ("cinema", "once a month", "films"), "B": ("theatre", "on weekends", "plays"), "C": ("concerts", "in summer", "music"), "Review": ("park", "often", "shows"), "core_sentences": "Do you go to…? / I go… / I see…", "core_chunks": "do you like it / have fun"}
ROUNDS[("Entertainment", "Simple", "U3-Music and Games")] = [
    r("Do you like {0}?", "Yes. I like {1}.", "ask like", "Yes. I like…"),
    r("What do you play?", "I play {2}.", "ask play", "I play…"),
    r("How often?", "Every {3}.", "ask frequency", "Every…"),
    r("That is cool.", "Sounds good.", "closing", "weak response"),
]
VOCAB[("Entertainment", "Simple", "U3-Music and Games")] = {"A": ("music", "pop", "the piano"), "B": ("games", "sport games", "on my phone"), "C": ("both", "rock and puzzles", "at weekends"), "Review": ("it", "that", "something"), "core_sentences": "Do you like…? / I like… / I play…", "core_chunks": "how often / that is cool"}
ROUNDS[("Entertainment", "Intermediate", "U1-Reasons and Preferences")] = [
    r("Why do you like {0}?", "I think that I like it because it {1}.", "ask reason", "I think that I like it because…"),
    r("How long have you liked it?", "I have liked it since I {2}.", "ask duration", "I have liked it since…"),
    r("What do you recommend?", "I think that {3} is good.", "ask recommend", "I think that…"),
    r("What if I do not like it?", "If you do not like it, try {4}.", "if + condition", "If you…, try…"),
    r("That makes sense.", "I think so too.", "filler", "I think so too"),
    r("Would you go with me?", "I think that I would if {5}.", "ask go", "I think that I would if…"),
    r("Thanks. I will try it.", "Good idea.", "thanks", "good idea"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Entertainment", "Intermediate", "U1-Reasons and Preferences")] = {
    "A": ("that show", "is funny", "was a teen", "the first season", "something else", "I am free"),
    "B": ("that band", "relaxes me", "heard them", "the last album", "another genre", "you buy the tickets"),
    "C": ("that game", "challenges me", "got a console", "the new one", "a different one", "we find a time"),
    "Review": ("it", "helps", "started", "that", "another", "possible"),
    "core_sentences": "I think that I like it because… / I have liked it since… / If you…, try…", "core_chunks": "why do you like / would you go with me",
}
ROUNDS[("Entertainment", "Intermediate", "U2-Recommendations")] = [
    r("What {0} would you recommend?", "I think that {1} is worth it because it {2}.", "ask recommend", "I think that… because…"),
    r("Have you seen it yourself?", "Yes, I have seen it when I {3}.", "ask seen", "I have seen it when…"),
    r("What did you think?", "I think that it was {4}.", "ask opinion", "I think that it was…"),
    r("What about for someone who likes {5}?", "I think that {6} would work.", "ask other", "I think that…"),
    r("I see.", "That makes sense.", "filler", "that makes sense"),
    r("Thanks for the suggestion.", "You are welcome.", "thanks", "you are welcome"),
    r("I will check it out.", "Good.", "closing", "good"),
    r("See you.", "See you.", "closing", "see you"),
]
VOCAB[("Entertainment", "Intermediate", "U2-Recommendations")] = {
    "A": ("film", "this one", "has a great story", "had a free evening", "moving", "action", "that one"),
    "B": ("series", "that one", "keeps you hooked", "was ill", "gripping", "comedy", "this show"),
    "C": ("concert", "that band", "puts on a show", "they came to town", "loud", "rock", "this venue"),
    "Review": ("one", "this", "is good", "went", "good", "that", "that"),
    "core_sentences": "I think that… because… / I have seen it when… / I think that…", "core_chunks": "would you recommend / thanks for the suggestion",
}
ROUNDS[("Entertainment", "Intermediate", "U3-Experiences")] = [
    r("What is the best {0} you have been to?", "I think that it was {1} because {2}.", "ask best", "I think that it was… because…"),
    r("When did you go?", "I have been there when I {3}.", "ask when", "I have been there when…"),
    r("What made it special?", "I think that the {4} was {5}.", "ask special", "I think that the… was…"),
    r("Would you go again?", "If I had the chance, I would {6}.", "if + past, would", "If I had…, I would…"),
    r("That makes sense.", "Yeah, maybe.", "filler", "filler"),
    r("What will you do next?", "I think that I will {7}.", "ask future", "I think that I will…"),
    r("Thanks for sharing.", "You are welcome.", "thanks", "you are welcome"),
    r("I will try to go.", "Good idea.", "closing", "good idea"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Entertainment", "Intermediate", "U3-Experiences")] = {
    "A": ("gig", "last year", "the crowd was great", "visited London", "atmosphere", "electric", "go again"),
    "B": ("play", "the one in May", "acting was strong", "had a gift", "ending", "surprising", "see more"),
    "C": ("festival", "last summer", "the weather was perfect", "took a break", "music", "diverse", "book early"),
    "Review": ("one", "that", "it was good", "went", "part", "good", "return"),
    "core_sentences": "I think that it was… because… / I have been there when… / If I had…, I would…", "core_chunks": "best you have been to / would you go again",
}
ROUNDS[("Entertainment", "Difficult", "U1-Taste and Quality")] = [
    r("How do you decide what is {0}?", "To be honest, although I {1}, I think that {2} because {3}.", "ask criteria", "To be honest, / although / I think that… because…"),
    r("How long have you felt that way?", "It has been {4} since I {5}.", "ask duration", "It has been… since I…"),
    r("What would you do if you had to choose one?", "If I had to choose one, I would {6}.", "if + past, would", "If I had to…, I would…"),
    r("Do you think that will change?", "I think that it will if {7}.", "I think that… if", "I think that… if…"),
    r("What do your friends say?", "They think that I have {8}.", "they think that…", "they think that…"),
    r("Do you agree?", "I think that they are right because {9}.", "agree / because", "I think that… because…"),
    r("Thanks for the chat.", "You are welcome.", "thanks", "you are welcome"),
    r("I will think about it.", "Good. Take care.", "closing", "take care"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Good luck.", "Thanks. You too.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
]
VOCAB[("Entertainment", "Difficult", "U1-Taste and Quality")] = {
    "A": ("good", "follow reviews", "story matters most", "I get moved", "years", "started reading more", "pick the book", "I discover something new", "odd taste", "they know me", "bye"),
    "B": ("worth watching", "trust friends", "acting makes it", "I care about craft", "months", "saw a masterpiece", "choose the classic", "we debate it", "high standards", "they respect it", "bye"),
    "C": ("quality", "try everything", "it is subjective", "I changed", "a year", "studied film", "go by mood", "I have time", "evolved", "they see it", "bye"),
    "Review": ("good", "try", "it depends", "I learned", "time", "changed", "pick one", "we see", "taste", "they agree", "bye"),
    "core_sentences": "Although I…, I think that… because… / It has been… since I… / If I had to…, I would…", "core_chunks": "to be honest / taste and quality",
}
ROUNDS[("Entertainment", "Difficult", "U2-Trends")] = [
    r("What would you do if {0} became the only option?", "You know, although it would be sad, I would {1} if I had to because {2}.", "ask hypothetical", "You know, / although / I would… if… because…"),
    r("Have you seen that trend?", "Yes. When I {3}, I felt {4}.", "ask experience", "When I…, I…"),
    r("What did you do?", "I think that I {5}. It was {6}.", "ask past", "I think that I…"),
    r("Would you do the same again?", "If I could go back, I would {7} because {8}.", "if + past, would", "If I could…, I would… because…"),
    r("What would you tell a young fan?", "Although everyone is different, I would say that {9}.", "although / would say that", "I would say that…"),
    r("Do you think that helps?", "I think that it does if {10}.", "I think that… if", "I think that… if…"),
    r("Thanks.", "You are welcome.", "thanks", "you are welcome"),
    r("I will remember that.", "Good. Bye.", "closing", "bye"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
    r("Take care.", "You too.", "closing", "you too"),
    r("Goodbye.", "Goodbye.", "closing", "goodbye"),
]
VOCAB[("Entertainment", "Difficult", "U2-Trends")] = {
    "A": ("streaming", "adapt", "choice is still there", "it took over", "mixed", "kept both", "okay", "enjoy the old ways", "I miss cinemas", "explore both", "they try", "bye"),
    "B": ("algorithm picks", "curate my own", "I discover more", "I noticed it", "trapped", "sought variety", "fine", "click less", "I was passive", "mix sources", "they do", "bye"),
    "C": ("everything went online", "embrace it", "access improved", "lockdown happened", "grateful", "upgraded my setup", "good", "keep live events", "I miss crowds", "balance both", "they listen", "bye"),
    "Review": ("that", "try", "it helped", "changed", "mixed", "adapted", "okay", "try", "it helped", "adapt", "they do", "bye"),
    "core_sentences": "Although…, I would… if… because… / If I could…, I would… / I think that…", "core_chunks": "you know / trends",
}
ROUNDS[("Entertainment", "Difficult", "U3-Discussion and Reflection")] = [
    r("How has your view on {0} changed?", "The thing is, although I used to {1}, I now think that {2} because {3}.", "ask change", "The thing is, / although I used to… / I now think that… because…"),
    r("When did that change?", "It has been {4} since I {5}.", "ask when", "It has been… since I…"),
    r("Do you prefer your view now?", "I think that it is {6}. If I could, I would {7}.", "I think that… / if I could", "I think that… / I would…"),
    r("What would you tell your past self?", "Although it was hard, I would say that {8}.", "although / would say that", "I would say that…"),
    r("Has your family noticed?", "They think that I have {9}.", "they think that…", "they think that…"),
    r("Do you agree?", "I think that they are right because {10}.", "agree / because", "I think that… because…"),
    r("What will you do next?", "If I have time, I will {11}.", "if + present, I will", "If…, I will…"),
    r("That sounds good.", "Thank you. You too.", "closing", "thank you"),
    r("Good luck.", "Thanks. Bye.", "wish", "thanks"),
    r("Take care.", "You too.", "closing", "you too"),
    r("See you.", "See you.", "closing", "see you"),
    r("Bye.", "Bye.", "closing", "bye"),
]
VOCAB[("Entertainment", "Difficult", "U3-Discussion and Reflection")] = {
    "A": ("films", "only watch blockbusters", "small films matter", "I grew older", "years", "found indie cinema", "better", "try more genres", "you miss a lot", "broaden", "changed", "they see it", "watch one new film", "bye"),
    "B": ("music", "stick to one genre", "variety enriches", "I travelled", "months", "heard world music", "clearer", "go to live gigs", "recordings are not enough", "explore", "grown", "they are right", "discover one new artist", "bye"),
    "C": ("gaming", "see it as a waste", "it is an art form", "I played a story game", "a year", "changed my mind", "richer", "play with others", "it connects people", "give it a go", "noticed", "they agree", "try a new game", "bye"),
    "Review": ("entertainment", "consume passively", "engagement matters", "I reflected", "time", "changed", "good", "try", "it helps", "engage", "right", "continue", "bye"),
    "core_sentences": "Although I used to…, I now think that… because… / It has been… since I… / I think that…", "core_chunks": "the thing is / discussion and reflection",
}

# ---------- 规则：原有场景每难度 5 个 Unit，新增场景每难度 3 个 Unit ----------
ORIGINAL_SCENES = ["Daily Life", "Eating Out", "Shopping"]
NEW_SCENES = [
    "Travel", "Health", "Transport", "Work", "Education",
    "Weather", "Hobbies", "Family", "Technology", "Entertainment",
]
SCENES = ORIGINAL_SCENES + NEW_SCENES
SCENE_ABBREV = {
    "Daily Life": "DL", "Eating Out": "EO", "Shopping": "SH",
    "Travel": "TR", "Health": "HL", "Transport": "TP", "Work": "WK",
    "Education": "ED", "Weather": "WH", "Hobbies": "HB", "Family": "FM",
    "Technology": "TC", "Entertainment": "ET",
}
DIFF_ABBREV = {"Simple": "S", "Intermediate": "I", "Difficult": "D"}
BATCHES = ["A", "B", "C", "Review"]

# ---------- 规则：原有场景每难度 5 个 Unit，新增场景每难度 3 个 Unit ----------
ORIGINAL_SCENES = ["Daily Life", "Eating Out", "Shopping"]
NEW_SCENES = [
    "Travel", "Health", "Transport", "Work", "Education",
    "Weather", "Hobbies", "Family", "Technology", "Entertainment",
]
SCENES = ORIGINAL_SCENES + NEW_SCENES
SCENE_ABBREV = {
    "Daily Life": "DL", "Eating Out": "EO", "Shopping": "SH",
    "Travel": "TR", "Health": "HL", "Transport": "TP", "Work": "WK",
    "Education": "ED", "Weather": "WH", "Hobbies": "HB", "Family": "FM",
    "Technology": "TC", "Entertainment": "ET",
}
DIFF_ABBREV = {"Simple": "S", "Intermediate": "I", "Difficult": "D"}
BATCHES = ["A", "B", "C", "Review"]

UNIT_THEMES = {
    "Daily Life": {
        "Simple": ["U1-Daily Routine", "U2-Expressing Plans", "U3-Expressing Habits", "U4-Expressing Feelings", "U5-Asking for Help"],
        "Intermediate": ["U1-Weekend Plans", "U2-Reasons for Choices", "U3-Conditional Plans", "U4-Opinion and Experience", "U5-Making Suggestions"],
        "Difficult": ["U1-Work Stress Reflection", "U2-Hypothetical Advice", "U3-Reflection on Change", "U4-Problem Solving", "U5-Long-term Goals"],
    },
    "Eating Out": {
        "Simple": ["U1-Ordering Food", "U2-Asking for Things", "U3-Paying the Bill", "U4-Table Talk", "U5-Leaving"],
        "Intermediate": ["U1-Reasons for Choice", "U2-Recommending Dishes", "U3-Dietary Needs", "U4-Complaints and Praise", "U5-Reservations"],
        "Difficult": ["U1-Preference and Condition", "U2-Fine Dining Experience", "U3-Food and Culture", "U4-Review and Recommend", "U5-Special Occasions"],
    },
    "Shopping": {
        "Simple": ["U1-Asking Price", "U2-Buying or Not", "U3-Size and Colour", "U4-Payment", "U5-Returns"],
        "Intermediate": ["U1-Reason for Purchase", "U2-Comparing Products", "U3-Discounts and Offers", "U4-Customer Service", "U5-Online Shopping"],
        "Difficult": ["U1-Regret or Satisfaction", "U2-Value and Quality", "U3-Consumer Rights", "U4-Sustainable Shopping", "U5-Investment Purchases"],
    },
    # 新增 10 个场景：每难度仅 3 个 Unit（U1、U2、U3），对话内容均为全新编写（见上方 ROUNDS/VOCAB）
    "Travel": {
        "Simple": ["U1-Booking and Plans", "U2-Asking Directions", "U3-Sightseeing"],
        "Intermediate": ["U1-Reasons for Travel", "U2-Recommendations", "U3-Travel Experiences"],
        "Difficult": ["U1-Travel Preferences", "U2-Culture and Places", "U3-Reflection on Trips"],
    },
    "Health": {
        "Simple": ["U1-At the Doctor", "U2-Medicine and Advice", "U3-Healthy Habits"],
        "Intermediate": ["U1-Symptoms and Feelings", "U2-Advice and Lifestyle", "U3-Health Choices"],
        "Difficult": ["U1-Health Concerns", "U2-Prevention and Change", "U3-Long-term Goals"],
    },
    "Transport": {
        "Simple": ["U1-Asking the Way", "U2-Buying Tickets", "U3-On the Bus or Train"],
        "Intermediate": ["U1-Comparing Options", "U2-Delays and Changes", "U3-Travel Tips"],
        "Difficult": ["U1-Commute Discussion", "U2-Transport Problems", "U3-Sustainable Transport"],
    },
    "Work": {
        "Simple": ["U1-Job and Schedule", "U2-Daily Tasks", "U3-Colleagues"],
        "Intermediate": ["U1-Reasons for Job", "U2-Challenges", "U3-Career Plans"],
        "Difficult": ["U1-Work-Life Balance", "U2-Change and Adaptation", "U3-Goals and Reflection"],
    },
    "Education": {
        "Simple": ["U1-Classes and Subjects", "U2-Homework", "U3-Exams and Results"],
        "Intermediate": ["U1-Study Methods", "U2-Choices and Reasons", "U3-Learning Experience"],
        "Difficult": ["U1-Learning Goals", "U2-Challenges", "U3-Future and Reflection"],
    },
    "Weather": {
        "Simple": ["U1-Today's Weather", "U2-Planning by Weather", "U3-Seasons"],
        "Intermediate": ["U1-Weather and Plans", "U2-Preferences", "U3-Weather Experiences"],
        "Difficult": ["U1-Weather and Mood", "U2-Climate and Change", "U3-Discussion"],
    },
    "Hobbies": {
        "Simple": ["U1-What You Like", "U2-When You Do It", "U3-Inviting Someone"],
        "Intermediate": ["U1-Reasons for Hobbies", "U2-Recommendations", "U3-Experiences"],
        "Difficult": ["U1-Passion and Time", "U2-New Hobbies", "U3-Balance and Reflection"],
    },
    "Family": {
        "Simple": ["U1-Family Members", "U2-Activities Together", "U3-Weekend Plans"],
        "Intermediate": ["U1-Family Life", "U2-Advice and Support", "U3-Changes"],
        "Difficult": ["U1-Family and Work", "U2-Values and Priorities", "U3-Reflection"],
    },
    "Technology": {
        "Simple": ["U1-Using Apps", "U2-Devices", "U3-Getting Help"],
        "Intermediate": ["U1-Preferences and Reasons", "U2-Recommendations", "U3-Problems and Fixes"],
        "Difficult": ["U1-Tech and Life", "U2-Change and Adaptation", "U3-Ethics and Discussion"],
    },
    "Entertainment": {
        "Simple": ["U1-Movies and Shows", "U2-Going Out", "U3-Music and Games"],
        "Intermediate": ["U1-Reasons and Preferences", "U2-Recommendations", "U3-Experiences"],
        "Difficult": ["U1-Taste and Quality", "U2-Trends", "U3-Discussion and Reflection"],
    },
}


def _max_placeholder_index(s):
    if "{" not in s:
        return -1
    idx = [int(m.group(1)) for m in re.finditer(r"\{(\d+)\}", s)]
    return max(idx) if idx else -1


def fill_round(round_tuple, vocab_tuple):
    a, b, hint_a, hint_b = round_tuple
    n = max(_max_placeholder_index(a), _max_placeholder_index(b),
            _max_placeholder_index(hint_a), _max_placeholder_index(hint_b)) + 1
    if n <= 0 or not vocab_tuple:
        return (a, b, hint_a, hint_b)
    v = list(vocab_tuple) + [""] * (n - len(vocab_tuple))
    try:
        return (
            a.format(*v) if "{" in a else a,
            b.format(*v) if "{" in b else b,
            hint_a.format(*v) if "{" in hint_a else hint_a,
            hint_b.format(*v) if "{" in hint_b else hint_b,
        )
    except (IndexError, KeyError):
        return (a, b, hint_a, hint_b)


def build_content(rounds_list, vocab_dict, batch):
    content = []
    vocab = vocab_dict.get(batch, vocab_dict.get("A", ()))
    for r in rounds_list:
        a, b, hint_a, hint_b = fill_round(r, vocab)
        content.append({"role": "A", "content": a, "hint": hint_a})
        content.append({"role": "B", "content": b, "hint": hint_b})
    return content


def main():
    records = []
    for scene in SCENES:
        for difficulty in ["Simple", "Intermediate", "Difficult"]:
            themes = UNIT_THEMES[scene][difficulty]
            first_key = (scene, difficulty, themes[0])
            for unit_idx, unit_theme in enumerate(themes, 1):
                for batch in BATCHES:
                    key = (scene, difficulty, unit_theme)
                    rounds_list = ROUNDS.get(key, ROUNDS.get(first_key))
                    vocab_dict = VOCAB.get(key, VOCAB.get(first_key))
                    if not rounds_list or not vocab_dict:
                        raise RuntimeError(f"Missing ROUNDS/VOCAB for {key}")
                    dialogue_id = f"{SCENE_ABBREV[scene]}-{DIFF_ABBREV[difficulty]}-U{unit_idx}-{batch}"
                    content = build_content(rounds_list, vocab_dict, batch)
                    rec = {
                        "scene": scene,
                        "difficulty": difficulty,
                        "unit": unit_theme,
                        "batch": batch,
                        "dialogue_id": dialogue_id,
                        "content": content,
                        "core_sentences": vocab_dict.get("core_sentences", ""),
                        "core_chunks": vocab_dict.get("core_chunks", ""),
                    }
                    records.append(rec)

    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    orig_count = len(ORIGINAL_SCENES) * 3 * 5 * 4
    new_count = len(NEW_SCENES) * 3 * 3 * 4
    print(f"Generated {len(records)} records (original: {orig_count} + new scenes: {new_count} = {orig_count + new_count}).")


if __name__ == "__main__":
    main()
