// components/chat/tools/ChatBlockRenderer.tsx - Updated with button blocks

import React from 'react';
import { 
  Block, 
  isTextBlock, 
  isKPIsBlock, 
  isChartBlock, 
  isTableBlock, 
  isTimelineBlock,
  isEmptyBlock, 
  isErrorBlock, 
  isFileDownloadBlock, 
  isStatusBlock,
  isButtonBlock,
  isButtonGroupBlock, 
  isConfirmationBlock,
  isActionPanelBlock,
  Action
} from './types';

// Import all block components
import { TextBlock } from './blocks/TextBlock';
import { KPIsBlock } from './blocks/KPIsBlock';
import { TableBlock } from './blocks/TableBlock';
import { ChartBlock } from './blocks/ChartBlock';
import { TimelineBlock } from './blocks/TimelineBlock';
import { EmptyBlock } from './blocks/EmptyBlock';
import { ErrorBlock } from './blocks/ErrorBlock';
import { FileDownloadBlock } from './blocks/FileDownloadBlock';
import { StatusBlock } from './blocks/StatusBlock';
import { 
  ButtonBlock, 
  ButtonGroupBlock, 
  ConfirmationBlock, 
  ActionPanelBlock 
} from './blocks/ButtonBlock';

interface ChatBlockRendererProps {
  blocks: Block[];
  onAction?: (action: Action) => void;
}

const ChatBlockRenderer: React.FC<ChatBlockRendererProps> = ({ 
  blocks, 
  onAction = () => {} 
}) => {
  const renderBlock = (block: Block, index: number) => {
    const key = `${block.type}-${index}`;

    try {
      // Handle button blocks first
      if (isButtonBlock(block)) {
        return <ButtonBlock key={key} block={block} onAction={onAction} />;
      }

      if (isButtonGroupBlock(block)) {
        return <ButtonGroupBlock key={key} block={block} onAction={onAction} />;
      }

      if (isConfirmationBlock(block)) {
        return <ConfirmationBlock key={key} block={block} onAction={onAction} />;
      }

      if (isActionPanelBlock(block)) {
        return <ActionPanelBlock key={key} block={block} onAction={onAction} />;
      }

      // Handle existing blocks
      if (isTextBlock(block)) {
        return <TextBlock key={key} block={block} />;
      }

      if (isKPIsBlock(block)) {
        return <KPIsBlock key={key} block={block} onAction={onAction} />;
      }

      if (isTableBlock(block)) {
        return <TableBlock key={key} block={block} onAction={onAction} />;
      }

      if (isChartBlock(block)) {
        return <ChartBlock key={key} block={block} />;
      }

      if (isTimelineBlock(block)) {
        return <TimelineBlock key={key} block={block} />;
      }

      if (isEmptyBlock(block)) {
        return <EmptyBlock key={key} block={block} />;
      }

      if (isErrorBlock(block)) {
        return <ErrorBlock key={key} block={block} />;
      }

      if (isFileDownloadBlock(block)) {
        return <FileDownloadBlock key={key} block={block} />;
      }

      if (isStatusBlock(block)) {
        return <StatusBlock key={key} block={block} />;
      }

      // Unknown block type fallback
      console.warn(`Unknown block type: ${(block as any).type}`);
      return (
        <ErrorBlock 
          key={key} 
          block={{
            type: 'error',
            title: 'Unknown Block Type',
            detail: `Block type "${(block as any).type}" is not supported.`
          }} 
        />
      );

    } catch (error) {
      console.error(`Error rendering block ${block.type}:`, error);
      return (
        <ErrorBlock 
          key={key} 
          block={{
            type: 'error',
            title: 'Block Rendering Error',
            detail: `Failed to render ${block.type} block: ${error instanceof Error ? error.message : 'Unknown error'}`
          }} 
        />
      );
    }
  };

  if (!blocks || blocks.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      {blocks.map(renderBlock)}
    </div>
  );
};

export default ChatBlockRenderer;

// Also provide named export for convenience
export { ChatBlockRenderer };