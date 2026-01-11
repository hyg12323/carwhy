// frontend\src\components\upload\UploadButton.jsx
function UploadButton({ onClick, disabled = false, text }) {
  return (
    <button
      type="button"
      className="upload-button"
      onClick={onClick}
      disabled={disabled}
      aria-disabled={disabled}
    >
      {text}
    </button>
  );
}

export default UploadButton;
