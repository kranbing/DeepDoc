import { useState, useCallback, useEffect, useRef } from 'react'

interface UsePdfNavigationOptions {
	numPages: number
	getPageOffset: (pageNumber: number) => number
	scrollContainerRef: React.RefObject<HTMLDivElement | null>
	onPageChange?: (page: number) => void
}

export function usePdfNavigation({
	numPages,
	getPageOffset,
	scrollContainerRef,
	onPageChange
}: UsePdfNavigationOptions) {
	const [currentPage, setCurrentPage] = useState<number>(1)
	const [inputValue, setInputValue] = useState<string>('1')
	const isProgrammaticScrollRef = useRef<boolean>(false)
	const lastProgrammaticPageRef = useRef<number>(0)

	// 跳转到指定页
	const goToPage = useCallback(
		(page: number) => {
			const target = Math.max(1, Math.min(page, numPages))

			// 标记为程序触发的滚动，并记录目标页码
			isProgrammaticScrollRef.current = true
			lastProgrammaticPageRef.current = target

			setCurrentPage(target)
			setInputValue(target.toString())
			onPageChange?.(target)

			// 计算目标页面的滚动位置
			const offset = getPageOffset(target)
			const container = scrollContainerRef.current
			if (container) {
				container.scrollTo({
					top: offset,
					behavior: 'instant'
				})

				// 延迟重置标记，确保滚动事件处理完成
				setTimeout(() => {
					isProgrammaticScrollRef.current = false
				}, 100)
			}
		},
		[numPages, getPageOffset, scrollContainerRef, onPageChange]
	)

	// 防抖处理输入框变化
	useEffect(() => {
		const timer = setTimeout(() => {
			const val = parseInt(inputValue)
			if (!isNaN(val) && val >= 1 && val <= numPages && val !== currentPage) {
				goToPage(val)
			} else if (isNaN(val) || val < 1 || val > numPages) {
				// 如果输入无效，恢复当前页码
				setInputValue(currentPage.toString())
			}
		}, 500) // 500ms 防抖延迟

		return () => clearTimeout(timer)
	}, [inputValue, numPages, currentPage, goToPage])

	// 上一页 / 下一页
	const prevPage = useCallback(() => goToPage(currentPage - 1), [currentPage, goToPage])
	const nextPage = useCallback(() => goToPage(currentPage + 1), [currentPage, goToPage])

	// 重置页码
	const resetPage = useCallback(() => {
		setCurrentPage(1)
		setInputValue('1')
	}, [])

	return {
		currentPage,
		inputValue,
		setInputValue,
		setCurrentPage,
		goToPage,
		prevPage,
		nextPage,
		resetPage,
		isProgrammaticScrollRef,
		lastProgrammaticPageRef
	}
}
