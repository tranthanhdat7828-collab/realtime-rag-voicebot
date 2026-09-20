const uploadBtn = document.getElementById("uploadBtn");
const fileInput = document.getElementById("fileInput");
const uploadResult = document.getElementById("uploadResult");
const knowledgeList = document.getElementById("knowledgeList");
const sendBtn = document.getElementById("sendBtn");
const questionInput = document.getElementById("questionInput");
const chatBox = document.getElementById("chatBox");

uploadBtn.addEventListener("click", uploadFile);
sendBtn.addEventListener("click", sendQuestion);
questionInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendQuestion();
    }
});

async function uploadFile() {
    const file = fileInput.files[0];

    if (!file) {
        uploadResult.innerText = "Vui lòng chọn file.";
        return;
    }
    uploadResult.innerText = "Đang upload...";
    uploadBtn.disabled = true;

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "upload thất bại");
        }

        uploadResult.innerHTML = `
        ✅ Upload thành công<br>
        File: ${data.filename}<br>
        Chunks file này: ${data.chunks}<br>
        Tổng chunks trong storage: ${data.total_chunks}`;

        const emptyFile = document.querySelector(".empty-file");
        if (emptyFile) {
            emptyFile.remove();
        }

        const fileDiv = document.createElement("div");
        fileDiv.className = "file-item";
        fileDiv.textContent = `📄 ${data.filename}`;

        knowledgeList.appendChild(fileDiv);
        fileInput.value = "";

    } catch (error) {
        uploadResult.textContent = `❌ ${error.message}`;
        console.error(error);
    } finally {
        uploadBtn.disabled = false;
    }
}

async function sendQuestion() {
    const question = questionInput.value.trim();
    if (!question) return;

    // 1. Khóa input tránh spam click
    questionInput.value = "";
    questionInput.disabled = true;
    sendBtn.disabled = true;

    // 2. Thêm tin nhắn của User vào khung chat an toàn qua DOM
    appendMessage(question, "user-message");

    // 3. Tạo sẵn bubble của Bot
    const botMsgDiv = appendMessage("", "bot-message");
    botMsgDiv.style.opacity = "0.7";

    const metaDiv = document.createElement("div");
    metaDiv.className = "bot-meta";
    chatBox.appendChild(metaDiv);

    const t0 = performance.now();
    let ttftRecorded = false;

    try {
        const response = await fetch("/query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question
            })
        });

        if (!response.ok) {
            throw new Error(`Lỗi máy chủ (${response.status})`);
        }

        if (!response.body) {
            throw new Error("Không nhận dữ liệu stream.");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let fullAnswer = "";
        let isFirstChunk = true;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            if (!chunk) {
                continue;
            }

            if (isFirstChunk) {
                const ttft = (performance.now() - t0).toFixed(0);
                metaDiv.textContent = `TTFT: ${ttft} ms`;

                botMsgDiv.textContent = "";
                botMsgDiv.style.opacity = "1";
                isFirstChunk = false;
                ttftRecorded = true;
            }
            fullAnswer += chunk;
            botMsgDiv.textContent = fullAnswer;
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        // Nếu stream rỗng hoặc không sinh chữ, xóa ngay bubble để tránh chấm xám
        if (!fullAnswer.trim()) {
            botMsgDiv.textContent = "⚠️ Hệ thống không trả về dữ liệu (0 chunks). Kiểm tra lại kết nối Qdrant/LLM.";
            botMsgDiv.style.color = "#d97706";
            botMsgDiv.style.opacity = "1";
            metaDiv.remove();
        }

    } catch (error) {
        botMsgDiv.textContent = `Lỗi: ${error.message}`;
        botMsgDiv.style.color = "#dc2626";
        botMsgDiv.style.opacity = "1";
        metaDiv.remove();
        console.error(error);
    } finally {
        // Mở lại input sau khi stream xong
        questionInput.disabled = false;
        sendBtn.disabled = false;
        questionInput.focus();
    }
}

// Hàm phụ trợ tạo DOM an toàn
function appendMessage(text, className) {
    const div = document.createElement("div");
    div.className = `message ${className}`;
    div.textContent = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div;
}
