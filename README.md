🚗 Automobile Accident Analysis System
자동차 사고 분석 및 사고 영향 예측 시스템

프로젝트 개요
본 프로젝트는 자동차 사고 이미지를 기반으로
사고 상태를 분석하고 사고 영향을 예측하는
AI 기반 자동차 사고 분석 시스템이다.

사고 유형 분석, 차량 파손 부위 탐지, 주행 가능 여부 판단 등
여러 AI 모델을 조합하여 사고 상황을 종합적으로 해석한다.

주요 기능
- 사고 유형 분류
- 차량 파손 부위 탐지 (YOLO 기반 객체 탐지)
- 주행 가능 여부 판단
- 이미지 기반 사고 분석 결과 제공 (REST API)

시스템 구성
- AI 모델 서버: Python, FastAPI
- 프론트엔드 웹 애플리케이션: React + Vite

기술 스택
- AI / Backend: Python, YOLO, FastAPI
- Frontend: React, Vite
- DevOps: Docker

특징
- 다중 AI 모델 기반 사고 분석 구조
- REST API 기반 AI 서빙
- 프론트엔드와 AI 서버 분리 설계
- Docker 기반 실행 환경
