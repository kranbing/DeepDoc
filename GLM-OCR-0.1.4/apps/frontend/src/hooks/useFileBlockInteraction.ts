import { useCallback } from 'react'
import type { Block } from '../store/useOcrStore'
import { findBlockAtPoint, convertPdfScreenToRelative, convertImageScreenToOriginal } from '../libs/blockUtils'

const COPY_BUTTON_SELECTOR = '[data-ocr-copy-button]'

interface UseFileBlockInteractionOptions {
	blocks: Block[]
	resultStatus: string | undefined
	setHoveredBlockId: (id: number | null) => void
	setClickedBlockId: (id: number | null) => void
	setShowCopyButton: (show: boolean) => void
}

export function useFileBlockInteraction({
	blocks,
	resultStatus,
	setHoveredBlockId,
	setClickedBlockId,
	setShowCopyButton
}: UseFileBlockInteractionOptions) {
	const isInteractionEnabled = resultStatus === 'completed' && blocks.length > 0

	const handlePdfInteraction = useCallback(
		(
			e: React.MouseEvent<HTMLDivElement>,
			pageNumber: number,
			pdfOriginalWidth: number,
			pdfOriginalHeight: number,
			isClick: boolean
		) => {
			if (!isInteractionEnabled) {
				if (!isClick) setHoveredBlockId(null)
				return
			}

			// 鼠标移动到复制按钮上时，不要清空高亮
			if ((e.target as HTMLElement).closest(COPY_BUTTON_SELECTOR)) {
				return
			}

			const canvas = (e.currentTarget as HTMLElement).querySelector(
				'.react-pdf__Page__canvas'
			) as HTMLCanvasElement | null
			if (!canvas) {
				if (!isClick) setHoveredBlockId(null)
				return
			}

			const rect = canvas.getBoundingClientRect()
			const screenX = e.clientX - rect.left
			const screenY = e.clientY - rect.top

			const { x: pdfX, y: pdfY } = convertPdfScreenToRelative(
				screenX,
				screenY,
				rect,
				pdfOriginalWidth,
				pdfOriginalHeight
			)

			const hit = findBlockAtPoint(blocks, pdfX, pdfY, pageNumber)

			if (isClick) {
				if (hit) {
					setClickedBlockId(hit.id)
					setShowCopyButton(true)
				} else {
					setClickedBlockId(null)
				}
			} else {
				if (hit) {
					setHoveredBlockId(hit.id)
					setShowCopyButton(true)
				} else {
					setHoveredBlockId(null)
				}
			}
		},
		[blocks, isInteractionEnabled, setHoveredBlockId, setClickedBlockId, setShowCopyButton]
	)

	const handleImageInteraction = useCallback(
		(e: React.MouseEvent<HTMLDivElement>, isClick: boolean) => {
			if (!isInteractionEnabled) {
				if (!isClick) setHoveredBlockId(null)
				return
			}

			// 鼠标移动到复制按钮上时，不要清空高亮
			if ((e.target as HTMLElement).closest(COPY_BUTTON_SELECTOR)) {
				return
			}

			const imgElement = e.currentTarget.querySelector('img')
			if (!imgElement) {
				if (!isClick) setHoveredBlockId(null)
				return
			}

			const imgRect = imgElement.getBoundingClientRect()
			const screenX = e.clientX - imgRect.left
			const screenY = e.clientY - imgRect.top

			const { x: imgX, y: imgY } = convertImageScreenToOriginal(
				screenX,
				screenY,
				imgElement
			)

			const hit = findBlockAtPoint(blocks, imgX, imgY)

			if (isClick) {
				if (hit) {
					setClickedBlockId(hit.id)
					setShowCopyButton(true)
				} else {
					setClickedBlockId(null)
				}
			} else {
				if (hit) {
					setHoveredBlockId(hit.id)
					setShowCopyButton(true)
				} else {
					setHoveredBlockId(null)
				}
			}
		},
		[blocks, isInteractionEnabled, setHoveredBlockId, setClickedBlockId, setShowCopyButton]
	)

	const handleMouseLeave = useCallback(
		(e: React.MouseEvent<HTMLDivElement>) => {
			// 从父元素移动到子元素（或其后代）不算真正离开
			const related = e.relatedTarget
			if (related instanceof Node && e.currentTarget.contains(related)) return
			setHoveredBlockId(null)
		},
		[setHoveredBlockId]
	)

	return {
		handlePdfClick: (e: React.MouseEvent<HTMLDivElement>, pageNumber: number, pdfOriginalWidth: number, pdfOriginalHeight: number) =>
			handlePdfInteraction(e, pageNumber, pdfOriginalWidth, pdfOriginalHeight, true),
		handlePdfMouseMove: (e: React.MouseEvent<HTMLDivElement>, pageNumber: number, pdfOriginalWidth: number, pdfOriginalHeight: number) =>
			handlePdfInteraction(e, pageNumber, pdfOriginalWidth, pdfOriginalHeight, false),
		handlePdfMouseLeave: handleMouseLeave,
		handleImageClick: (e: React.MouseEvent<HTMLDivElement>) =>
			handleImageInteraction(e, true),
		handleImageMouseMove: (e: React.MouseEvent<HTMLDivElement>) =>
			handleImageInteraction(e, false),
		handleImageMouseLeave: handleMouseLeave
	}
}
