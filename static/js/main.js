// JavaScript principal para As Plot Center

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar funcionalidades
    initializeFlashMessages();
    initializeFileUpload();
    initializeFormValidation();
    initializeSearch();
    initializeModals();
});

// Manejo de mensajes flash
function initializeFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(message => {
        // Auto-ocultar mensajes después de 5 segundos
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
}

// Manejo de subida de archivos
function initializeFileUpload() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Validar tamaño del archivo (16MB máximo)
                const maxSize = 16 * 1024 * 1024; // 16MB en bytes
                if (file.size > maxSize) {
                    alert('El archivo es demasiado grande. El tamaño máximo permitido es 16MB.');
                    input.value = '';
                    return;
                }
                
                // Validar tipo de archivo
                const allowedTypes = ['pdf', 'dwg', 'dxf', 'jpg', 'jpeg', 'png'];
                const fileExtension = file.name.split('.').pop().toLowerCase();
                
                if (!allowedTypes.includes(fileExtension)) {
                    alert('Tipo de archivo no permitido. Formatos permitidos: PDF, DWG, DXF, JPG, PNG');
                    input.value = '';
                    return;
                }
                
                // Mostrar información del archivo
                showFileInfo(file);
            }
        });
    });
}

// Mostrar información del archivo seleccionado
function showFileInfo(file) {
    const fileInfo = document.querySelector('.file-upload-info');
    if (fileInfo) {
        const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);
        fileInfo.innerHTML = `
            <i class="fas fa-file"></i>
            <p><strong>${file.name}</strong></p>
            <p>Tamaño: ${sizeInMB} MB</p>
            <p>Tipo: ${file.type || 'Desconocido'}</p>
        `;
    }
}

// Validación de formularios
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
}

// Validar formulario
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'Este campo es obligatorio');
            isValid = false;
        } else {
            clearFieldError(field);
            
            // Validaciones específicas
            if (field.type === 'email' && !isValidEmail(field.value)) {
                showFieldError(field, 'Ingrese un email válido');
                isValid = false;
            }
            
            if (field.type === 'tel' && !isValidPhone(field.value)) {
                showFieldError(field, 'Ingrese un teléfono válido');
                isValid = false;
            }
        }
    });
    
    return isValid;
}

// Mostrar error en campo
function showFieldError(field, message) {
    clearFieldError(field);
    
    field.style.borderColor = '#dc3545';
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.style.color = '#dc3545';
    errorDiv.style.fontSize = '0.8rem';
    errorDiv.style.marginTop = '0.25rem';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

// Limpiar error de campo
function clearFieldError(field) {
    field.style.borderColor = '';
    
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

// Validar email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Validar teléfono
function isValidPhone(phone) {
    const phoneRegex = /^[\+]?[0-9\s\-\(\)]{10,}$/;
    return phoneRegex.test(phone);
}

// Funcionalidad de búsqueda
function initializeSearch() {
    const searchInputs = document.querySelectorAll('input[type="text"][name="search"]');
    
    searchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            
            // Debounce: esperar 500ms después del último input
            searchTimeout = setTimeout(() => {
                performSearch(this);
            }, 500);
        });
    });
}

// Realizar búsqueda
function performSearch(input) {
    const form = input.closest('form');
    if (form) {
        form.submit();
    }
}

// Inicializar modales
function initializeModals() {
    // Confirmación de eliminación
    const deleteButtons = document.querySelectorAll('a[href*="eliminar"]');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('¿Estás seguro de que quieres eliminar este elemento?')) {
                e.preventDefault();
            }
        });
    });
}

// Utilidades generales
const Utils = {
    // Formatear fecha
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
    },
    
    // Formatear moneda
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('es-VE', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },
    
    // Mostrar loading
    showLoading: function(element) {
        element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cargando...';
        element.disabled = true;
    },
    
    // Ocultar loading
    hideLoading: function(element, originalText) {
        element.innerHTML = originalText;
        element.disabled = false;
    },
    
    // Copiar al portapapeles
    copyToClipboard: function(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showNotification('Copiado al portapapeles', 'success');
        }).catch(() => {
            this.showNotification('Error al copiar', 'error');
        });
    },
    
    // Mostrar notificación
    showNotification: function(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            ${message}
        `;
        
        // Estilos para la notificación
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#d4edda' : type === 'error' ? '#f8d7da' : '#d1ecf1'};
            color: ${type === 'success' ? '#155724' : type === 'error' ? '#721c24' : '#0c5460'};
            padding: 1rem;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remover después de 3 segundos
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
};

// Agregar estilos CSS para animaciones
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .field-error {
        animation: fadeIn 0.3s ease;
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);

// Exportar utilidades para uso global
window.Utils = Utils;





