from __future__ import annotations

from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


def build_category_dataset() -> tuple[list[str], list[str]]:
    samples = [
        ("laptop stand quote qty 50 unit_price 88 shipping 20 lead_time 5", "office_hardware"),
        ("office chair quotation fabric model A quantity 30 unit price 260", "office_hardware"),
        ("display screen module price 320 lead_time 10 tax included", "electronics"),
        ("sensor board cable assembly quote 100pcs fob shenzhen", "electronics"),
        ("display driver board quotation quantity 20 unit price 300", "electronics"),
        ("oled screen module quote lead_time 14 shipping 50", "electronics"),
        ("touch panel lcd display quotation tax included", "electronics"),
        ("screen cable connector module报价 交期 10天 单价 25", "electronics"),
        ("carton box packaging quote 2000pcs delivery 7days", "packaging"),
        ("bubble mailer packaging bag报价 5000个 含税 运费另计", "packaging"),
        ("packaging carton printed box quotation 3000pcs", "packaging"),
        ("gift box shipping carton delivery 9 days", "packaging"),
        ("steel bracket industrial fastener quote delivery 15 days", "industrial_parts"),
        ("bearing sensor housing cnc parts quotation", "industrial_parts"),
        ("cnc metal fixture screw housing quote", "industrial_parts"),
        ("motor bracket bearing shell delivery 18 days", "industrial_parts"),
        ("纸箱 包装 报价 交期 7天 单价 1.6", "packaging"),
        ("显示屏 模组 报价 单价 320 交期 12天", "electronics"),
        ("显示模组 屏线 连接器 报价 交期 8天", "electronics"),
        ("传感器 电路板 排线 报价 单价 18", "electronics"),
        ("办公支架 报价 数量 50 单价 88", "office_hardware"),
        ("办公椅 升降桌 报价 交期 6天", "office_hardware"),
        ("机械 零件 轴承 外壳 报价 交期 20天", "industrial_parts"),
    ]
    texts = [item[0] for item in samples]
    labels = [item[1] for item in samples]
    return texts, labels


def build_document_dataset() -> tuple[list[str], list[str]]:
    samples = [
        ("formal quotation total amount tax included payment terms net30", "formal_quote"),
        ("please quote 100pcs with lead time and shipping", "request_for_quote"),
        ("老板这边给你报个价 单价88 交期5天", "chat_quote"),
        ("need price for 200 carton boxes urgent reply", "request_for_quote"),
        ("quotation sheet product unit price total price valid until may", "formal_quote"),
        ("微信里先报价 含税 运费另算", "chat_quote"),
        ("pdf quotation with item table delivery schedule", "formal_quote"),
        ("能不能先给个报价和交期", "request_for_quote"),
        ("先口头报价 一个80 量大再谈", "chat_quote"),
        ("quotation for display module item total amount and shipping", "formal_quote"),
        ("need your best quotation for screen module this week", "request_for_quote"),
        ("微信先报个价 明天确认数量", "chat_quote"),
    ]
    texts = [item[0] for item in samples]
    labels = [item[1] for item in samples]
    return texts, labels


def train_pipeline(texts: list[str], labels: list[str]) -> Pipeline:
    return Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), analyzer="char_wb", min_df=1)),
            ("clf", LogisticRegression(max_iter=400, random_state=42)),
        ]
    ).fit(texts, labels)


def main() -> None:
    category_texts, category_labels = build_category_dataset()
    document_texts, document_labels = build_document_dataset()

    category_pipeline = train_pipeline(category_texts, category_labels)
    document_pipeline = train_pipeline(document_texts, document_labels)

    output_dir = Path("models")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "quote_text_classifier.joblib"

    joblib.dump(
        {
            "category_pipeline": category_pipeline,
            "document_pipeline": document_pipeline,
            "category_labels": sorted(set(category_labels)),
            "document_type_labels": sorted(set(document_labels)),
        },
        output_path,
    )

    print(output_path)


if __name__ == "__main__":
    main()
