// frontend\src\components\upload\UploadInput.jsx
function UploadInput({ onChange, multiple = false, inputRef }) {
  const handleChange = (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    const validFiles = files.filter(file =>
      file.type.startsWith("image/")
    );

    if (validFiles.length === 0) {
      alert("이미지 파일만 업로드 가능합니다.");
      e.target.value = "";
      return;
    }

    onChange(validFiles);
    e.target.value = "";
  };

  return (
    <input
      ref={inputRef}
      type="file"
      accept="image/*"
      multiple={multiple}
      onChange={handleChange}
      style={{ display: "none" }}   // ✅ 화면에서 완전 제거
    />
  );
}

export default UploadInput;
