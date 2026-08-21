/* ========== Shared Utilities ========== */

function esc(value) {
  const el = document.createElement('div');
  el.textContent = value == null ? '' : String(value);
  return el.innerHTML;
}

let toastTimer = null;
function showToast(message) {
  const el = document.getElementById('toast');
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2600);
}

function getLocalServerEditorUrl() {
  const fileName = location.pathname.split('/').pop() || 'editor.html';
  return `http://localhost:8000/${fileName}${location.search}${location.hash}`;
}

function handleFileProtocolAccess() {
  if (location.protocol !== 'file:') return false;
  const url = getLocalServerEditorUrl();
  document.body.innerHTML = `
    <div style="max-width:760px;margin:80px auto;padding:0 20px;font-family:'IBM Plex Sans SC','Noto Sans JP',sans-serif;">
      <div style="background:#fff;border:1px solid #d8e1eb;border-radius:18px;padding:24px;box-shadow:0 12px 32px rgba(31,45,61,0.05)">
        <div style="font-size:22px;font-weight:700;color:#1f2d3d;margin-bottom:12px">请通过本地服务器打开编辑工具</div>
        <div style="font-size:14px;line-height:1.9;color:#546476">
          检测到你是直接打开本地 HTML 文件。浏览器会拦截对 JSON 的读取。<br>
          请改用：<a href="${url}" style="color:#1668dc">${url}</a><br>
          如果本地服务还没开，先运行 <strong>start_server.bat</strong> 或 <strong>启动本地服务器.bat</strong>。
        </div>
      </div>
    </div>
  `;
  setTimeout(() => { window.location.href = url; }, 1200);
  return true;
}
