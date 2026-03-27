import { useState, useEffect } from 'react'
import type { RefObject } from 'react'
import type { Block } from '../store/useOcrStore'

interface PageMetrics {
	width: number
	height: number
	offsetX: number
	offsetY: number
}

// 获取 PDF 页面 metrics 用于定位高亮层
export function usePdfPageMetrics(
	viewerRef: RefObject<HTMLDivElement>,
	pdfUrl: string | null,
	fileType: string | undefined,
	isValid: boolean,
	activeBlock: Block | null,
	pdfOriginalWidth: number,
	pdfOriginalHeight: number
): Record<number, PageMetrics> {
	const [pdfPageMetrics, setPdfPageMetrics] = useState<Record<number, PageMetrics>>({})

	useEffect(() => {
		if (!viewerRef.current || !pdfUrl || fileType !== 'application/pdf') return
		if (!isValid) return
		if (!activeBlock) return

		const pagesToWatch = new Set<number>()
		if (activeBlock?.pageIndex) pagesToWatch.add(activeBlock.pageIndex)

		let cancelled = false
		const observers: ResizeObserver[] = []
		const rafIds: number[] = []

		const observePage = (pageNumber: number) => {
			const tryAttach = () => {
				if (cancelled || !viewerRef.current) return
				const pageWrapper = viewerRef.current.querySelector(
					`[data-pdf-page="${pageNumber}"]`
				) as HTMLElement | null
				const canvas = pageWrapper?.querySelector(
					'.react-pdf__Page__canvas'
				) as HTMLCanvasElement | null

				if (!pageWrapper || !canvas) {
					const id = requestAnimationFrame(tryAttach)
					rafIds.push(id)
					return
				}

				const update = () => {
					if (cancelled) return
					const wrapperRect = pageWrapper.getBoundingClientRect()
					const canvasRect = canvas.getBoundingClientRect()
					setPdfPageMetrics(prev => ({
						...prev,
						[pageNumber]: {
							width: canvasRect.width,
							height: canvasRect.height,
							offsetX: canvasRect.left - wrapperRect.left,
							offsetY: canvasRect.top - wrapperRect.top
						}
					}))
				}

				update()
				const ro = new ResizeObserver(update)
				ro.observe(canvas)
				observers.push(ro)
			}

			tryAttach()
		}

		pagesToWatch.forEach(observePage)

		return () => {
			cancelled = true
			observers.forEach(o => o.disconnect())
			rafIds.forEach(id => cancelAnimationFrame(id))
		}
	}, [viewerRef, pdfUrl, fileType, isValid, activeBlock?.pageIndex, pdfOriginalWidth, pdfOriginalHeight])

	return pdfPageMetrics
}
