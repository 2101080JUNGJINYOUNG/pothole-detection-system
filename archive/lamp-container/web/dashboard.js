// Deep-Guardian Dashboard JavaScript

let map, markers = [];
let currentTab = 'map';
let authStatus = { authenticated: false, user: null, is_admin: false };

// 초기화
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
});

// 인증 확인
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/status');
        authStatus = await response.json();
        
        if (authStatus.authenticated) {
            document.getElementById('mainContainer').style.display = 'block';
            document.getElementById('loginModal').style.display = 'none';
            document.getElementById('userName').textContent = authStatus.user.username;
            if (authStatus.is_admin) {
                document.getElementById('adminReviewBtn').style.display = 'inline-block';
            }
            initDashboard();
        } else {
            document.getElementById('mainContainer').style.display = 'none';
            document.getElementById('loginModal').style.display = 'block';
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        document.getElementById('loginModal').style.display = 'block';
    }
}

// 로그인
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        if (data.success) {
            checkAuthStatus();
        } else {
            alert('로그인 실패: ' + (data.error || '알 수 없는 오류'));
        }
    } catch (error) {
        alert('로그인 오류: ' + error.message);
    }
});

// 로그아웃
async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        checkAuthStatus();
    } catch (error) {
        console.error('Logout failed:', error);
    }
}

// 대시보드 초기화
function initDashboard() {
    initMap();
    loadStatistics();
    loadData();
    loadVideoResults();
}

// 지도 초기화
function initMap() {
    map = L.map('map').setView([37.5665, 126.9780], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
}

// 통계 로드
async function loadStatistics() {
    try {
        const days = document.getElementById('filterDays').value || 7;
        const response = await fetch(`/api/statistics?days=${days}`);
        const stats = await response.json();
        
        if (stats.error) {
            console.error('Statistics error:', stats.error);
            return;
        }
        
        // 통계 카드 업데이트
        const cardsContainer = document.getElementById('statisticsCards');
        cardsContainer.innerHTML = `
            <div class="status-card">
                <h3>전체 탐지 수</h3>
                <div class="value">${stats.total_count.toLocaleString()}</div>
            </div>
            <div class="status-card">
                <h3>검증 통과</h3>
                <div class="value">${stats.validated_count.toLocaleString()}</div>
            </div>
            <div class="status-card">
                <h3>평균 깊이 비율</h3>
                <div class="value">${stats.avg_depth_ratio.toFixed(3)}</div>
            </div>
            <div class="status-card">
                <h3>최대 우선순위</h3>
                <div class="value">${stats.max_priority.toFixed(1)}</div>
            </div>
        `;
        
        // 통계 차트 (통계 탭이 활성화된 경우)
        if (currentTab === 'statistics') {
            updateStatisticsCharts(stats);
        }
    } catch (error) {
        console.error('Load statistics failed:', error);
    }
}

// 통계 차트 업데이트
function updateStatisticsCharts(stats) {
    const container = document.getElementById('statisticsCharts');
    
    // 위험도 분포 차트
    if (stats.risk_distribution && stats.risk_distribution.length > 0) {
        const riskData = stats.risk_distribution.map(r => ({ x: r.risk_level, y: r.count }));
        const riskChart = {
            data: [{
                x: riskData.map(d => d.x),
                y: riskData.map(d => d.y),
                type: 'bar'
            }],
            layout: { title: '위험도별 분포', height: 300 }
        };
        container.innerHTML = '<div id="riskChart"></div><div id="locationChart"></div>';
        Plotly.newPlot('riskChart', riskChart.data, riskChart.layout);
    }
    
    // 위치 유형 분포 차트
    if (stats.location_distribution && stats.location_distribution.length > 0) {
        const locationData = stats.location_distribution.map(l => ({ x: l.location_type, y: l.count }));
        const locationChart = {
            data: [{
                x: locationData.map(d => d.x),
                y: locationData.map(d => d.y),
                type: 'bar'
            }],
            layout: { title: '위치 유형별 분포', height: 300 }
        };
        Plotly.newPlot('locationChart', locationChart.data, locationChart.layout);
    }
}

// 데이터 로드
async function loadData() {
    try {
        const params = new URLSearchParams();
        params.append('limit', '500');
        params.append('days', document.getElementById('filterDays').value || '0');
        params.append('min_depth', document.getElementById('filterMinDepth').value || '0');
        params.append('min_priority', document.getElementById('filterMinPriority').value || '0');
        params.append('validated', document.getElementById('filterValidated').value || 'all');
        
        const riskLevels = Array.from(document.getElementById('filterRiskLevel').selectedOptions).map(o => o.value);
        riskLevels.forEach(level => params.append('risk_level', level));
        
        const response = await fetch(`/api/potholes?${params.toString()}`);
        const data = await response.json();
        
        if (data.error) {
            console.error('Load data error:', data.error);
            return;
        }
        
        // 지도 업데이트
        updateMap(data.potholes);
        
        // 목록 업데이트
        updateList(data.potholes);
    } catch (error) {
        console.error('Load data failed:', error);
    }
}

// 지도 업데이트
function updateMap(potholes) {
    // 기존 마커 제거
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
    
    if (potholes.length === 0) return;
    
    potholes.forEach(pothole => {
        const marker = L.marker([pothole.latitude, pothole.longitude])
            .addTo(map)
            .bindPopup(`
                <strong>포트홀 #${pothole.id}</strong><br>
                깊이 비율: ${pothole.depth_ratio}<br>
                검증: ${pothole.validation_result ? '통과' : '실패'}<br>
                위험도: ${pothole.risk_level || 'N/A'}<br>
                <button onclick="showImage(${pothole.id})">이미지 보기</button>
            `);
        markers.push(marker);
    });
    
    // 지도 범위 조정
    if (markers.length > 0) {
        const group = new L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

// 목록 업데이트
function updateList(potholes) {
    const container = document.getElementById('potholeList');
    
    if (potholes.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 20px; color: #666;">포트홀 데이터가 없습니다.</p>';
        return;
    }
    
    container.innerHTML = potholes.map(pothole => {
        const riskBadge = pothole.risk_level ? `<span class="badge ${pothole.risk_level}">${pothole.risk_level}</span>` : '';
        const validationBadge = `<span class="badge ${pothole.validation_result ? 'valid' : 'invalid'}">${pothole.validation_result ? '검증 통과' : '검증 실패'}</span>`;
        const imageUrl = pothole.image_path ? `/api/image/${pothole.id}` : '';
        
        return `
            <div class="pothole-item">
                ${imageUrl ? `<img src="${imageUrl}" class="pothole-image" onclick="showImage(${pothole.id})" alt="포트홀 이미지">` : '<div style="width: 100px; height: 100px; background: #eee; border-radius: 5px;"></div>'}
                <div class="pothole-info">
                    <strong>포트홀 #${pothole.id}</strong>
                    <div>위도: ${pothole.latitude}, 경도: ${pothole.longitude}</div>
                    <div>깊이 비율: ${pothole.depth_ratio} | 우선순위: ${pothole.priority_score || 0}</div>
                    <div>탐지 시간: ${new Date(pothole.detected_at).toLocaleString('ko-KR')}</div>
                    <div style="margin-top: 5px;">
                        ${riskBadge} ${validationBadge}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// 이미지 미리보기
async function showImage(potholeId) {
    const modal = document.getElementById('imageModal');
    const img = document.getElementById('modalImage');
    img.src = `/api/image/${potholeId}`;
    modal.style.display = 'block';
}

function closeImageModal() {
    document.getElementById('imageModal').style.display = 'none';
}

// 탭 전환
function showTab(tabName) {
    currentTab = tabName;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(tabName + 'Tab').classList.add('active');
    
    if (tabName === 'statistics') {
        loadStatistics();
    } else if (tabName === 'videos') {
        loadVideoResults();
    }
}

// 데이터 내보내기
function exportData(format) {
    const params = new URLSearchParams();
    params.append('format', format);
    params.append('limit', '10000');
    params.append('days', document.getElementById('filterDays').value || '0');
    params.append('validated', document.getElementById('filterValidated').value || 'all');
    
    window.open(`/api/export?${params.toString()}`, '_blank');
}

// 비디오 결과 로드
async function loadVideoResults() {
    try {
        const response = await fetch('/api/video-results');
        const data = await response.json();
        
        const container = document.getElementById('videoResults');
        if (data.videos && data.videos.length > 0) {
            container.innerHTML = data.videos.map(video => `
                <div style="padding: 15px; border-bottom: 1px solid #eee;">
                    <h3>${video.video_name || video.directory}</h3>
                    <div>상태: ${video.status === 'processing' ? '🟢 처리 중' : '✅ 완료'}</div>
                    <div>총 프레임: ${video.total_frames}</div>
                    <div>처리된 프레임: ${video.processed_frames}</div>
                    <div>총 탐지 수: ${video.total_detections}</div>
                    ${video.status === 'completed' && video.result_video_path ? 
                        `<a href="/shared_images/video_results/${video.directory}/${video.result_video_path.split('/').pop()}" download>동영상 다운로드</a>` : ''}
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p style="text-align: center; padding: 20px; color: #666;">비디오 결과가 없습니다.</p>';
        }
    } catch (error) {
        console.error('Load video results failed:', error);
    }
}

// 관리자 검토 페이지
function showAdminReview() {
    // 관리자 검토 페이지는 별도 구현 필요
    alert('관리자 검토 페이지는 별도 구현이 필요합니다.');
}

// 챗봇
function toggleChatbot() {
    document.getElementById('chatbotContainer').classList.toggle('open');
}

async function sendChatMessage() {
    const input = document.getElementById('chatbotInput');
    const message = input.value.trim();
    if (!message) return;
    
    const messagesDiv = document.getElementById('chatbotMessages');
    const userMsg = document.createElement('div');
    userMsg.className = 'chatbot-message user';
    userMsg.textContent = message;
    messagesDiv.appendChild(userMsg);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    input.value = '';
    
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'chatbot-message bot';
    loadingMsg.textContent = '답변 생성 중...';
    messagesDiv.appendChild(loadingMsg);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, use_advanced: true })
        });
        
        const data = await response.json();
        loadingMsg.remove();
        
        const botMsg = document.createElement('div');
        botMsg.className = 'chatbot-message bot';
        botMsg.textContent = data.success ? data.response : `오류: ${data.error}`;
        messagesDiv.appendChild(botMsg);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    } catch (error) {
        loadingMsg.remove();
        const errorMsg = document.createElement('div');
        errorMsg.className = 'chatbot-message bot';
        errorMsg.textContent = `연결 오류: ${error.message}`;
        messagesDiv.appendChild(errorMsg);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
}

// 모달 외부 클릭 시 닫기
window.onclick = function(event) {
    const modal = document.getElementById('imageModal');
    if (event.target === modal) {
        closeImageModal();
    }
}

