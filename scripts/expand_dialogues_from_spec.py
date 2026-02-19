#!/usr/bin/env python3
"""
按 docs/SCENE_NPC_DB_SPEC.md 补全 data/dialogues.json 中缺失的场景与 NPC 对话。
运行：python scripts/expand_dialogues_from_spec.py
会读取现有 dialogues.json，追加新记录后写回。新记录为英文学习对话，含 learn/review/immersive 三套。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIALOGUES_PATH = ROOT / "data" / "dialogues.json"


def turn(role: str, content: str, hint: str) -> dict:
    return {"role": role, "content": content, "hint": hint}


def dialogue_record(
    big_scene: str,
    small_scene: str,
    npc: str,
    dialogue_set: int,
    usage: str,
    dialogue_id: str,
    content: list,
    core_sentences: str,
    core_chunks: str,
    big_scene_name: str,
    small_scene_name: str,
    npc_name: str,
) -> dict:
    return {
        "big_scene": big_scene,
        "small_scene": small_scene,
        "npc": npc,
        "dialogue_set": dialogue_set,
        "usage": usage,
        "dialogue_id": dialogue_id,
        "content": content,
        "core_sentences": core_sentences,
        "core_chunks": core_chunks,
        "big_scene_name": big_scene_name,
        "small_scene_name": small_scene_name,
        "npc_name": npc_name,
    }


def new_dialogues():
    """生成所有新增对话（出行交通、购物消费、工作职场、社交人情）。"""
    out = []

    # ----- 出行交通：机场 - 地勤 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Good morning. Do you have your boarding pass?", "greeting / ask"),
                turn("B", "Yes, here it is.", "Yes, here it is."),
                turn("A", "Window or aisle?", "Window or aisle?"),
                turn("B", "Aisle, please.", "Aisle, please."),
                turn("A", "Your gate is B12. Boarding at 10:30.", "gate / boarding time"),
                turn("B", "Where is gate B12?", "Where is gate B12?"),
                turn("A", "Go straight, then turn left. You'll see the signs.", "directions"),
                turn("B", "Thank you very much.", "Thank you very much."),
                turn("A", "You're welcome. Have a nice flight.", "response"),
            ]
            core_s = "Do you have...? / Window or aisle? / Where is gate...?"
            core_c = "boarding pass / turn left / have a nice flight"
        elif set_no == 2:
            content = [
                turn("A", "Hi. May I see your passport and ticket?", "ask documents"),
                turn("B", "Sure. Here you go.", "Sure. Here you go."),
                turn("A", "Are you checking any bags?", "Are you checking any bags?"),
                turn("B", "Just this one. Carry-on.", "Just this one. Carry-on."),
                turn("A", "Your seat is 14A. Gate A5.", "seat / gate"),
                turn("B", "What time is boarding?", "What time is boarding?"),
                turn("A", "In about forty minutes.", "time"),
                turn("B", "Thanks for your help.", "Thanks for your help."),
                turn("A", "No problem. Safe travels.", "response"),
            ]
            core_s = "May I see...? / Are you checking...? / What time is boarding?"
            core_c = "passport and ticket / carry-on / safe travels"
        else:
            content = [
                turn("A", "Hello. Flight to Shanghai?", "confirm flight"),
                turn("B", "Yes. Is it on time?", "Yes. Is it on time?"),
                turn("A", "Yes. You can board in twenty minutes.", "on time / board"),
                turn("B", "Which gate?", "Which gate?"),
                turn("A", "Gate C8. Down the hall to your right.", "gate / direction"),
                turn("B", "Do I need to show my passport again?", "Do I need to show my passport again?"),
                turn("A", "Yes, at the gate. Have it ready.", "remind"),
                turn("B", "Okay. Thank you.", "Okay. Thank you."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Is it on time? / Which gate? / Do I need to show...?"
            core_c = "on time / have it ready"
        out.append(dialogue_record(
            "transport", "airport", "ground_staff", set_no, usage,
            f"CX-AIRPORT-GROUND-{did_suffix}", content, core_s, core_c,
            "出行交通", "机场", "地勤"
        ))

    # ----- 出行交通：机场 - 安检员 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Next, please. Laptop and liquids out, please.", "instruction"),
                turn("B", "Okay. Are water bottles allowed?", "Okay. Are water bottles allowed?"),
                turn("A", "Empty ones are. You can fill up after security.", "rule"),
                turn("B", "Do I put my bag here?", "Do I put my bag here?"),
                turn("A", "Yes. Step through when the light turns green.", "yes / next step"),
                turn("B", "Got it. Thank you.", "Got it. Thank you."),
                turn("A", "Have a good day.", "response"),
            ]
            core_s = "Laptop and liquids out / Are...allowed? / Do I put...here?"
            core_c = "step through / after security"
        elif set_no == 2:
            content = [
                turn("A", "Please take off your belt and watch.", "instruction"),
                turn("B", "Sure. Phone too?", "Sure. Phone too?"),
                turn("A", "Yes, in the tray. Keys and coins as well.", "yes / details"),
                turn("B", "Is this lane for first class?", "Is this lane for first class?"),
                turn("A", "No, that's the next one. This is general.", "clarify"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Take off.../ Phone too? / Is this lane for...?"
            core_c = "in the tray / first class"
        else:
            content = [
                turn("A", "Any liquids in your bag?", "ask"),
                turn("B", "Just a small hand sanitizer.", "Just a small hand sanitizer."),
                turn("A", "That's fine if it's under 100ml. Put it in the tray.", "rule"),
                turn("B", "Do I need to take my shoes off?", "Do I need to take my shoes off?"),
                turn("A", "No, not today. Just walk through.", "no / instruction"),
                turn("B", "Okay. Thank you.", "Okay. Thank you."),
                turn("A", "Safe flight.", "response"),
            ]
            core_s = "Any liquids...? / Do I need to take...off?"
            core_c = "under 100ml / walk through"
        out.append(dialogue_record(
            "transport", "airport", "security_check", set_no, usage,
            f"CX-AIRPORT-SECURITY-{did_suffix}", content, core_s, core_c,
            "出行交通", "机场", "安检员"
        ))

    # ----- 出行交通：机场 - 空姐/空少 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Welcome aboard. Can I help you find your seat?", "welcome"),
                turn("B", "Yes, I'm in 22C.", "Yes, I'm in 22C."),
                turn("A", "Just a few rows back. On your right.", "direction"),
                turn("B", "Where can I put my bag?", "Where can I put my bag?"),
                turn("A", "In the overhead bin. I can help if it's heavy.", "overhead / offer"),
                turn("B", "Thanks. Can I have a blanket?", "Thanks. Can I have a blanket?"),
                turn("A", "Sure. I'll bring one after takeoff.", "sure / timing"),
                turn("B", "Thank you.", "Thank you."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Can I help you find...? / Where can I put...? / Can I have...?"
            core_c = "welcome aboard / overhead bin / after takeoff"
        elif set_no == 2:
            content = [
                turn("A", "Would you like something to drink?", "offer"),
                turn("B", "Water, please.", "Water, please."),
                turn("A", "Still or sparkling?", "Still or sparkling?"),
                turn("B", "Still, thanks.", "Still, thanks."),
                turn("A", "Here you go. We have tea and juice too.", "hand / more options"),
                turn("B", "I'm fine for now. When is lunch?", "I'm fine for now. When is lunch?"),
                turn("A", "In about an hour.", "time"),
                turn("B", "Okay. Thank you.", "Okay. Thank you."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Would you like...? / Still or sparkling? / When is...?"
            core_c = "still or sparkling / for now"
        else:
            content = [
                turn("A", "We're about to land. Please put your seat upright.", "announce"),
                turn("B", "Like this?", "Like this?"),
                turn("A", "Yes, that's good. And fasten your seatbelt.", "yes / remind"),
                turn("B", "How long until we land?", "How long until we land?"),
                turn("A", "About fifteen minutes.", "time"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "You're welcome. Thanks for flying with us.", "response"),
            ]
            core_s = "Put your seat upright / Fasten your seatbelt / How long until...?"
            core_c = "about to land / fasten your seatbelt"
        out.append(dialogue_record(
            "transport", "airport", "flight_attendant", set_no, usage,
            f"CX-AIRPORT-FLIGHT-{did_suffix}", content, core_s, core_c,
            "出行交通", "机场", "空姐/空少"
        ))

    # ----- 出行交通：火车站 - 售票员 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Next. Where to?", "ask destination"),
                turn("B", "Shanghai, please. One ticket for today.", "Shanghai, please. One ticket for today."),
                turn("A", "Morning or afternoon?", "Morning or afternoon?"),
                turn("B", "The next available one.", "The next available one."),
                turn("A", "That's the 10:15. High-speed. Two hundred yuan.", "train / price"),
                turn("B", "Okay. Window seat if possible.", "Okay. Window seat if possible."),
                turn("A", "Here's your ticket. Platform 3. Board at 10:00.", "ticket / platform"),
                turn("B", "Thank you.", "Thank you."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Where to? / Morning or afternoon? / Window seat if possible"
            core_c = "next available / high-speed / platform"
        elif set_no == 2:
            content = [
                turn("A", "Can I help you?", "offer"),
                turn("B", "I need two tickets to Beijing for tomorrow.", "I need two tickets to Beijing for tomorrow."),
                turn("A", "We have 8 a.m. and 2 p.m. Which do you prefer?", "options"),
                turn("B", "The morning one.", "The morning one."),
                turn("A", "Four hundred and sixty yuan total.", "total price"),
                turn("B", "Do you take WeChat Pay?", "Do you take WeChat Pay?"),
                turn("A", "Yes. Scan here.", "yes / pay"),
                turn("B", "Done. Thanks.", "Done. Thanks."),
                turn("A", "No problem. Have a good trip.", "response"),
            ]
            core_s = "I need...tickets / Which do you prefer? / Do you take...?"
            core_c = "WeChat Pay / have a good trip"
        else:
            content = [
                turn("A", "Next in line. Where are you heading?", "ask"),
                turn("B", "Hangzhou. One way.", "Hangzhou. One way."),
                turn("A", "Today? We have trains every hour.", "confirm / frequency"),
                turn("B", "The one around noon.", "The one around noon."),
                turn("A", "11:42. Seventy-eight yuan.", "time / price"),
                turn("B", "That's fine. Here's eighty.", "That's fine. Here's eighty."),
                turn("A", "Two yuan change. Platform 1.", "change / platform"),
                turn("B", "Thank you.", "Thank you."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Where are you heading? / One way / The one around noon"
            core_c = "one way / change"
        out.append(dialogue_record(
            "transport", "train_station", "ticket_clerk", set_no, usage,
            f"CX-TRAIN-TICKET-{did_suffix}", content, core_s, core_c,
            "出行交通", "火车站 / 高铁站", "售票员"
        ))

    # ----- 出行交通：火车站 - 检票员 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Ticket, please.", "ask ticket"),
                turn("B", "Here.", "Here."),
                turn("A", "Platform 2. Train leaves in five minutes.", "platform / time"),
                turn("B", "Which way is platform 2?", "Which way is platform 2?"),
                turn("A", "Down the stairs, turn right.", "direction"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "Hurry. Don't miss it.", "remind"),
            ]
            core_s = "Ticket, please / Which way is...? / Don't miss it"
            core_c = "platform / down the stairs"
        elif set_no == 2:
            content = [
                turn("A", "Boarding pass and ID.", "ask"),
                turn("B", "Here you go.", "Here you go."),
                turn("A", "Car 5, Seat 12A. Go to the front of the platform.", "seat / direction"),
                turn("B", "Is this the right train for Nanjing?", "Is this the right train for Nanjing?"),
                turn("A", "Yes. Board now.", "confirm"),
                turn("B", "Thank you.", "Thank you."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Boarding pass and ID / Is this the right train for...?"
            core_c = "car / seat / board"
        else:
            content = [
                turn("A", "Tickets, please. Line up.", "instruction"),
                turn("B", "Two tickets. We're together.", "Two tickets. We're together."),
                turn("A", "Car 8. Seats 3A and 3B. That way.", "car / seats / direction"),
                turn("B", "Can we bring this bag on?", "Can we bring this bag on?"),
                turn("A", "Yes, if it fits under the seat.", "yes / condition"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "Have a good journey.", "response"),
            ]
            core_s = "Tickets, please / Can we bring...on?"
            core_c = "line up / fits under the seat"
        out.append(dialogue_record(
            "transport", "train_station", "ticket_checker", set_no, usage,
            f"CX-TRAIN-CHECKER-{did_suffix}", content, core_s, core_c,
            "出行交通", "火车站 / 高铁站", "检票员"
        ))

    # ----- 出行交通：地铁/公交 - 司机 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Step back. Doors closing.", "announce"),
                turn("B", "Does this bus go to the railway station?", "Does this bus go to the railway station?"),
                turn("A", "Yes. It's about ten stops.", "yes / how many stops"),
                turn("B", "How much is the fare?", "How much is the fare?"),
                turn("A", "Two yuan. Drop it in the box or use the card reader.", "fare / how to pay"),
                turn("B", "I'll use my card. Thanks.", "I'll use my card. Thanks."),
                turn("A", "No problem.", "response"),
            ]
            core_s = "Does this bus go to...? / How much is the fare?"
            core_c = "doors closing / card reader"
        elif set_no == 2:
            content = [
                turn("A", "Move to the rear, please. More people getting on.", "instruction"),
                turn("B", "Is the next stop the museum?", "Is the next stop the museum?"),
                turn("A", "No, one more after this.", "no / one more"),
                turn("B", "Thanks. I'll get off there.", "Thanks. I'll get off there."),
                turn("A", "Okay. Press the bell when we're close.", "remind"),
                turn("B", "Got it. Thank you.", "Got it. Thank you."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Is the next stop...? / One more after this"
            core_c = "move to the rear / press the bell"
        else:
            content = [
                turn("A", "Hold on. Sharp turn.", "warning"),
                turn("B", "Excuse me, do you stop near the airport?", "Excuse me, do you stop near the airport?"),
                turn("A", "Yes. Terminal 2 is the last stop.", "yes / last stop"),
                turn("B", "Perfect. That's where I'm going.", "Perfect. That's where I'm going."),
                turn("A", "We'll be there in about twenty minutes.", "time"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "No problem.", "response"),
            ]
            core_s = "Do you stop near...? / That's where I'm going"
            core_c = "sharp turn / terminal"
        out.append(dialogue_record(
            "transport", "bus_metro", "driver", set_no, usage,
            f"CX-BUS-DRIVER-{did_suffix}", content, core_s, core_c,
            "出行交通", "地铁 / 公交", "司机"
        ))

    # ----- 出行交通：地铁/公交 - 售票员 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Where to?", "ask"),
                turn("B", "Three tickets to Xizhimen, please.", "Three tickets to Xizhimen, please."),
                turn("A", "That's six yuan each. Eighteen total.", "price"),
                turn("B", "Here's twenty.", "Here's twenty."),
                turn("A", "Two yuan change. Here are your tickets.", "change / tickets"),
                turn("B", "Which line do we take?", "Which line do we take?"),
                turn("A", "Line 2. Down the stairs, follow the signs.", "line / direction"),
                turn("B", "Thank you.", "Thank you."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Where to? / Which line do we take?"
            core_c = "down the stairs / follow the signs"
        elif set_no == 2:
            content = [
                turn("A", "Need a recharge? Your card balance is low.", "remind"),
                turn("B", "Yes. Add fifty yuan, please.", "Yes. Add fifty yuan, please."),
                turn("A", "Done. Your new balance is sixty-two.", "done / balance"),
                turn("B", "Can I use this for the bus too?", "Can I use this for the bus too?"),
                turn("A", "Yes. Same card for metro and bus.", "yes"),
                turn("B", "Great. Thanks.", "Great. Thanks."),
                turn("A", "No problem.", "response"),
            ]
            core_s = "Add fifty yuan / Can I use this for...too?"
            core_c = "recharge / balance"
        else:
            content = [
                turn("A", "Single trip or day pass?", "ask"),
                turn("B", "Day pass. How much?", "Day pass. How much?"),
                turn("A", "Twenty yuan. Unlimited rides today.", "price / unlimited"),
                turn("B", "I'll take one. Here's twenty.", "I'll take one. Here's twenty."),
                turn("A", "Here's your pass. Tap at the gate.", "pass / instruction"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Single trip or day pass? / How much?"
            core_c = "day pass / unlimited rides / tap at the gate"
        out.append(dialogue_record(
            "transport", "bus_metro", "conductor", set_no, usage,
            f"CX-BUS-CONDUCTOR-{did_suffix}", content, core_s, core_c,
            "出行交通", "地铁 / 公交", "售票员"
        ))

    # ----- 出行交通：出租车/网约车 - 司机 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Where to?", "ask"),
                turn("B", "The airport, please. Terminal 2.", "The airport, please. Terminal 2."),
                turn("A", "Got it. About forty minutes in this traffic.", "confirm / time"),
                turn("B", "That's fine. How much will it be?", "That's fine. How much will it be?"),
                turn("A", "Around eighty yuan by meter.", "around / meter"),
                turn("B", "Can I pay by phone?", "Can I pay by phone?"),
                turn("A", "Yes. WeChat or Alipay both work.", "yes"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "No problem.", "response"),
            ]
            core_s = "Where to? / How much will it be? / Can I pay by phone?"
            core_c = "by meter / WeChat or Alipay"
        elif set_no == 2:
            content = [
                turn("A", "Hi. You ordered a car to 123 Main Street?", "confirm"),
                turn("B", "Yes, that's me.", "Yes, that's me."),
                turn("A", "Hop in. I'll put the AC on.", "invite / service"),
                turn("B", "Could you take the highway? I'm in a hurry.", "Could you take the highway? I'm in a hurry."),
                turn("A", "Sure. There might be a toll. About ten yuan.", "sure / toll"),
                turn("B", "That's okay. Thanks.", "That's okay. Thanks."),
                turn("A", "No problem.", "response"),
            ]
            core_s = "You ordered a car to...? / Could you take the highway?"
            core_c = "hop in / in a hurry / toll"
        else:
            content = [
                turn("A", "Hello. Going to the train station?", "confirm"),
                turn("B", "Yes. My train is at 3. Is that enough time?", "Yes. My train is at 3. Is that enough time?"),
                turn("A", "Yeah, we'll be there in twenty minutes.", "yes / time"),
                turn("B", "Great. Please drop me at the south entrance.", "Great. Please drop me at the south entrance."),
                turn("A", "South entrance. No problem.", "repeat"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "You're welcome. Have a good trip.", "response"),
            ]
            core_s = "Is that enough time? / Please drop me at..."
            core_c = "south entrance / have a good trip"
        out.append(dialogue_record(
            "transport", "taxi", "taxi_driver", set_no, usage,
            f"CX-TAXI-DRIVER-{did_suffix}", content, core_s, core_c,
            "出行交通", "出租车 / 网约车", "司机"
        ))

    # ----- 出行交通：酒店 - 前台 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Good evening. Do you have a reservation?", "greeting"),
                turn("B", "Yes. The name is Wang.", "Yes. The name is Wang."),
                turn("A", "Let me check. Yes, a double room for two nights.", "confirm"),
                turn("B", "That's right. Is breakfast included?", "That's right. Is breakfast included?"),
                turn("A", "Yes. It's from 7 to 10 in the lobby.", "yes / time and place"),
                turn("B", "What time is check-out?", "What time is check-out?"),
                turn("A", "12 noon. Here's your key. Room 508. Elevator on your left.", "time / key / direction"),
                turn("B", "Thank you.", "Thank you."),
                turn("A", "You're welcome. Enjoy your stay.", "response"),
            ]
            core_s = "Do you have a reservation? / Is breakfast included? / What time is check-out?"
            core_c = "double room / check-out / elevator"
        elif set_no == 2:
            content = [
                turn("A", "Hi. How can I help you?", "offer"),
                turn("B", "I'd like to book a room for tonight.", "I'd like to book a room for tonight."),
                turn("A", "We have standard and deluxe. Deluxe has a city view.", "options"),
                turn("B", "Standard is fine. How much?", "Standard is fine. How much?"),
                turn("A", "Three hundred and fifty yuan per night.", "price"),
                turn("B", "Okay. I'll take it.", "Okay. I'll take it."),
                turn("A", "ID, please. I'll need a deposit of two hundred.", "ID / deposit"),
                turn("B", "Here. Can I pay by card?", "Here. Can I pay by card?"),
                turn("A", "Yes. Here's your receipt. Room 312.", "yes / receipt"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "I'd like to book.../ How much? / Can I pay by card?"
            core_c = "standard and deluxe / deposit / receipt"
        else:
            content = [
                turn("A", "Checking out? Room number?", "ask"),
                turn("B", "508. Here's my key.", "508. Here's my key."),
                turn("A", "One moment. Your total is seven hundred yuan.", "total"),
                turn("B", "Can I get an invoice?", "Can I get an invoice?"),
                turn("A", "Sure. Company name?", "sure / ask"),
                turn("B", "ABC Company. Tax ID on file.", "ABC Company. Tax ID on file."),
                turn("A", "Here you go. Thank you for staying with us.", "hand / thank"),
                turn("B", "Thank you. Goodbye.", "Thank you. Goodbye."),
                turn("A", "Goodbye. Safe travels.", "response"),
            ]
            core_s = "Checking out? / Can I get an invoice?"
            core_c = "invoice / tax ID / on file"
        out.append(dialogue_record(
            "transport", "hotel", "hotel_reception", set_no, usage,
            f"CX-HOTEL-RECEPTION-{did_suffix}", content, core_s, core_c,
            "出行交通", "酒店", "前台"
        ))

    # ----- 出行交通：酒店 - 客房服务 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Housekeeping. May I come in?", "announce"),
                turn("B", "Yes, come in. Could I get some extra towels?", "Yes, come in. Could I get some extra towels?"),
                turn("A", "Of course. How many would you like?", "of course / ask"),
                turn("B", "Two, please.", "Two, please."),
                turn("A", "I'll bring them right up. Anything else?", "confirm / offer"),
                turn("B", "No, that's all. Thank you.", "No, that's all. Thank you."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "May I come in? / Could I get...? / Anything else?"
            core_c = "housekeeping / extra towels"
        elif set_no == 2:
            content = [
                turn("A", "Room service. Your order is here.", "deliver"),
                turn("B", "Thanks. Just put it on the table.", "Thanks. Just put it on the table."),
                turn("A", "Sure. Would you like me to open the curtains?", "sure / offer"),
                turn("B", "Yes, please. And can I have a late check-out?", "Yes, please. And can I have a late check-out?"),
                turn("A", "I'll check with the front desk. Usually until 2 p.m.", "check / usually"),
                turn("B", "Okay. Thanks.", "Okay. Thanks."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Just put it on.../ Can I have a late check-out?"
            core_c = "room service / late check-out"
        else:
            content = [
                turn("A", "Hi. You called for an extra pillow?", "confirm"),
                turn("B", "Yes. And do you have an iron?", "Yes. And do you have an iron?"),
                turn("A", "Yes. I'll bring both. One moment.", "yes / both"),
                turn("B", "Thank you. What's the WiFi password?", "Thank you. What's the WiFi password?"),
                turn("A", "It's on the desk. Room number and 'guest'.", "location / hint"),
                turn("B", "Got it. Thanks.", "Got it. Thanks."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Do you have an iron? / What's the WiFi password?"
            core_c = "extra pillow / WiFi password"
        out.append(dialogue_record(
            "transport", "hotel", "housekeeping", set_no, usage,
            f"CX-HOTEL-HOUSE-{did_suffix}", content, core_s, core_c,
            "出行交通", "酒店", "客房服务"
        ))

    # ----- 出行交通：酒店 - 保洁 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Good morning. Cleaning. Is now a good time?", "ask"),
                turn("B", "Could you come back in half an hour?", "Could you come back in half an hour?"),
                turn("A", "Sure. I'll come back at 10.", "sure / time"),
                turn("B", "Thanks. I'm in a meeting.", "Thanks. I'm in a meeting."),
                turn("A", "No problem. See you then.", "no problem"),
            ]
            core_s = "Is now a good time? / Could you come back in...?"
            core_c = "cleaning / come back"
        elif set_no == 2:
            content = [
                turn("A", "Housekeeping. May I clean your room?", "ask"),
                turn("B", "Yes. The bathroom needs more soap.", "Yes. The bathroom needs more soap."),
                turn("A", "I'll leave some. Do you need new sheets?", "confirm / offer"),
                turn("B", "No, the bed is fine. Thanks.", "No, the bed is fine. Thanks."),
                turn("A", "You're welcome. Have a good day.", "response"),
            ]
            core_s = "May I clean your room? / The bathroom needs..."
            core_c = "new sheets"
        else:
            content = [
                turn("A", "Hi. I'm here to change the towels.", "purpose"),
                turn("B", "Come in. I'm leaving in a few minutes.", "Come in. I'm leaving in a few minutes."),
                turn("A", "I'll be quick. Trash too?", "quick / offer"),
                turn("B", "Yes, please. Thank you.", "Yes, please. Thank you."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "I'm here to.../ I'll be quick"
            core_c = "change the towels"
        out.append(dialogue_record(
            "transport", "hotel", "cleaning", set_no, usage,
            f"CX-HOTEL-CLEAN-{did_suffix}", content, core_s, core_c,
            "出行交通", "酒店", "保洁"
        ))

    # ----- 购物消费：超市/便利店 - 收银员 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Next, please. Did you find everything?", "greeting"),
                turn("B", "Yes. How much is it?", "Yes. How much is it?"),
                turn("A", "Eighty-five yuan. Card or cash?", "total / pay method"),
                turn("B", "Card, please.", "Card, please."),
                turn("A", "Tap or insert. Thank you. Receipt?", "instruction / receipt"),
                turn("B", "No, thanks. Have a good day.", "No, thanks. Have a good day."),
                turn("A", "You too. Bye.", "response"),
            ]
            core_s = "Did you find everything? / How much is it? / Card or cash?"
            core_c = "tap or insert / receipt"
        elif set_no == 2:
            content = [
                turn("A", "That'll be forty-two fifty.", "total"),
                turn("B", "Do you have a bag?", "Do you have a bag?"),
                turn("A", "Yes. Small or large? Five jiao for large.", "options / price"),
                turn("B", "One large, please.", "One large, please."),
                turn("A", "Forty-three yuan total. Pay here.", "total / pay"),
                turn("B", "Here you go.", "Here you go."),
                turn("A", "Thanks. Next!", "thanks"),
            ]
            core_s = "Do you have a bag? / Small or large?"
            core_c = "five jiao / pay here"
        else:
            content = [
                turn("A", "Hi. Cash or mobile?", "ask"),
                turn("B", "WeChat. Is there a discount today?", "WeChat. Is there a discount today?"),
                turn("A", "Members get 10% off. Do you have a membership card?", "discount / member"),
                turn("B", "No. Just today's total.", "No. Just today's total."),
                turn("A", "Seventy-six yuan. Scan here.", "total / scan"),
                turn("B", "Done. Thanks.", "Done. Thanks."),
                turn("A", "Thank you. Bye.", "response"),
            ]
            core_s = "Is there a discount today? / Do you have a membership card?"
            core_c = "members get 10% off / scan here"
        out.append(dialogue_record(
            "shopping", "supermarket", "cashier", set_no, usage,
            f"GW-SUPER-CASHIER-{did_suffix}", content, core_s, core_c,
            "购物消费", "超市 / 便利店", "收银员"
        ))

    # ----- 购物消费：超市/便利店 - 导购员 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Hi. Looking for something?", "offer"),
                turn("B", "Where is the milk?", "Where is the milk?"),
                turn("A", "Dairy is in the back, on the left.", "location"),
                turn("B", "Do you have oat milk?", "Do you have oat milk?"),
                turn("A", "Yes. Same aisle, top shelf.", "yes / where"),
                turn("B", "Thanks a lot.", "Thanks a lot."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Where is...? / Do you have...?"
            core_c = "dairy / aisle / top shelf"
        elif set_no == 2:
            content = [
                turn("A", "Can I help you find anything?", "offer"),
                turn("B", "I'm looking for soy sauce.", "I'm looking for soy sauce."),
                turn("A", "That's in Aisle 7. Seasonings.", "aisle / section"),
                turn("B", "Which brand do you recommend?", "Which brand do you recommend?"),
                turn("A", "The one on sale is good. Yellow label.", "recommend"),
                turn("B", "Okay. I'll try it. Thanks.", "Okay. I'll try it. Thanks."),
                turn("A", "No problem.", "response"),
            ]
            core_s = "I'm looking for.../ Which brand do you recommend?"
            core_c = "on sale / yellow label"
        else:
            content = [
                turn("A", "Need any help?", "offer"),
                turn("B", "Where are the frozen dumplings?", "Where are the frozen dumplings?"),
                turn("A", "Freezer section. Straight ahead, then right.", "direction"),
                turn("B", "Are they on special today?", "Are they on special today?"),
                turn("A", "Yes. Buy two get one free.", "yes / promotion"),
                turn("B", "Great. Thank you.", "Great. Thank you."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Where are...? / Are they on special today?"
            core_c = "freezer section / buy two get one free"
        out.append(dialogue_record(
            "shopping", "supermarket", "guide", set_no, usage,
            f"GW-SUPER-GUIDE-{did_suffix}", content, core_s, core_c,
            "购物消费", "超市 / 便利店", "导购员"
        ))

    # ----- 购物消费：商场/服装店 - 店员 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Hi. Can I help you?", "greeting"),
                turn("B", "I'm just looking. Do you have this in blue?", "I'm just looking. Do you have this in blue?"),
                turn("A", "Yes. What size?", "yes / size"),
                turn("B", "Medium.", "Medium."),
                turn("A", "Here you go. The fitting room is over there.", "hand / fitting room"),
                turn("B", "Can I try it on?", "Can I try it on?"),
                turn("A", "Sure. Let me know if you need another size.", "sure / offer"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Do you have this in blue? / Can I try it on?"
            core_c = "just looking / fitting room"
        elif set_no == 2:
            content = [
                turn("A", "Welcome. Looking for something special?", "welcome"),
                turn("B", "A gift for my mom. She likes scarves.", "A gift for my mom. She likes scarves."),
                turn("A", "We have some new ones. This silk one is popular.", "suggest"),
                turn("B", "How much is it?", "How much is it?"),
                turn("A", "Two hundred and ninety yuan. We can gift-wrap for free.", "price / service"),
                turn("B", "I'll take it. Can I get a receipt?", "I'll take it. Can I get a receipt?"),
                turn("A", "Sure. Pay at the counter. Thank you.", "sure / thank"),
                turn("B", "Thank you.", "Thank you."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "A gift for.../ How much is it? / Can I get a receipt?"
            core_c = "gift-wrap / pay at the counter"
        else:
            content = [
                turn("A", "Hi. Need a size?", "offer"),
                turn("B", "Yes. This jacket in large?", "Yes. This jacket in large?"),
                turn("A", "Let me check. Yes, we have one left.", "check / stock"),
                turn("B", "Is it on sale?", "Is it on sale?"),
                turn("A", "Yes. 20% off. Four hundred yuan now.", "yes / discount"),
                turn("B", "I'll try it. Where's the fitting room?", "I'll try it. Where's the fitting room?"),
                turn("A", "Behind you. I'll hold it at the counter.", "direction / hold"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "No problem.", "response"),
            ]
            core_s = "This jacket in large? / Is it on sale?"
            core_c = "20% off / hold it at the counter"
        out.append(dialogue_record(
            "shopping", "mall", "shop_staff", set_no, usage,
            f"GW-MALL-STAFF-{did_suffix}", content, core_s, core_c,
            "购物消费", "商场 / 服装店", "店员"
        ))

    # ----- 购物消费：商场/服装店 - 导购 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Hi. What style are you looking for?", "ask"),
                turn("B", "Something casual for work.", "Something casual for work."),
                turn("A", "These shirts are popular. Cotton and easy to wash.", "recommend"),
                turn("B", "Do you have them in light blue?", "Do you have them in light blue?"),
                turn("A", "Yes. Here. Size M or L?", "yes / size"),
                turn("B", "M. How much?", "M. How much?"),
                turn("A", "One ninety-nine. Want to try?", "price / try"),
                turn("B", "Yes, please. Thanks.", "Yes, please. Thanks."),
                turn("A", "Fitting room this way.", "direction"),
            ]
            core_s = "What style are you looking for? / Do you have them in...?"
            core_c = "casual / easy to wash"
        elif set_no == 2:
            content = [
                turn("A", "That looks good on you.", "compliment"),
                turn("B", "Really? Is it too tight?", "Really? Is it too tight?"),
                turn("A", "No. The fit is right. We have it in black too.", "no / suggest"),
                turn("B", "I'll stick with this color. I'll take it.", "I'll stick with this color. I'll take it."),
                turn("A", "Great. I'll ring it up at the counter.", "confirm"),
                turn("B", "Thanks for your help.", "Thanks for your help."),
                turn("A", "You're welcome. Come again.", "response"),
            ]
            core_s = "Is it too tight? / I'll take it"
            core_c = "the fit is right / ring it up"
        else:
            content = [
                turn("A", "Looking for shoes? We have a new range.", "offer"),
                turn("B", "I need something comfortable for walking.", "I need something comfortable for walking."),
                turn("A", "These have good support. Try this pair.", "recommend"),
                turn("B", "What size is this?", "What size is this?"),
                turn("A", "Forty-two. Let me get you the other foot.", "size / service"),
                turn("B", "They feel good. I'll take them.", "They feel good. I'll take them."),
                turn("A", "Good choice. Pay over there.", "confirm / pay"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "I need something comfortable / What size is this?"
            core_c = "good support / the other foot"
        out.append(dialogue_record(
            "shopping", "mall", "mall_guide", set_no, usage,
            f"GW-MALL-GUIDE-{did_suffix}", content, core_s, core_c,
            "购物消费", "商场 / 服装店", "导购"
        ))

    # ----- 购物消费：理发店 - 理发师 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Hi. How would you like it today?", "ask"),
                turn("B", "Just a trim. Keep the length.", "Just a trim. Keep the length."),
                turn("A", "Same style? Any thinning on the sides?", "confirm / suggest"),
                turn("B", "A little shorter on the sides, please.", "A little shorter on the sides, please."),
                turn("A", "Got it. Shampoo first?", "got it / shampoo"),
                turn("B", "Yes, please.", "Yes, please."),
                turn("A", "Lean back. Comfortable?", "instruction / comfortable"),
                turn("B", "Yes. Thanks.", "Yes. Thanks."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "How would you like it today? / Just a trim / A little shorter on the sides"
            core_c = "keep the length / shampoo first"
        elif set_no == 2:
            content = [
                turn("A", "Next. What can I do for you?", "offer"),
                turn("B", "I want a new look. Maybe layers?", "I want a new look. Maybe layers?"),
                turn("A", "Layers would suit you. Shoulder length or shorter?", "agree / option"),
                turn("B", "Shoulder length. And some bangs?", "Shoulder length. And some bangs?"),
                turn("A", "Sure. We can do that. Sit here.", "sure / sit"),
                turn("B", "How long will it take?", "How long will it take?"),
                turn("A", "About forty minutes. Relax.", "time / relax"),
                turn("B", "Okay. Thanks.", "Okay. Thanks."),
                turn("A", "No problem.", "response"),
            ]
            core_s = "I want a new look / Maybe layers? / How long will it take?"
            core_c = "layers / shoulder length / bangs"
        else:
            content = [
                turn("A", "Hi. Trim or full cut?", "ask"),
                turn("B", "Full cut. And a wash.", "Full cut. And a wash."),
                turn("A", "Any product? Gel or wax?", "product"),
                turn("B", "Just a little wax. Nothing too heavy.", "Just a little wax. Nothing too heavy."),
                turn("A", "Got it. Thirty yuan for the cut, fifteen for the wash.", "price"),
                turn("B", "That's fine. Go ahead.", "That's fine. Go ahead."),
                turn("A", "Thanks. I'll start.", "thanks"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Trim or full cut? / Just a little wax"
            core_c = "gel or wax / nothing too heavy"
        out.append(dialogue_record(
            "shopping", "barber", "barber_staff", set_no, usage,
            f"GW-BARBER-STAFF-{did_suffix}", content, core_s, core_c,
            "购物消费", "理发店", "理发师"
        ))

    # ----- 购物消费：理发店 - 前台 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Hi. Do you have an appointment?", "ask"),
                turn("B", "No. Is there a free slot now?", "No. Is there a free slot now?"),
                turn("A", "We have one in twenty minutes. Or you can wait.", "option"),
                turn("B", "I'll wait. How much for a cut?", "I'll wait. How much for a cut?"),
                turn("A", "Forty for men, fifty for women. Wash is extra.", "price"),
                turn("B", "Men's cut, please. No wash.", "Men's cut, please. No wash."),
                turn("A", "Okay. Take a seat. We'll call you.", "okay / wait"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Do you have an appointment? / Is there a free slot now?"
            core_c = "free slot / wash is extra"
        elif set_no == 2:
            content = [
                turn("A", "Next, please. Name?", "call / ask"),
                turn("B", "Wang. I had a 3 o'clock.", "Wang. I had a 3 o'clock."),
                turn("A", "Yes. Mr. Wang. Please go to Chair 2. Tony will help you.", "confirm / assign"),
                turn("B", "Thanks. Do you take cards?", "Thanks. Do you take cards?"),
                turn("A", "Yes. You pay when you're done.", "yes / when"),
                turn("B", "Okay. Thank you.", "Okay. Thank you."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "I had a 3 o'clock / Do you take cards?"
            core_c = "chair 2 / pay when you're done"
        else:
            content = [
                turn("A", "Hi. Would you like to book for next time?", "offer"),
                turn("B", "Yes. Same time next week?", "Yes. Same time next week?"),
                turn("A", "Let me check. Tuesday at 3? We have that.", "check / confirm"),
                turn("B", "Perfect. Under Wang.", "Perfect. Under Wang."),
                turn("A", "Done. We'll send a reminder.", "done / reminder"),
                turn("B", "Great. Thanks.", "Great. Thanks."),
                turn("A", "You're welcome. See you next week.", "response"),
            ]
            core_s = "Would you like to book for next time? / Same time next week?"
            core_c = "under Wang / send a reminder"
        out.append(dialogue_record(
            "shopping", "barber", "barber_front", set_no, usage,
            f"GW-BARBER-FRONT-{did_suffix}", content, core_s, core_c,
            "购物消费", "理发店", "前台"
        ))

    # ----- 购物消费：电影院 - 售票员 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Hi. Which movie?", "ask"),
                turn("B", "The new action one. Two tickets for the 7 o'clock show.", "The new action one. Two tickets for the 7 o'clock show."),
                turn("A", "We have front, middle, or back. Middle?", "seats"),
                turn("B", "Middle, please. How much?", "Middle, please. How much?"),
                turn("A", "Sixty each. One hundred twenty total.", "price"),
                turn("B", "Do you have student discount?", "Do you have student discount?"),
                turn("A", "Yes. Student ID? Fifty each.", "yes / student"),
                turn("B", "Here. So one hundred.", "Here. So one hundred."),
                turn("A", "Right. Here are your tickets. Screen 3.", "confirm / screen"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "You're welcome. Enjoy the movie.", "response"),
            ]
            core_s = "Which movie? / Do you have student discount?"
            core_c = "front middle back / screen"
        elif set_no == 2:
            content = [
                turn("A", "Next. What can I get you?", "offer"),
                turn("B", "One for the 9 p.m. show. Comedy.", "One for the 9 p.m. show. Comedy."),
                turn("A", "We have seats left in the back row.", "seats"),
                turn("B", "That's fine. And a large popcorn and two drinks.", "That's fine. And a large popcorn and two drinks."),
                turn("A", "Eighty for the ticket, forty for the combo. One twenty.", "price"),
                turn("B", "Here's one fifty.", "Here's one fifty."),
                turn("A", "Thirty change. Screen 1. Enjoy.", "change / enjoy"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "One for the 9 p.m. show / And a large popcorn"
            core_c = "back row / combo"
        else:
            content = [
                turn("A", "Hi. Booking or walk-in?", "ask"),
                turn("B", "Walk-in. What's showing soon?", "Walk-in. What's showing soon?"),
                turn("A", "Next one is in 15 minutes. Romance. Screen 2.", "next / screen"),
                turn("B", "One ticket. Center seat if possible.", "One ticket. Center seat if possible."),
                turn("A", "We have Row 8, Seat 10. Good view.", "seat / view"),
                turn("B", "Perfect. How much?", "Perfect. How much?"),
                turn("A", "Fifty-five. Pay here.", "price"),
                turn("B", "Done. Thanks.", "Done. Thanks."),
                turn("A", "Thank you. Enjoy.", "response"),
            ]
            core_s = "What's showing soon? / Center seat if possible"
            core_c = "walk-in / good view"
        out.append(dialogue_record(
            "shopping", "cinema", "cinema_clerk", set_no, usage,
            f"GW-CINEMA-CLERK-{did_suffix}", content, core_s, core_c,
            "购物消费", "电影院", "售票员"
        ))

    # ----- 购物消费：电影院 - 检票员 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Ticket, please. Screen 3 is to your left.", "ask / direction"),
                turn("B", "Here. Is it okay to bring this in?", "Here. Is it okay to bring this in?"),
                turn("A", "No outside food. We have snacks inside.", "rule"),
                turn("B", "Okay. Thanks.", "Okay. Thanks."),
                turn("A", "Enjoy the movie.", "response"),
            ]
            core_s = "Is it okay to bring this in?"
            core_c = "no outside food / snacks inside"
        elif set_no == 2:
            content = [
                turn("A", "Tickets. The show starts in five minutes.", "ask / time"),
                turn("B", "Two tickets. Row 5.", "Two tickets. Row 5."),
                turn("A", "Go straight. Row 5 is in the middle.", "direction"),
                turn("B", "Thanks. Where are the restrooms?", "Thanks. Where are the restrooms?"),
                turn("A", "Down the hall, on the right. Hurry back.", "location"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "Where are the restrooms?"
            core_c = "go straight / down the hall"
        else:
            content = [
                turn("A", "Ticket? Screen 1, straight ahead.", "ask / direction"),
                turn("B", "Can we go in now? The ads are on.", "Can we go in now? The ads are on."),
                turn("A", "Yes. Find your seat. Movie starts in ten.", "yes / remind"),
                turn("B", "Thanks.", "Thanks."),
                turn("A", "Enjoy.", "response"),
            ]
            core_s = "Can we go in now?"
            core_c = "ads are on"
        out.append(dialogue_record(
            "shopping", "cinema", "cinema_checker", set_no, usage,
            f"GW-CINEMA-CHECKER-{did_suffix}", content, core_s, core_c,
            "购物消费", "电影院", "检票员"
        ))

    # ----- 工作职场：办公室 - 领导 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Do you have a minute? I need to talk about the project.", "request"),
                turn("B", "Sure. What's up?", "Sure. What's up?"),
                turn("A", "The deadline is tight. Can you finish the report by Friday?", "situation / ask"),
                turn("B", "I'll try. I might need help with the data.", "I'll try. I might need help with the data."),
                turn("A", "Talk to Li. She can share the numbers. Any other issues?", "suggest / ask"),
                turn("B", "No. I'll get it done. Thanks.", "No. I'll get it done. Thanks."),
                turn("A", "Good. Let me know if you need anything.", "close"),
            ]
            core_s = "Do you have a minute? / Can you finish...by Friday?"
            core_c = "deadline is tight / let me know"
        elif set_no == 2:
            content = [
                turn("A", "Good job on the presentation. The client liked it.", "praise"),
                turn("B", "Thank you. The team helped a lot.", "Thank you. The team helped a lot."),
                turn("A", "We have a follow-up meeting next week. Can you prepare the slides?", "next step / ask"),
                turn("B", "Yes. When is it?", "Yes. When is it?"),
                turn("A", "Wednesday at 2. Send me a draft by Monday.", "time / deadline"),
                turn("B", "Okay. I'll do that. Thanks.", "Okay. I'll do that. Thanks."),
                turn("A", "Thanks. Keep it up.", "close"),
            ]
            core_s = "Good job on.../ Can you prepare...?"
            core_c = "follow-up meeting / send me a draft"
        else:
            content = [
                turn("A", "I need the sales figures by end of day. Is that possible?", "request"),
                turn("B", "I'm on it. I'll email them by 5.", "I'm on it. I'll email them by 5."),
                turn("A", "Great. And please copy the director.", "great / add"),
                turn("B", "Will do. Anything else?", "Will do. Anything else?"),
                turn("A", "No, that's all. Thanks.", "no / thanks"),
                turn("B", "You're welcome.", "You're welcome."),
                turn("A", "Okay.", "close"),
            ]
            core_s = "I need...by end of day / Is that possible?"
            core_c = "I'm on it / copy the director"
        out.append(dialogue_record(
            "work", "office", "boss", set_no, usage,
            f"GZ-OFFICE-BOSS-{did_suffix}", content, core_s, core_c,
            "工作职场", "办公室", "领导"
        ))

    # ----- 工作职场：办公室 - 同事 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Hey. Are you free for lunch? A few of us are going out.", "invite"),
                turn("B", "Sure. What time?", "Sure. What time?"),
                turn("A", "Around 12. The usual place.", "time / place"),
                turn("B", "Sounds good. I'll finish this email first.", "Sounds good. I'll finish this email first."),
                turn("A", "No rush. See you then.", "no rush"),
                turn("B", "See you.", "See you."),
                turn("A", "Bye.", "bye"),
            ]
            core_s = "Are you free for lunch? / What time?"
            core_c = "the usual place / no rush"
        elif set_no == 2:
            content = [
                turn("A", "Hi. Do you have the file from the meeting?", "ask"),
                turn("B", "Which one? Yesterday's or this morning's?", "Which one? Yesterday's or this morning's?"),
                turn("A", "This morning. The budget sheet.", "specify"),
                turn("B", "I'll send it to you. One sec.", "I'll send it to you. One sec."),
                turn("A", "Thanks. I need it for the report.", "thanks / reason"),
                turn("B", "Done. Check your inbox.", "Done. Check your inbox."),
                turn("A", "Got it. Thanks again.", "got it"),
            ]
            core_s = "Do you have the file...? / Which one?"
            core_c = "budget sheet / check your inbox"
        else:
            content = [
                turn("A", "Coffee run? I'm going to the café.", "offer"),
                turn("B", "Yes, please. Latte, medium. Here's the money.", "Yes, please. Latte, medium. Here's the money."),
                turn("A", "Keep it. My treat today.", "refuse / treat"),
                turn("B", "Really? Thanks! Next time it's on me.", "Really? Thanks! Next time it's on me."),
                turn("A", "Deal. Back in ten.", "deal / time"),
                turn("B", "Okay. Thanks.", "Okay. Thanks."),
                turn("A", "No problem.", "response"),
            ]
            core_s = "Coffee run? / Next time it's on me"
            core_c = "my treat / back in ten"
        out.append(dialogue_record(
            "work", "office", "colleague", set_no, usage,
            f"GZ-OFFICE-COLLEAGUE-{did_suffix}", content, core_s, core_c,
            "工作职场", "办公室", "同事"
        ))

    # ----- 工作职场：办公室 - 下属 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Hi. I've finished the draft. Can you take a look?", "submit / ask"),
                turn("B", "Sure. Send it over. When do you need feedback?", "Sure. Send it over. When do you need feedback?"),
                turn("A", "By tomorrow morning if possible. The meeting is at 10.", "deadline / reason"),
                turn("B", "I'll read it tonight. Any specific part to focus on?", "I'll read it tonight. Any specific part to focus on?"),
                turn("A", "The conclusion. I'm not sure if it's strong enough.", "focus / worry"),
                turn("B", "Okay. I'll give you notes by 9. Sound good?", "okay / confirm"),
                turn("A", "Perfect. Thank you.", "Perfect. Thank you."),
                turn("B", "You're welcome.", "response"),
            ]
            core_s = "I've finished...Can you take a look? / When do you need feedback?"
            core_c = "send it over / sound good"
        elif set_no == 2:
            content = [
                turn("A", "I'm stuck on this part. Can you help?", "ask help"),
                turn("B", "Of course. What's the problem?", "Of course. What's the problem?"),
                turn("A", "The numbers don't match. I've checked twice.", "explain"),
                turn("B", "Let me see. Maybe the source file was updated.", "suggest"),
                turn("A", "I'll check. Thanks for the tip.", "I'll check. Thanks for the tip."),
                turn("B", "No problem. Come back if you're still stuck.", "no problem / offer"),
                turn("A", "I will. Thanks.", "I will. Thanks."),
                turn("B", "You're welcome.", "response"),
            ]
            core_s = "I'm stuck on...Can you help? / What's the problem?"
            core_c = "the numbers don't match / come back if"
        else:
            content = [
                turn("A", "I need to leave early today. Is that okay?", "request"),
                turn("B", "What time? We have the call at 4.", "What time? We have the call at 4."),
                turn("A", "I can stay for the call. I'll leave right after.", "I can stay for the call. I'll leave right after."),
                turn("B", "That's fine. Just send me the minutes.", "approve / ask"),
                turn("A", "I will. Thanks for understanding.", "I will. Thanks for understanding."),
                turn("B", "No problem. See you tomorrow.", "no problem"),
                turn("A", "See you.", "see you"),
            ]
            core_s = "I need to leave early / Is that okay?"
            core_c = "stay for the call / send me the minutes"
        out.append(dialogue_record(
            "work", "office", "subordinate", set_no, usage,
            f"GZ-OFFICE-SUB-{did_suffix}", content, core_s, core_c,
            "工作职场", "办公室", "下属"
        ))

    # ----- 工作职场：面试 - 面试官 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Good morning. Please have a seat. Tell me about yourself.", "greeting / ask"),
                turn("B", "I'm a recent graduate. I studied marketing. I've done two internships.", "I'm a recent graduate. I studied marketing. I've done two internships."),
                turn("A", "Why do you want to work here?", "why"),
                turn("B", "I like your products and company culture. I want to grow with the team.", "I like your products and company culture. I want to grow with the team."),
                turn("A", "What's your biggest strength?", "What's your biggest strength?"),
                turn("B", "I'm a quick learner and I work well with others.", "I'm a quick learner and I work well with others."),
                turn("A", "When can you start?", "When can you start?"),
                turn("B", "I can start next month. I need to give two weeks' notice.", "I can start next month. I need to give two weeks' notice."),
                turn("A", "We'll be in touch. Thank you for coming.", "close"),
                turn("B", "Thank you for your time.", "Thank you for your time."),
            ]
            core_s = "Tell me about yourself / Why do you want to work here? / When can you start?"
            core_c = "company culture / quick learner / give notice"
        elif set_no == 2:
            content = [
                turn("A", "Hi. Thanks for coming. How did you hear about us?", "ask"),
                turn("B", "Through your website. I've been following your company for a while.", "Through your website. I've been following your company for a while."),
                turn("A", "Describe a challenge you faced at work.", "Describe a challenge you faced at work."),
                turn("B", "We had a tight deadline. I organized the team and we delivered on time.", "We had a tight deadline. I organized the team and we delivered on time."),
                turn("A", "Where do you see yourself in five years?", "Where do you see yourself in five years?"),
                turn("B", "I hope to be a team lead and contribute to bigger projects.", "I hope to be a team lead and contribute to bigger projects."),
                turn("A", "Do you have any questions for us?", "Do you have any questions for us?"),
                turn("B", "Yes. What does a typical day look like in this role?", "Yes. What does a typical day look like in this role?"),
                turn("A", "Good question. I'll explain. We'll call you next week.", "answer / close"),
                turn("B", "Thank you. I look forward to hearing from you.", "Thank you. I look forward to hearing from you."),
            ]
            core_s = "Describe a challenge.../ Where do you see yourself...? / Do you have any questions?"
            core_c = "tight deadline / typical day"
        else:
            content = [
                turn("A", "Sit down, please. Your résumé says you speak English. How fluent?", "ask"),
                turn("B", "I can handle meetings and emails. I've used it in my last job.", "I can handle meetings and emails. I've used it in my last job."),
                turn("A", "What salary are you expecting?", "What salary are you expecting?"),
                turn("B", "I'm open. Based on the role and the market.", "I'm open. Based on the role and the market."),
                turn("A", "We offer benefits and annual leave. Anything else to add?", "we offer / ask"),
                turn("B", "No. I'm excited about this opportunity. Thank you.", "No. I'm excited about this opportunity. Thank you."),
                turn("A", "Thanks for your time. We'll get back to you soon.", "close"),
                turn("B", "Thank you. Goodbye.", "Thank you. Goodbye."),
            ]
            core_s = "How fluent? / What salary are you expecting?"
            core_c = "I'm open / get back to you"
        out.append(dialogue_record(
            "work", "interview", "interviewer", set_no, usage,
            f"GZ-INTERVIEW-INTER-{did_suffix}", content, core_s, core_c,
            "工作职场", "面试", "面试官"
        ))

    # ----- 工作职场：会议/接待 - 客户 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Welcome. Thanks for coming. Can I get you some water or tea?", "welcome / offer"),
                turn("B", "Tea, please. Green tea if you have it.", "Tea, please. Green tea if you have it."),
                turn("A", "Sure. Let's start. You've seen the proposal?", "sure / start"),
                turn("B", "Yes. We have a few questions about the timeline.", "Yes. We have a few questions about the timeline."),
                turn("A", "Go ahead. We're flexible on the first phase.", "go ahead / flexible"),
                turn("B", "Good. And what about the budget?", "Good. And what about the budget?"),
                turn("A", "We can send a detailed breakdown by Friday.", "offer"),
                turn("B", "That would be great. Thank you.", "That would be great. Thank you."),
                turn("A", "You're welcome. Let's keep in touch.", "close"),
            ]
            core_s = "Can I get you...? / We have a few questions about..."
            core_c = "proposal / timeline / breakdown"
        elif set_no == 2:
            content = [
                turn("A", "Hi. Good to see you again. How was the trip?", "greeting"),
                turn("B", "Smooth. Thanks for asking. Shall we get started?", "Smooth. Thanks for asking. Shall we get started?"),
                turn("A", "Yes. Here's the agenda. We'll go through the points.", "yes / agenda"),
                turn("B", "We'd like to discuss the contract terms first.", "We'd like to discuss the contract terms first."),
                turn("A", "Of course. Page 3. What would you like to change?", "of course / ask"),
                turn("B", "The payment schedule. We prefer 30 days instead of 14.", "prefer / change"),
                turn("A", "I'll check with our team and get back to you.", "check / get back"),
                turn("B", "Thanks. We can sign once that's agreed.", "Thanks. We can sign once that's agreed."),
                turn("A", "Perfect. We'll email you by tomorrow.", "perfect / when"),
            ]
            core_s = "Shall we get started? / We'd like to discuss..."
            core_c = "contract terms / payment schedule"
        else:
            content = [
                turn("A", "Thank you for the presentation. We're interested.", "thank / interest"),
                turn("B", "Great. What's the next step?", "Great. What's the next step?"),
                turn("A", "We need to talk to our boss. We'll have an answer by next week.", "need / timeline"),
                turn("B", "Can we send a follow-up proposal with more details?", "Can we send a follow-up proposal with more details?"),
                turn("A", "Yes. Please do. The more info, the better.", "yes / encourage"),
                turn("B", "We'll send it today. Thank you for your time.", "We'll send it today. Thank you for your time."),
                turn("A", "Thank you. We'll be in touch.", "thank / close"),
                turn("B", "Looking forward to it. Goodbye.", "Looking forward to it. Goodbye."),
            ]
            core_s = "What's the next step? / Can we send a follow-up...?"
            core_c = "the more info the better / be in touch"
        out.append(dialogue_record(
            "work", "meeting", "client", set_no, usage,
            f"GZ-MEETING-CLIENT-{did_suffix}", content, core_s, core_c,
            "工作职场", "会议 / 接待", "客户"
        ))

    # ----- 工作职场：会议/接待 - 合作伙伴 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Good to meet you. We've heard a lot about your company.", "greeting"),
                turn("B", "Likewise. We're excited about this partnership.", "Likewise. We're excited about this partnership."),
                turn("A", "So are we. Let's talk about how we can work together.", "agree / propose"),
                turn("B", "We have ideas for a joint project. Can we share the deck?", "We have ideas for a joint project. Can we share the deck?"),
                turn("A", "Please. We have the projector ready.", "please / ready"),
                turn("B", "Great. Here we go.", "Great. Here we go."),
                turn("A", "Interesting. We'll need to discuss internally.", "interest / next"),
                turn("B", "Sure. Take your time. We're here if you have questions.", "Sure. Take your time. We're here if you have questions."),
                turn("A", "Thanks. Let's schedule a follow-up.", "thanks / schedule"),
            ]
            core_s = "We're excited about.../ Can we share...?"
            core_c = "joint project / discuss internally"
        elif set_no == 2:
            content = [
                turn("A", "The contract looks good. We have one concern.", "opinion / concern"),
                turn("B", "What's that? We can try to address it.", "What's that? We can try to address it."),
                turn("A", "The exclusivity clause. We'd like it limited to two years.", "clause / request"),
                turn("B", "We can do that. I'll have legal draft an addendum.", "agree / action"),
                turn("A", "Perfect. When can we sign?", "Perfect. When can we sign?"),
                turn("B", "How about next Monday? We'll send the final version by Friday.", "suggest / when"),
                turn("A", "That works. Thanks for being flexible.", "That works. Thanks for being flexible."),
                turn("B", "You're welcome. Looking forward to working with you.", "response"),
            ]
            core_s = "We have one concern / When can we sign?"
            core_c = "exclusivity clause / addendum"
        else:
            content = [
                turn("A", "Thanks for the collaboration so far. It's going well.", "thank / progress"),
                turn("B", "We think so too. The team gets along well.", "We think so too. The team gets along well."),
                turn("A", "We'd like to expand. Maybe another project next quarter.", "expand / suggest"),
                turn("B", "We're open to that. Let's set up a call to brainstorm.", "We're open to that. Let's set up a call to brainstorm."),
                turn("A", "Good idea. I'll send a calendar invite.", "good idea / action"),
                turn("B", "Great. Talk soon.", "Great. Talk soon."),
                turn("A", "Bye.", "bye"),
            ]
            core_s = "It's going well / We'd like to expand"
            core_c = "next quarter / set up a call"
        out.append(dialogue_record(
            "work", "meeting", "partner", set_no, usage,
            f"GZ-MEETING-PARTNER-{did_suffix}", content, core_s, core_c,
            "工作职场", "会议 / 接待", "合作伙伴"
        ))

    # ----- 工作职场：电话沟通 - 客服 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Hello. Thank you for calling. How can I help you?", "greeting"),
                turn("B", "Hi. I have a problem with my order. It hasn't arrived.", "Hi. I have a problem with my order. It hasn't arrived."),
                turn("A", "I'm sorry to hear that. Can I have your order number?", "sorry / ask"),
                turn("B", "Yes. It's 12345.", "Yes. It's 12345."),
                turn("A", "One moment. I see it. It was shipped yesterday. You should get it by Friday.", "check / info"),
                turn("B", "Okay. Can you send me the tracking link?", "Okay. Can you send me the tracking link?"),
                turn("A", "Sure. I'll email it to you. Is there anything else?", "sure / offer"),
                turn("B", "No. Thank you.", "No. Thank you."),
                turn("A", "You're welcome. Have a good day.", "close"),
            ]
            core_s = "I have a problem with.../ Can I have your order number?"
            core_c = "I'm sorry to hear that / tracking link"
        elif set_no == 2:
            content = [
                turn("A", "Good afternoon. Customer service. How may I assist you?", "greeting"),
                turn("B", "I'd like to cancel my subscription.", "I'd like to cancel my subscription."),
                turn("A", "I can help with that. May I ask why?", "help / ask why"),
                turn("B", "I'm not using it anymore.", "I'm not using it anymore."),
                turn("A", "Understood. I'll process the cancellation. It will take effect at the end of the month.", "process / when"),
                turn("B", "That's fine. Will I get a refund?", "That's fine. Will I get a refund?"),
                turn("A", "Yes. Within 5 to 7 business days. Anything else?", "yes / time / offer"),
                turn("B", "No. Thanks.", "No. Thanks."),
                turn("A", "Thank you for calling. Goodbye.", "close"),
            ]
            core_s = "I'd like to cancel.../ May I ask why?"
            core_c = "take effect / business days"
        else:
            content = [
                turn("A", "Hello. You're through to support. What's the issue?", "greeting"),
                turn("B", "My password doesn't work. I need to reset it.", "My password doesn't work. I need to reset it."),
                turn("A", "I'll send you a reset link. What's your email?", "action / ask"),
                turn("B", "wang@email.com.", "wang@email.com."),
                turn("A", "Done. Check your inbox. The link is valid for one hour.", "done / remind"),
                turn("B", "Got it. Thank you.", "Got it. Thank you."),
                turn("A", "You're welcome. Call back if you need more help.", "response"),
            ]
            core_s = "I need to reset it / What's your email?"
            core_c = "reset link / valid for one hour"
        out.append(dialogue_record(
            "work", "phone", "customer_service", set_no, usage,
            f"GZ-PHONE-SERVICE-{did_suffix}", content, core_s, core_c,
            "工作职场", "电话沟通", "客服"
        ))

    # ----- 工作职场：电话沟通 - 接线员 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Hello. ABC Company. How can I direct your call?", "greeting"),
                turn("B", "I'd like to speak to Mr. Zhang in Sales.", "I'd like to speak to Mr. Zhang in Sales."),
                turn("A", "One moment. I'll put you through.", "one moment / put through"),
                turn("B", "Thank you.", "Thank you."),
                turn("A", "You're welcome. Please hold.", "hold"),
            ]
            core_s = "How can I direct your call? / I'd like to speak to..."
            core_c = "put you through / please hold"
        elif set_no == 2:
            content = [
                turn("A", "Good morning. Dr. Li's office. Can I help you?", "greeting"),
                turn("B", "I need to make an appointment for next week.", "I need to make an appointment for next week."),
                turn("A", "We have Tuesday at 10 or Thursday at 3. Which do you prefer?", "options"),
                turn("B", "Thursday at 3, please.", "Thursday at 3, please."),
                turn("A", "Done. Your name and phone number?", "done / ask"),
                turn("B", "Wang. 138-0000-0000.", "Wang. 138-0000-0000."),
                turn("A", "You're booked. We'll send a reminder. Goodbye.", "confirm / goodbye"),
                turn("B", "Thank you. Goodbye.", "Thank you. Goodbye."),
            ]
            core_s = "I need to make an appointment / Which do you prefer?"
            core_c = "you're booked / send a reminder"
        else:
            content = [
                turn("A", "Hello. He's in a meeting. Can I take a message?", "busy / offer"),
                turn("B", "Yes. Please tell him Wang called about the contract.", "Yes. Please tell him Wang called about the contract."),
                turn("A", "Wang, contract. Does he have your number?", "repeat / ask"),
                turn("B", "Yes. He has it. Thanks.", "Yes. He has it. Thanks."),
                turn("A", "I'll pass it on. Goodbye.", "confirm / goodbye"),
                turn("B", "Goodbye.", "Goodbye."),
            ]
            core_s = "Can I take a message? / Please tell him...called about..."
            core_c = "pass it on"
        out.append(dialogue_record(
            "work", "phone", "operator", set_no, usage,
            f"GZ-PHONE-OPERATOR-{did_suffix}", content, core_s, core_c,
            "工作职场", "电话沟通", "接线员"
        ))

    # ----- 社交人情：朋友聚会 - 朋友 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Hey! Long time no see. How have you been?", "greeting"),
                turn("B", "I've been good. Busy with work. How about you?", "I've been good. Busy with work. How about you?"),
                turn("A", "Same. We should hang out more. Are you free this weekend?", "same / suggest"),
                turn("B", "Yes. What do you have in mind?", "Yes. What do you have in mind?"),
                turn("A", "Maybe dinner? Or we could see a movie.", "options"),
                turn("B", "Dinner sounds great. Where?", "Dinner sounds great. Where?"),
                turn("A", "That new place on Main Street? I'll book a table.", "suggest / action"),
                turn("B", "Perfect. Text me the time.", "Perfect. Text me the time."),
                turn("A", "Will do. See you then.", "will do"),
            ]
            core_s = "Long time no see / How have you been? / What do you have in mind?"
            core_c = "hang out / sounds great"
        elif set_no == 2:
            content = [
                turn("A", "Cheers! Happy birthday!", "toast"),
                turn("B", "Thank you! I'm so glad you could come.", "Thank you! I'm so glad you could come."),
                turn("A", "Wouldn't miss it. The cake looks amazing.", "wouldn't miss / compliment"),
                turn("B", "My mom made it. Do you want a piece?", "My mom made it. Do you want a piece?"),
                turn("A", "Yes, please. And another drink?", "yes / offer"),
                turn("B", "I'm good. Maybe later. Let's take a photo.", "I'm good. Maybe later. Let's take a photo."),
                turn("A", "Good idea. Everyone, gather round!", "good idea / gather"),
                turn("B", "Say cheese!", "Say cheese!"),
                turn("A", "Cheese! Nice one.", "cheese / nice"),
            ]
            core_s = "I'm so glad you could come / Do you want a piece?"
            core_c = "wouldn't miss it / gather round"
        else:
            content = [
                turn("A", "So what's new? Any plans for the holiday?", "ask"),
                turn("B", "I'm thinking of traveling. Maybe Japan.", "I'm thinking of traveling. Maybe Japan."),
                turn("A", "Nice! I went last year. You'll love it. Need any tips?", "nice / offer"),
                turn("B", "Yes! Where did you stay?", "Yes! Where did you stay?"),
                turn("A", "In Tokyo. I can send you the hotel link. It was cheap and clean.", "answer / offer"),
                turn("B", "That would be great. Thanks.", "That would be great. Thanks."),
                turn("A", "No problem. Let me know when you book.", "no problem"),
                turn("B", "I will. Thanks again.", "I will. Thanks again."),
            ]
            core_s = "What's new? / Any plans for...? / Need any tips?"
            core_c = "I'm thinking of / send you the link"
        out.append(dialogue_record(
            "social", "party", "friend", set_no, usage,
            f"SJ-PARTY-FRIEND-{did_suffix}", content, core_s, core_c,
            "社交人情", "朋友聚会", "朋友"
        ))

    # ----- 社交人情：朋友聚会 - 同学 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Hi! You're in my English class, right?", "recognize"),
                turn("B", "Yes. I sit in the back. Nice to meet you properly.", "Yes. I sit in the back. Nice to meet you properly."),
                turn("A", "Same. Did you do the homework? The essay was hard.", "same / homework"),
                turn("B", "I did. I'm not sure if it's good. Want to compare?", "I did. I'm not sure if it's good. Want to compare?"),
                turn("A", "Sure. Let's meet before class. In the library?", "sure / suggest"),
                turn("B", "Okay. 9 a.m.?", "Okay. 9 a.m.?"),
                turn("A", "Perfect. See you then.", "perfect"),
                turn("B", "See you.", "See you."),
            ]
            core_s = "You're in my...class, right? / Want to compare?"
            core_c = "nice to meet you properly / before class"
        elif set_no == 2:
            content = [
                turn("A", "The exam is next week. Are you nervous?", "topic / ask"),
                turn("B", "A bit. I've been reviewing. How about you?", "A bit. I've been reviewing. How about you?"),
                turn("A", "Same. We could study together. I have notes.", "same / offer"),
                turn("B", "That would help. When are you free?", "That would help. When are you free?"),
                turn("A", "Tomorrow afternoon? Coffee shop?", "suggest"),
                turn("B", "Sounds good. 2 p.m.?", "Sounds good. 2 p.m.?"),
                turn("A", "Done. I'll bring the notes.", "done"),
                turn("B", "Thanks. See you.", "Thanks. See you."),
            ]
            core_s = "Are you nervous? / We could study together"
            core_c = "I've been reviewing / coffee shop"
        else:
            content = [
                turn("A", "Are you going to the graduation party?", "ask"),
                turn("B", "Yes. Are you? I heard it's at the Riverside Hotel.", "Yes. Are you? I heard it's at the Riverside Hotel."),
                turn("A", "Yeah. This Saturday. I'm going with a few classmates.", "yes / with whom"),
                turn("B", "Maybe we can go together. Share a ride?", "Maybe we can go together. Share a ride?"),
                turn("A", "Good idea. I'll drive. Pick you up at 6?", "good idea / offer"),
                turn("B", "Perfect. Text me your address. Thanks!", "Perfect. Text me your address. Thanks!"),
                turn("A", "No problem. See you Saturday.", "no problem"),
                turn("B", "See you. Bye.", "See you. Bye."),
            ]
            core_s = "Are you going to...? / Maybe we can go together"
            core_c = "share a ride / pick you up"
        out.append(dialogue_record(
            "social", "party", "classmate", set_no, usage,
            f"SJ-PARTY-CLASSMATE-{did_suffix}", content, core_s, core_c,
            "社交人情", "朋友聚会", "同学"
        ))

    # ----- 社交人情：打招呼/闲聊 - 陌生人 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Nice weather today, isn't it?", "small talk"),
                turn("B", "Yes, it is. Finally stopped raining.", "Yes, it is. Finally stopped raining."),
                turn("A", "Are you from around here?", "Are you from around here?"),
                turn("B", "No. I'm just visiting. I'm here for work.", "No. I'm just visiting. I'm here for work."),
                turn("A", "How long are you staying?", "How long are you staying?"),
                turn("B", "A week. So far so good.", "A week. So far so good."),
                turn("A", "Well, enjoy your stay. Bye.", "well / bye"),
                turn("B", "Thanks. Bye.", "Thanks. Bye."),
            ]
            core_s = "Nice weather today, isn't it? / Are you from around here?"
            core_c = "just visiting / so far so good"
        elif set_no == 2:
            content = [
                turn("A", "Excuse me. Is this seat taken?", "ask"),
                turn("B", "No. Go ahead. Sit down.", "No. Go ahead. Sit down."),
                turn("A", "Thanks. Busy day?", "thanks / small talk"),
                turn("B", "Yeah. Lots of meetings. You?", "Yeah. Lots of meetings. You?"),
                turn("A", "Same. I'm waiting for my train. Another hour.", "same / situation"),
                turn("B", "Time to relax then. I like people-watching here.", "relax / hobby"),
                turn("A", "Me too. Well, have a good trip.", "me too / wish"),
                turn("B", "You too. Bye.", "You too. Bye."),
            ]
            core_s = "Is this seat taken? / Busy day?"
            core_c = "go ahead / people-watching"
        else:
            content = [
                turn("A", "Hi. Do you mind if I sit here?", "ask"),
                turn("B", "Not at all. Please.", "Not at all. Please."),
                turn("A", "Thanks. That's a nice bag. Where did you get it?", "thanks / compliment / ask"),
                turn("B", "Online. It was on sale.", "Online. It was on sale."),
                turn("A", "I might look for one. Anyway, have a good day.", "might / close"),
                turn("B", "You too. Bye.", "You too. Bye."),
            ]
            core_s = "Do you mind if I sit here? / Where did you get it?"
            core_c = "not at all / on sale"
        out.append(dialogue_record(
            "social", "chat", "stranger", set_no, usage,
            f"SJ-CHAT-STRANGER-{did_suffix}", content, core_s, core_c,
            "社交人情", "打招呼 / 闲聊", "陌生人"
        ))

    # ----- 社交人情：兴趣爱好 - 玩伴 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "Do you play basketball? We need one more for a game.", "ask / invite"),
                turn("B", "I do. When and where?", "I do. When and where?"),
                turn("A", "Saturday morning. The court near the park. 9 o'clock.", "when / where"),
                turn("B", "I'll be there. Should I bring a ball?", "I'll be there. Should I bring a ball?"),
                turn("A", "We have one. Just bring yourself and some water.", "we have / just bring"),
                turn("B", "Perfect. See you Saturday.", "Perfect. See you Saturday."),
                turn("A", "See you. It'll be fun.", "see you"),
            ]
            core_s = "Do you play...? / We need one more / When and where?"
            core_c = "I'll be there / bring yourself"
        elif set_no == 2:
            content = [
                turn("A", "You like hiking too? We're going to the mountain this weekend.", "share / invite"),
                turn("B", "I love hiking. Is it a long trail?", "I love hiking. Is it a long trail?"),
                turn("A", "About four hours round trip. We start early to avoid the heat.", "time / plan"),
                turn("B", "What should I bring?", "What should I bring?"),
                turn("A", "Water, snacks, and good shoes. Sunscreen too.", "list"),
                turn("B", "Got it. Count me in. Thanks.", "Got it. Count me in. Thanks."),
                turn("A", "Great. I'll send you the details.", "great"),
            ]
            core_s = "You like...too? / What should I bring?"
            core_c = "round trip / count me in"
        else:
            content = [
                turn("A", "Want to join our board game night? We play every Friday.", "invite"),
                turn("B", "Sounds fun. I'm not very good though.", "Sounds fun. I'm not very good though."),
                turn("A", "No worries. We're all learning. It's casual.", "no worries / casual"),
                turn("B", "Okay. Where do you meet?", "Okay. Where do you meet?"),
                turn("A", "At my place. I'll send you the address.", "place / send"),
                turn("B", "Great. What time?", "Great. What time?"),
                turn("A", "7 p.m. Bring a snack if you want. See you.", "time / bring / see you"),
                turn("B", "See you. Thanks.", "See you. Thanks."),
            ]
            core_s = "Want to join...? / Where do you meet?"
            core_c = "no worries / board game night"
        out.append(dialogue_record(
            "social", "hobby", "playmate", set_no, usage,
            f"SJ-HOBBY-PLAYMATE-{did_suffix}", content, core_s, core_c,
            "社交人情", "兴趣爱好", "玩伴"
        ))

    # ----- 社交人情：兴趣爱好 - 同好 -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "That's a great camera. Do you do photography?", "compliment / ask"),
                turn("B", "Yes. Just as a hobby. Do you?", "Yes. Just as a hobby. Do you?"),
                turn("A", "Me too. I mostly do street photography. You?", "me too / ask"),
                turn("B", "Landscapes. I went to the mountains last month. Got some good shots.", "Landscapes. I went to the mountains last month. Got some good shots."),
                turn("A", "Nice. We have a photo group. We meet once a month. Want to join?", "nice / invite"),
                turn("B", "I'd love to. How do I join?", "I'd love to. How do I join?"),
                turn("A", "I'll add you on WeChat. We post the events there.", "add / explain"),
                turn("B", "Perfect. Thanks.", "Perfect. Thanks."),
                turn("A", "You're welcome. See you at the next meetup.", "response"),
            ]
            core_s = "Do you do photography? / Want to join?"
            core_c = "just as a hobby / street photography"
        elif set_no == 2:
            content = [
                turn("A", "You're reading the new bestseller? How is it?", "notice / ask"),
                turn("B", "Really good. I'm almost done. Have you read it?", "Really good. I'm almost done. Have you read it?"),
                turn("A", "Not yet. Is it worth buying?", "Not yet. Is it worth buying?"),
                turn("B", "Yes. Or borrow from the library. I got my copy there.", "yes / suggest"),
                turn("A", "I'll check. Thanks for the recommendation.", "I'll check. Thanks for the recommendation."),
                turn("B", "No problem. Let me know what you think when you're done.", "no problem"),
                turn("A", "I will. Bye.", "I will. Bye."),
            ]
            core_s = "How is it? / Is it worth buying?"
            core_c = "bestseller / worth buying"
        else:
            content = [
                turn("A", "That concert was amazing. Are you a fan too?", "share / ask"),
                turn("B", "Yes! I've been following them for years.", "Yes! I've been following them for years."),
                turn("A", "Same. Did you get the new album?", "Same. Did you get the new album?"),
                turn("B", "Yes. I pre-ordered it. It's great.", "Yes. I pre-ordered it. It's great."),
                turn("A", "I'll get it this weekend. We should go to a show together sometime.", "plan / suggest"),
                turn("B", "Definitely. Let's stay in touch.", "Definitely. Let's stay in touch."),
                turn("A", "Sure. Here's my number. Text me.", "sure / contact"),
                turn("B", "Will do. Nice meeting you.", "Will do. Nice meeting you."),
            ]
            core_s = "Are you a fan too? / Did you get the new album?"
            core_c = "pre-ordered / stay in touch"
        out.append(dialogue_record(
            "social", "hobby", "hobbyist", set_no, usage,
            f"SJ-HOBBY-HOBBYIST-{did_suffix}", content, core_s, core_c,
            "社交人情", "兴趣爱好", "同好"
        ))

    # ----- 社交人情：赞美/安慰/道歉 - 通用 NPC -----
    for set_no, usage, did_suffix in [(1, "learn", "1"), (2, "review", "2"), (3, "immersive", "3")]:
        if set_no == 1:
            content = [
                turn("A", "You did a great job on the project. Really impressed.", "praise"),
                turn("B", "Thank you. That means a lot. The team helped too.", "Thank you. That means a lot. The team helped too."),
                turn("A", "You're too modest. Your presentation was clear and strong.", "modest / praise again"),
                turn("B", "I'm glad it went well. Thanks for the feedback.", "I'm glad it went well. Thanks for the feedback."),
                turn("A", "Keep it up. We need more people like you.", "encourage"),
                turn("B", "I'll try. Thank you again.", "I'll try. Thank you again."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "You did a great job / That means a lot / Thanks for the feedback"
            core_c = "really impressed / keep it up"
        elif set_no == 2:
            content = [
                turn("A", "I heard about your loss. I'm so sorry.", "condolence"),
                turn("B", "Thank you. It's been hard.", "Thank you. It's been hard."),
                turn("A", "I can't imagine. If you need anything, just say.", "empathy / offer"),
                turn("B", "That's kind. I'll be okay. Thanks for being here.", "That's kind. I'll be okay. Thanks for being here."),
                turn("A", "Anytime. Take care of yourself.", "anytime / take care"),
                turn("B", "I will. Thank you.", "I will. Thank you."),
                turn("A", "You're welcome.", "response"),
            ]
            core_s = "I'm so sorry / If you need anything, just say"
            core_c = "I can't imagine / take care of yourself"
        else:
            content = [
                turn("A", "I'm really sorry about yesterday. I was wrong.", "apologize"),
                turn("B", "It's okay. I know you didn't mean it.", "It's okay. I know you didn't mean it."),
                turn("A", "Still. I shouldn't have said that. I'll be more careful.", "still / promise"),
                turn("B", "Thanks for saying that. Let's move on.", "Thanks for saying that. Let's move on."),
                turn("A", "Thanks for understanding. I appreciate it.", "thanks"),
                turn("B", "No problem. We're good.", "No problem. We're good."),
                turn("A", "Good. See you tomorrow.", "good"),
            ]
            core_s = "I'm really sorry about.../ I shouldn't have said that"
            core_c = "didn't mean it / let's move on"
        out.append(dialogue_record(
            "social", "praise", "companion", set_no, usage,
            f"SJ-PRAISE-COMPANION-{did_suffix}", content, core_s, core_c,
            "社交人情", "赞美 / 安慰 / 道歉", "通用 NPC（朋友/同事/家人）"
        ))

    return out


def main():
    if not DIALOGUES_PATH.exists():
        print(f"Error: {DIALOGUES_PATH} not found", file=sys.stderr)
        sys.exit(1)
    with open(DIALOGUES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("Error: dialogues.json is not a list", file=sys.stderr)
        sys.exit(1)
    existing_ids = {d.get("dialogue_id") for d in data if d.get("dialogue_id")}
    new_list = new_dialogues()
    to_add = [d for d in new_list if d["dialogue_id"] not in existing_ids]
    if not to_add:
        print("No new dialogues to add (all IDs already exist).")
        return
    data.extend(to_add)
    with open(DIALOGUES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Added {len(to_add)} new dialogue(s). Total: {len(data)}.")


if __name__ == "__main__":
    main()
