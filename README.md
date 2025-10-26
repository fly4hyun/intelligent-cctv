# Intelligent CCTV – Edge Loitering / Intrusion / Marketing Detection

> 배회·침입·마케팅 행동을 Edge 환경에서 실시간 탐지/판정하는 지능형 CCTV 알고리즘 개발
> 기간: 2024.04 – 2024.08 | 역할: 알고리즘 개발 및 Jetson 포팅

---

## Summary

* 영상 저장 없이 Edge 디바이스에서 **탐지 → 추적 → ID 안정화 → 이벤트 판정 → 메타 송신** 일관 처리 파이프라인 구축
* **배회·침입 알고리즘 KISA 지능형 CCTV 성능시험 인증 통과 (F1 ≥ 0.9)**

---

## Model & Pipeline

* **Detection** — YOLO 기반 사람 검출
* **Tracking** — 기본 Tracking ID 불안정 → **Re‑mapping 알고리즘 직접 구현 (IOU×연속프레임×중심조건)**
* **Event Logic** — 배회·침입·마케팅 Rule 기반 체류시간/영역 판정 및 Alarm 메타 생성
* **Serving** — Edge 단에서 메타정보만 전송 (영상 저장 없음)

---

## My Contribution

* Tracking ID Re‑mapping 알고리즘 설계/구현으로 실환경 ID 안정화 확보
* Remap ID 기반 **프레임 메타(Table: frame/id/area 포함여부) 구조화**
* 이벤트 후처리(배회/침입/마케팅) Rule Engine 구현 및 Alarm 기록
* NVIDIA Jetson Orin NX 환경에 실시간 동작 가능하도록 최적화/통합
* 동일 파이프라인 기반 **쓰러짐(Fall)** 항목 확장 개발

---

## Performance & Outcome

* 본인이 개발·세팅한 배회·침입 알고리즘이 **KISA 지능형 CCTV 성능시험 인증 통과 (F1 ≥ 0.9)** 에 사용됨
* Edge 환경에서 영상 저장 없이 메타만 송신하는 실사용 수준 프로토타입 완성

---

## Certification Link

[https://www.ksecurity.or.kr/user/extra/kisis/94/certification/certificationView2/jsp/LayOutPage.do?setIdx=2&dataIdx=2339&selField=&searchDivision=&column&search=](https://www.ksecurity.or.kr/user/extra/kisis/94/certification/certificationView2/jsp/LayOutPage.do?setIdx=2&dataIdx=2339&selField=&searchDivision=&column&search=)

---
