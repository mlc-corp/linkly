// static/js/index.js

// Cargar links al iniciar
document.addEventListener('DOMContentLoaded', cargarLinks);

// Manejar submit del formulario
document.getElementById('linkForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    await crearLink();
});

function showMessage(message, type = 'error') {
    const container = document.getElementById('messageContainer');
    const className = type === 'success' ? 'success-message' : 'error-message';
    container.innerHTML = `<div class="${className}">${message}</div>`;
    
    // Limpiar mensaje después de 5 segundos
    setTimeout(() => {
        container.innerHTML = '';
    }, 5000);
}

async function cargarLinks() {
    try {
        const response = await fetch('/api/links');
        
        if (!response.ok) {
            throw new Error('Error al cargar los links');
        }
        
        const data = await response.json();
        const links = data.items || [];
        
        mostrarLinks(links);
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('linksTableContainer').innerHTML = 
            '<div class="error-message">Error al cargar los links. Verifica que el servidor esté funcionando.</div>';
    }
}

function mostrarLinks(links) {
    const container = document.getElementById('linksTableContainer');
    
    if (links.length === 0) {
        container.innerHTML = '<div class="mensaje-vacio">No hay links todavía. ¡Crea tu primer link!</div>';
        return;
    }

    const tableHTML = `
        <table>
            <thead>
                <tr>
                    <th>Título</th>
                    <th>Slug</th>
                    <th>Destino</th>
                    <th>Variantes</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                ${links.map(link => `
                    <tr>
                        <td>${escapeHtml(link.title || link.slug)}</td>
                        <td class="slug-cell">${escapeHtml(link.slug)}</td>
                        <td class="url-cell" title="${escapeHtml(link.destinationUrl)}">
                            ${escapeHtml(link.destinationUrl)}
                        </td>
                        <td class="variants-cell">
                            ${link.variants ? link.variants.join(', ') : 'default'}
                        </td>
                        <td class="actions-cell">
                            <button class="btn-ver" onclick="verDetalle('${link.linkId}')">
                                Ver
                            </button>
                            <button class="btn-eliminar" onclick="eliminarLink('${link.linkId}', '${escapeHtml(link.slug)}')">
                                Eliminar
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    container.innerHTML = tableHTML;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function crearLink() {
    const title = document.getElementById('title').value.trim();
    const slug = document.getElementById('slug').value.trim();
    const destinationUrl = document.getElementById('destinationUrl').value.trim();
    const variantsInput = document.getElementById('variants').value.trim();

    // Validaciones básicas
    if (!title || !slug || !destinationUrl) {
        showMessage('Por favor completa todos los campos obligatorios');
        return;
    }

    // Validar formato del slug
    if (!/^[a-z0-9-]+$/.test(slug)) {
        showMessage('El slug solo puede contener letras minúsculas, números y guiones');
        return;
    }

    // Procesar variantes
    let variants = variantsInput 
        ? variantsInput.split(',').map(v => v.trim()).filter(Boolean)
        : [];

    const linkData = {
        title,
        slug,
        destinationUrl,
        variants
    };

    try {
        const response = await fetch('/api/links', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(linkData)
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('Link creado exitosamente', 'success');
            limpiarFormulario();
            cargarLinks();
        } else {
            showMessage(data.error || 'Error al crear el link');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error al conectar con el servidor');
    }
}

function limpiarFormulario() {
    document.getElementById('title').value = '';
    document.getElementById('slug').value = '';
    document.getElementById('destinationUrl').value = '';
    document.getElementById('variants').value = '';
}

function verDetalle(linkId) {
    globalThis.location.href = `/app/links/${linkId}`;
}

async function eliminarLink(linkId, slug) {
    if (!confirm(`¿Estás seguro de eliminar el link "${slug}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/links/${linkId}`, {
            method: 'DELETE'
        });

        if (response.ok || response.status === 204) {
            showMessage('Link eliminado exitosamente', 'success');
            cargarLinks();
        } else {
            const data = await response.json();
            showMessage(data.error || 'Error al eliminar el link');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error al conectar con el servidor');
    }
}