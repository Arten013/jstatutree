ETYPES_DICT = {
    # その法令が本来の目的とする事項についての実質的な規定が置かれる部分
    "MainProvision": "本則",

    # 本則の諸規定に伴って必要とされる付随的な規定が置かれる部分
    "SupplProvision": "附則", 

    # 条文の論理的な体系に基づいた区分
    # 条文が多い法令においてのみ使用
    "Part": "編",
    "Chapter": "章",
    "Section": "節",
    "Subsection": "款",
    "Division": "目",

    # 本則を構成する基本単位となるもの
    "Article": "条",

    # 条の中に必ず1つ以上設けられる要素
    # いわゆる条文が記される部分
    "Paragraph": "項",

    # 項の条文の中で事物の名称等を列記する必要がある場合に用いられるもの
    "Item": "号",

    # 号が複数階層を持った場合
    "Subitem1": "号",
    "Subitem2": "号", 
    "Subitem3": "号",
    "Subitem4": "号",
    "Subitem5": "号",

    # 文字列
    "ArticleCaption": "条見出し",
    "ParagraphSentence": "文",
    "ItemSentence": "文",
    } 
ETYPES = [
    "MainProvision",
    "SupplProvision",
    "Part",
    "Chapter",
    "Section",
    "Subsection",
    "Division",
    "Article",
    "Paragraph",
    "Item",
    "Subitem1",
    "Subitem2", 
    "Subitem3",
    "Subitem4",
    "Subitem5",
    "ArticleCaption",
    "ParagraphSentence",
    "ItemSentence",
]

BASIC_ETYPE_SET = [e for e in ETYPES if e != "SupplProvision"]
ETYPES_INV = dict([(e, i) for i, e in enumerate(ETYPES)])