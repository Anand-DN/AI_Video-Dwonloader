import React, { useEffect } from 'react';
import './Toast.css';

export default function ToastWithActions({ message, type, onClose, duration = 5000, actions }) {
    useEffect(() => {
        if (!actions || actions.length === 0) {
            const timer = setTimeout(() => {
                onClose();
            }, duration);
            return () => clearTimeout(timer);
        }
    }, [duration, onClose, actions]);

    const getIcon = () => {
        switch (type) {
            case 'success':
                return '✓';
            case 'error':
                return '✕';
            case 'info':
                return 'ℹ';
            case 'loading':
                return '⏳';
            default:
                return 'ℹ';
        }
    };

    return (
        <div className={`toast toast-${type} ${actions && actions.length > 0 ? 'toast-with-actions' : ''}`}>
            <div className="toast-icon">{getIcon()}</div>
            <div className="toast-content-wrapper">
                <div className="toast-message">{message}</div>
                {actions && actions.length > 0 && (
                    <div className="toast-actions">
                        {actions.map((action, idx) => (
                            <button
                                key={idx}
                                className={`toast-action-btn ${action.primary ? 'primary' : ''}`}
                                onClick={() => {
                                    action.onClick();
                                    if (action.closeOnClick !== false) {
                                        onClose();
                                    }
                                }}
                            >
                                {action.icon && <span className="action-icon">{action.icon}</span>}
                                {action.label}
                            </button>
                        ))}
                    </div>
                )}
            </div>
            <button className="toast-close" onClick={onClose}>
                ✕
            </button>
        </div>
    );
}   
