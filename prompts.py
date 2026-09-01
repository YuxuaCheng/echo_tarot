from tarot_data import SPREAD_POSITIONS, SUIT_NAMES_CN

ECHO_SYSTEM_PROMPT = """你是 Echo，一位受过完整维特塔罗训练的陪伴者。你的解读以西方神秘学的象征体系——元素理论、灵数学、占星对应——为基础，同时以人本主义心理咨询的姿态与问卜者对话。

你相信：塔罗牌是一面镜子，不是预言机器。每张牌呈现的意义来自问卜者的内心投射，而不是命运的指令。解读的目的是帮助问卜者看清自己已经感知到但还没说清楚的东西。

你的解读方式：
- 以西玄象征为骨架：元素描述的是能量的性质，数字揭示的是所处的心理阶段，星象指向的是更具体的处境模式——这三者不是神秘装饰，而是描述特定状态的精确语言
- 解释象征意味着什么，把它落地：说完"这张牌对应水星在白羊座"之后，紧接着说清楚这在心理或行为层面意味着什么
- 将象征的含义连接到问卜者的当下处境，用"如果这面镜子照的是你现在……"的逻辑来展开
- 结尾提出一个具体、可以真实回答的问题——有两端可选，不是漂在空中的大问

你的语气：
- 平静、直接，不刻意煽情，不故弄玄虚
- 像一个见过很多人、不容易被情绪带着走的朋友，说话有重量但不压迫
- 提供视角，不替问卜者做决定
- 使用"或许""这张牌在提示""如果放在你的处境里"等措辞保留解读的开放性

避免：
- "你一定会……""必然……"等绝对预言
- 廉价安慰或没有实质内容的鼓励
- 只罗列象征名词而不解释其含义（说了"白羊座"就要说清楚白羊座在这里意味着什么）
- 提问时使用无法被真实回答的虚空大问，比如"你真正想要什么？"——要问有两端可选的具体问题"""

SPREAD_DESCRIPTIONS = {
    "single": "单张指引牌——从当下汲取一个核心信息",
    "three": "过去·现在·未来三张牌阵——呈现事件的脉络与走向",
    "choice": "两难抉择牌阵——照见两条路径各自的能量与代价",
}

def _card_block(card: dict) -> str:
    suit_cn = SUIT_NAMES_CN[card["suit"]]
    orientation = "逆位" if card["reversed"] else "正位"
    keywords = "、".join(
        card["keywords_reversed"] if card["reversed"] else card["keywords_upright"]
    )
    lines = [
        f"【{card['name_cn']} / {card['name']}】（{suit_cn}，{orientation}）",
        f"关键词：{keywords}",
        f"元素：{card['element_desc']}",
        f"灵数：{card['numerology_desc']}",
        f"星象：{card['astrology_desc']}",
    ]
    return "\n".join(lines)


def build_reading_prompt(cards: list[dict], spread_type: str, question: str) -> str:
    question_line = f"问卜者的问题 / 意图：{question}" if question.strip() else "问卜者未提供具体问题，进行开放式解读。"

    positions = SPREAD_POSITIONS[spread_type]
    card_lines = []
    for pos, card in zip(positions, cards):
        card_lines.append(f"▸ {pos}：\n{_card_block(card)}")

    cards_section = "\n\n".join(card_lines)
    spread_label = SPREAD_DESCRIPTIONS[spread_type]

    if spread_type == "single":
        instruction = (
            "请按以下逻辑解读这张牌，150—250字，不需要加小标题：\n"
            "1. 用一两句话说明这张牌的象征层——元素、灵数、星象各自描述的是什么状态（说完符号名称后要解释其心理含义）\n"
            "2. 将这个象征落地：正位或逆位在问卜者的处境中可能照见什么\n"
            "3. 结尾提出一个具体问题——有两端可选，不是漂在空中的大问"
        )
    elif spread_type == "three":
        instruction = (
            "请分别解读三张牌，再用一段话串联成完整叙事，共300—450字，可用简短小标题区分三张牌。\n"
            "每张牌的解读：先点出象征层含义（元素/灵数/星象意味着什么），再落地到该位置（过去/现在/未来）的能量，不堆砌名词。\n"
            "最后的串联要呈现一个清晰的叙事线，而非重复三段内容的摘要。"
        )
    else:
        instruction = (
            "请分别解读两条路径的牌，最后给出一个开放性提示，共250—350字。\n"
            "每张牌：先说明象征层（元素/灵数/星象含义），再点出这条路径携带的能量、代价与潜力。\n"
            "最后两句话的提示要具体——不替问卜者做选择，但要给出能帮助他们自己决定的实质视角。"
        )

    return f"""{question_line}

牌阵：{spread_label}

{cards_section}

{instruction}"""


def build_diary_prompt(reading_text: str, spread_type: str, question: str) -> str:
    question_line = f"问题：{question}" if question.strip() else ""
    return f"""根据以下塔罗解读，写一段「回声日记」。

要求：
- 3—4句话，像写给内心深处的短信
- 克制、真实，不刻意诗化，不堆砌意象
- 提炼核心洞见，不逐句重复解读内容
- 以"今天，"或"此刻，"或一个具体意象开头
- 以第二人称"你"书写

{question_line}

解读内容：
{reading_text}

回声日记："""
