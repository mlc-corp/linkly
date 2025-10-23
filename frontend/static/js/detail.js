// static/js/detail.js

const linkId = document.getElementById('linkIdData').value;

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

function mostrarContenido(link, metrics) {
    const container = document.getElementById('contentContainer');
    
    const variantsHTML = link.variants && link.variants.length > 0
        ? link.variants.map(variant => `
            <div class="variant-card">
                <div>
                    <div class="variant-name">${escapeHtml(variant)}</div>
                    <div class="variant-url">linkly.space/${escapeHtml(link.slug)}/${escapeHtml(variant)}</div>
                </div>
                <button class="btn-copy" onclick="copiarURL(event, '${escapeHtml(link.slug)}', '${escapeHtml(variant)}')">
                    Copiar
                </button>
            </div>
        `).join('')
        : '<div class="variant-card"><div class="variant-name">default</div><div class="variant-url">linkly.space/' + escapeHtml(link.slug) + '</div></div>';

    let metricsHTML = '';
    
    if (metrics && metrics.totals && metrics.totals.clicks > 0) {
        const totals = metrics.totals;
        
        metricsHTML = `
            <div class="card">
                <h2>📈 Métricas Totales</h2>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">${totals.clicks.toLocaleString()}</div>
                        <div class="metric-label">Clics Totales</div>
                    </div>
                </div>

                ${totals.byVariant ? generarBreakdown('Por Variante', totals.byVariant, totals.clicks) : ''}
                ${totals.byDevice ? generarBreakdown('Por Dispositivo', totals.byDevice, totals.clicks) : ''}
                ${totals.byCountry ? generarBreakdown('Por País', totals.byCountry, totals.clicks) : ''}
            </div>
        `;
    } else {
        metricsHTML = `
            <div class="card">
                <h2>📈 Métricas</h2>
                <div class="empty-metrics">
                    Este link aún no ha recibido clics. Comparte las URLs para empezar a ver métricas.
                </div>
            </div>
        `;
    }

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

        ${metricsHTML}
    `;
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
            <div class="breakdown-list">
                ${items}
            </div>
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatearFecha(isoDate) {
    if (!isoDate) return 'N/A';
    
    const date = new Date(isoDate);
    const opciones = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    return date.toLocaleDateString('es-ES', opciones);
}

async function copiarURL(event, slug, variant) {
    const url = `https://linkly.space/${slug}/${variant}`;
    
    try {
        await navigator.clipboard.writeText(url);
        
        // Feedback visual
        event.target.textContent = '✓ Copiado';
        event.target.style.background = '#27ae60';
        
        setTimeout(() => {
            event.target.textContent = 'Copiar';
            event.target.style.background = '#3498db';
        }, 2000);
    } catch (error) {
        console.error('Error al copiar:', error);
        alert('No se pudo copiar la URL. Por favor, cópiala manualmente: ' + url);
    }
}