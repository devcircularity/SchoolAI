// components/chat/tools/blocks/ButtonBlock.tsx
import React, { useState } from 'react';
import { 
  ButtonBlock as ButtonBlockType, 
  ButtonGroupBlock as ButtonGroupBlockType, 
  ConfirmationBlock as ConfirmationBlockType, 
  ActionPanelBlock as ActionPanelBlockType 
} from '../types';

interface ButtonProps {
  button: ButtonBlockType['button'];
  onAction: (action: any) => void;
}

const Button: React.FC<ButtonProps> = ({ button, onAction }) => {
  const [isLoading, setIsLoading] = useState(false);
  
  const getVariantClass = (variant: string) => {
    const variants = {
      primary: 'btn-primary',
      secondary: 'btn-secondary', 
      success: 'btn-success',
      warning: 'btn-warning',
      danger: 'btn-danger',
      outline: 'btn-outline'
    };
    return variants[variant as keyof typeof variants] || 'btn-primary';
  };
  
  const getSizeClass = (size: string) => {
    const sizes = {
      sm: 'btn-sm',
      md: '',
      lg: 'btn-lg'
    };
    return sizes[size as keyof typeof sizes] || '';
  };
  
  const handleClick = async () => {
    if (button.disabled || isLoading) return;
    
    setIsLoading(true);
    try {
      await onAction(button.action);
    } finally {
      setIsLoading(false);
    }
  };
  
  const buttonClasses = [
    'btn',
    getVariantClass(button.variant || 'primary'),
    getSizeClass(button.size || 'md'),
    button.disabled && 'opacity-50 cursor-not-allowed',
    isLoading && 'loading'
  ].filter(Boolean).join(' ');
  
  return (
    <button
      className={buttonClasses}
      onClick={handleClick}
      disabled={button.disabled || isLoading}
    >
      {button.icon && (
        <span className="mr-2">
          <i className={`icon-${button.icon}`} />
        </span>
      )}
      {isLoading ? 'Loading...' : button.label}
    </button>
  );
};

export const ButtonBlock: React.FC<{ 
  block: ButtonBlockType; 
  onAction: (action: any) => void;
}> = ({ block, onAction }) => {
  return (
    <div className="mb-4">
      <Button button={block.button} onAction={onAction} />
    </div>
  );
};

export const ButtonGroupBlock: React.FC<{ 
  block: ButtonGroupBlockType; 
  onAction: (action: any) => void;
}> = ({ block, onAction }) => {
  const containerClass = block.layout === 'vertical' 
    ? 'flex flex-col gap-2' 
    : 'flex flex-wrap gap-2';
    
  const alignClass = {
    left: 'justify-start',
    center: 'justify-center', 
    right: 'justify-end'
  }[block.align || 'left'];
  
  return (
    <div className={`mb-4 ${containerClass} ${alignClass}`}>
      {block.buttons.map((button, index) => (
        <Button key={index} button={button} onAction={onAction} />
      ))}
    </div>
  );
};

export const ConfirmationBlock: React.FC<{ 
  block: ConfirmationBlockType; 
  onAction: (action: any) => void;
}> = ({ block, onAction }) => {
  const [showDialog, setShowDialog] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const handleInitialClick = () => {
    setShowDialog(true);
  };
  
  const handleConfirm = async () => {
    setIsLoading(true);
    try {
      await onAction(block.button.action);
      setShowDialog(false);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleCancel = () => {
    setShowDialog(false);
  };
  
  return (
    <div className="mb-4">
      <Button 
        button={{
          ...block.button,
          action: { type: 'confirm', payload: {} }
        }} 
        onAction={handleInitialClick} 
      />
      
      {showDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-2">
              {block.button.dialog.title}
            </h3>
            <p className="text-gray-600 mb-6">
              {block.button.dialog.message}
            </p>
            
            <div className="flex justify-end gap-3">
              <button
                className="btn btn-secondary"
                onClick={handleCancel}
                disabled={isLoading}
              >
                {block.button.dialog.cancelLabel || 'Cancel'}
              </button>
              <button
                className={`btn btn-${block.button.dialog.confirmVariant || 'primary'} ${isLoading ? 'loading' : ''}`}
                onClick={handleConfirm}
                disabled={isLoading}
              >
                {isLoading ? 'Processing...' : (block.button.dialog.confirmLabel || 'Confirm')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export const ActionPanelBlock: React.FC<{ 
  block: ActionPanelBlockType; 
  onAction: (action: any) => void;
}> = ({ block, onAction }) => {
  const getColumnClass = (columns: number) => {
    const columnClasses = {
      1: 'grid-cols-1',
      2: 'grid-cols-1 md:grid-cols-2',
      3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
    };
    return columnClasses[columns as keyof typeof columnClasses] || 'grid-cols-1';
  };
  
  return (
    <div className="mb-6">
      {block.title && (
        <h3 className="text-lg font-semibold mb-4">{block.title}</h3>
      )}
      
      <div className={`grid gap-4 ${getColumnClass(block.columns || 1)}`}>
        {block.items.map((item, index) => (
          <div key={index} className="card p-4 border rounded-lg">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  {item.icon && (
                    <i className={`icon-${item.icon} text-blue-500`} />
                  )}
                  <h4 className="font-medium">{item.title}</h4>
                </div>
                
                {item.description && (
                  <p className="text-gray-600 text-sm mb-3">
                    {item.description}
                  </p>
                )}
              </div>
            </div>
            
            <div className="mt-3">
              <Button button={item.button} onAction={onAction} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};