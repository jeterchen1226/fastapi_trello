document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    // 登入
    const loginSuccess = urlParams.get('login');
    const userName = urlParams.get('name');
    if (loginSuccess === "success" && userName) {
        const decodedName = decodeURIComponent(userName);
        showSuccessAlert(`歡迎回來，${decodedName}。`);
        window.history.replaceState({}, document.title, window.location.pathname);
    }
    // 登出
    const logoutSuccess = urlParams.get('logout');
    if (logoutSuccess === 'success') {
        showSuccessAlert('登出成功。');
        window.history.replaceState({}, document.title, window.location.pathname);
    }
    // 註冊
    const registerSuccess = urlParams.get('register');
    if (registerSuccess === "success" && userName) {
        const decodedName = decodeURIComponent(userName);
        showSuccessAlert(`註冊成功！歡迎 ${decodedName}。`);
        window.history.replaceState({}, document.title, window.location.pathname);
    }
    const flashMessage = getCookie('flash_message');
    if (flashMessage) {
        const [category, encodedMessage] = flashMessage.split(':', 2);
        const message = decodeURIComponent(encodedMessage);
        if (category === 'success') {
            showSuccessAlert(message);
        } else if (category === 'error') {
            showErrorAlert(message);
        }
        document.cookie = 'flash_message=; Max-Age=0; path=/;';
    }
    const errorElement = document.getElementById('error-message');
    if (errorElement && errorElement.textContent) {
        showErrorAlert(errorElement.textContent);
        errorElement.style.display = 'none';
    }
});
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}