import type { Block } from '../store/useOcrStore'

/**
 * 检查点是否在 bbox 内
 */
export function isPointInBbox(
	x: number,
	y: number,
	bbox: [number, number, number, number]
): boolean {
	const [x1, y1, x2, y2] = bbox
	return x >= x1 && x <= x2 && y >= y1 && y <= y2
}

/**
 * 查找包含指定坐标的 block
 */
export function findBlockAtPoint(
	blocks: Block[],
	x: number,
	y: number,
	pageIndex?: number
): Block | undefined {
	return blocks.find(block => {
		if (!block.bbox) return false
		if (pageIndex !== undefined && block.pageIndex !== pageIndex) return false
		return isPointInBbox(x, y, block.bbox)
	})
}

/**
 * PDF 坐标转换：从屏幕坐标转换为 PDF 相对坐标
 */
export function convertPdfScreenToRelative(
	screenX: number,
	screenY: number,
	canvasRect: DOMRect,
	pdfOriginalWidth: number,
	pdfOriginalHeight: number
): { x: number; y: number } {
	const scaleX = canvasRect.width / pdfOriginalWidth
	const scaleY = canvasRect.height / pdfOriginalHeight
	return {
		x: screenX / scaleX,
		y: screenY / scaleY
	}
}

/**
 * 图片坐标转换：从屏幕坐标转换为原始图片坐标
 */
export function convertImageScreenToOriginal(
	screenX: number,
	screenY: number,
	imgElement: HTMLImageElement
): { x: number; y: number } {
	const imgRect = imgElement.getBoundingClientRect()
	const imgNaturalWidth = imgElement.naturalWidth
	const imgNaturalHeight = imgElement.naturalHeight
	const imgDisplayWidth = imgRect.width
	const imgDisplayHeight = imgRect.height

	const scaleX = imgNaturalWidth / imgDisplayWidth
	const scaleY = imgNaturalHeight / imgDisplayHeight

	return {
		x: screenX * scaleX,
		y: screenY * scaleY
	}
}
