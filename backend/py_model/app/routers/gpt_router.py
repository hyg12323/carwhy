from fastapi import APIRouter, HTTPException
from app.services.gpt_service import (
    generate_gpt_solution,
    generate_gpt_followup
)

router = APIRouter(prefix="/api/gpt")


@router.post("/summary")
def gpt_summary(data: dict):
    try:
        accident = data.get("accident") or {}
        yolo = data.get("yolo") or {}
        drivable = data.get("drivable") or {}
        mode = data.get("mode", "OVERALL")

        print("🔥 GPT SUMMARY REQUEST")
        print("   mode =", mode)
        print("   accident keys =", list(accident.keys()) if isinstance(accident, dict) else type(accident))
        print("   yolo keys =", list(yolo.keys()) if isinstance(yolo, dict) else type(yolo))
        print("   drivable keys =", list(drivable.keys()) if isinstance(drivable, dict) else type(drivable))

        # ❗ YOLO 데이터는 절대 여기서 가공하지 않는다
        # ❗ generate_gpt_solution 내부에서 extract_damaged_parts로 처리

        return generate_gpt_solution(
            accident=accident,
            yolo=yolo,
            drivable=drivable,
            mode=mode
        )

    except Exception as e:
        print("🔥 GPT SUMMARY ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
def gpt_chat(data: dict):
    try:
        question = data.get("question", "")
        summary_text = data.get("summary_text", "")

        if not summary_text:
            raise ValueError("summary_text가 전달되지 않았습니다.")

        print("🔥 GPT CHAT REQUEST")
        print("   question =", question)

        from openai import OpenAI
        client = OpenAI()

        prompt = f"""
다음은 차량 사고에 대한 AI 종합 분석 결과다.
이 내용을 기반으로 사용자의 질문에 답변해라.

[종합 분석 결과]
{summary_text}

사용자 질문:
{question}

답변 규칙:
- 종합 분석 결과에 **없는 내용은 추측하지 말 것**
- 기존 결론을 뒤집지 말 것
- 상담사처럼 현실적인 조언 위주로 설명할 것
- 필요하면 수리 / 점검 / 보험 관점에서 설명할 것
"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "너는 차량 사고 분석 리포트를 설명해주는 전문 상담사다."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.45
        )

        return {
            "answer": response.choices[0].message.content.strip()
        }

    except Exception as e:
        print("🔥 GPT CHAT ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))
