// static/js/detail.js

const linkId = document.getElementById('linkIdData').value;
const BASE_DOMAIN = globalThis.BASE_DOMAIN || 'linkly.space';

document.addEventListener('DOMContentLoaded', async () => {
    await cargarDatos();
});

async function cargarDatos() {
    try {
        // Cargar información del link y métricas en paralelo
        const [linkResponse, metricsResponse] = await Promise.all([
            fetch(`/api/links/${linkId}`),
            fetch(`/api/links/${linkId}/metrics`)
        ]);

        if (!linkResponse.ok) {
            throw new Error('No se pudo cargar la información del link');
        }

        const linkData = await linkResponse.json();
        
        let metricsData = null;
        if (metricsResponse.ok) {
            metricsData = await metricsResponse.json();
        }

        mostrarContenido(linkData, metricsData);
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('contentContainer').innerHTML = `
            <div class="card">
                <div class="error-message">
                    Error al cargar la información. Por favor, verifica que el servidor esté funcionando.
                </div>
            </div>
        `;
    }
}

async function refrescarMetricas() {
    const refreshBtn = document.getElementById('refreshMetricsBtn');
    
    // Mostrar estado de carga en el botón
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.textContent = '⟳ Actualizando...';
    }
    
    try {
        const metricsResponse = await fetch(`/api/links/${linkId}/metrics`);
        
        let metricsData = null;
        if (metricsResponse.ok) {
            metricsData = await metricsResponse.json();
        }
        
        // Actualizar solo la sección de métricas
        actualizarSeccionMetricas(metricsData);
        
        // Mostrar mensaje de éxito temporal
        mostrarMensajeRefresh('✓ Métricas actualizadas', 'success');
        
    } catch (error) {
        console.error('Error al refrescar métricas:', error);
        mostrarMensajeRefresh('✗ Error al actualizar métricas', 'error');
    } finally {
        // Restaurar el botón
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.textContent = '⟳ Actualizar Métricas';
        }
    }
}

function mostrarMensajeRefresh(mensaje, tipo) {
    const existingMsg = document.getElementById('refreshMessage');
    if (existingMsg) {
        existingMsg.remove();
    }
    
    const msgDiv = document.createElement('div');
    msgDiv.id = 'refreshMessage';
    msgDiv.className = tipo === 'success' ? 'success-message' : 'error-message';
    msgDiv.textContent = mensaje;
    msgDiv.style.marginBottom = '20px';
    
    const container = document.getElementById('contentContainer');
    container.insertBefore(msgDiv, container.firstChild);
    
    setTimeout(() => {
        msgDiv.remove();
    }, 3000);
}

function actualizarSeccionMetricas(metrics) {
    const metricsContainer = document.getElementById('metricsSection');
    
    if (!metricsContainer) return;
    
    let metricsHTML = '';
    
    if (metrics?.totals?.clicks > 0) {
        const totals = metrics.totals;
        
        metricsHTML = `
            <h2>📈 Métricas Totales</h2>
            <div class="metrics-actions">
                <button id="refreshMetricsBtn" class="btn-refresh" onclick="refrescarMetricas()">
                    ⟳ Actualizar Métricas
                </button>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">${totals.clicks.toLocaleString()}</div>
                    <div class="metric-label">Clics Totales</div>
                </div>
            </div>

            ${totals.byVariant ? generarBreakdown('Por Variante', totals.byVariant, totals.clicks) : ''}
            ${totals.byDevice ? generarBreakdown('Por Dispositivo', totals.byDevice, totals.clicks) : ''}
            ${totals.byCountry ? generarBreakdown('Por País', totals.byCountry, totals.clicks) : ''}
        `;
    } else {
        metricsHTML = `
            <h2>📈 Métricas</h2>
            <div class="metrics-actions">
                <button id="refreshMetricsBtn" class="btn-refresh" onclick="refrescarMetricas()">
                    ⟳ Actualizar Métricas
                </button>
            </div>
            <div class="empty-metrics">
                Este link aún no ha recibido clics. Comparte las URLs para empezar a ver métricas.
            </div>
        `;
    }
    
    metricsContainer.innerHTML = metricsHTML;
}

function mostrarContenido(link, metrics) {
    const container = document.getElementById('contentContainer');
    
    const variantsHTML = link.variants && link.variants.length > 0
        ? link.variants.map(variant => `
            <div class="variant-card">
                <div>
                    <div class="variant-name">${escapeHtml(variant)}</div>
                    <div class="variant-url">${BASE_DOMAIN}/${escapeHtml(link.slug)}/${escapeHtml(variant)}</div>
                </div>
                <button class="btn-copy" onclick="copiarURL(event, '${escapeHtml(link.slug)}', '${escapeHtml(variant)}')">
                    Copiar
                </button>
            </div>
        `).join('')
        : `<div class="variant-card">
            <div>
                <div class="variant-name">default</div>
                <div class="variant-url">${BASE_DOMAIN}/${escapeHtml(link.slug)}</div>
            </div>
            <button class="btn-copy" onclick="copiarURL(event, '${escapeHtml(link.slug)}', 'default')">
                Copiar
            </button>
        </div>`;

    container.innerHTML = `
        <div class="card">
            <h2>ℹ️ Información General</h2>
            
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Título</div>
                    <div class="info-value">${escapeHtml(link.title || link.slug)}</div>
                </div>
                
                <div class="info-item">
                    <div class="info-label">Slug</div>
                    <div class="info-value slug-value">${escapeHtml(link.slug)}</div>
                </div>
                
                <div class="info-item">
                    <div class="info-label">Fecha de Creación</div>
                    <div class="info-value">${formatearFecha(link.createdAt)}</div>
                </div>
            </div>

            <div class="info-item" style="margin-bottom: 20px;">
                <div class="info-label">URL de Destino</div>
                <div class="info-value">${escapeHtml(link.destinationUrl)}</div>
            </div>

            <div class="variants-section">
                <div class="breakdown-title">🔗 URLs Generadas</div>
                ${variantsHTML}
            </div>
        </div>

        <div class="card" id="metricsSection">
            <div class="loading">Cargando métricas...</div>
        </div>
    `;
    
    // Actualizar la sección de métricas
    actualizarSeccionMetricas(metrics);
}

function generarBreakdown(titulo, data, total) {
    if (!data || Object.keys(data).length === 0) {
        return '';
    }

    const items = Object.entries(data)
        .sort((a, b) => b[1] - a[1])
        .map(([name, value]) => {
            const percentage = ((value / total) * 100).toFixed(1);
            return `
                <div class="breakdown-item">
                    <div>
                        <div class="breakdown-name">${escapeHtml(name)}</div>
                        <div class="breakdown-bar">
                            <div class="breakdown-bar-fill" style="width: ${percentage}%"></div>
                        </div>
                    </div>
                    <div class="breakdown-value">${value.toLocaleString()}</div>
                </div>
            `;
        }).join('');

    return `
        <div class="breakdown-section">
            <div class="breakdown-title">${titulo}</div>
            <div class="breakdown-container">
                ${items}
            </div>
        </div>
    `;
}

function formatearFecha(fechaISO) {
    if (!fechaISO) return 'N/A';
    
    const fecha = new Date(fechaISO);
    const opciones = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    return fecha.toLocaleDateString('es-ES', opciones);
}

function copiarURL(event, slug, variant) {
    event.preventDefault();
    
    const url = `${BASE_DOMAIN}/${slug}/${variant}`;
    
    navigator.clipboard.writeText(url).then(() => {
        const button = event.target;
        const originalText = button.textContent;
        
        button.textContent = '✓ Copiado';
        button.style.backgroundColor = '#28a745';
        
        setTimeout(() => {
            button.textContent = originalText;
            button.style.backgroundColor = '';
        }, 2000);
    }).catch(err => {
        console.error('Error al copiar:', err);
        alert('No se pudo copiar la URL');
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.toString().replaceAll(/[&<>"']/g, m => map[m]);
}