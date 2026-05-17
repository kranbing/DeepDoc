import { useState, useRef, useCallback } from 'react'

interface UsePdfZoomOptions {
	initialScale?: number
	onScaleChange?: (scale: number) => void
}

export function usePdfZoom({ initialScale = 1.0, onScaleChange }: UsePdfZoomOptions = {}) {
	const [scale, setScale] = useState<number>(initialScale)
	const isInitialScaleSetRef = useRef<boolean>(false)

	const zoomIn = useCallback(() => {
		setScale(prev => {
			const newScale = Math.min(prev + 0.2, 2.0)
			onScaleChange?.(newScale)
			return newScale
		})
	}, [onScaleChange])

	const zoomOut = useCallback(() => {
		setScale(prev => {
			const newScale = Math.max(prev - 0.2, 0.6)
			onScaleChange?.(newScale)
			return newScale
		})
	}, [onScaleChange])

	const resetZoom = useCallback(() => {
		isInitialScaleSetRef.current = false // 重置标记，允许重新计算自适应缩放
		setScale(1.0)
		onScaleChange?.(1.0)
	}, [onScaleChange])

	const setAutoScale = useCallback(
		(autoScale: number) => {
			if (!isInitialScaleSetRef.current) {
				setScale(autoScale)
				isInitialScaleSetRef.current = true
				onScaleChange?.(autoScale)
			}
		},
		[onScaleChange]
	)

	return {
		scale,
		setScale,
		zoomIn,
		zoomOut,
		resetZoom,
		setAutoScale,
		isInitialScaleSetRef
	}
}
