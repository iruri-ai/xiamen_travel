const API_BASE = '/api';
let currentPage = 1;
let currentFilters = {
    keyword: '',
    area: '',
    sort_by: 'popularity',
    tag_id: null
};
let selectedTags = [];
let currentAttractionId = null;
let currentUser = null;

function loadCurrentUser() {
    const token = localStorage.getItem('access_token');
    if (token) {
        fetch(`${API_BASE}/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(response => response.json())
        .then(data => {
            if (data.code === 200) {
                currentUser = data.data;
                updateAuthUI();
            } else {
                clearAuth();
            }
        })
        .catch(() => {
            clearAuth();
        });
    }
}

function updateAuthUI() {
    const loginBtn = document.getElementById('login-btn');
    const registerBtn = document.getElementById('register-btn');
    const userMenu = document.getElementById('user-menu');
    const userName = document.getElementById('user-name');
    const adminBtn = document.getElementById('admin-attraction-btn');
    
    if (currentUser) {
        loginBtn.style.display = 'none';
        registerBtn.style.display = 'none';
        userMenu.style.display = 'flex';
        userName.textContent = currentUser.nickname || currentUser.username;
        
        if (currentUser.role === 'admin') {
            adminBtn.style.display = 'block';
        } else {
            adminBtn.style.display = 'none';
        }
    } else {
        loginBtn.style.display = 'block';
        registerBtn.style.display = 'block';
        userMenu.style.display = 'none';
    }
}

function clearAuth() {
    currentUser = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    updateAuthUI();
}

const api = {
    async get(path, params = {}) {
        const urlParams = new URLSearchParams();
        for (const [key, value] of Object.entries(params)) {
            if (Array.isArray(value)) {
                value.forEach(v => urlParams.append(key, v));
            } else {
                urlParams.set(key, value);
            }
        }
        const query = urlParams.toString();
        const url = `${API_BASE}${path}${query ? '?' + query : ''}`;
        const token = localStorage.getItem('access_token');
        const headers = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        const response = await fetch(url, { headers });
        const data = await response.json();
        if (data.code !== 200) {
            throw new Error(data.message || 'API Error');
        }
        return data;
    },
    
    async post(path, body) {
        const token = localStorage.getItem('access_token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        const response = await fetch(`${API_BASE}${path}`, {
            method: 'POST',
            headers,
            body: JSON.stringify(body)
        });
        const data = await response.json();
        if (data.code !== 200) {
            throw new Error(data.message || 'API Error');
        }
        return data;
    },
    
    async delete(path) {
        const token = localStorage.getItem('access_token');
        const headers = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        const response = await fetch(`${API_BASE}${path}`, {
            method: 'DELETE',
            headers
        });
        const data = await response.json();
        if (data.code !== 200) {
            throw new Error(data.message || 'API Error');
        }
        return data;
    },
    
    async put(path, body) {
        const token = localStorage.getItem('access_token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        const response = await fetch(`${API_BASE}${path}`, {
            method: 'PUT',
            headers,
            body: JSON.stringify(body)
        });
        const data = await response.json();
        if (data.code !== 200) {
            throw new Error(data.message || 'API Error');
        }
        return data;
    },

    async authPost(path, body) {
        const response = await fetch(`${API_BASE}${path}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        return await response.json();
    },

    async authGet(path) {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE}${path}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        return await response.json();
    }
};

function showToast(message, duration = 3000) {
    const toast = document.getElementById('toast');
    toast.querySelector('.toast-message').textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), duration);
}

async function loadAttractions(page = 1) {
    currentPage = page;
    const grid = document.getElementById('attractions-grid');
    grid.innerHTML = '<div class="loading">加载景点中...</div>';
    
    try {
        const params = {
            page: currentPage,
            per_page: 6,
            sort_by: currentFilters.sort_by,
            sort_order: 'DESC'
        };
        
        if (currentFilters.keyword) {
            params.keyword = currentFilters.keyword;
        }
        if (currentFilters.area) {
            params.area = currentFilters.area;
        }
        selectedTags.forEach(tagId => {
            params.tag_id = params.tag_id || [];
            params.tag_id.push(tagId);
        });
        
        const result = await api.get('/attractions', params);
        renderAttractions(result.data.items);
        renderPagination(result.data);
    } catch (error) {
        grid.innerHTML = `<div class="loading">加载失败: ${error.message}</div>`;
    }
}

function renderAttractions(attractions) {
    const grid = document.getElementById('attractions-grid');
    
    if (!attractions || attractions.length === 0) {
        grid.innerHTML = '<div class="loading">暂无景点数据</div>';
        return;
    }
    
    grid.innerHTML = attractions.map(attr => `
        <div class="attraction-card" data-id="${attr.id}">
            <img src="${attr.image}" alt="${attr.name}" class="attraction-image" 
                 onerror="this.src='/static/images/default.jpg'">
            <div class="attraction-info">
                <h3 class="attraction-name">${attr.name}</h3>
                <p class="attraction-desc">${attr.desc}</p>
                <div class="attraction-meta">
                    <span class="attraction-rating">${attr.rating_stars} ${attr.rating}</span>
                    <div class="attraction-tags">
                        ${(attr.tag_names || []).slice(0, 3).map(t => 
                            `<span class="attraction-tag">${t}</span>`
                        ).join('')}
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    grid.querySelectorAll('.attraction-card').forEach(card => {
        card.addEventListener('click', () => {
            showAttractionDetail(parseInt(card.dataset.id));
        });
    });
}

function renderPagination(data) {
    const pagination = document.getElementById('pagination');
    if (data.pages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    if (currentPage > 1) {
        html += `<button class="page-btn" onclick="loadAttractions(${currentPage - 1})">上一页</button>`;
    }
    
    for (let i = 1; i <= data.pages; i++) {
        if (i === 1 || i === data.pages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" 
                    onclick="loadAttractions(${i})">${i}</button>`;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            html += '<span>...</span>';
        }
    }
    
    if (currentPage < data.pages) {
        html += `<button class="page-btn" onclick="loadAttractions(${currentPage + 1})">下一页</button>`;
    }
    
    pagination.innerHTML = html;
}

async function loadAreas() {
    try {
        const result = await api.get('/attractions/areas');
        const select = document.getElementById('area-filter');
        select.innerHTML = '<option value="">全部区域</option>' + 
            result.data.map(area => `<option value="${area}">${area}</option>`).join('');
    } catch (error) {
        console.error('加载区域失败:', error);
    }
}

async function loadTags() {
    try {
        const result = await api.get('/tags');
        const container = document.getElementById('tags-filter');
        container.innerHTML = result.data.map(tag => `
            <span class="tag-chip" data-id="${tag.id}">${tag.name}</span>
        `).join('');
        
        container.querySelectorAll('.tag-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const tagId = parseInt(chip.dataset.id);
                if (selectedTags.includes(tagId)) {
                    selectedTags = selectedTags.filter(id => id !== tagId);
                    chip.classList.remove('active');
                } else {
                    selectedTags.push(tagId);
                    chip.classList.add('active');
                }
                loadAttractions(1);
            });
        });
    } catch (error) {
        console.error('加载标签失败:', error);
    }
}

async function loadThemeOptions() {
    try {
        const result = await api.get('/tags');
        const container = document.getElementById('theme-options');
        container.innerHTML = `
            <label class="theme-checkbox select-all">
                <input type="checkbox" id="select-all-themes">
                <span class="checkbox-custom"></span>
                <span class="theme-label">全选</span>
            </label>
            ${result.data.map(tag => `
                <label class="theme-checkbox">
                    <input type="checkbox" name="theme" value="${tag.name}" data-id="${tag.id}">
                    <span class="checkbox-custom" style="border-color: ${tag.color || '#d9d9d9'}"></span>
                    <span class="theme-label">${tag.name}</span>
                </label>
            `).join('')}
        `;
        
        document.getElementById('select-all-themes').addEventListener('change', (e) => {
            const checkboxes = document.querySelectorAll('#theme-options input[name="theme"]');
            checkboxes.forEach(cb => cb.checked = e.target.checked);
        });
    } catch (error) {
        console.error('加载主题选项失败:', error);
        const fallbackThemes = ['亲子', '摄影', '人文', '海边', '美食', '历史', '低强度'];
        const container = document.getElementById('theme-options');
        container.innerHTML = fallbackThemes.map(theme => `
            <label class="theme-checkbox">
                <input type="checkbox" name="theme" value="${theme}">
                <span class="checkbox-custom"></span>
                <span class="theme-label">${theme}</span>
            </label>
        `).join('');
    }
}



async function showAttractionDetail(id) {
    currentAttractionId = id;
    const modal = document.getElementById('attraction-modal');
    const body = document.getElementById('modal-body');
    
    modal.classList.add('show');
    
    try {
        const [attrResult, commentsResult] = await Promise.all([
            api.get(`/attractions/${id}`),
            api.get('/comments', { attraction_id: id, per_page: 10 })
        ]);
        
        const attr = attrResult.data;
        const comments = commentsResult.data.items || [];
        
        const commentHtml = comments.length > 0 ? comments.map(c => {
            const isOwn = currentUser && c.user_id === currentUser.id;
            const deleteBtn = isOwn ? `<button class="comment-delete-btn" onclick="deleteComment(${c.id})">删除</button>` : '';
            return `
            <div class="comment-item" id="comment-${c.id}" data-user-id="${c.user_id}">
                <div class="comment-header">
                    <span class="comment-user">${c.username}</span>
                    <span class="comment-rating">${c.rating_stars}</span>
                    ${deleteBtn}
                </div>
                <p>${c.content}</p>
                <div class="comment-time">${c.formatted_time}</div>
            </div>
            `;
        }).join('') : '<p style="color:#999;">暂无评论</p>';
        
        body.innerHTML = `
            <img src="${attr.image}" alt="${attr.name}" class="modal-image">
            <h2 class="modal-title">${attr.name}</h2>
            <div class="modal-info">
                <span>${attr.rating_stars} ${attr.rating}</span>
                <span>📍 ${attr.address}</span>
                <span>⏰ ${attr.open_time}</span>
                <span>🎫 ${attr.ticket_info}</span>
                <span>⏱️ ${attr.formatted_duration}</span>
                <span>💬 ${attr.comment_count}条评论</span>
            </div>
            <div class="attraction-tags" style="margin-bottom:20px;">
                ${(attr.tag_names || []).map(t => `<span class="attraction-tag">${t}</span>`).join('')}
            </div>
            <p class="modal-desc">${attr.desc}</p>
            <div class="modal-actions">
                <button class="btn btn-success" onclick="toggleFavorite(${attr.id})">
                    <span id="fav-btn-${attr.id}">收藏</span>
                </button>
                <button class="btn btn-outline">分享</button>
            </div>
            <div class="comments-section">
                <h3>游客评论</h3>
                <div class="comment-form">
                    <textarea id="comment-input" placeholder="写下您的评论..."></textarea>
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <select id="rating-input" style="padding:10px;">
                            <option value="5">★★★★★</option>
                            <option value="4">★★★★</option>
                            <option value="3">★★★</option>
                            <option value="2">★★</option>
                            <option value="1">★</option>
                        </select>
                        <button class="btn btn-primary" onclick="submitComment(${attr.id})">发表评论</button>
                    </div>
                </div>
                <div class="comment-list" id="comment-list">
                    ${commentHtml}
                </div>
            </div>
        `;
        
        checkFavoriteStatus(attr.id);
    } catch (error) {
        body.innerHTML = `<p>加载失败: ${error.message}</p>`;
    }
}

function getAuthUserId() {
    return currentUser ? currentUser.id : localStorage.getItem('user_id') || generateAnonymousId();
}

function generateAnonymousId() {
    const id = 'anon_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('user_id', id);
    return id;
}

async function toggleFavorite(attractionId) {
    if (!currentUser) {
        showToast('请先登录');
        document.getElementById('login-btn').click();
        return;
    }
    
    try {
        const btn = document.getElementById(`fav-btn-${attractionId}`);
        const isFavorited = btn.textContent === '已收藏';
        const userId = currentUser.id;
        
        if (isFavorited) {
            const favorites = await api.get('/favorites', { user_id: userId });
            const fav = favorites.data.find(f => f.attraction_id === attractionId);
            if (fav) {
                await api.delete(`/favorites/${fav.id}?user_id=${userId}`);
                btn.textContent = '收藏';
                showToast('已取消收藏');
            }
        } else {
            await api.post('/favorites', { 
                attraction_id: attractionId, 
                user_id: userId 
            });
            btn.textContent = '已收藏';
            showToast('收藏成功');
        }
    } catch (error) {
        showToast(error.message);
    }
}

async function checkFavoriteStatus(attractionId) {
    if (!currentUser) {
        const btn = document.getElementById(`fav-btn-${attractionId}`);
        if (btn) btn.textContent = '收藏';
        return;
    }
    
    try {
        const userId = currentUser.id;
        const result = await api.get('/favorites', { user_id: userId });
        const isFavorited = result.data.some(f => f.attraction_id === attractionId);
        const btn = document.getElementById(`fav-btn-${attractionId}`);
        if (btn) {
            btn.textContent = isFavorited ? '已收藏' : '收藏';
        }
    } catch (error) {
        console.error('检查收藏状态失败:', error);
    }
}

async function submitComment(attractionId) {
    if (!currentUser) {
        showToast('请先登录');
        document.getElementById('login-btn').click();
        return;
    }
    
    const input = document.getElementById('comment-input');
    const rating = document.getElementById('rating-input');
    const content = input.value.trim();
    
    if (!content) {
        showToast('请输入评论内容');
        return;
    }
    
    try {
        const result = await api.post('/comments', {
            attraction_id: attractionId,
            user_id: currentUser.id,
            username: currentUser.nickname || currentUser.username,
            content: content,
            rating: parseInt(rating.value)
        });
        
        input.value = '';
        showToast('评论提交成功');
        
        const comment = result.data;
        const commentList = document.getElementById('comment-list');
        const deleteBtn = `<button class="comment-delete-btn" onclick="deleteComment(${comment.id})">删除</button>`;
        const newComment = `
            <div class="comment-item" id="comment-${comment.id}" data-user-id="${currentUser?.id || ''}">
                <div class="comment-header">
                    <span class="comment-user">${comment.username}</span>
                    <span class="comment-rating">${comment.rating_stars}</span>
                    ${deleteBtn}
                </div>
                <p>${comment.content}</p>
                <div class="comment-time">${comment.formatted_time}</div>
            </div>
        `;
        commentList.insertAdjacentHTML('afterbegin', newComment);
        
    } catch (error) {
        showToast(error.message);
    }
}

async function deleteComment(commentId) {
    if (!confirm('确定要删除这条评论吗？')) {
        return;
    }
    
    try {
        await api.delete(`/comments/${commentId}`);
        showToast('评论删除成功');
        
        const commentEl = document.getElementById(`comment-${commentId}`);
        if (commentEl) {
            commentEl.remove();
        }
    } catch (error) {
        showToast(error.message || '删除失败');
    }
}

function refreshCommentNicknames(newNickname) {
    if (!currentUser) return;
    
    document.querySelectorAll('.comment-item[data-user-id="' + currentUser.id + '"] .comment-user').forEach(el => {
        el.textContent = newNickname;
    });
}

let currentWeatherData = null;

async function loadWeather() {
    const summaryEl = document.getElementById('weather-summary');
    const cardEl = document.getElementById('weather-card');
    
    try {
        const result = await api.get('/weather/xiamen');
        currentWeatherData = result.data;
        const weather = result.data;
        
        summaryEl.innerHTML = `
            <span>${weather.city}</span>
            <span class="weather-badge">实时: ${weather.current.weather}</span>
            <span>${weather.current.temp}°C</span>
        `;
        
        cardEl.innerHTML = `
            <div class="weather-section">
                <div class="weather-section-title">📍 实时天气</div>
                <div class="weather-current">
                    <div class="weather-temp-large">${weather.current.temp}°</div>
                    <div class="weather-current-info">
                        <div class="weather-status">${weather.current.weather}</div>
                        <div class="weather-meta">
                            <span>湿度: ${weather.current?.humidity || 'N/A'}</span>
                            <span>空气: ${weather.current?.air || 'N/A'}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="weather-divider"></div>
            
            <div class="weather-section">
                <div class="weather-section-title">🌤️ 今日预报</div>
                <div class="weather-forecast">
                    <div class="forecast-item">
                        <div class="forecast-label">天气状况</div>
                        <div class="forecast-value">${weather.weather}</div>
                    </div>
                    <div class="forecast-item">
                        <div class="forecast-label">温度范围</div>
                        <div class="forecast-value">${weather.temp_low} ~ ${weather.temp_high}</div>
                    </div>
                    <div class="forecast-item">
                        <div class="forecast-label">风向风力</div>
                        <div class="forecast-value">${weather.wind || 'N/A'} ${weather.windSpeed || ''}</div>
                    </div>
                </div>
            </div>
            
            <div class="weather-living">
                <div class="living-title">生活指数</div>
                <div class="living-items">
                    ${(weather.living || []).slice(0, 8).map(item => `
                        <div class="living-item">
                            <span class="living-name">${item.name}</span>
                            <span class="living-index">${item.index}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            ${weather.is_fallback ? '<p class="weather-notice">* 数据来自缓存或默认值</p>' : ''}
        `;
    } catch (error) {
        summaryEl.innerHTML = '<span>天气加载失败</span>';
        cardEl.innerHTML = '<div class="weather-loading">天气数据暂时不可用</div>';
    }
}

async function getRecommendation() {
    if (!currentUser) {
        showToast('请先登录');
        document.getElementById('login-btn').click();
        return;
    }
    
    const resultEl = document.getElementById('recommendation-result');
    const themes = [];
    
    document.querySelectorAll('#theme-options input:checked').forEach(cb => {
        themes.push(cb.value);
    });
    
    const duration = document.getElementById('duration-select').value;
    
    try {
        resultEl.innerHTML = '<div class="loading">正在获取推荐...</div>';
        resultEl.classList.add('show');
        
        let recommendation;
        try {
            const result = await api.post('/routes/llm/recommend', {
                preferences: { themes, duration: duration, travel_style: '随意' },
                weather: currentWeatherData || {}
            });
            recommendation = result.data;
        } catch (e) {
            console.warn('LLM推荐失败，使用备用接口:', e);
            const result = await api.get('/routes/recommend', { 
                theme: themes[0] || '', 
                duration: duration 
            });
            recommendation = result.data;
        }
        
        const scheduleHtml = recommendation.schedule && recommendation.schedule.length > 0 
            ? `<div class="recommendation-schedule">
                <h4>📅 时间安排</h4>
                <div class="schedule-list">
                    ${recommendation.schedule.map(s => {
                        const attr = recommendation.attractions.find(a => a.id === s.attraction_id);
                        return `
                            <div class="schedule-item">
                                <span class="schedule-time">${s.start_time} - ${s.end_time}</span>
                                <span class="schedule-name">${attr ? attr.name : '未知景点'}</span>
                                <span class="schedule-duration">${attr ? attr.formatted_duration : '未知时长'}</span>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>` 
            : '';
        
        resultEl.innerHTML = `
            <div class="recommendation-reason">${recommendation.reason || '基于您的偏好推荐'}</div>
            ${scheduleHtml}
            <div class="recommendation-attractions">
                ${recommendation.attractions.map((a, index) => {
                    const schedule = recommendation.schedule ? recommendation.schedule[index] : null;
                    return `
                    <div class="recommendation-attraction">
                        <div class="attraction-rank">${index + 1}</div>
                        <img src="${a.image}" alt="${a.name}" 
                             onerror="this.src='/static/images/default.jpg'">
                        <div class="attraction-content">
                            <div class="attraction-header">
                                <strong>${a.name}</strong>
                                ${schedule ? `<span class="attraction-time">${schedule.start_time} - ${schedule.end_time}</span>` : ''}
                            </div>
                            <p class="attraction-desc">${a.desc || ''}</p>
                            <div class="attraction-meta">
                                <span class="meta-item">⏰ ${a.open_time || '开放时间未知'}</span>
                                <span class="meta-item">⏱️ ${a.formatted_duration}</span>
                            </div>
                            <div class="attraction-recommend-reason">
                                <strong>💡 推荐理由：</strong>${a.recommend_reason || '适合游玩'}
                            </div>
                        </div>
                    </div>
                `;
                }).join('')}
            </div>
            <div class="recommendation-tips">
                <strong>💡 小贴士：</strong>${recommendation.tips || '祝您旅途愉快！'}
            </div>
        `;
        
    } catch (error) {
        resultEl.innerHTML = `<div class="loading">推荐失败: ${error.message}</div>`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadAttractions(1);
    loadAreas();
    loadTags();
    loadThemeOptions();
    loadWeather();
    
    const searchInput = document.getElementById('search-input');
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentFilters.keyword = e.target.value;
            loadAttractions(1);
        }, 500);
    });
    
    document.getElementById('area-filter').addEventListener('change', (e) => {
        currentFilters.area = e.target.value;
        loadAttractions(1);
    });
    
    document.getElementById('sort-filter').addEventListener('change', (e) => {
        currentFilters.sort_by = e.target.value;
        loadAttractions(1);
    });
    
    document.getElementById('recommend-btn').addEventListener('click', getRecommendation);
    
    const modal = document.getElementById('attraction-modal');
    modal.querySelector('.modal-close').addEventListener('click', () => {
        modal.classList.remove('show');
    });
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('show');
        }
    });
    
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
            document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
            this.classList.add('active');
        });
    });

    loadCurrentUser();

    initAuthModal();
});

function initAuthModal() {
    const authModal = document.getElementById('auth-modal');
    const loginBtn = document.getElementById('login-btn');
    const registerBtn = document.getElementById('register-btn');
    const authClose = document.querySelector('.auth-close');
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const formLogin = document.getElementById('form-login');
    const formRegister = document.getElementById('form-register');
    const linkToRegister = document.getElementById('link-to-register');
    const linkToLogin = document.getElementById('link-to-login');
    const submitLogin = document.getElementById('submit-login');
    const submitRegister = document.getElementById('submit-register');
    const logoutBtn = document.getElementById('logout-btn');

    function showAuthModal() {
        authModal.classList.add('show');
    }

    function hideAuthModal() {
        authModal.classList.remove('show');
        clearFormErrors();
    }

    function switchToLogin() {
        tabLogin.classList.add('active');
        tabRegister.classList.remove('active');
        formLogin.style.display = 'block';
        formRegister.style.display = 'none';
        clearFormErrors();
    }

    function switchToRegister() {
        tabRegister.classList.add('active');
        tabLogin.classList.remove('active');
        formRegister.style.display = 'block';
        formLogin.style.display = 'none';
        clearFormErrors();
    }

    function clearFormErrors() {
        document.querySelectorAll('.form-error').forEach(el => el.textContent = '');
    }

    function showFieldError(fieldId, message) {
        document.getElementById(fieldId).textContent = message;
    }

    loginBtn.addEventListener('click', showAuthModal);
    registerBtn.addEventListener('click', () => {
        showAuthModal();
        switchToRegister();
    });
    authClose.addEventListener('click', hideAuthModal);
    authModal.addEventListener('click', (e) => {
        if (e.target === authModal) {
            hideAuthModal();
        }
    });

    tabLogin.addEventListener('click', switchToLogin);
    tabRegister.addEventListener('click', switchToRegister);
    linkToRegister.addEventListener('click', (e) => {
        e.preventDefault();
        switchToRegister();
    });
    linkToLogin.addEventListener('click', (e) => {
        e.preventDefault();
        switchToLogin();
    });

    submitLogin.addEventListener('click', async () => {
        clearFormErrors();
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;

        if (!username) {
            showFieldError('login-username-error', '请输入用户名或邮箱');
            return;
        }
        if (!password) {
            showFieldError('login-password-error', '请输入密码');
            return;
        }

        const result = await api.authPost('/auth/login', { username, password });
        if (result.code === 200) {
            localStorage.setItem('access_token', result.data.access_token);
            localStorage.setItem('refresh_token', result.data.refresh_token);
            currentUser = result.data.user;
            updateAuthUI();
            hideAuthModal();
            showToast('登录成功');
        } else {
            showFieldError('login-password-error', result.message);
        }
    });

    submitRegister.addEventListener('click', async () => {
        clearFormErrors();
        const username = document.getElementById('reg-username').value.trim();
        const email = document.getElementById('reg-email').value.trim();
        const password = document.getElementById('reg-password').value;
        const confirm = document.getElementById('reg-confirm').value;

        if (!username) {
            showFieldError('reg-username-error', '请输入用户名');
            return;
        }
        if (username.length < 2 || username.length > 50) {
            showFieldError('reg-username-error', '用户名长度必须在2-50个字符之间');
            return;
        }
        if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            showFieldError('reg-email-error', '邮箱格式不正确');
            return;
        }
        if (!password) {
            showFieldError('reg-password-error', '请输入密码');
            return;
        }
        if (password.length < 6) {
            showFieldError('reg-password-error', '密码长度至少6位');
            return;
        }
        if (password !== confirm) {
            showFieldError('reg-confirm-error', '两次输入的密码不一致');
            return;
        }

        const result = await api.authPost('/auth/register', { 
            username, 
            email: email || undefined, 
            password 
        });
        if (result.code === 200) {
            localStorage.setItem('access_token', result.data.access_token);
            localStorage.setItem('refresh_token', result.data.refresh_token);
            currentUser = result.data.user;
            updateAuthUI();
            hideAuthModal();
            showToast('注册成功');
        } else {
            if (result.message.includes('用户名')) {
                showFieldError('reg-username-error', result.message);
            } else if (result.message.includes('邮箱')) {
                showFieldError('reg-email-error', result.message);
            } else {
                showFieldError('reg-password-error', result.message);
            }
        }
    });

    logoutBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        clearAuth();
        showToast('已退出登录');
    });

    document.getElementById('user-profile').addEventListener('click', async (e) => {
        e.preventDefault();
        openProfileModal();
    });

    document.getElementById('user-favorites').addEventListener('click', async (e) => {
        e.preventDefault();
        openFavoritesModal();
    });

    document.getElementById('user-comments').addEventListener('click', async (e) => {
        e.preventDefault();
        openCommentsModal();
    });

    document.getElementById('admin-attraction-btn').addEventListener('click', async (e) => {
        e.preventDefault();
        openAdminAttractionModal();
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.add('show');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
    }
}

async function openProfileModal() {
    openModal('profile-modal');
    const content = document.getElementById('profile-content');
    content.innerHTML = '<p>加载中...</p>';
    
    try {
        const user = currentUser;
        if (!user) {
            content.innerHTML = '<p>请先登录</p>';
            return;
        }
        
        const result = await api.get('/auth/me');
        const profile = result.data || user;
        
        const displayName = profile.nickname || profile.username || '未设置';
        
        content.innerHTML = `
            <div class="profile-info">
                <div class="profile-row">
                    <span class="profile-label">昵称</span>
                    <div style="display:flex; gap:10px; align-items:center;">
                        <span class="profile-value">${displayName}</span>
                        <button class="btn btn-sm btn-outline" onclick="editNickname('${profile.nickname || ''}')">修改</button>
                    </div>
                </div>
                <div class="profile-row">
                    <span class="profile-label">登录账号</span>
                    <span class="profile-value">${profile.username || '-'}</span>
                </div>
                <div class="profile-row">
                    <span class="profile-label">邮箱</span>
                    <span class="profile-value">${profile.email || '-'}</span>
                </div>
                <div class="profile-row">
                    <span class="profile-label">角色</span>
                    <span class="profile-value">${profile.role === 'admin' ? '管理员' : '普通用户'}</span>
                </div>
                <div class="profile-row">
                    <span class="profile-label">注册时间</span>
                    <span class="profile-value">${profile.created_at ? profile.created_at.split(' ')[0] : '-'}</span>
                </div>
            </div>
        `;
    } catch (error) {
        content.innerHTML = `<p>加载失败：${error.message}</p>`;
    }
}

async function editNickname(currentNickname) {
    const newNickname = prompt('请输入新昵称:', currentNickname);
    if (newNickname === null) {
        return;
    }
    
    const trimmed = newNickname.trim();
    if (!trimmed) {
        showToast('昵称不能为空');
        return;
    }
    
    if (trimmed.length > 50) {
        showToast('昵称长度不能超过50个字符');
        return;
    }
    
    try {
        const result = await api.put('/auth/profile', { nickname: trimmed });
        if (result.code === 200) {
            showToast('昵称修改成功');
            currentUser.nickname = trimmed;
            openProfileModal();
            
            const userNameEl = document.getElementById('user-name');
            if (userNameEl) {
                userNameEl.textContent = trimmed;
            }
            
            refreshCommentNicknames(trimmed);
        } else {
            showToast(result.message || '修改失败');
        }
    } catch (error) {
        showToast(error.message || '修改失败');
    }
}

async function openFavoritesModal() {
    openModal('favorites-modal');
    const content = document.getElementById('favorites-content');
    content.innerHTML = '<p>加载中...</p>';
    
    try {
        const result = await api.get('/favorites');
        const favorites = result.data || [];
        
        if (favorites.length === 0) {
            content.innerHTML = '<p style="color:#999;">暂无收藏</p>';
            return;
        }
        
        content.innerHTML = `
            <div class="favorites-list">
                ${favorites.map(f => `
                    <div class="favorite-item" id="favorite-${f.id}">
                        <img src="${f.image_url || '/static/images/default.jpg'}" class="favorite-image" alt="${f.attraction_name}">
                        <div class="favorite-info">
                            <div class="favorite-name">${f.attraction_name}</div>
                            <div class="favorite-address">${f.address || ''}</div>
                            <div class="favorite-rating">${'★'.repeat(Math.round(f.rating || 0))} ${f.rating || 0}</div>
                        </div>
                        <div class="favorite-actions">
                            <button class="btn btn-sm" onclick="showAttractionDetail(${f.attraction_id}); closeModal('favorites-modal')">查看</button>
                            <button class="btn btn-sm btn-outline" onclick="removeFavorite(${f.id})">取消收藏</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        content.innerHTML = `<p>加载失败：${error.message}</p>`;
    }
}

async function removeFavorite(favoriteId) {
    if (!confirm('确定取消收藏吗？')) {
        return;
    }
    
    try {
        await api.delete(`/favorites/${favoriteId}`);
        showToast('取消收藏成功');
        
        const favoriteEl = document.getElementById(`favorite-${favoriteId}`);
        if (favoriteEl) {
            favoriteEl.remove();
        }
    } catch (error) {
        showToast(error.message || '操作失败');
    }
}

async function openCommentsModal() {
    openModal('comments-modal');
    const content = document.getElementById('comments-content');
    content.innerHTML = '<p>加载中...</p>';
    
    try {
        const result = await api.get('/comments', { user_id: currentUser?.id });
        const comments = result.data?.items || [];
        
        if (comments.length === 0) {
            content.innerHTML = '<p style="color:#999;">暂无评论</p>';
            return;
        }
        
        content.innerHTML = `
            <div class="comments-list">
                ${comments.map(c => `
                    <div class="comment-item" id="comment-${c.id}" data-user-id="${c.user_id}">
                        <div style="flex:1;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                                <span style="font-weight:bold;">${c.attraction_name || '未知景点'}</span>
                                <span>${c.rating_stars}</span>
                            </div>
                            <div style="margin-bottom:5px;">
                                <span class="comment-user" style="font-size:14px; color:var(--text-secondary);">${c.username}</span>
                            </div>
                            <p style="margin-bottom:5px;">${c.content}</p>
                            <div style="color:var(--text-secondary); font-size:14px;">${c.formatted_time}</div>
                        </div>
                        <div class="comment-actions">
                            <button class="btn btn-sm" onclick="showAttractionDetail(${c.attraction_id}); closeModal('comments-modal')">查看景点</button>
                        <button class="btn btn-sm btn-outline" onclick="deleteComment(${c.id})">删除</button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    } catch (error) {
        content.innerHTML = `<p>加载失败：${error.message}</p>`;
    }
}

async function openAdminAttractionModal() {
    if (!currentUser || currentUser.role !== 'admin') {
        showToast('无管理员权限');
        return;
    }
    openModal('admin-attraction-modal');
    await loadAdminAttractionList();
}

async function loadAdminAttractionList() {
    const list = document.getElementById('admin-attraction-list');
    try {
        const result = await api.get('/attractions?per_page=100');
        const attractions = result.data.items;
        
        if (attractions.length === 0) {
            list.innerHTML = '<p>暂无景点</p>';
            return;
        }
        
        list.innerHTML = attractions.map(attr => `
            <div class="admin-item">
                <div>
                    <span style="font-weight:bold;">${attr.name}</span>
                    <span style="color:var(--text-secondary); font-size:14px; margin-left:10px;">${attr.area || '-'}</span>
                    <span style="color:var(--text-secondary); font-size:14px; margin-left:10px;">¥${attr.price}</span>
                </div>
                <div class="admin-item-actions">
                    <button class="btn btn-sm" onclick="editAttraction(${attr.id})">编辑</button>
                    <button class="btn btn-sm btn-outline" onclick="deleteAttractionAdmin(${attr.id})">删除</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        list.innerHTML = `<p>加载失败：${error.message}</p>`;
    }
}

function showAttractionForm(attraction = null) {
    const form = document.getElementById('admin-attraction-form');
    const title = document.getElementById('admin-attraction-title');
    
    if (attraction) {
        document.getElementById('form-attraction-id').value = attraction.id;
        document.getElementById('form-name').value = attraction.name || '';
        document.getElementById('form-description').value = attraction.desc || attraction.description || '';
        document.getElementById('form-image_url').value = attraction.image || attraction.image_url || '';
        document.getElementById('form-address').value = attraction.address || '';
        document.getElementById('form-open_time').value = attraction.open_time || '';
        document.getElementById('form-recommended_duration').value = attraction.recommended_duration || 120;
        document.getElementById('form-area').value = attraction.area || '';
        document.getElementById('form-price').value = attraction.price || 0;
        document.getElementById('form-tags').value = (attraction.tag_names || []).join(',');
        document.getElementById('form-rating').value = attraction.rating || 5.0;
        title.textContent = '编辑景点';
    } else {
        document.getElementById('form-attraction-id').value = '';
        document.getElementById('form-name').value = '';
        document.getElementById('form-description').value = '';
        document.getElementById('form-image_url').value = '';
        document.getElementById('form-address').value = '';
        document.getElementById('form-open_time').value = '';
        document.getElementById('form-recommended_duration').value = 120;
        document.getElementById('form-area').value = '';
        document.getElementById('form-price').value = 0;
        document.getElementById('form-tags').value = '';
        document.getElementById('form-rating').value = 5.0;
        title.textContent = '添加景点';
    }
    
    form.style.display = 'block';
    form.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function cancelAttractionForm() {
    document.getElementById('admin-attraction-form').style.display = 'none';
    document.getElementById('admin-attraction-title').textContent = '景点管理';
}

async function editAttraction(id) {
    try {
        const result = await api.get(`/attractions/${id}`);
        showAttractionForm(result.data);
    } catch (error) {
        showToast(error.message);
    }
}

async function saveAttraction() {
    const id = document.getElementById('form-attraction-id').value;
    const tagsInput = document.getElementById('form-tags').value;
    const tags = tagsInput.split(',').map(t => t.trim()).filter(t => t);
    
    const data = {
        name: document.getElementById('form-name').value,
        description: document.getElementById('form-description').value,
        image_url: document.getElementById('form-image_url').value,
        address: document.getElementById('form-address').value,
        open_time: document.getElementById('form-open_time').value,
        recommended_duration: parseInt(document.getElementById('form-recommended_duration').value) || 120,
        area: document.getElementById('form-area').value,
        price: parseFloat(document.getElementById('form-price').value) || 0,
        rating: parseFloat(parseFloat(document.getElementById('form-rating').value).toFixed(1)) || 5.0,
        tags: tags
    };
    
    try {
        if (id) {
            await api.put(`/attractions/${id}`, data);
            showToast('景点更新成功');
        } else {
            await api.post('/attractions', data);
            showToast('景点创建成功');
        }
        cancelAttractionForm();
        await loadAdminAttractionList();
    } catch (error) {
        showToast(error.message);
    }
}

async function deleteAttractionAdmin(id) {
    if (!confirm('确定要删除这个景点吗？删除后将无法恢复，且相关的评论、收藏也会被删除。')) {
        return;
    }
    
    try {
        await api.delete(`/attractions/${id}`);
        showToast('景点删除成功');
        await loadAdminAttractionList();
    } catch (error) {
        showToast(error.message);
    }
}
