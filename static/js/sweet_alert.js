function showSuccessAlert (message) {
        Swal.fire({
            title: "成功",
            text: message,
            icon: "success",
            draggable: true
        });
    }
    function showErrorAlert (message) {
        Swal.fire({
            title: "錯誤",
            text: message,
            icon: "error",
            draggable: true
        });
    }
    function showConfirmAlert(title, text, callback) {
        Swal.fire({
            title: title,
            text: text,
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "確定",
            cancelButtonText: "取消",
        }).then((result) => {
            if (result.isConfirmed) {
                callback();
            }
        });
    }