"""
Rule-based content analysis.

No external AI API is required.

The analyzer works offline and produces explainable
heuristic scores.

Platform support:
    - Instagram
    - LinkedIn
    - X
    - Facebook
"""

import re

from collections import Counter


# ============================================================
# STOPWORDS
# ============================================================

STOPWORDS = set("""
a an the and or but if then so to of in on at for with from by is are was were
be been being this that these those it its it's your you my our their his her
as up down out over under again further once here there when where why how
all any both each few more most other some such no nor not only own same than
too very can will just don't should now i we you they them us not have has had
do does did doing not new get got make made just also
""".split())


# ============================================================
# POSITIVE WORDS
# ============================================================

POSITIVE_WORDS = set("""
great amazing awesome love excited excellent fantastic wonderful best happy
proud thrilled delighted incredible perfect brilliant beautiful success
win winning grateful thankful inspiring inspired joy exciting fun beautiful
launch launching new innovative powerful game-changer breakthrough celebrate
""".split())


# ============================================================
# NEGATIVE WORDS
# ============================================================

NEGATIVE_WORDS = set("""
bad terrible awful hate sad angry worst disappointing fail failed failure
problem issue broken worried worry concerned frustrated frustrating annoying
delay delayed cancelled cancel sorry unfortunately
""".split())


# ============================================================
# CTA DETECTION
# ============================================================

CALL_TO_ACTION_PATTERN = re.compile(
    r"\b("
    r"comment|share|follow|click|link in bio|dm us|subscribe|"
    r"tag someone|swipe|check out|sign up|learn more|shop now|"
    r"read more|book now|save this"
    r")\b",
    re.IGNORECASE
)


# ============================================================
# MOOD HASHTAGS
# ============================================================

MOOD_HASHTAGS = {

    "positive": [
        "#motivation",
        "#inspiration",
        "#goodvibes"
    ],

    "negative": [
        "#realtalk",
        "#honesty"
    ],

    "neutral": [
        "#community",
        "#trending"
    ]

}


# ============================================================
# PLATFORM HASHTAGS
# ============================================================

PLATFORM_HASHTAGS = {

    "Instagram": [
        "#instagram",
        "#instagood",
        "#contentcreator"
    ],

    "LinkedIn": [
        "#linkedin",
        "#professional",
        "#career"
    ],

    "X": [
        "#x",
        "#socialmedia",
        "#discussion"
    ],

    "Facebook": [
        "#facebook",
        "#community",
        "#socialmedia"
    ]

}


# ============================================================
# HELPERS
# ============================================================

def _syllables_in(word: str) -> int:

    word = word.lower().strip(
        ".,!?;:\"'()"
    )


    if not word:
        return 0


    vowels = "aeiouy"

    count = 0

    prev_was_vowel = False


    for ch in word:

        is_vowel = ch in vowels


        if is_vowel and not prev_was_vowel:

            count += 1


        prev_was_vowel = is_vowel


    if word.endswith("e") and count > 1:

        count -= 1


    return max(
        count,
        1
    )


def _split_sentences(text: str):

    pieces = re.split(
        r"[.!?]+(?:\s|$)",
        text
    )


    return [
        p.strip()
        for p in pieces
        if p.strip()
    ]


# ============================================================
# INSIGHT ENGINE
# ============================================================

class InsightEngine:
    """
    Evaluates extracted post text and produces
    platform-aware feedback.
    """

    def evaluate(
        self,
        text: str,
        platform: str = "Instagram"
    ):

        # Safety fallback
        if platform not in {
            "Instagram",
            "LinkedIn",
            "X",
            "Facebook"
        }:

            platform = "Instagram"


        # -----------------------------------------
        # BASIC METRICS
        # -----------------------------------------

        hashtags = re.findall(
            r"#\w+",
            text
        )

        mentions = re.findall(
            r"@\w+",
            text
        )

        emojis = re.findall(
            r"[\U0001F300-\U0001FAFF\u2600-\u27BF]",
            text
        )

        question_marks = text.count("?")

        has_cta = bool(
            CALL_TO_ACTION_PATTERN.search(text)
        )

        has_link = bool(
            re.search(
                r"(https?://|www\.)",
                text,
                re.IGNORECASE
            )
        )

        word_count = len(
            re.findall(
                r"\S+",
                text
            )
        )


        metrics = {

            "word_count":
                word_count,

            "hashtag_count":
                len(hashtags),

            "mention_count":
                len(mentions),

            "emoji_count":
                len(emojis),

            "question_marks":
                question_marks,

            "has_cta":
                has_cta,

            "has_link":
                has_link

        }


        # -----------------------------------------
        # ANALYSIS
        # -----------------------------------------

        readability = self._readability(
            text
        )

        tone = self._tone(
            text
        )

        readiness = self._readiness_score(
            metrics,
            readability,
            tone
        )

        hashtag_ideas = self._hashtag_ideas(
            text,
            tone["label"],
            hashtags,
            platform
        )

        rewritten_caption = self._rewrite_caption(
            text,
            hashtag_ideas,
            has_cta,
            question_marks > 0,
            platform
        )

        notes = self._build_notes(
            metrics,
            has_link,
            platform
        )


        # -----------------------------------------
        # FINAL RESULT
        # -----------------------------------------

        return {

            "platform":
                platform,

            "metrics":
                metrics,

            "readability":
                readability,

            "tone":
                tone,

            "readiness":
                readiness,

            "hashtag_ideas":
                hashtag_ideas,

            "rewritten_caption":
                rewritten_caption,

            "notes":
                notes

        }


    # ========================================================
    # READABILITY
    # ========================================================

    def _readability(
        self,
        text: str
    ):

        words = re.findall(
            r"[A-Za-z']+",
            text
        )

        sentences = _split_sentences(
            text
        )


        if not words or not sentences:

            return {
                "score": None,
                "label": "Not enough text"
            }


        syllables = sum(
            _syllables_in(w)
            for w in words
        )


        words_per_sentence = (
            len(words) /
            len(sentences)
        )


        syllables_per_word = (
            syllables /
            len(words)
        )


        flesch = (
            206.835
            - 1.015 * words_per_sentence
            - 84.6 * syllables_per_word
        )


        flesch = max(
            0,
            min(
                100,
                round(flesch, 1)
            )
        )


        if flesch >= 80:

            label = "Very easy"

        elif flesch >= 60:

            label = "Easy"

        elif flesch >= 50:

            label = "Fairly readable"

        elif flesch >= 30:

            label = "Fairly difficult"

        else:

            label = "Difficult"


        return {
            "score": flesch,
            "label": label
        }


    # ========================================================
    # TONE
    # ========================================================

    def _tone(
        self,
        text: str
    ):

        words = re.findall(
            r"[A-Za-z']+",
            text.lower()
        )


        positive_hits = sum(
            1
            for w in words
            if w in POSITIVE_WORDS
        )


        negative_hits = sum(
            1
            for w in words
            if w in NEGATIVE_WORDS
        )


        total = (
            positive_hits +
            negative_hits
        )


        if total == 0:

            return {

                "label":
                    "Neutral",

                "polarity":
                    0.0,

                "positive_hits":
                    positive_hits,

                "negative_hits":
                    negative_hits

            }


        polarity = round(
            (
                positive_hits -
                negative_hits
            ) / total,
            2
        )


        if polarity > 0.2:

            label = "Positive"

        elif polarity < -0.2:

            label = "Negative"

        else:

            label = "Neutral"


        return {

            "label":
                label,

            "polarity":
                polarity,

            "positive_hits":
                positive_hits,

            "negative_hits":
                negative_hits

        }


    # ========================================================
    # KEYWORDS
    # ========================================================

    def _keywords(
        self,
        text: str,
        limit: int = 8
    ):

        words = re.findall(
            r"[A-Za-z']{4,}",
            text.lower()
        )


        filtered = [
            w
            for w in words
            if w not in STOPWORDS
        ]


        counts = Counter(
            filtered
        )


        return [
            word
            for word, _
            in counts.most_common(limit)
        ]


    # ========================================================
    # HASHTAG IDEAS
    # ========================================================

    def _hashtag_ideas(
        self,
        text: str,
        tone_label: str,
        existing_hashtags: list,
        platform: str,
        limit: int = 8
    ):

        keywords = self._keywords(
            text,
            limit=limit
        )


        existing_lower = {
            h.lower()
            for h in existing_hashtags
        }


        ideas = []


        # Keyword hashtags

        for kw in keywords:

            tag = f"#{kw}"


            if (
                tag.lower()
                not in existing_lower
                and tag not in ideas
            ):

                ideas.append(tag)


        # Mood hashtags

        mood_key = (
            tone_label.lower()
            if tone_label.lower()
            in MOOD_HASHTAGS
            else "neutral"
        )


        for tag in MOOD_HASHTAGS[mood_key]:

            if (
                tag.lower()
                not in existing_lower
                and tag not in ideas
            ):

                ideas.append(tag)


        # Platform hashtags

        for tag in PLATFORM_HASHTAGS.get(
            platform,
            []
        ):

            if (
                tag.lower()
                not in existing_lower
                and tag not in ideas
            ):

                ideas.append(tag)


        return ideas[:limit]


    # ========================================================
    # CAPTION REWRITE
    # ========================================================

    def _rewrite_caption(
        self,
        text: str,
        hashtags_to_add: list,
        has_cta: bool,
        has_question: bool,
        platform: str
    ):

        cleaned = text.strip()


        sentences = _split_sentences(
            cleaned
        )


        if len(sentences) > 4:

            cleaned = (
                ". ".join(
                    sentences[:3]
                )
                .rstrip(".")
                + "."
            )


        parts = [
            cleaned
        ]


        # Platform-specific question

        if not has_question:

            if platform == "LinkedIn":

                parts.append(
                    "\n\nWhat are your thoughts on this?"
                )

            elif platform == "X":

                parts.append(
                    "\n\nWhat do you think?"
                )

            elif platform == "Facebook":

                parts.append(
                    "\n\nWhat do you think about this?"
                )

            else:

                parts.append(
                    "\n\nWhat's your take on this?"
                )


        # CTA

        if not has_cta:

            if platform == "LinkedIn":

                parts.append(
                    "\n\nShare your perspective in the comments."
                )

            elif platform == "X":

                parts.append(
                    "\n\nReply with your thoughts or repost if you agree."
                )

            elif platform == "Facebook":

                parts.append(
                    "\n\nLeave a comment or share this with someone who needs to see it."
                )

            else:

                parts.append(
                    "\n\nDrop a comment or share this with someone who needs to see it."
                )


        # Hashtags

        if hashtags_to_add:

            parts.append(
                "\n\n" +
                " ".join(
                    hashtags_to_add[:6]
                )
            )


        return "".join(parts).strip()


    # ========================================================
    # READINESS SCORE
    # ========================================================

    def _readiness_score(
        self,
        metrics: dict,
        readability: dict,
        tone: dict
    ):

        breakdown = []

        total = 0


        def add(
            factor,
            points,
            max_points
        ):

            nonlocal total

            total += points

            breakdown.append({

                "factor":
                    factor,

                "points":
                    points,

                "max":
                    max_points

            })


        wc = metrics[
            "word_count"
        ]


        if 15 <= wc <= 120:

            add(
                "Length",
                20,
                20
            )

        elif (
            8 <= wc < 15
            or
            120 < wc <= 180
        ):

            add(
                "Length",
                12,
                20
            )

        else:

            add(
                "Length",
                5,
                20
            )


        hc = metrics[
            "hashtag_count"
        ]


        if 3 <= hc <= 8:

            add(
                "Hashtags",
                15,
                15
            )

        elif 1 <= hc <= 10:

            add(
                "Hashtags",
                9,
                15
            )

        else:

            add(
                "Hashtags",
                3,
                15
            )


        add(
            "Call-to-action",
            15 if metrics["has_cta"] else 3,
            15
        )


        add(
            "Engagement hook",
            10 if metrics["question_marks"] > 0 else 3,
            10
        )


        add(
            "Emojis",
            10 if metrics["emoji_count"] > 0 else 4,
            10
        )


        r = readability.get(
            "score"
        )


        if r is None:

            add(
                "Readability",
                8,
                15
            )

        elif r >= 60:

            add(
                "Readability",
                15,
                15
            )

        elif r >= 40:

            add(
                "Readability",
                10,
                15
            )

        else:

            add(
                "Readability",
                5,
                15
            )


        if tone["label"] == "Positive":

            add(
                "Tone",
                15,
                15
            )

        elif tone["label"] == "Neutral":

            add(
                "Tone",
                11,
                15
            )

        else:

            add(
                "Tone",
                6,
                15
            )


        score = max(
            0,
            min(
                100,
                total
            )
        )


        if score >= 75:

            band = "Strong"

        elif score >= 50:

            band = "Moderate"

        else:

            band = "Needs work"


        return {

            "score":
                score,

            "band":
                band,

            "breakdown":
                breakdown

        }


    # ========================================================
    # NOTES
    # ========================================================

    def _build_notes(
        self,
        metrics: dict,
        has_link: bool,
        platform: str = "Instagram"
    ):

        notes = []

        wc = metrics[
            "word_count"
        ]


        # Length

        if wc < 10:

            notes.append({

                "type":
                    "Length",

                "severity":
                    "warning",

                "message":
                    "Post is very short. "
                    "Add more context or a hook "
                    "to draw readers in."

            })

        elif wc > 150:

            notes.append({

                "type":
                    "Length",

                "severity":
                    "warning",

                "message":
                    "Post is long for most feeds. "
                    "Consider trimming to the core message."

            })

        else:

            notes.append({

                "type":
                    "Length",

                "severity":
                    "good",

                "message":
                    f"Good length ({wc} words) "
                    "for most platforms."

            })


        # Hashtags

        if metrics[
            "hashtag_count"
        ] == 0:

            notes.append({

                "type":
                    "Hashtags",

                "severity":
                    "warning",

                "message":
                    "No hashtags found. "
                    "See the suggested hashtags below."

            })

        elif metrics[
            "hashtag_count"
        ] > 10:

            notes.append({

                "type":
                    "Hashtags",

                "severity":
                    "warning",

                "message":
                    f"{metrics['hashtag_count']} hashtags "
                    "may look spammy. "
                    "Trim to 5-10."

            })

        else:

            notes.append({

                "type":
                    "Hashtags",

                "severity":
                    "good",

                "message":
                    f"{metrics['hashtag_count']} hashtag(s) used."

            })


        # CTA

        if not metrics[
            "has_cta"
        ]:

            notes.append({

                "type":
                    "Call-to-action",

                "severity":
                    "warning",

                "message":
                    "No clear call-to-action. "
                    "Try the rewritten caption below."

            })

        else:

            notes.append({

                "type":
                    "Call-to-action",

                "severity":
                    "good",

                "message":
                    "Call-to-action detected."

            })


        # Question

        if metrics[
            "question_marks"
        ] == 0:

            notes.append({

                "type":
                    "Engagement hook",

                "severity":
                    "info",

                "message":
                    "Consider asking a question "
                    "to encourage replies."

            })


        # Emojis

        if metrics[
            "emoji_count"
        ] == 0:

            notes.append({

                "type":
                    "Emojis",

                "severity":
                    "info",

                "message":
                    "No emojis detected. "
                    "A couple can add visual appeal."

            })


        # Link

        if has_link:

            notes.append({

                "type":
                    "Links",

                "severity":
                    "info",

                "message":
                    "Outbound link detected -- "
                    "some platforms deprioritize linked posts."

            })


        # ====================================================
        # PLATFORM-SPECIFIC FEEDBACK
        # ====================================================

        if platform == "Instagram":

            if metrics[
                "hashtag_count"
            ] == 0:

                notes.append({

                    "type":
                        "Instagram",

                    "severity":
                        "info",

                    "message":
                        "Consider adding relevant "
                        "Instagram hashtags."

                })


            if metrics[
                "emoji_count"
            ] == 0:

                notes.append({

                    "type":
                        "Instagram",

                    "severity":
                        "info",

                    "message":
                        "A few relevant emojis can "
                        "make an Instagram caption "
                        "more visually engaging."

                })


        elif platform == "LinkedIn":

            if metrics[
                "emoji_count"
            ] > 3:

                notes.append({

                    "type":
                        "LinkedIn",

                    "severity":
                        "warning",

                    "message":
                        "Consider reducing emojis "
                        "for a more professional "
                        "LinkedIn style."

                })


            if wc < 20:

                notes.append({

                    "type":
                        "LinkedIn",

                    "severity":
                        "info",

                    "message":
                        "Consider adding more context "
                        "or professional insight."

                })


        elif platform == "X":

            if wc > 40:

                notes.append({

                    "type":
                        "X",

                    "severity":
                        "warning",

                    "message":
                        "Consider shortening the post "
                        "for a more concise X-style message."

                })


            if metrics[
                "hashtag_count"
            ] > 2:

                notes.append({

                    "type":
                        "X",

                    "severity":
                        "info",

                    "message":
                        "Consider using fewer hashtags "
                        "to keep the post clean."

                })


        elif platform == "Facebook":

            if metrics[
                "question_marks"
            ] == 0:

                notes.append({

                    "type":
                        "Facebook",

                    "severity":
                        "info",

                    "message":
                        "Try adding a question to "
                        "encourage Facebook discussions."

                })


        return notes