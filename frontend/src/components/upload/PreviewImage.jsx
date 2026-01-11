// frontend\src\components\upload\PreviewImage.jsx
function PreviewImage({ src }) {
  if (!src) return null;

  return (
    <div className="preview-item">
      <img src={src} alt="업로드 미리보기" />
    </div>
  );
}

export default PreviewImage;
