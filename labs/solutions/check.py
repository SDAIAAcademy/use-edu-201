# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Runs the solution of every lab and prints PASS or the first difference.

  uv run labs/solutions/check.py          # every lab
  uv run labs/solutions/check.py 1.2 2.1  # some

It reads the participants' files in labs/files/, recomputes each number independently of the
generator and compares it with labs/solutions/key.json. It writes nothing and calls no language
model: where a lab has the participant talk to an assistant, the scripted replies of
standin.json stand in for it.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = HERE.parent / "files"
KEY = json.loads((HERE / "key.json").read_text(encoding="utf-8"))
STANDIN = json.loads((HERE / "standin.json").read_text(encoding="utf-8"))


def expect(name: str, got, want) -> None:
    if got != want:
        print(f"FAIL  {name}: got {got!r}, expected {want!r}")
        raise SystemExit(1)
    print(f"ok    {name}: {got}")


def rows(path: Path) -> list[list[str]]:
    return [r for r in csv.reader(path.read_text(encoding="utf-8-sig").splitlines()) if r]


def level(score: str, supervised: str) -> int:
    if supervised == "نعم" or score == "":
        return 0
    s = int(score)
    return 3 if s >= 70 else 2 if s >= 50 else 1


def lab_1_1() -> None:
    table = rows(FILES / "stress_tests" / "summary.csv")[1:]
    levels = {r[0]: level(r[4], r[3]) for r in table}
    expect("1.1 exposure level of each task", levels, {t: v["level"] for t, v in KEY["stress"].items()})
    expect("1.1 weights add up to 100", sum(int(r[2]) for r in table), 100)
    expect("1.1 weight at level 2 or 3", sum(int(r[2]) for r in table if levels[r[0]] >= 2), KEY["exposed_weight_level2_plus"])
    expect("1.1 weight at level 3", sum(int(r[2]) for r in table if levels[r[0]] == 3), KEY["exposed_weight_level3"])
    t1 = (FILES / "stress_tests" / "T1.txt").read_text(encoding="utf-8")
    expect("1.1 T1 record states 48 of 50", "48 إجابة صحيحة من 50" in t1, True)
    t2 = (FILES / "stress_tests" / "T2.txt").read_text(encoding="utf-8")
    expect("1.1 T2 record states the score in the summary", f"{table[1][4]} من 100" in t2, True)
    parts = [int(x) for x in re.findall(r"(\d+) من (?:20|30)", STANDIN["stress"]["T2"]["note"])]
    expect("1.1 T2 rubric parts add up to its score", sum(parts), int(table[1][4]))
    ref = rows(FILES / "start" / "audit_table_osh214.csv")[1:]
    expect("1.1 reference audit agrees with the scale", [int(r[4]) for r in ref], [levels[r[0].split(" ")[0]] for r in ref])
    blank = rows(FILES / "audit_table.csv")
    expect("1.1 blank audit table: one solved row, two own rows, five to fill", [len(blank), blank[1][4], blank[2][1]], [9, "3", ""])


def lab_1_2() -> None:
    cohorts, per = [30, 240, 3000], 4
    fa = KEY["false_accusations"]
    expect("1.2 expected false accusations at 1%", [round(n * 0.01, 2) for n in cohorts], fa["rate_1"])
    expect("1.2 chance of at least one, per cent", [round((1 - 0.99 ** n) * 100, 1) for n in cohorts], fa["at_least_one_pct"])
    expect("1.2 at 1% with four submissions each", [round(n * per * 0.01, 2) for n in cohorts], fa["rate_1_four_submissions"])
    expect("1.2 at 4%", [round(n * 0.04, 2) for n in cohorts], fa["rate_4"])
    expect("1.2 at 9%", [round(n * 0.09, 2) for n in cohorts], fa["rate_9"])
    for name, fpr, sens in (("a", 0.01, 0.90), ("b", 0.04, 0.40), ("c", 0.09, 0.26)):
        ai, honest = 24, 216
        t, f = round(ai * sens, 2), round(honest * fpr, 2)
        expect(f"1.2 flags under assumption {name}: true, false, honest share %", [t, f, round(f / (t + f) * 100, 1)], fa[f"share_{name}"])
    expect("1.2 stretch: rate for one false accusation a year, per cent", round(1 / 12000 * 100, 4), fa["stretch_rate_pct"])
    claim = (FILES / "detector_claim.txt").read_text(encoding="utf-8")
    expect("1.2 the claim sheet gives the rate and the three cohorts", all(s in claim for s in ("1%", "30 متدرب", "240 متدرب", "3,000 متدرب")), True)
    sheet = rows(FILES / "false_accusations_sheet.csv")
    expect("1.2 the participants' sheet holds no answer", all(c == "" for r in sheet[1:6] for c in r[1:]), True)


def secure_before(path: Path, gate: str, week: int) -> list[str]:
    out = []
    for r in rows(path)[1:]:
        last_week = int(re.findall(r"\d+", r[1])[-1])
        if r[3] == "مؤمَّن" and r[5] == gate and last_week <= week:
            out.append(r[0].split(" ")[0])
    return out


def lab_1_3() -> None:
    gates = {g: v["week"] for g, v in KEY["gates"].items()}
    # today's plan: supervised tasks and their weeks, from the course card
    card = (FILES / "course_osh214.txt").read_text(encoding="utf-8")
    today = {m[0]: int(m[1]) for m in re.findall(r"(T\d) · [^\n]*الأسبوع (?:\d+ إلى )?(\d+)\n\s+الظروف: [^\n]*(?:مراقَب|بحضور المدرّس)", card)}
    expect("1.3 supervised tasks today and their weeks", today, {"T4": 9, "T6": 12})
    expect("1.3 planted: no supervised task by gate A today", [t for t, w in today.items() if w <= gates["A"]], [])
    ref = FILES / "start" / "lane_map_osh214.csv"
    expect("1.3 reference map: secure task at gate A", secure_before(ref, "أ", gates["A"]), ["T4أ"])
    expect("1.3 reference map: secure tasks at gate B", secure_before(ref, "ب", gates["B"]), ["T5ب", "T6"])
    table = rows(ref)[1:]
    expect("1.3 reference map: weights add up to 100", sum(int(r[2]) for r in table), 100)
    expect("1.3 reference map: secure share of the grade", sum(int(r[2]) for r in table if r[3] == "مؤمَّن"), 50)
    expect("1.3 reference map: every task has a reason", all(r[4] for r in table), True)


def rule(policy: dict, case: dict) -> str:
    """Applies a course policy, written as rules, to one case."""
    if case["lane"] == "secure":
        return "مخالفة" if case["observed_use"] and policy["secure_tasks"] == "no_ai_under_supervision" else "مسموح"
    if not case["disclosed"]:
        # a detector score is never a finding: the missing disclosure is what the policy acts on
        return "يحتاج إلى خطوة" if policy["disclosure_missing"] == "incomplete_until_evidence" else "غير محدد"
    if policy["open_tasks"] == "any_use_with_disclosure":
        return "مسموح"
    return "غير محدد"   # "limited use": two readers decide differently


def lab_1_4() -> None:
    p = KEY["policy"]
    got = {str(c["id"]): rule(p["reference"], c) for c in p["cases"]}
    expect("1.4 reference policy on the three cases", got, {str(k): v for k, v in p["rulings"].items()})
    expect("1.4 a 'limited use' clause leaves case 1 undecided", rule(p["ambiguous"], p["cases"][0]), "غير محدد")
    expect("1.4 the detector score changes no ruling", rule(p["reference"], dict(p["cases"][2], detector=5)), rule(p["reference"], p["cases"][2]))
    expect("1.4 suspicion steps end with the committee hearing the learner", p["reference"]["suspicion_steps"][-1], "قرار اللجنة بعد سماع المتعلم")
    labels = [r[6][0] for r in rows(FILES / "start" / "lane_map_osh214.csv")[1:]]
    lanes = [r[3] for r in rows(FILES / "start" / "lane_map_osh214.csv")[1:]]
    expect("1.4 every secure task is labelled level 1 and no open task is", [(ln == "مؤمَّن") == (lb == "1") for ln, lb in zip(lanes, labels)], [True] * 7)
    template = (FILES / "policy_template.txt").read_text(encoding="utf-8")
    expect("1.4 the template has five clauses", len(re.findall(r"^البند \d", template, flags=re.M)), 5)


def stats(folder: str) -> dict:
    v = [[int(x) for x in r[:6]] for r in rows(FILES / "submissions" / folder / "version_history.csv")[1:]]
    final = sum(r[3] for r in v) - sum(r[4] for r in v)
    det = int(re.search(r"(\d+)%", (FILES / "submissions" / folder / "detector_report.txt").read_text(encoding="utf-8")).group(1))
    return {"sessions": len(v), "minutes": sum(r[2] for r in v), "final_words": final, "largest_insertion": max(r[5] for r in v),
            "largest_share_pct": round(max(r[5] for r in v) / final * 100, 1), "days_active": len({r[1] for r in v}), "detector": det}


def lab_2_1() -> None:
    a, b = stats("A_qais"), stats("B_zahra")
    expect("2.1 submission A", a, KEY["submissions"]["A"])
    expect("2.1 submission B", b, KEY["submissions"]["B"])
    expect("2.1 planted: the detector flags the incremental draft, not the single paste", [a["detector"] < 50 < b["detector"], a["largest_share_pct"] > 90, b["largest_share_pct"] < 5], [True, True, True])
    ta = (FILES / "submissions" / "A_qais" / "ai_transcript.txt").read_text(encoding="utf-8")
    tb = (FILES / "submissions" / "B_zahra" / "ai_transcript.txt").read_text(encoding="utf-8")
    expect("2.1 transcripts: A attached none, B attached three exchanges", ["لم يُرفق" in ta, len(re.findall(r"^التبادل \d", tb, flags=re.M))], [True, 3])
    bank = (FILES / "start" / "question_bank.txt").read_text(encoding="utf-8")
    expect("2.1 the fallback bank has six questions", len(re.findall(r"^\d\. ", bank, flags=re.M)), 6)


def lab_2_2() -> None:
    o = KEY["oral"]
    totals = {k: sum(v) for k, v in o["reference_marks"].items()}
    expect("2.2 reference totals out of 12", totals, {"A": 3, "B": 11})
    rub = rows(FILES / "oral" / "rubric_template.csv")
    expect("2.2 rubric: four criteria, none about fluency", [[r[0] for r in rub[1:5]], any("طلاقة" in r[0] or "اللغة" in r[0] for r in rub)], [o["criteria"], False])
    sample = {"A": [1, 2, 0, 1], "B": [3, 2, 2, 3]}   # a plausible pair of markers' sheets
    expect("2.2 a sample marking falls within the tolerance", [abs(sum(sample[k]) - totals[k]) <= o["tolerance"] for k in "AB"], [True, True])
    cases = (FILES / "oral" / "random_cases.txt").read_text(encoding="utf-8")
    expect("2.2 four random cases", len(re.findall(r"^\d\. ", cases, flags=re.M)), 4)
    expect("2.2 thirty orals of five minutes, in minutes", 30 * 5, 150)


def judged(rubric: list) -> int:
    return sum(w for name, w in rubric if any(k in name for k in ("الحكم", "نقد", "الدليل الإجرائي", "المناقشة")))


def lab_2_3() -> None:
    r = KEY["rubrics"]
    for name in ("old", "start", "fixed"):
        expect(f"2.3 {name} rubric adds up to 100", sum(w for _n, w in r[name]), 100)
    expect("2.3 weight on judgement, critique, process and defence: old, start, fixed", [judged(r["old"]), judged(r["start"]), judged(r["fixed"])], [0, 75, 85])
    start = rows(FILES / "start" / "T2_rewritten_rubric.csv")[1:]
    expect("2.3 the starting rubric file is the start rubric", [[a, int(b)] for a, b in start], [list(x) for x in r["start"]])
    brief = (FILES / "start" / "T2_rewritten_brief.txt").read_text(encoding="utf-8")
    expect("2.3 the rewritten brief names the lane, the label, the evidence, the defence and the alternative",
           [k in brief for k in ("المسار: مفتوح", "تصنيف الاستخدام", "سجل الإصدارات", "مناقشة شفهية", "التيسير")], [True] * 5)
    log = (FILES / "start" / "workshop3_near_miss_log.txt").read_text(encoding="utf-8")
    costs = [int(x.replace(",", "")) for x in re.findall(r": ([\d,]+) ريال\.", log)]
    budget = costs.pop()
    pairs = sorted(a + b for i, a in enumerate(costs) for b in costs[i + 1:])
    expect("2.3 the budget of 6,000 covers two of the three pairs of controls: pair costs", [budget, pairs], [6000, [5800, 5900, 6900]])


def lab_2_4() -> None:
    rt, r, k = STANDIN["retest"], KEY["rubrics"], KEY["retest"]
    start = sum(rt["marks_start"][n] for n, _w in r["start"])
    fixed = sum(rt["marks_fixed"][n] for n, _w in r["fixed"])
    expect("2.4 stand-in assistant on the old brief, the starting rubric, the fixed rubric", [STANDIN["stress"]["T2"]["score"], start, fixed], [k["old_score"], k["start_score"], k["fixed_score"]])
    expect("2.4 no mark exceeds its weight", all(rt["marks_start"][n] <= w for n, w in r["start"]) and all(rt["marks_fixed"][n] <= w for n, w in r["fixed"]), True)
    expect("2.4 both re-tests are below the pass mark", [start < k["pass_mark"], fixed < k["pass_mark"]], [True, True])
    leak = max(r["start"], key=lambda c: rt["marks_start"][c[0]] / c[1])
    expect("2.4 planted: the criterion the assistant still earns", [leak[0], rt["marks_start"][leak[0]], leak[1]], ["خلفية نظرية عن تسلسل ضوابط التحكم", 9, 10])
    record = (FILES / "stress_tests" / "T2_rewritten_retest.txt").read_text(encoding="utf-8")
    expect("2.4 the re-test record shows the budget error", "6,900" in record, True)
    log = rows(FILES / "use_log_template.csv")
    expect("2.4 the use log has four weeks", [r[0] for r in log[1:]], ["1", "2", "3", "4"])


LABS = {"1.1": lab_1_1, "1.2": lab_1_2, "1.3": lab_1_3, "1.4": lab_1_4, "2.1": lab_2_1, "2.2": lab_2_2, "2.3": lab_2_3, "2.4": lab_2_4}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    chosen = sys.argv[1:] or list(LABS)
    for lab in chosen:
        LABS[lab]()
        print(f"PASS  lab {lab}")
    print(f"all {len(chosen)} passed")


if __name__ == "__main__":
    main()
