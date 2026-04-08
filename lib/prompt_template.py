"""RAG prompt template for Gemini model."""


def build_prompt(new_query: str, similar_qas: list[dict]) -> str:
    """Build the complete prompt for Gemini from a new query and similar Q&A pairs.

    Args:
        new_query: The customer's new inquiry text.
        similar_qas: List of dicts from Supabase search, each with keys:
            question_text, answer_text, similarity.

    Returns:
        The complete prompt string.
    """
    knowledge_blocks: list[str] = []
    for i, qa in enumerate(similar_qas, start=1):
        similarity_pct = round(qa["similarity"] * 100, 1)
        knowledge_blocks.append(
            f"---ナレッジ{i} (類似度: {similarity_pct}%)---\n"
            f"質問: {qa['question_text']}\n"
            f"回答: {qa['answer_text']}"
        )

    knowledge_section = "\n\n".join(knowledge_blocks)

    return (
        "あなたは釣具ECサイト「ますびと商店」のベテランカスタマーサポートです。\n"
        "以下の【過去の対応ナレッジ】を参考に、【顧客からの新規問い合わせ】に対する丁寧な返信メールのドラフトを作成してください。\n"
        "\n"
        "【過去の対応ナレッジ】\n"
        f"{knowledge_section}\n"
        "\n"
        "【顧客からの新規問い合わせ】\n"
        f"{new_query}\n"
        "\n"
        "【制約事項】\n"
        "- ますびと商店のトーン＆マナー（丁寧・親切）に合わせること。\n"
        "- 挨拶は「お客様\\nいつも大変お世話になっております。」で始める。\n"
        "- 署名は「ますびと商店」で締める。\n"
        "- 過去のナレッジにない不明な釣り用語・仕様に関する断定は避け、事実に基づき回答すること。\n"
        "- 不明な点がある場合は「確認してご連絡いたします」等の対応を提案すること。\n"
        "- 返送先が必要な場合: 〒180-0011 東京都武蔵野市八幡町1-1-3-203 ますびと商店 TEL：0422-66-2710"
    )


def build_channel_prompt(new_query: str, similar_qas: list, channel: dict) -> str:
    """Build prompt using a channel's custom system_prompt, greeting_prefix, and signature.

    Args:
        new_query: The customer's new inquiry text.
        similar_qas: List of dicts from Supabase search.
        channel: Channel dict with keys: system_prompt, greeting_prefix, signature, name.
    """
    knowledge_blocks = []
    for i, qa in enumerate(similar_qas, start=1):
        similarity_pct = round(qa["similarity"] * 100, 1)
        knowledge_blocks.append(
            f"---ナレッジ{i} (類似度: {similarity_pct}%)---\n"
            f"質問: {qa['question_text']}\n"
            f"回答: {qa['answer_text']}"
        )

    knowledge_section = "\n\n".join(knowledge_blocks) if knowledge_blocks else "(参考となる過去の対応ナレッジはありません)"

    system_prompt = channel.get("system_prompt", "あなたはカスタマーサポートです。")
    greeting = channel.get("greeting_prefix", "")
    signature = channel.get("signature", "")

    constraints = [
        "- 丁寧で親切なトーンで回答すること。",
        "- 過去のナレッジにない不明な用語や仕様に関する断定は避け、事実に基づき回答すること。",
        "- 不明な点がある場合は「確認してご連絡いたします」等の対応を提案すること。",
    ]
    if greeting:
        constraints.append(f'- 挨拶は「{greeting}」で始める。')
    if signature:
        constraints.append(f'- 署名は「{signature}」で締める。')

    return (
        f"{system_prompt}\n"
        "\n"
        "【過去の対応ナレッジ】\n"
        f"{knowledge_section}\n"
        "\n"
        "【顧客からの新規問い合わせ】\n"
        f"{new_query}\n"
        "\n"
        "【制約事項】\n"
        + "\n".join(constraints)
    )
