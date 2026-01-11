export async function analyzeImages(files) {
  // =========================
  // single (❗절대 수정 안 함)
  // =========================
  if (files.length === 1) {
    const formData = new FormData();
    formData.append("image", files[0]);

    const res = await fetch("http://127.0.0.1:8000/pipeline/single", {
      method: "POST",
      body: formData,
    });

    // // single
    // const res = await fetch("/pipeline/single", {
    //   method: "POST",
    //   body: formData,
    // });

    if (!res.ok) throw new Error("single failed");
    return await res.json();
  }

  // =========================
  // 🔥 multi (여기만 수정)
  // =========================
  const formData = new FormData();

  files.forEach((file, idx) => {
    // ⭐ FastAPI가 요구하는 key = images
    // ⭐ filename 명시 필수
    formData.append(
      "images",
      file,
      file.name || `image_${idx}.jpg`
    );
  });

  const res = await fetch("http://127.0.0.1:8000/pipeline/multi", {
    method: "POST",
    body: formData,
  });

    //   // multi
    // const res = await fetch("/pipeline/multi", {
    //   method: "POST",
    //   body: formData,
    // });
    
  if (!res.ok) {
    const t = await res.text();
    console.error("MULTI ERROR:", t);
    throw new Error("multi failed");
  }

  return await res.json();
}
