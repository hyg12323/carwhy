// frontend\src\pages\UploadPage.jsx
import "../styles/upload.css";
import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";

import UploadInput from "../components/upload/UploadInput";
import UploadButton from "../components/upload/UploadButton";

import { analyzeImages } from "../api/analyze";

const MAX_IMAGES = 7;

function UploadPage() {
  const [files, setFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // + 버튼 클릭 → 파일 선택
  const handleAddClick = () => {
    fileInputRef.current?.click();
  };

  // 파일 누적 추가
  const handleFileChange = (selectedFiles) => {
    if (!selectedFiles || selectedFiles.length === 0) return;

    let nextFiles = [...files, ...selectedFiles];

    if (nextFiles.length > MAX_IMAGES) {
      alert(`이미지는 최대 ${MAX_IMAGES}장까지 업로드할 수 있습니다.`);
      nextFiles = nextFiles.slice(0, MAX_IMAGES);
    }

    // 기존 URL 해제
    previews.forEach((url) => URL.revokeObjectURL(url));

    const nextPreviews = nextFiles.map((file) =>
      URL.createObjectURL(file)
    );

    setFiles(nextFiles);
    setPreviews(nextPreviews);
  };

  // ❌ 이미지 삭제
  const handleRemoveImage = (index) => {
    // URL 해제
    URL.revokeObjectURL(previews[index]);

    const nextFiles = files.filter((_, i) => i !== index);
    const nextPreviews = previews.filter((_, i) => i !== index);

    setFiles(nextFiles);
    setPreviews(nextPreviews);
  };

  // 🔥 실제 분석 요청
  const handleSubmit = async () => {
    if (files.length === 0) return;

    try {
      const result = await analyzeImages(files);

      navigate("/result", {
        state: {
          result,
          image: previews[0],
          images: previews,
        },
      });
    } catch (error) {
      console.error(error);
      alert("분석 중 오류가 발생했습니다.");
    }
  };

  return (
    <div className="page">
      <div className="top">
        <p className="page-title">사고 예방 및 예측 AI</p>
      </div>

      <div className="middle">
        <h1 className="platfrom-title">Carwhy</h1>
      </div>

      <div className="bottom">
        <p className="upload-guide">사고 차량 사진을 업로드 해주세요</p>

        <p className="upload-notice">
          ⚠️ 여러 장의 사진을 업로드할 수 있지만,<br />
          <strong>하나의 사고(한 차량)에 대해서만 분석 가능합니다.</strong>
        </p>

        <div className="card">
          <div className="upload-section">
            {/* 숨겨진 input */}
            <UploadInput
              multiple
              onChange={handleFileChange}
              inputRef={fileInputRef}
            />

            {/* 업로드 버튼 */}
            <div className="upload-add" onClick={handleAddClick}>
              <span className="plus">+</span>
              <span className="text">사진 업로드</span>
            </div>

            {/* 미리보기 */}
            {previews.length > 0 && (
              <div className="preview-grid">
                {previews.map((src, idx) => (
                  <div key={idx} className="preview-wrapper">
                    <img src={src} alt={`preview-${idx}`} />
                    <button
                      className="preview-remove"
                      onClick={() => handleRemoveImage(idx)}
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}

            <UploadButton
              onClick={handleSubmit}
              disabled={files.length === 0}
              text="분석 요청"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default UploadPage;
