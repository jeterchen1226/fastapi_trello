document.addEventListener("htmx:afterSwap", function (event) {
    checkForMessages();
});

document.addEventListener("DOMContentLoaded", function() {
    checkForMessages();
});

document.addEventListener("htmx:afterRequest", function (event) {
    if (!event.detail.xhr.getResponseHeader("HX-Redirect")) {
        checkForMessages();
    }
});

function checkForMessages() {
    const messageData = document.getElementById("message-data");
    if (messageData) {
        const message = messageData.getAttribute("data-message");
        const type = messageData.getAttribute("data-type");
        if (message && type) {
            if (type === "success") {
                showSuccessAlert("成功", message);
            } else if (type === "error") {
                showErrorAlert("錯誤", message);
            }
            messageData.remove();
        }
    }
}

function confirmDeleteTask(taskId, taskName) {
    showConfirmAlert("確認刪除", `確定要刪除「${taskName}」該任務嗎？`,
        function() {
            htmx.ajax("POST", `/tasks/${taskId}/delete`, {
                target: "#main-content",
                swap: "innerHTML"
            });
        }
    );
}