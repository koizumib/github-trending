import json

from trending_digest.storage import Store
from trending_digest.validate import validate_all

GOOD = {
    "repo": "o/r", "summarized_at": "2026-09-30",
    "short": "HTTP の負荷をかける小さな CLI。URL を指定して同時接続数とリクエスト数を決められる。",
    "what": "Web サーバーに負荷をかけて応答時間を測る CLI。",
    "can_do": ["同時接続数を指定してリクエストを送る"], "how_to_use": "go install で入れる。",
    "use_cases": ["リリース前の簡単な負荷試験"], "for_whom": "Web サーバーを運用する人",
    "similar": ["ab（Apache Bench）：ほぼ同じ用途"], "tech": "Go",
    "caveats": "", "sources": ["readme"], "confidence": "high", "confidence_note": "",
}


def write(store: Store, name: str, obj) -> None:
    path = store.dir / "repos" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False))


def test_good_summary_passes(tmp_path):
    store = Store(tmp_path / "data")
    write(store, "o__r.json", GOOD)
    problems, _ = validate_all(store, tmp_path / ".work")
    assert problems == {}


def test_missing_field_and_bad_confidence(tmp_path):
    store = Store(tmp_path / "data")
    bad = dict(GOOD, confidence="maybe")
    del bad["what"]
    write(store, "o__r.json", bad)
    problems, _ = validate_all(store, tmp_path / ".work")
    text = "\n".join(problems["data/repos/o__r.json"])
    assert "what" in text and "maybe" in text


def test_low_confidence_needs_note(tmp_path):
    store = Store(tmp_path / "data")
    write(store, "o__r.json", dict(GOOD, confidence="low", confidence_note=""))
    problems, _ = validate_all(store, tmp_path / ".work")
    assert "confidence_note" in "\n".join(problems["data/repos/o__r.json"])


def test_filename_must_match_repo(tmp_path):
    store = Store(tmp_path / "data")
    write(store, "wrong.json", GOOD)
    problems, _ = validate_all(store, tmp_path / ".work")
    assert "o__r.json" in "\n".join(problems["data/repos/wrong.json"])


def test_queue_leftovers_are_noted(tmp_path):
    store = Store(tmp_path / "data")
    write(store, "o__r.json", GOOD)
    store.dir.joinpath("daily").mkdir(parents=True)
    store.daily_path("2026-09-30").write_text(json.dumps(
        {"date": "2026-09-30", "items": [], "errors": [{"repo": "f/ail", "reason": "README が空"}]}))
    work = tmp_path / ".work"
    work.mkdir()
    (work / "queue.json").write_text(json.dumps({"date": "2026-09-30", "items": [
        {"repo": "o/r"}, {"repo": "f/ail"}, {"repo": "l/eft"}]}))
    problems, notes = validate_all(store, work)
    assert problems == {}
    assert notes == ["l/eft: 要約も errors の記録もない"]
