// API 基础 URL
const API_BASE = window.location.origin;

// 全局变量
let currentTab = 'image';
let uploadedFiles = {};
let taskIds = {};

// 切换标签页
function switchTab(tabName) {
    currentTab = tabName;
    
    // 更新标签按钮
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // 更新内容
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// 显示状态消息
function showStatus(message, type = 'info') {
    const statusEl = document.getElementById('statusMessage');
    statusEl.textContent = message;
    statusEl.className = `status-message ${type}`;
    statusEl.style.display = 'block';
    
    setTimeout(() => {
        statusEl.style.display = 'none';
    }, 5000);
}

// ==================== 图片处理 ====================

document.getElementById('imageFile').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        if (file.size > 10 * 1024 * 1024) {
            showStatus('文件大小超过 10MB 限制', 'error');
            return;
        }
        
        uploadedFiles.image = file;
        document.getElementById('imageProcessBtn').disabled = false;
        
        // 预览原图
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('imageOriginal').src = e.target.result;
        };
        reader.readAsDataURL(file);
        
        showStatus('图片已上传，可以开始处理', 'success');
    }
});

// 拖拽上传
setupDragDrop('imageUpload', 'imageFile');

document.getElementById('imageProcessBtn').addEventListener('click', async function() {
    const file = uploadedFiles.image;
    if (!file) return;
    
    this.disabled = true;
    document.getElementById('imageLoader').style.display = 'block';
    document.getElementById('imageProgress').style.display = 'block';
    document.getElementById('imageResult').style.display = 'none';
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        updateProgress('image', 10, '上传中...');
        
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('上传失败');
        }
        
        const result = await response.json();
        taskIds.image = result.task_id;
        
        updateProgress('image', 30, '处理中...');
        
        // 轮询任务状态
        pollTaskStatus('image', result.task_id);
        
    } catch (error) {
        showStatus('处理失败: ' + error.message, 'error');
        this.disabled = false;
        document.getElementById('imageLoader').style.display = 'none';
        document.getElementById('imageProgress').style.display = 'none';
    }
});

// ==================== 视频处理 ====================

document.getElementById('videoFile').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        if (file.size > 500 * 1024 * 1024) {
            showStatus('文件大小超过 500MB 限制', 'error');
            return;
        }
        
        uploadedFiles.video = file;
        document.getElementById('videoProcessBtn').disabled = false;
        
        // 预览原视频
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('videoOriginal').src = e.target.result;
        };
        reader.readAsDataURL(file);
        
        showStatus('视频已上传，可以开始处理', 'success');
    }
});

setupDragDrop('videoUpload', 'videoFile');

document.getElementById('videoProcessBtn').addEventListener('click', async function() {
    const file = uploadedFiles.video;
    if (!file) return;
    
    this.disabled = true;
    document.getElementById('videoLoader').style.display = 'block';
    document.getElementById('videoProgress').style.display = 'block';
    document.getElementById('videoResult').style.display = 'none';
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('keep_audio', document.getElementById('videoKeepAudio').checked);
    formData.append('frame_by_frame', document.getElementById('videoFrameByFrame').checked);
    
    try {
        updateProgress('video', 5, '上传中...');
        
        const response = await fetch(`${API_BASE}/upload_video`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('上传失败');
        }
        
        const result = await response.json();
        taskIds.video = result.task_id;
        
        updateProgress('video', 10, '处理中...');
        showStatus('视频处理已开始，这可能需要几分钟...', 'info');
        
        // 轮询任务状态
        pollTaskStatus('video', result.task_id);
        
    } catch (error) {
        showStatus('处理失败: ' + error.message, 'error');
        this.disabled = false;
        document.getElementById('videoLoader').style.display = 'none';
        document.getElementById('videoProgress').style.display = 'none';
    }
});

// ==================== 批量处理 ====================

document.getElementById('batchFiles').addEventListener('change', function(e) {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;
    
    uploadedFiles.batch = files;
    document.getElementById('batchProcessBtn').disabled = false;
    
    // 显示文件列表
    const listEl = document.getElementById('batchFileList');
    listEl.innerHTML = '<h3>已选择的文件:</h3>';
    files.forEach(file => {
        const div = document.createElement('div');
        div.className = 'feature-item';
        div.innerHTML = `
            <span class="feature-icon">📄</span>
            <span>${file.name} (${formatFileSize(file.size)})</span>
        `;
        listEl.appendChild(div);
    });
    
    showStatus(`已选择 ${files.length} 个文件`, 'success');
});

setupDragDrop('batchUpload', 'batchFiles');

document.getElementById('batchProcessBtn').addEventListener('click', async function() {
    const files = uploadedFiles.batch;
    if (!files || files.length === 0) return;
    
    this.disabled = true;
    document.getElementById('batchProgress').style.display = 'block';
    
    // 获取批量处理设置
    const videoMode = document.getElementById('batchVideoMode').value;
    const keepAudio = document.getElementById('batchKeepAudio').checked;
    
    try {
        const results = [];
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const progress = Math.round((i / files.length) * 100);
            updateProgress('batch', progress, `处理中 ${i + 1}/${files.length}: ${file.name}`);
            
            const formData = new FormData();
            formData.append('file', file);
            
            let endpoint;
            if (file.type.startsWith('video/')) {
                endpoint = '/upload_video';
                
                // 根据选择的模式添加参数
                if (videoMode === 'frame_by_frame') {
                    // 逐帧检测模式
                    formData.append('frame_by_frame', true);
                } else if (videoMode === 'fast') {
                    // 快速模式
                    formData.append('use_fast', true);
                }
                // 标准模式不需要额外参数
                
                formData.append('keep_audio', keepAudio);
            } else {
                endpoint = '/upload';
            }
            
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                results.push(result);
                
                // 等待任务完成
                await waitForTask(result.task_id);
            }
        }
        
        updateProgress('batch', 100, '全部完成!');
        document.getElementById('batchResult').style.display = 'block';
        showStatus(`批量处理完成，共 ${results.length} 个文件`, 'success');
        
    } catch (error) {
        showStatus('批量处理失败: ' + error.message, 'error');
    } finally {
        this.disabled = false;
    }
});

// ==================== 工具函数 ====================

// 更新进度条
function updateProgress(type, percent, text) {
    const fillEl = document.getElementById(`${type}ProgressFill`);
    const textEl = document.getElementById(`${type}ProgressText`);
    
    if (fillEl) {
        fillEl.style.width = percent + '%';
        fillEl.textContent = Math.round(percent) + '%';
    }
    
    if (textEl) {
        textEl.textContent = text;
    }
}

// 轮询任务状态
async function pollTaskStatus(type, taskId, interval = 2000) {
    let retryCount = 0;
    const checkStatus = async () => {
        try {
            const response = await fetch(`${API_BASE}/status/${taskId}`);
            if (!response.ok) {
                if (response.status === 500) {
                    retryCount++;
                    if (retryCount > 3) throw new Error("服务器内部持续故障");
                }
                if (response.status === 404) throw new Error("任务已丢失，请重新上传");
            }
            const result = await response.json();
            
            if (result.status === 'completed') {
                updateProgress(type, 100, '处理完成!');
                document.getElementById(`${type}Loader`).style.display = 'none';
                
                // 显示结果
                if (type === 'image') {
                    const downloadUrl = `${API_BASE}/download/${taskId}`;
                    document.getElementById('imageProcessed').src = downloadUrl;
                    document.getElementById('imageResult').style.display = 'block';
                } else if (type === 'video' || type === 'fastVideo') {
                    const downloadUrl = `${API_BASE}/download/${taskId}`;
                    if (type === 'video') {
                        document.getElementById('videoProcessed').src = downloadUrl;
                        document.getElementById('videoResult').style.display = 'block';
                    } else {
                        document.getElementById('fastVideoResult').style.display = 'block';
                    }
                }
                
                showStatus('处理完成！可以下载结果', 'success');
                document.getElementById(`${type}ProcessBtn`).disabled = false;
                
            } else if (result.status === 'failed') {
                showStatus('处理失败: ' + result.message, 'error');
                document.getElementById(`${type}Loader`).style.display = 'none';
                document.getElementById(`${type}Progress`).style.display = 'none';
                document.getElementById(`${type}ProcessBtn`).disabled = false;
                
            } else if (result.status === 'processing') {
                // 估算进度
                const progress = 30 + Math.random() * 40;
                updateProgress(type, progress, result.message || '处理中...');
                setTimeout(checkStatus, interval);
            } else {
                setTimeout(checkStatus, interval);
            }
        } catch (error) {
            console.error('状态检查失败:', error);
            setTimeout(checkStatus, interval);
            document.getElementById(`${type}ProcessBtn`).disabled = false;
            // 停止 setTimeout，不再轮询
        }
    };
    
    checkStatus();
}

// 等待任务完成
async function waitForTask(taskId) {
    return new Promise((resolve, reject) => {
        const check = async () => {
            try {
                const response = await fetch(`${API_BASE}/status/${taskId}`);
                const result = await response.json();
                
                if (result.status === 'completed') {
                    resolve(result);
                } else if (result.status === 'failed') {
                    reject(new Error(result.message));
                } else {
                    setTimeout(check, 2000);
                }
            } catch (error) {
                reject(error);
            }
        };
        check();
    });
}

// 设置拖拽上传
function setupDragDrop(areaId, inputId) {
    const area = document.getElementById(areaId);
    const input = document.getElementById(inputId);
    
    area.addEventListener('dragover', (e) => {
        e.preventDefault();
        area.classList.add('dragover');
    });
    
    area.addEventListener('dragleave', () => {
        area.classList.remove('dragover');
    });
    
    area.addEventListener('drop', (e) => {
        e.preventDefault();
        area.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            input.files = files;
            input.dispatchEvent(new Event('change'));
        }
    });
}

// 下载结果
function downloadImage() {
    const taskId = taskIds.image;
    if (taskId) {
        window.location.href = `${API_BASE}/download/${taskId}`;
    }
}

function downloadVideo() {
    const taskId = taskIds.video;
    if (taskId) {
        window.location.href = `${API_BASE}/download/${taskId}`;
    }
}

function downloadBatchResults() {
    // TODO: 实现批量下载
    showStatus('批量下载功能开发中...', 'info');
}

// 打开文件夹
async function openImageFile() {
    const taskId = taskIds.image;
    if (taskId) {
        try {
            const response = await fetch(`${API_BASE}/open_file/${taskId}`);
            const result = await response.json();
            if (result.success) {
                showStatus('文件夹已打开！', 'success');
            } else {
                showStatus(result.message || '打开失败', 'error');
                // 尝试直接打开输出目录
                await openOutputFolder();
            }
        } catch (error) {
            showStatus('打开失败: ' + error.message, 'error');
            // 尝试直接打开输出目录
            await openOutputFolder();
        }
    }
}

async function openVideoFile() {
    const taskId = taskIds.video;
    if (taskId) {
        try {
            const response = await fetch(`${API_BASE}/open_file/${taskId}`);
            const result = await response.json();
            if (result.success) {
                showStatus('文件夹已打开！', 'success');
            } else {
                showStatus(result.message || '打开失败', 'error');
                await openOutputFolder();
            }
        } catch (error) {
            showStatus('打开失败: ' + error.message, 'error');
            await openOutputFolder();
        }
    }
}

async function openOutputFolder() {
    try {
        const response = await fetch(`${API_BASE}/open_folder`);
        const result = await response.json();
        if (result.success) {
            showStatus('输出文件夹已打开！', 'success');
        } else {
            showStatus('打开文件夹失败: ' + result.message, 'error');
        }
    } catch (error) {
        showStatus('打开文件夹失败: ' + error.message, 'error');
    }
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(2) + ' MB';
    return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB';
}

// 页面加载完成
document.addEventListener('DOMContentLoaded', function() {
    console.log('智能水印去除工具已加载');
    showStatus('欢迎使用智能水印去除工具！', 'success');
});
