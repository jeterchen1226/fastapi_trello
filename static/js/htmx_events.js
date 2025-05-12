document.addEventListener("DOMContentLoaded", function () {
    document.body.addEventListener("htmx:afterSwap", function (event) {
        const messageEl = document.getElementById("message-data");
        if (messageEl) {
            const message = messageEl.getAttribute("data-message");
            const type = messageEl.getAttribute("data-type");
            if (type === "error") {
                showErrorAlert(message);
            } else {
                showSuccessAlert(message);
            }
            messageEl.remove();
        }
    });
    document.body.addEventListener("htmx:responseError", function (event) {
        const response = event.detail.xhr.response;
        if (response && response.includes('id="message-data"')) {
            const tempDiv = document.createElement("div");
            tempDiv.innerHTML = response;
            const messageEl = tempDiv.querySelector("#message-data");
            if (messageEl) {
                const message = messageEl.getAttribute("data-message");
                const type = messageEl.getAttribute("data-type");
                if (type === "error") {
                    showErrorAlert(message);
                    return;
                }
            }
        }
        // 如果上面的檢查失敗，嘗試解析 JSON 錯誤
        try {
            const error = JSON.parse(response);
            showErrorAlert(error.detail || "操作失敗");
        } catch (e) {
            // 如果無法解析 JSON，顯示默認錯誤
            showErrorAlert("操作失敗");
        }
    });
});