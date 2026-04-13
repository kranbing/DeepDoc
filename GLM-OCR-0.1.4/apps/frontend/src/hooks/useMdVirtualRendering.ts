import { useState, useRef, useEffect, useCallback, useLayoutEffect } from 'react'

interface MdVirtualRenderingConfig {
	bufferSize: number // 缓冲区大小
	defaultItemHeight: number // 默认项目高度
	itemGap?: number // 项目之间的间距
	startIndex?: number // 起始索引（PDF 从 1 开始，blocks 从 0 开始）
}

interface UseMdVirtualRenderingOptions {
	containerRef: React.RefObject<HTMLElement | null>
	totalItems: number
	config: MdVirtualRenderingConfig
	scale?: number // 可选的缩放因子（PDF 使用）
	onItemRender?: (index: number, element: HTMLElement) => void // 项目渲染完成回调
}

export function useMdVirtualRendering({
	containerRef,
	totalItems,
	config,
	scale = 1,
	onItemRender
}: UseMdVirtualRenderingOptions) {
	const { bufferSize, defaultItemHeight, itemGap = 0, startIndex = 0 } = config

	const [visibleRange, setVisibleRange] = useState<[number, number]>([
		startIndex,
		startIndex
	])
	const [itemHeights, setItemHeights] = useState<Record<number, number>>({})
	const [totalHeight, setTotalHeight] = useState<number>(0)
	const [viewportHeight, setViewportHeight] = useState<number>(0)
	const resizeObserverRef = useRef<ResizeObserver | null>(null)

	// 计算项目的累计偏移量
	const getItemOffset = useCallback(
		(itemIndex: number): number => {
			let offset = 0
			const actualIndex = itemIndex - startIndex
			for (let i = 0; i < actualIndex; i++) {
				const index = i + startIndex
				const height = itemHeights[index] || defaultItemHeight
				offset += height * scale + itemGap
			}
			return offset
		},
		[itemHeights, defaultItemHeight, itemGap, scale, startIndex]
	)

	// 计算总高度
	useLayoutEffect(() => {
		if (totalItems === 0) {
			setTotalHeight(0)
			return
		}
		let height = 0
		for (let i = 0; i < totalItems; i++) {
			const index = i + startIndex
			const itemHeight = itemHeights[index] || defaultItemHeight
			height += itemHeight * scale
		}
		// 添加项目之间的间距
		if (totalItems > 0) {
			height += (totalItems - 1) * itemGap
		}
		setTotalHeight(height)
	}, [totalItems, itemHeights, defaultItemHeight, itemGap, scale, startIndex])

	// 根据滚动位置计算可见范围
	const calculateVisibleRange = useCallback(() => {
		if (!containerRef.current || viewportHeight === 0 || totalItems === 0) {
			return [startIndex, startIndex] as [number, number]
		}

		const scrollTop = containerRef.current.scrollTop

		// 找到第一个部分可见的项目
		let startIdx = startIndex
		for (let i = 0; i < totalItems; i++) {
			const index = i + startIndex
			const itemOffset = getItemOffset(index)
			const itemHeight = (itemHeights[index] || defaultItemHeight) * scale
			const itemBottom = itemOffset + itemHeight

			if (itemBottom > scrollTop) {
				startIdx = index
				break
			}
		}

		// 找到最后一个部分可见的项目
		const viewportBottom = scrollTop + viewportHeight
		let endIdx = startIndex + totalItems - 1
		for (let i = startIdx - startIndex; i < totalItems; i++) {
			const index = i + startIndex
			const itemOffset = getItemOffset(index)
			const itemHeight = (itemHeights[index] || defaultItemHeight) * scale
			if (itemOffset + itemHeight >= viewportBottom) {
				endIdx = index
				break
			}
		}

		// 添加缓冲区
		startIdx = Math.max(startIndex, startIdx - bufferSize)
		endIdx = Math.min(startIndex + totalItems - 1, endIdx + bufferSize)

		return [startIdx, endIdx] as [number, number]
	}, [
		viewportHeight,
		totalItems,
		itemHeights,
		defaultItemHeight,
		itemGap,
		scale,
		getItemOffset,
		bufferSize,
		startIndex,
		containerRef
	])

	// 更新可见范围
	const updateVisibleRange = useCallback(() => {
		const [start, end] = calculateVisibleRange()
		setVisibleRange([start, end])
	}, [calculateVisibleRange])

	// 监听滚动
	useEffect(() => {
		const container = containerRef.current
		if (!container) return

		const handleScroll = () => {
			updateVisibleRange()
		}

		container.addEventListener('scroll', handleScroll)
		return () => container.removeEventListener('scroll', handleScroll)
	}, [updateVisibleRange, containerRef])

	// 监听容器尺寸变化
	useEffect(() => {
		const container = containerRef.current
		if (!container) return

		const updateHeight = () => {
			setViewportHeight(container.clientHeight)
			updateVisibleRange()
		}

		updateHeight()

		resizeObserverRef.current = new ResizeObserver(() => {
			updateHeight()
		})
		resizeObserverRef.current.observe(container)

		return () => {
			resizeObserverRef.current?.disconnect()
			resizeObserverRef.current = null
		}
	}, [updateVisibleRange, containerRef])

	// 监听缩放变化，更新可见范围
	useEffect(() => {
		updateVisibleRange()
	}, [scale, updateVisibleRange])

	// 更新项目高度
	const updateItemHeight = useCallback(
		(itemIndex: number, height: number) => {
			// 如果使用了缩放，需要存储原始高度
			const originalHeight = scale !== 1 ? height / scale : height
			setItemHeights(prev => {
				if (prev[itemIndex] !== originalHeight) {
					return { ...prev, [itemIndex]: originalHeight }
				}
				return prev
			})
		},
		[scale]
	)

	// 处理项目渲染成功
	const handleItemRenderSuccess = useCallback(
		(itemIndex: number, element: HTMLElement) => {
			const renderedHeight = element.offsetHeight
			updateItemHeight(itemIndex, renderedHeight)
			onItemRender?.(itemIndex, element)
		},
		[updateItemHeight, onItemRender]
	)

	// 初始化时更新可见范围
	useEffect(() => {
		updateVisibleRange()
	}, [totalItems, updateVisibleRange])

	return {
		visibleRange,
		itemHeights,
		totalHeight,
		viewportHeight,
		getItemOffset,
		handleItemRenderSuccess,
		updateVisibleRange
	}
}
