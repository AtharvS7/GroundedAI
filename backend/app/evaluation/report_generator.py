"""PDF report generator for evaluation results.

Generates a professional PDF report using reportlab with:
- Cover page, executive summary, metric charts, and conclusion.
"""

from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


def generate_eval_report(
    eval_results: List[Dict],
    output_path: str = "groundedai_eval_report.pdf",
) -> str:
    """Generate a PDF evaluation report.

    Args:
        eval_results: List of evaluation result dictionaries.
        output_path: File path for the generated PDF.

    Returns:
        Path to the generated PDF file.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        logger.error("reportlab not installed. Cannot generate PDF report.")
        return ""

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    styles = getSampleStyleSheet()
    story = []

    # Title style
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor("#6C63FF"),
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor("#3B82F6"),
    )

    # ── Cover Page ──────────────────────────────────────────
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("GroundedAI", title_style))
    story.append(
        Paragraph("Evaluation Report", styles["Heading2"])
    )
    story.append(Spacer(1, 0.5 * inch))
    story.append(
        Paragraph(
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph("Model: mistral:7b-instruct-q4_K_M", styles["Normal"])
    )
    story.append(
        Paragraph(
            "Embedding: all-MiniLM-L6-v2 (384d)", styles["Normal"]
        )
    )
    story.append(Spacer(1, 1 * inch))

    # ── Executive Summary ───────────────────────────────────
    story.append(Paragraph("Executive Summary", heading_style))

    if eval_results:
        avg_rouge = sum(r.get("rouge_l", 0) for r in eval_results) / len(
            eval_results
        )
        avg_bleu = sum(r.get("bleu_4", 0) for r in eval_results) / len(
            eval_results
        )
        avg_faith = sum(
            r.get("faithfulness", 0) for r in eval_results
        ) / len(eval_results)
        avg_delta = sum(
            r.get("hallucination_delta", 0) for r in eval_results
        ) / len(eval_results)

        summary_data = [
            ["Metric", "Average Score"],
            ["ROUGE-L (F1)", f"{avg_rouge:.4f}"],
            ["BLEU-4", f"{avg_bleu:.4f}"],
            ["Faithfulness", f"{avg_faith:.4f}"],
            ["Hallucination Delta", f"{avg_delta:+.4f}"],
            ["Queries Evaluated", str(len(eval_results))],
        ]

        summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6C63FF")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8F9FA")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F3F5")]),
                ]
            )
        )
        story.append(summary_table)
    else:
        story.append(
            Paragraph("No evaluation results available.", styles["Normal"])
        )

    story.append(Spacer(1, 0.5 * inch))

    # ── Detailed Results ────────────────────────────────────
    story.append(Paragraph("Detailed Results", heading_style))

    if eval_results:
        detail_headers = [
            "Query ID",
            "ROUGE-L",
            "BLEU-4",
            "Faith.",
            "P@5",
            "R@5",
            "MRR",
            "Δ Hall.",
        ]
        detail_data = [detail_headers]

        for r in eval_results[:20]:  # Limit to 20 rows
            detail_data.append(
                [
                    r.get("query_id", "")[:8] + "...",
                    f"{r.get('rouge_l', 0):.3f}",
                    f"{r.get('bleu_4', 0):.3f}",
                    f"{r.get('faithfulness', 0):.3f}",
                    f"{r.get('precision_k', 0):.3f}",
                    f"{r.get('recall_k', 0):.3f}",
                    f"{r.get('mrr', 0):.3f}",
                    f"{r.get('hallucination_delta', 0):+.3f}",
                ]
            )

        col_widths = [1.0 * inch] + [0.7 * inch] * 7
        detail_table = Table(detail_data, colWidths=col_widths)
        detail_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3B82F6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F3F5")]),
                ]
            )
        )
        story.append(detail_table)

    story.append(Spacer(1, 0.5 * inch))

    # ── Conclusion ──────────────────────────────────────────
    story.append(Paragraph("Conclusion", heading_style))
    if eval_results:
        avg_delta = sum(
            r.get("hallucination_delta", 0) for r in eval_results
        ) / len(eval_results)

        if avg_delta > 0:
            conclusion = (
                f"The RAG pipeline demonstrates a positive hallucination "
                f"reduction delta of {avg_delta:+.4f}, confirming that "
                f"retrieval-augmented generation produces more faithful "
                f"responses than baseline LLM inference alone."
            )
        else:
            conclusion = (
                "The evaluation results suggest further tuning may be "
                "needed to improve RAG pipeline faithfulness."
            )
        story.append(Paragraph(conclusion, styles["Normal"]))
    else:
        story.append(
            Paragraph(
                "Run evaluations to generate conclusive results.",
                styles["Normal"],
            )
        )

    # Build PDF
    doc.build(story)
    logger.info(f"Evaluation report generated: {output_path}")
    return output_path
