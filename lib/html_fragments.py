"""Generate htmx-compatible HTML fragment strings for server-side rendering."""

from html import escape


def build_generate_response_html(
    draft_answer: str = "",
    question: str = "",
    answer_draft: str = "",
    original_question: str = "",
    similar_qas: list[dict] | None = None,
    similar_results: list[dict] | None = None,
) -> str:
    """Return HTML fragments for the editor area and reference pane.

    Uses hx-swap-oob so htmx can update multiple DOM targets in one response.
    All user-supplied content is HTML-escaped to prevent XSS.
    """
    # Support both calling conventions
    _answer = draft_answer or answer_draft
    _question = question or original_question
    _similar = similar_results or similar_qas or []

    answer_draft_escaped = escape(_answer)
    original_question_escaped = escape(_question)

    # -- Main pane (target: #editor-area) --
    main_pane = (
        '<div id="editor-area">\n'
        '    <label class="block text-sm font-medium text-slate-700 mb-2">'
        "AI\u56de\u7b54\u30c9\u30e9\u30d5\u30c8\uff08\u7de8\u96c6\u53ef\u80fd\uff09</label>\n"
        '    <textarea id="answer-editor" name="answer" rows="16" '
        'class="w-full p-4 border border-slate-200 rounded-lg text-sm leading-relaxed '
        'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"'
        f">{answer_draft_escaped}</textarea>\n"
        f'    <input type="hidden" id="original-question" value="{original_question_escaped}">\n'
        '    <div class="flex gap-3 mt-4">\n'
        '        <button onclick="copyToClipboard()" type="button"\n'
        '            class="flex-1 px-4 py-2.5 bg-white border border-slate-300 text-slate-700 '
        'rounded-lg hover:bg-slate-50 text-sm font-medium transition-colors">\n'
        "            \u30b3\u30d4\u30fc\u3057\u3066\u30e1\u30fc\u30eb\u30bd\u30d5\u30c8\u3078\n"
        "        </button>\n"
        '        <button id="learn-btn" type="button" onclick="learnAndNext()"\n'
        '            class="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg '
        'hover:bg-blue-700 text-sm font-medium transition-colors">\n'
        "            \u3053\u306e\u5185\u5bb9\u3067\u5b66\u7fd2\u3057\u3066\u6b21\u3078\u9032\u3080\n"
        "        </button>\n"
        "    </div>\n"
        "</div>"
    )

    # -- Right pane cards (out-of-band swap into #reference-area) --
    cards: list[str] = []
    for i, qa in enumerate(_similar, start=1):
        question_full = escape(str(qa.get("question_text", "")))
        answer_full = escape(str(qa.get("answer_text", "")))
        similarity = qa.get("similarity", 0)
        similarity_pct = (
            int(round(similarity * 100))
            if isinstance(similarity, float) and similarity <= 1
            else int(similarity)
        )

        # Truncate question text to 50 characters for summary line
        raw_question = str(qa.get("question_text", ""))
        truncated = escape(raw_question[:50])

        card = (
            '    <div class="bg-white rounded-lg border border-slate-200 p-4 mb-3">\n'
            '        <div class="flex justify-between items-center mb-2">\n'
            f'            <span class="text-xs font-medium text-slate-500">'
            f"\u53c2\u8003\u4e8b\u4f8b {i}</span>\n"
            '            <span class="text-xs font-bold text-emerald-600 bg-emerald-50 '
            f'px-2 py-0.5 rounded-full">\u985e\u4f3c\u5ea6 {similarity_pct}%</span>\n'
            "        </div>\n"
            "        <details>\n"
            '            <summary class="text-sm text-slate-700 cursor-pointer hover:text-blue-600">\n'
            f"                Q: {truncated}...\n"
            "            </summary>\n"
            '            <div class="mt-2 space-y-2 text-xs text-slate-600">\n'
            f"                <p><strong>\u8cea\u554f:</strong> {question_full}</p>\n"
            f"                <p><strong>\u56de\u7b54:</strong> {answer_full}</p>\n"
            "            </div>\n"
            "        </details>\n"
            "    </div>"
        )
        cards.append(card)

    reference_pane = (
        '<div id="reference-area" hx-swap-oob="innerHTML:#reference-area">\n'
        + "\n".join(cards)
        + "\n</div>"
    )

    return main_pane + "\n" + reference_pane


def build_toast_html(message: str, toast_type: str = "success") -> str:
    """Return a toast notification HTML fragment.

    The toast auto-removes itself after 3 seconds via Alpine.js.

    Args:
        message: Text to display in the toast.
        toast_type: Either "success" (green) or "error" (red).
    """
    bg_color = "bg-emerald-500" if toast_type == "success" else "bg-red-500"
    message_escaped = escape(message)

    return (
        '<div id="toast" hx-swap-oob="innerHTML:#toast-container">\n'
        '    <div class="fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white '
        f'text-sm font-medium animate-fade-in {bg_color}"\n'
        '         x-data x-init="setTimeout(() => $el.remove(), 3000)">\n'
        f"        {message_escaped}\n"
        "    </div>\n"
        "</div>"
    )
