window.taskSortable = function() {
    return {
        init() {
            const rootElement = this.$el;
            const laneId = rootElement.dataset.laneId;
            const sortable = Sortable.create(rootElement, {
                group: "tasks",
                animation: 150,
                ghostClass: "bg-gray-200",
                dragClass: "opacity-75",
                emptyInsertThreshold: 30,
                onEnd: function (evt) {
                    const taskElement = evt.item;
                    const taskId = taskElement.dataset.id;
                    const newIndex = evt.newIndex;
                    const targetLaneId = evt.to.dataset.laneId;
                    const fromLane = evt.from;
                    const toLane = evt.to;
                    // 更新空泳道提示
                    updateEmptyPlaceholder(fromLane);
                    updateEmptyPlaceholder(toLane);
                    const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
                    fetch(`/tasks/${taskId}/position`, {
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-CSRFToken': csrf
                        },
                        body: new URLSearchParams({
                            'new_index': newIndex + 1,
                            'target_lane_id': targetLaneId
                        })
                    }).then(response => {
                        if (!response.ok) {
                            return response.text().then(text => {
                                throw new Error(text || "更新任務位置失敗");
                            });
                        }
                        return response.json();
                    }).then((data) => {
                        console.log("任務位置更新成功", data);
                        showSuccessAlert('任務位置已更新');
                    }).catch((error) => {
                        console.error("錯誤：", error);
                        showErrorAlert("更新任務位置失敗：" + (error.message || "伺服器錯誤"));
                    });
                },
            });
        }
    }
};

// 更新泳道的空白提示
function updateEmptyPlaceholder(laneElement) {
    if (!laneElement) return;
    const taskItems = laneElement.querySelectorAll(".task-item");
    const placeholder = laneElement.querySelector(".empty-placeholder");
    if (taskItems.length === 0) {
        // 如果泳道中沒有任務，顯示 “尚無任務” 提示字
        if (!placeholder) {
            const emptyPlaceholder = document.createElement("div");
            emptyPlaceholder.className = "min-h-8 empty-placeholder text-gray-500 text-sm italic";
            emptyPlaceholder.textContent = "尚無任務";
            laneElement.appendChild(emptyPlaceholder);
        }
    } else {
        // 如果泳道中有任務就移除 “尚無任務” 的提示字
        if (placeholder) {
            placeholder.remove();
        }
    }
}
window.laneSortable = function() {
    return {
        init() {
            const rootElement = this.$el;
            const projectId = rootElement.dataset.projectId;
            const sortable = Sortable.create(rootElement, {
                animation: 150,
                handle: ".lane-handle",
                ghostClass: "bg-gray-100",
                dragClass: "opacity-75",
                onEnd: function (evt) {
                    const laneElement = evt.item;
                    const laneId = laneElement.dataset.id;
                    const newIndex = evt.newIndex;
                    const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
                    fetch(`/lanes/${laneId}/position`, {
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-CSRFToken': csrf
                        },
                        body: new URLSearchParams({
                            'new_index': newIndex + 1,
                            'project_id': projectId
                        })
                    }).then(response => {
                        if (!response.ok) {
                            return response.text().then(text => {
                                throw new Error(text || '更新泳道位置失敗');
                            });
                        }
                        return response.json();
                    }).then(data => {
                        console.log('泳道位置更新成功', data);
                        showSuccessAlert('泳道位置已更新');
                    }).catch(error => {
                        console.error('錯誤:', error);
                        showErrorAlert('更新泳道位置失敗：' + (error.message || '伺服器錯誤'));
                    });
                },
            });
        }
    }
};

// DOM 載入完成後初始化
document.addEventListener('DOMContentLoaded', function() {
    // 處理 HTMX 動態內容
    document.body.addEventListener('htmx:afterSwap', function(event) {
        if (window.Alpine && Alpine.initTree) {
            Alpine.initTree(document.body);
        }
    });
    console.log('sortable.js 初始化完成。');
});