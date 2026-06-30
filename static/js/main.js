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
let userId = localStorage.getItem('user_id') || generateUserId();

function generateUserId() {
    const id = 'user_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('user_id', id);
    return id;
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
        const response = await fetch(url);
        const data = await response.json();
        if (data.code !== 200) {
            throw new Error(data.message || 'API Error');
        }
        return data;
    },
    
    async post(path, body) {
        const response = await fetch(`${API_BASE}${path}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await response.json();
        if (data.code !== 200) {
            throw new Error(data.message || 'API Error');
        }
        return data;
    },
    
    async delete(path) {
        const response = await fetch(`${API_BASE}${path}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        if (data.code !== 200) {
            throw new Error(data.message || 'API Error');
        }
        return data;
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
        
        const commentHtml = comments.length > 0 ? comments.map(c => `
            <div class="comment-item">
                <div class="comment-header">
                    <span class="comment-user">${c.username}</span>
                    <span class="comment-rating">${c.rating_stars}</span>
                </div>
                <p>${c.content}</p>
                <div class="comment-time">${c.formatted_time}</div>
            </div>
        `).join('') : '<p style="color:#999;">暂无评论</p>';
        
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

async function toggleFavorite(attractionId) {
    try {
        const btn = document.getElementById(`fav-btn-${attractionId}`);
        const isFavorited = btn.textContent === '已收藏';
        
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
    try {
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
            username: '游客',
            content: content,
            rating: parseInt(rating.value)
        });
        
        input.value = '';
        showToast('评论提交成功');
        
        const comment = result.data;
        const commentList = document.getElementById('comment-list');
        const newComment = `
            <div class="comment-item">
                <div class="comment-header">
                    <span class="comment-user">${comment.username}</span>
                    <span class="comment-rating">${comment.rating_stars}</span>
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
                preferences: { themes, duration: parseInt(duration), travel_style: '随意' },
                weather: currentWeatherData || {}
            });
            recommendation = result.data;
        } catch (e) {
            console.warn('LLM推荐失败，使用备用接口:', e);
            const result = await api.get('/routes/recommend', { 
                theme: themes[0] || '', 
                duration: parseInt(duration) 
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
});
