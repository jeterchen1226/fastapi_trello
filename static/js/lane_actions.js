document.addEventListener("htmx:afterSwap", function (event) {
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
});

function confirmDelete (laneId, laneName) {
    showConfirmAlert("確認刪除", `確定要刪除「${laneName}」該泳道嗎？`,
        function() {
            htmx.ajax("POST", `/lanes/${laneId}/delete`, {
                target: "#main-content",
                swap: "innerHTML"
            });
        }
    );
}