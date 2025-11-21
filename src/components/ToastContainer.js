import React from 'react';
import Toast from './Toast';
import './Toast.css';
import ToastWithActions from './ToastWithActions';

export default function ToastContainer({ toasts, removeToast }) {
    return (
        <div className="toast-container">
            {toasts.map((toast) => {
                if (toast.actions && toast.actions.length > 0) {
                    return (
                        <ToastWithActions
                            key={toast.id}
                            message={toast.message}
                            type={toast.type}
                            actions={toast.actions}
                            onClose={() => removeToast(toast.id)}
                            duration={toast.duration}
                        />
                    );
                }
                return (
                    <Toast
                        key={toast.id}
                        message={toast.message}
                        type={toast.type}
                        onClose={() => removeToast(toast.id)}
                        duration={toast.duration}
                    />
                );
            })}
        </div>
    );
}
