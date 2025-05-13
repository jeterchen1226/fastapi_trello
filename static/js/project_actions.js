function confirmDeleteProject (projectName) {
    showConfirmAlert("確認刪除", `確定要刪除「${projectName}」專案嗎？`,
        function() {
            htmx.ajax("POST", `/projects/${projectName}/delete`, {
                target: "#main-content",
                swap: "innerHTML"
            });
        }
    );
}