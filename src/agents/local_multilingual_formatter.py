"""Evidence-gated multilingual formatting for local RAG.

Deterministic templates; no external translation or LLM calls.
"""

import re

from src.agents.local_rag_formatter import format_rag_answer
from src.agents.local_fact_extractor import extract_return_facts
from src.rag.metadata_filter import (
    RETURN_TERMS,
    DELIVERY_TERMS,
    WARRANTY_TERMS,
    contains_term,
)


def detect_language(question):
    """Detect supported language from conservative lexical signals."""
    text = question.casefold()

    french = (
        "quelle", "quelles", "quel", "quels",
        "livraison", "garantie", "puis-je",
        "retourner", "jours", "produit",
    )
    german = (
        "wie", "welche", "welcher", "welches",
        "lieferung", "garantie für", "rückgabe",
        "werktage", "bestellung", "gilt",
        "kann", "ich", "zurückgeben",
        "zurückschicken", "zurücksenden",
    )

    fr = sum(contains_term(text, (term,)) for term in french)
    de = sum(contains_term(text, (term,)) for term in german)

    if fr > de and fr > 0:
        return "fr"

    if de > fr and de > 0:
        return "de"

    return "en"


def detect_topic(question):
    """Return a topic only when exactly one is detected."""
    text = question.casefold()
    matches = []

    for topic, terms in (
        ("RETURN", RETURN_TERMS),
        ("DELIVERY", DELIVERY_TERMS),
        ("WARRANTY", WARRANTY_TERMS),
    ):
        if contains_term(text, terms):
            matches.append(topic)

    # German delivery compounds may not match standalone
    # lexical terms such as "Lieferung".
    german_delivery_expressions = (
        "standardlieferung",
        "lieferzeit",
        "lieferdauer",
        "lieferverzögerung",
    )

    if any(
        contains_term(text, (term,))
        for term in german_delivery_expressions
    ):
        if "DELIVERY" not in matches:
            matches.append("DELIVERY")

    # Additional multilingual return expressions.
    return_expressions = (
        "retourner",
        "retourner un produit",
        "zurückgeben",
        "zurückgeben?",
        "zurückschicken",
    )

    if any(
        contains_term(text, (term,))
        for term in return_expressions
    ):
        if "RETURN" not in matches:
            matches.append("RETURN")

    return matches[0] if len(matches) == 1 else None


def format_multilingual_answer(documents, question):
    """Use templates only when the required facts are evidenced."""
    language = detect_language(question)
    topic = detect_topic(question)

    evidence = " ".join(
        str(doc.get("chunk_text", ""))
        for doc in documents
        if doc.get("chunk_text")
    )

    if not evidence.strip():
        return format_rag_answer(documents, question=question)

    if topic == "WARRANTY":
        product_match = re.search(
            r"\bPROD-\d+\b",
            question,
            flags=re.IGNORECASE,
        )

        period_match = re.search(
            r"\b(?:warranty period\s*:\s*)"
            r"(\d+)\s+months?\b",
            evidence,
            flags=re.IGNORECASE,
        )

        if product_match and period_match:
            product_id = product_match.group(0).upper()
            months = int(period_match.group(1))

            # Only use evidence belonging to the requested product.
            matching_documents = [
                doc for doc in documents
                if product_id.casefold()
                in (
                    str(doc.get("file_name", "")) + " " +
                    str(doc.get("chunk_text", ""))
                ).casefold()
            ]

            matching_evidence = " ".join(
                str(doc.get("chunk_text", ""))
                for doc in matching_documents
            )

            matching_period = re.search(
                r"\bwarranty period\s*:\s*(\d+)\s+months?\b",
                matching_evidence,
                flags=re.IGNORECASE,
            )

            if matching_period:
                months = int(matching_period.group(1))

                templates = {
                    "fr": (
                        f"La garantie du produit {product_id} "
                        f"est de {months} mois."
                    ),
                    "de": (
                        f"Die Garantie für das Produkt {product_id} "
                        f"beträgt {months} Monate."
                    ),
                    "en": (
                        f"The warranty for product {product_id} "
                        f"is {months} months."
                    ),
                }

                answer = templates[language]

                if re.search(
                    r"\bmanufacturing defects\b",
                    matching_evidence,
                    flags=re.IGNORECASE,
                ):
                    coverage_templates = {
                        "fr": (
                            " La garantie couvre les défauts "
                            "de fabrication."
                        ),
                        "de": (
                            " Die Garantie deckt "
                            "Herstellungsfehler ab."
                        ),
                        "en": (
                            " The warranty covers "
                            "manufacturing defects."
                        ),
                    }

                    answer += coverage_templates[language]

                return answer

    # Mixed return/warranty questions require the return
    # policy explanation, even when generic topic detection
    # returns None.
    mixed_return_warranty = bool(
        re.search(
            r"\b(?:warranty|garantie|gewährleistung)\b",
            question,
            flags=re.IGNORECASE,
        )
        and re.search(
            r"\b(?:return|refund|retour|retourner|"
            r"rückgabe|zurückgeben|erstattung)\b",
            question,
            flags=re.IGNORECASE,
        )
    )

    if mixed_return_warranty:
        topic = "RETURN"

    if topic == "DELIVERY":
        duration = re.search(
            r"\b(?:2\s*(?:to|and|-)\s*4\s*business days"
            r"|2\s*(?:und|bis|-)\s*4\s*Werktagen"
            r"|between\s+2\s+and\s+4\s+business days)\b",
            evidence,
            flags=re.IGNORECASE,
        )

        if duration:
            templates = {
                "fr": (
                    "La livraison standard prend généralement "
                    "entre 2 et 4 jours ouvrables."
                ),
                "de": (
                    "Die Standardlieferung dauert normalerweise "
                    "zwischen 2 und 4 Werktagen."
                ),
                "en": (
                    "Standard delivery normally takes "
                    "between 2 and 4 business days."
                ),
            }

            paragraphs = [templates[language]]

            tracking_evidence = re.search(
                r"(?:check their order status using their order number"
                r"|status ihrer Bestellung anhand ihrer Bestellnummer"
                r"|check their order status using their order number)",
                evidence,
                flags=re.IGNORECASE,
            )

            if tracking_evidence:
                tracking_templates = {
                    "fr": (
                        "Vous pouvez suivre le statut de votre "
                        "commande à l'aide de votre numéro "
                        "de commande."
                    ),
                    "de": (
                        "Sie können den Status Ihrer Bestellung "
                        "mit Ihrer Bestellnummer überprüfen."
                    ),
                    "en": (
                        "You can check your order status "
                        "using your order number."
                    ),
                }

                paragraphs.append(tracking_templates[language])

            delay_evidence = re.search(
                r"(?:marked as DELAYED.*?"
                r"(?:verify|check).*?logistics"
                r"|als DELAYED markiert.*?"
                r"Logistikdaten prüfen"
                r"|delayed orders.*?"
                r"(?:consult|verify).*?"
                r"(?:order information|logistics information))",
                evidence,
                flags=re.IGNORECASE,
            )

            if delay_evidence:
                delay_templates = {
                    "fr": (
                        "En cas de retard, le service client "
                        "doit vérifier les informations "
                        "logistiques les plus récentes avant "
                        "de communiquer une date de livraison."
                    ),
                    "de": (
                        "Bei einer Lieferverzögerung sollte "
                        "der Kundenservice die aktuellen "
                        "Logistikdaten prüfen, bevor er einen "
                        "Liefertermin mitteilt."
                    ),
                    "en": (
                        "For delayed orders, customer support "
                        "should verify the latest logistics "
                        "information before providing a "
                        "delivery date."
                    ),
                }

                paragraphs.append(delay_templates[language])

            return "\n\n".join(paragraphs)

    if topic == "RETURN":
        return_documents = [
            doc for doc in documents
            if (
                "return_policy" in str(
                    doc.get("file_name", "")
                ).lower()
                or "returns_faq" in str(
                    doc.get("file_name", "")
                ).lower()
            )
        ]

        facts = extract_return_facts(return_documents)

        if facts:
            templates = {
                "fr": {
                    "return_window": (
                        "Les clients peuvent demander un retour "
                        "dans les 30 jours suivant la livraison."
                    ),
                    "product_condition": (
                        "Le produit doit normalement être retourné "
                        "dans un état acceptable."
                    ),
                    "order_verification": (
                        "Le service client doit vérifier la "
                        "commande avant d'approuver le retour."
                    ),
                    "refund": (
                        "Le remboursement est traité après "
                        "l'inspection du produit retourné."
                    ),
                    "exceptions": (
                        "Certains produits peuvent être soumis "
                        "à des conditions particulières."
                    ),
                },
                "de": {
                    "return_window": (
                        "Kunden können innerhalb von 30 Tagen "
                        "nach der Lieferung eine Rückgabe beantragen."
                    ),
                    "product_condition": (
                        "Das Produkt muss normalerweise in einem "
                        "akzeptablen Zustand zurückgegeben werden."
                    ),
                    "order_verification": (
                        "Der Kundenservice muss die Bestellung "
                        "vor der Genehmigung prüfen."
                    ),
                    "refund": (
                        "Die Erstattung erfolgt nach der "
                        "Prüfung des zurückgesendeten Produkts."
                    ),
                    "exceptions": (
                        "Für bestimmte Produkte können "
                        "besondere Rückgabebedingungen gelten."
                    ),
                },
                "en": {
                    "return_window": (
                        "Customers may request a return within "
                        "30 days after delivery."
                    ),
                    "product_condition": (
                        "Returned products must normally be "
                        "in acceptable condition."
                    ),
                    "order_verification": (
                        "Customer service must verify the order "
                        "before approving a return."
                    ),
                    "refund": (
                        "Refunds are processed after inspection "
                        "of the returned product."
                    ),
                    "exceptions": (
                        "Some products may have specific "
                        "return conditions."
                    ),
                },
            }

            # The current templates apply to the verified
            # 30-day synthetic policy only.
            window = facts.get("return_window", "")
            has_30_day_window = bool(
                re.search(
                    r"\b30\s+days\b",
                    window,
                    flags=re.IGNORECASE,
                )
            )

            categories = (
                "return_window",
                "product_condition",
                "order_verification",
                "refund",
                "exceptions",
            )

            paragraphs = [
                templates[language][category]
                for category in categories
                if category in facts
                and (
                    category != "return_window"
                    or has_30_day_window
                )
            ]

            if paragraphs:
                # Answer explicitly when the question concerns
                # a return after the standard 30-day window.
                after_window = bool(
                    re.search(
                        r"\b(?:après|after|nach)\s+30\s+"
                        r"(?:jours|days|tagen)\b",
                        question,
                        flags=re.IGNORECASE,
                    )
                )

                requested_days = re.search(
                    r"\b(?:after|après|nach)\s+(\d+)\s+"
                    r"(?:days?|jours?|tagen?)\b",
                    question,
                    flags=re.IGNORECASE,
                )

                beyond_standard_window = bool(
                    requested_days
                    and int(requested_days.group(1)) > 30
                )

                if (
                    has_30_day_window
                    and (after_window or beyond_standard_window)
                ):
                    explanations = {
                        "fr": (
                            "Après 30 jours suivant la livraison, "
                            "le délai standard pour demander un "
                            "retour est dépassé. Cela ne permet "
                            "pas de conclure automatiquement "
                            "qu'aucune exception n'est possible. "
                            "Le service client doit vérifier "
                            "les conditions applicables."
                        ),
                        "de": (
                            "Nach 30 Tagen ab Lieferung ist die "
                            "reguläre Rückgabefrist überschritten. "
                            "Ob eine Ausnahme möglich ist, muss "
                            "der Kundenservice anhand der "
                            "geltenden Bedingungen prüfen."
                        ),
                        "en": (
                            "After 30 days from delivery, the "
                            "standard return request window has "
                            "expired. Customer service must check "
                            "the applicable conditions before "
                            "determining whether an exception "
                            "is possible."
                        ),
                    }

                    return (
                        explanations[language]
                        + "\n\n"
                        + "\n\n".join(paragraphs)
                    )

                warranty_return_question = bool(
                    re.search(
                        r"\b(?:warranty|garantie|gewährleistung)\b",
                        question,
                        flags=re.IGNORECASE,
                    )
                    and re.search(
                        r"\b(?:return|refund|retour|retourner|"
                        r"rückgabe|zurückgeben|erstattung)\b",
                        question,
                        flags=re.IGNORECASE,
                    )
                )

                if warranty_return_question and has_30_day_window:
                    distinctions = {
                        "fr": (
                            "La garantie et le retour sont des "
                            "procédures distinctes. Une garantie "
                            "ne prolonge pas automatiquement le "
                            "délai standard de retour de 30 jours. "
                            "Le service client doit vérifier les "
                            "conditions applicables à la garantie."
                        ),
                        "de": (
                            "Garantie und Rückgabe sind "
                            "unterschiedliche Verfahren. "
                            "Eine Garantie verlängert die "
                            "reguläre Rückgabefrist von "
                            "30 Tagen nicht automatisch. "
                            "Der Kundenservice muss die "
                            "geltenden Bedingungen prüfen."
                        ),
                        "en": (
                            "Warranty and returns are separate "
                            "processes. A warranty does not "
                            "automatically extend the standard "
                            "30-day return window. "
                            "Customer service must verify the "
                            "applicable warranty conditions."
                        ),
                    }

                    return (
                        distinctions[language]
                        + "\n\n"
                        + "\n\n".join(paragraphs)
                    )

                return "\n\n".join(paragraphs)

    return format_rag_answer(documents, question=question)
