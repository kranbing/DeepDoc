import type { Block } from '@/store/useOcrStore'
import { CopyButton } from './CopyButton'

interface HighlightOverlayProps {
	block: Block
	showCopyButton: boolean
	style: {
		left: number
		top: number
		width: number
		height: number
	}
	copyButtonClassName?: string
}

export function HighlightOverlay({
	block,
	showCopyButton,
	style,
	copyButtonClassName
}: HighlightOverlayProps) {
	return (
		<div
			className='absolute pointer-events-none z-10'
			style={{
				left: `${style.left}px`,
				top: `${style.top}px`,
				width: `${style.width}px`,
				height: `${style.height}px`,
				backgroundColor: 'rgba(255, 237, 74, 0.3)',
				border: '2px solid rgba(255, 237, 74, 0.8)'
			}}
		>
			{showCopyButton && (
				<CopyButton content={block.content} className={copyButtonClassName} />
			)}
		</div>
	)
}
