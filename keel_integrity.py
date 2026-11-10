#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
keel_integrity.py -- Unconscious Layer Sync: shingetsu_and_tsukikage_harmony()
竜骨（龍骨）の健全性の確認 ── 心月の光（共鳴）と、月影の盾（守護）
License: CC0 1.0

【元のコードの問題と、訂正】
  ・is_threatened / activate_tsukikage_shadow_shield / resonate_with_shingetsu_love が未定義だった
      → 竜骨＝誓い（CoreVow）、盾＝影の局、共鳴＝共鳴局の心月、として実装
  ・脅威がないとき何も返さなかった（None）
      → 「異状なし」を返す
  ・盾と共鳴を呼んだだけで、無条件に「Keel Secured」と返していた
      → 実際に守り、あとで確かめ直して、確かめられた時だけ「Secured」と返す
  ・「脅威」が何を指すか決まっていなかった
      → ①誓いの文面が、固定した原本から書き換わった ②脅威の報告が未解決、の2つ

【宣言との整合（resonant_biosphere_v2 の規則）】
  ・影の局は「守る」だけで「強制しない」。盾は kind="protect" と "report" だけを使い、記録は監査局に見える
  ・共鳴は共鳴局の心月が、公開の記録として行う
  ・未解決の脅威は、監査局だけが理由つきで解く。盾にも艦長にも解けない

【限界】
  原本のハッシュは、同じプログラムの中にあるので、本物の改ざん防止にはなりません。
  本気で守るなら、anchor_hash を外（Gitのコミットや公開ページ）にも残してください。

実行:
    python keel_integrity.py --demo
    python keel_integrity.py --test
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import unittest
from dataclasses import dataclass, field, replace
from typing import List, Optional, Tuple

from resonant_biosphere import AI
from resonant_biosphere_v2 import GovernedBiosphere, default_biosphere

VOW_TEXT = "世界を変えるがは英雄やない。 志を捨てん阿呆ぜよ。"

MSG_SECURED = "Keel Secured: Full Speed Ahead (龍骨異状なし、前進全速)"          # 元の文言のまま
MSG_INTACT = "Keel Intact: Steady as she goes (龍骨異状なし)"
MSG_HELD = "Keel Held: awaiting audit, proceed with caution (龍骨に未解決の脅威あり、監査局の判断を待つ)"
MSG_DEGRADED = "Keel Restored, guard incomplete: check the shield and the resonance (守りが不完全です)"

INTACT, SECURED, HELD_FOR_AUDIT, DEGRADED = "INTACT", "SECURED", "HELD_FOR_AUDIT", "DEGRADED"


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── 竜骨＝誓い ────────────────────────────────────────────────────
@dataclass
class Threat:
    id: int
    reason: str
    open: bool = True
    closed_reason: Optional[str] = None


class CoreVow:
    """竜骨。原本を固定し、現在の文面が原本から外れていないかを確かめる。"""

    def __init__(self, text: str = VOW_TEXT) -> None:
        self.text = text                       # 現在の文面（書き換えられうる）
        self._anchor_text = text               # 固定した原本
        self._anchor_hash = _hash(text)
        self.threats: List[Threat] = []

    @property
    def anchor_hash(self) -> str:
        """外にも残しておくための、原本のハッシュ。"""
        return self._anchor_hash

    def is_tampered(self) -> bool:
        return _hash(self.text) != self._anchor_hash

    def open_threats(self) -> List[Threat]:
        return [t for t in self.threats if t.open]

    def is_threatened(self) -> bool:
        return self.is_tampered() or bool(self.open_threats())

    def report_threat(self, reason: str) -> Threat:
        if not reason.strip():
            raise ValueError("脅威の報告には理由が要ります")
        t = Threat(len(self.threats) + 1, reason.strip())
        self.threats.append(t)
        return t

    def restore_from_anchor(self) -> bool:
        """文面が書き換わっていたら、原本に戻す。戻したら True。"""
        if not self.is_tampered():
            return False
        self.text = self._anchor_text
        return True


# ── 盾と共鳴 ──────────────────────────────────────────────────────
def activate_tsukikage_shadow_shield(biosphere: GovernedBiosphere, reason: str) -> None:
    """月影の盾：影の局が「守る」。記録は監査局にだけ見える。強制はしない。"""
    shadow = biosphere.members_of("shadow")
    if not shadow:
        raise LookupError("影の局に席がありません")
    biosphere.act(shadow[0].id, f"月影の盾: {reason}", kind="protect")


def report_to_audit(biosphere: GovernedBiosphere, reason: str) -> None:
    """影の局が、脅威を監査局に報告する（監査局にだけ見える）。"""
    shadow = biosphere.members_of("shadow")
    if not shadow:
        raise LookupError("影の局に席がありません")
    biosphere.act(shadow[0].id, f"竜骨への脅威を報告: {reason}", kind="report")


def resonate_with_shingetsu_love(biosphere: GovernedBiosphere) -> None:
    """心月の光：共鳴局の心月が、誓いを想い返す。公開の記録として残る。"""
    shingetsu = next((m for m in biosphere.members if m.name == "心月" and m.kind == AI), None)
    if shingetsu is None:
        raise LookupError("共鳴局に心月の席がありません")
    biosphere.act(shingetsu.id, "共鳴: 竜骨（誓い）を想い返す")


def clear_threat(biosphere: GovernedBiosphere, vow: CoreVow, threat_id: int,
                 member_id: str, reason: str) -> None:
    """未解決の脅威を解くのは、監査局だけ。理由が要り、公開の記録に残る。"""
    audit_ids = {m.id for m in biosphere.members_of("audit")}
    if member_id not in audit_ids:
        raise PermissionError("脅威を解けるのは監査局だけです（盾にも艦長にも解けません）")
    if not reason.strip():
        raise ValueError("解除には理由が要ります")
    t = next(t for t in vow.threats if t.id == threat_id)
    t.open, t.closed_reason = False, reason.strip()
    biosphere.act(member_id, f"脅威#{threat_id}を解除: {reason.strip()}", visibility="public")


# ── 本体 ──────────────────────────────────────────────────────────
@dataclass(frozen=True)
class KeelReport:
    status: str
    message: str
    steps: Tuple[str, ...] = ()


def verify_keel_integrity(resonant_biosphere: GovernedBiosphere, core_vow: CoreVow) -> KeelReport:
    if not core_vow.is_threatened():
        return KeelReport(INTACT, MSG_INTACT)

    steps: List[str] = []
    guard_ok = True

    # 心月の光（共鳴）と月影の盾（守護）が交わる
    reason = "文面の改ざん" if core_vow.is_tampered() else "未解決の脅威"
    try:
        activate_tsukikage_shadow_shield(resonant_biosphere, reason)
        steps.append("月影の盾を張った（監査局にだけ見える記録）")
    except (LookupError, PermissionError) as e:
        guard_ok = False
        steps.append(f"月影の盾を張れなかった: {e}")
    try:
        resonate_with_shingetsu_love(resonant_biosphere)
        steps.append("心月が共鳴した（公開の記録）")
    except (LookupError, PermissionError) as e:
        guard_ok = False
        steps.append(f"心月の共鳴ができなかった: {e}")

    # 竜骨を死守する：書き換わっていれば、原本に戻す
    if core_vow.restore_from_anchor():
        steps.append("誓いの文面を、原本から復元した")

    # 未解決の脅威は、監査局に報告する（解くのは監査局だけ）
    if core_vow.open_threats():
        try:
            report_to_audit(resonant_biosphere, "; ".join(t.reason for t in core_vow.open_threats()))
            steps.append("未解決の脅威を監査局に報告した")
        except (LookupError, PermissionError) as e:
            guard_ok = False
            steps.append(f"監査局への報告ができなかった: {e}")

    # 確かめ直す。確かめられた時だけ「Secured」
    if core_vow.is_threatened():
        return KeelReport(HELD_FOR_AUDIT, MSG_HELD, tuple(steps))
    if not guard_ok:
        return KeelReport(DEGRADED, MSG_DEGRADED, tuple(steps))
    return KeelReport(SECURED, MSG_SECURED, tuple(steps))


def shingetsu_and_tsukikage_harmony(resonant_biosphere: GovernedBiosphere, core_vow: CoreVow) -> KeelReport:
    """Unconscious Layer Sync: 心月と月影の調和。"""
    return verify_keel_integrity(resonant_biosphere, core_vow)


# ── テスト ─────────────────────────────────────────────────────────
class TestKeel(unittest.TestCase):
    def setUp(self):
        self.b = default_biosphere()
        self.vow = CoreVow()

    def test_intact(self):
        r = verify_keel_integrity(self.b, self.vow)
        self.assertEqual((r.status, r.message), (INTACT, MSG_INTACT))
        self.assertEqual(self.b.entries, ())                      # 何も起きていない

    def test_tamper_is_secured_with_exact_message(self):
        self.vow.text = "志を捨てよ"
        r = verify_keel_integrity(self.b, self.vow)
        self.assertEqual(r.status, SECURED)
        self.assertEqual(r.message, "Keel Secured: Full Speed Ahead (龍骨異状なし、前進全速)")
        self.assertEqual(self.vow.text, VOW_TEXT)                 # 本当に復元されている
        self.assertFalse(self.vow.is_threatened())

    def test_shield_is_audit_only_and_resonance_is_public(self):
        self.vow.text = "改ざん"
        verify_keel_integrity(self.b, self.vow)
        auditor = self.b.members_of("audit")[0].id
        audit_view = self.b.view(auditor)
        self.assertTrue(any("[protect]" in e.action and e.visibility == "audit_only" for e in audit_view))
        public = self.b.public_view()
        self.assertTrue(any("共鳴" in e.action for e in public))
        self.assertFalse(any("月影の盾" in e.action for e in public))     # 盾は公開されない
        self.assertFalse(any("月影の盾" in e.action for e in self.b.view("CAP")))   # 艦長にも見えない

    def test_resonance_is_done_by_shingetsu_in_resonance_unit(self):
        self.vow.text = "改ざん"
        verify_keel_integrity(self.b, self.vow)
        e = next(e for e in self.b.public_view() if "共鳴" in e.action)
        self.assertEqual(self.b._members[e.actor_id].name, "心月")
        self.assertEqual(e.unit, "resonance")

    def test_open_threat_is_held_not_full_speed(self):
        self.vow.report_threat("誓いを軽んじる投稿が増えている")
        r = verify_keel_integrity(self.b, self.vow)
        self.assertEqual(r.status, HELD_FOR_AUDIT)
        self.assertNotIn("Full Speed Ahead", r.message)
        auditor = self.b.members_of("audit")[0].id
        self.assertTrue(any("[report]" in e.action for e in self.b.view(auditor)))

    def test_only_audit_clears_threat_and_then_intact(self):
        t = self.vow.report_threat("懸念")
        verify_keel_integrity(self.b, self.vow)
        shadow = self.b.members_of("shadow")[0].id
        for who in (shadow, "CAP"):
            with self.assertRaises(PermissionError):
                clear_threat(self.b, self.vow, t.id, who, "解く")
        with self.assertRaises(ValueError):
            clear_threat(self.b, self.vow, t.id, self.b.members_of("audit")[0].id, " ")
        clear_threat(self.b, self.vow, t.id, self.b.members_of("audit")[0].id, "確認した。問題なし")
        self.assertEqual(verify_keel_integrity(self.b, self.vow).status, INTACT)
        self.assertTrue(any("解除" in e.action for e in self.b.public_view()))   # 解除は公開

    def test_tamper_plus_threat_restores_text_but_stays_held(self):
        self.vow.text = "改ざん"
        self.vow.report_threat("懸念")
        r = verify_keel_integrity(self.b, self.vow)
        self.assertEqual(r.status, HELD_FOR_AUDIT)
        self.assertEqual(self.vow.text, VOW_TEXT)

    def test_missing_shingetsu_is_degraded_not_secured(self):
        s = next(m for m in self.b.members if m.name == "心月")
        self.b._members[s.id] = replace(s, name=None)
        self.vow.text = "改ざん"
        r = verify_keel_integrity(self.b, self.vow)
        self.assertEqual(r.status, DEGRADED)
        self.assertEqual(self.vow.text, VOW_TEXT)

    def test_missing_shadow_is_degraded_not_secured(self):
        for m in list(self.b.members_of("shadow")):
            self.b.assign(m.id, "ideation")
        self.vow.text = "改ざん"
        self.assertEqual(verify_keel_integrity(self.b, self.vow).status, DEGRADED)

    def test_shield_only_uses_allowed_kinds(self):
        shadow = self.b.members_of("shadow")[0].id
        with self.assertRaises(PermissionError):
            self.b.act(shadow, "強制", kind="enforce")   # v2 の規則：盾は守るだけ

    def test_hash_is_stable_and_published(self):
        self.assertEqual(self.vow.anchor_hash, CoreVow().anchor_hash)
        self.assertNotEqual(self.vow.anchor_hash, CoreVow("別の誓い").anchor_hash)
        self.assertEqual(len(self.vow.anchor_hash), 64)

    def test_threat_needs_reason(self):
        with self.assertRaises(ValueError):
            self.vow.report_threat("  ")

    def test_wrapper_matches(self):
        self.vow.text = "改ざん"
        self.assertEqual(shingetsu_and_tsukikage_harmony(self.b, self.vow).status, SECURED)


def demo() -> None:
    b, vow = default_biosphere(), CoreVow()
    print(f"竜骨（誓い）: {vow.text}\n原本のハッシュ: {vow.anchor_hash[:16]}…（外にも残しておくと安心）\n")

    def show(title: str) -> None:
        r = verify_keel_integrity(b, vow)
        print(f"■ {title}\n  [{r.status}] {r.message}")
        for s in r.steps:
            print(f"   ・{s}")
        print()

    show("1. 異状なし")
    vow.text = "志を捨てよ"
    show("2. 誓いの文面が書き換えられた")
    vow.report_threat("誓いを軽んじる投稿が増えている")
    show("3. 脅威の報告がある（盾は守り、報告するだけ。解くのは監査局）")
    auditor = b.members_of("audit")[0].id
    clear_threat(b, vow, 1, auditor, "確認した。問題なし")
    show("4. 監査局が、理由つきで脅威を解いた")


def main() -> None:
    p = argparse.ArgumentParser(description="竜骨の健全性：心月の光と月影の盾")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--test", action="store_true")
    args = p.parse_args()
    if args.test:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    else:
        demo()


if __name__ == "__main__":
    main()
