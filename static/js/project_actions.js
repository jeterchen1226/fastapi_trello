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

// 確認移除成員
function confirmRemoveMember(memberName, memberId, projectName) {
    showConfirmAlert(
        '確認移除成員',
        `確定要將 ${memberName} 從專案中移除嗎？`,
        function() {
            // 確認後執行移除操作
            htmx.ajax('POST', `/projects/${projectName}/remove_member`, {
                values: { member_id: memberId },
                target: '#members-content',
                swap: 'outerHTML'
            }).then(() => {
                showSuccessAlert(`已成功移除 ${memberName}`);
            }).catch((error) => {
                showErrorAlert('移除成員失敗');
                console.error('移除成員錯誤:', error);
            });
        }
    );
}