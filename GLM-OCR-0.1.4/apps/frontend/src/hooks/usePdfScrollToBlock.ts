import { useEffect, useRef } from 'react'
import type { RefObject } from 'react'
import type { Block } from '../store/useOcrStore'

export function usePdfScrollToBlock(
	clickedBlockId: number | null,
	clickedBlock: Block | null,
	viewerRef: RefObject<HTMLDivElement>,
	pdfOriginalWidth: number,
	pdfOriginalHeight: number,
	resultStatus: string | undefined
) {
	const isScrollingRef = useRef(false)

	useEffect(() => {
		if (resultStatus !== 'completed' || !pdfOriginalWidth || !pdfOriginalHeight) return

		if (
			!clickedBlockId ||
			!clickedBlock ||
			!viewerRef.current ||
			!clickedBlock.bbox ||
			clickedBlock.bbox.length < 2
		)
			return

		// 标记正在滚动，防止触发其他更新
		isScrollingRef.current = true

		const scrollToBlock = () => {
			// 查找 PDF 查看器的滚动容器（PdfViewer 内部）
			const scrollContainer = viewerRef.current?.querySelector(
				'.pdf-scroll-container'
			) as HTMLElement

			if (!scrollContainer) {
				isScrollingRef.current = false
				return
			}

			const pageNumber = clickedBlock.pageIndex ?? 1

			// 先尝试查找页面元素
			let pageWrapper = viewerRef.current?.querySelector(
				`[data-pdf-page="${pageNumber}"]`
			) as HTMLElement | null
			let canvas = pageWrapper?.querySelector(
				'.react-pdf__Page__canvas'
			) as HTMLCanvasElement | null

			// 如果页面还未渲染，先滚动到目标页面的大概位置
			if (!pageWrapper || !canvas) {
				// 尝试从已渲染的页面获取当前缩放比例
				let currentScale = 1
				const visibleRenderedPage = viewerRef.current?.querySelector(
					'[data-pdf-visible]'
				) as HTMLElement | null
				const visibleCanvas = visibleRenderedPage?.querySelector(
					'.react-pdf__Page__canvas'
				) as HTMLCanvasElement | null

				if (visibleCanvas && visibleRenderedPage) {
					// 从第一个已渲染页面推断缩放比例
					const displayHeight = visibleRenderedPage.getBoundingClientRect().height
					if (pdfOriginalHeight > 0) {
						currentScale = displayHeight / pdfOriginalHeight
					}
				}

				// 计算目标页面的累计高度（考虑缩放）
				let pageOffset = 20 // 容器 padding
				for (let i = 1; i < pageNumber; i++) {
					const pageHeight = pdfOriginalHeight * currentScale
					pageOffset += pageHeight + 20 // 页面高度 + 间距
				}

				// 先滚动到页面顶部
				scrollContainer.scrollTo({
					top: pageOffset,
					behavior: 'instant'
				})

				// 等待页面渲染，然后重试
				let retryCount = 0
				const maxRetries = 50 // 最多重试 50 次（约 5 秒）
				const checkAndScroll = () => {
					retryCount++
					if (retryCount > maxRetries) {
						isScrollingRef.current = false
						return
					}

					pageWrapper = viewerRef.current?.querySelector(
						`[data-pdf-page="${pageNumber}"]`
					) as HTMLElement | null
					canvas = pageWrapper?.querySelector(
						'.react-pdf__Page__canvas'
					) as HTMLCanvasElement | null

					if (!pageWrapper || !canvas) {
						// 如果还没渲染，继续等待
						requestAnimationFrame(checkAndScroll)
						return
					}

					// 页面已渲染，执行精确定位
					performPreciseScroll(scrollContainer, pageWrapper, canvas)
				}

				// 延迟一下再开始检查，给虚拟渲染一些时间
				setTimeout(() => {
					checkAndScroll()
				}, 100)
				return
			}

			// 页面已渲染，直接执行精确定位
			performPreciseScroll(scrollContainer, pageWrapper, canvas)
		}

		// 执行精确定位到 block
		const performPreciseScroll = (
			scrollContainer: HTMLElement,
			pageWrapper: HTMLElement,
			canvas: HTMLCanvasElement
		) => {
			// 获取页面元素在滚动容器中的位置
			const pageRect = pageWrapper.getBoundingClientRect()
			const containerRect = scrollContainer.getBoundingClientRect()

			// 计算页面相对于滚动容器的偏移
			const pageOffsetY = pageRect.top - containerRect.top + scrollContainer.scrollTop

			const canvasRect = canvas.getBoundingClientRect()
			const scaleY = canvasRect.height / pdfOriginalHeight

			// bbox 现在是相对坐标（每页内的坐标），直接使用
			const yWithinPage = clickedBlock.bbox?.[1] ?? 0

			// 计算目标位置：页面偏移 + bbox 的 y 坐标 * 缩放比例
			const targetY = pageOffsetY + yWithinPage * scaleY - 100 // 100px 的顶部边距

			// 执行滚动
			scrollContainer.scrollTo({
				top: targetY,
				behavior: 'instant'
			})

			// 滚动完成后重置标志
			setTimeout(() => {
				isScrollingRef.current = false
			}, 100) // 短暂延迟以确保滚动完成
		}

		// 延迟执行以确保页面信息已更新
		const timer = setTimeout(scrollToBlock, 200)
		return () => {
			clearTimeout(timer)
			isScrollingRef.current = false
		}
	}, [clickedBlockId, clickedBlock, viewerRef, pdfOriginalHeight, pdfOriginalWidth, resultStatus])
}
