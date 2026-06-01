from endo_ai_assistant import EndoscopyReport, EndoscopyType, render_report
from endo_ai_assistant.dev_extractors import SyntheticGastroscopyExtractor


RAW_INPUT = (
    "ЭГДС. В антральном отделе желудка по малой кривизне эрозия до 3 мм, "
    "фибринозный налет. В луковице ДПК язвенный дефект 6 мм без признаков "
    "активного кровотечения."
)


def build_synthetic_report() -> EndoscopyReport:
    return SyntheticGastroscopyExtractor().extract(
        raw_input=RAW_INPUT,
        exam_type=EndoscopyType.GASTROSCOPY,
    )


if __name__ == "__main__":
    print(render_report(build_synthetic_report()))
