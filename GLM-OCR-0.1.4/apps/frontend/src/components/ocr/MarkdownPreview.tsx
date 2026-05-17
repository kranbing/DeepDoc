// src/components/MarkdownPreview.tsx

'use client'

import { useRef, useMemo, useCallback, useState, useEffect } from 'react'
import { useOcrStore } from '@/store/useOcrStore'
import ReactMarkdown from 'react-markdown'
import rehypeRaw from 'rehype-raw'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
import './markdown.css'
import rehypeMathInHtml from '@/libs/rehypeMathInHtml'
import { useMdVirtualRendering } from '@/hooks/useMdVirtualRendering'
import { CopyButton } from './CopyButton'

// 虚拟渲染配置
const VIRTUAL_CONFIG = {
	BUFFER_BLOCKS: 10, // 可视区前后各渲染的缓冲块数
	PLACEHOLDER_HEIGHT: 100, // 默认块高度（像素）
	DEFAULT_BLOCK_HEIGHT: 150, // 默认块高度
};

// KaTeX 配置：禁用严格模式警告
const katexOptions = {
	throwOnError: false, // 不抛出错误，而是渲染为文本
	strict: false, // 禁用严格模式检查
}

export function MarkdownPreview() {
	const { blocks, hoveredBlockId, clickedPdfBlockId, setHoveredBlockId, setClickedBlockId } = useOcrStore()

	const [showCopyButton, setShowCopyButton] = useState(false)

	const markdownRef = useRef<HTMLDivElement>(null)

	// 使用虚拟渲染 hook
	const {
		visibleRange,
		itemHeights: blockHeights,
		totalHeight,
		getItemOffset,
		updateVisibleRange,
		handleItemRenderSuccess: handleBlockRenderSuccess
	} = useMdVirtualRendering({
		containerRef: markdownRef,
		totalItems: blocks.length,
		config: {
			bufferSize: VIRTUAL_CONFIG.BUFFER_BLOCKS,
			defaultItemHeight: VIRTUAL_CONFIG.DEFAULT_BLOCK_HEIGHT,
			itemGap: 8, // my-2 = 8px
			startIndex: 0
		}
	})

	// 滚动定位逻辑：当 clickedPdfBlockId 变化时，自动滚动到对应的元素
	useEffect(() => {

		const container = markdownRef.current
		if (!clickedPdfBlockId || !container || !getItemOffset) return

		// 找到目标 block 的索引
		const targetIndex = blocks.findIndex(block => String(block.id) === String(clickedPdfBlockId))
		if (targetIndex === -1) return

		// 计算目标元素的偏移量
		const itemOffset = getItemOffset(targetIndex)

		// 获取元素高度（使用实际高度或默认高度）
		const itemHeight = (blockHeights[targetIndex] || VIRTUAL_CONFIG.DEFAULT_BLOCK_HEIGHT)

		// 计算目标滚动位置：将元素居中显示
		// 公式：itemOffset - (容器高度 / 2) + (元素高度 / 2)
		const containerHeight = container.clientHeight
		const padding = 24
		const targetScrollTop = itemOffset - containerHeight / 2 + itemHeight / 2

		// 先更新可见范围，确保目标元素被渲染
		updateVisibleRange?.()

		// 使用 requestAnimationFrame 确保 DOM 更新后再滚动
		requestAnimationFrame(() => {
			container.scrollTo({
				top: Math.max(0, targetScrollTop - padding),
				// behavior: 'smooth'
			})
		})
	}, [
		clickedPdfBlockId,
		blocks,
		getItemOffset,
		blockHeights,
		updateVisibleRange
	])

	// 图片错误处理函数 - 使用 useCallback 缓存，避免每次渲染都重新创建
	const handleImageError = useCallback((e: React.SyntheticEvent<HTMLImageElement, Event>) => {
		const target = e.target as HTMLImageElement
		// 如果已经是缺省图，就不再替换，避免无限循环
		if (target.dataset.fallback === 'true') {
			return
		}
		target.style.display = 'none'
	}, [])

	// 使用 useMemo 缓存 components 对象，避免每次渲染都重新创建
	// 必须在所有早期返回之前调用，遵守 React Hooks 规则
	const markdownComponents = useMemo(
		() => ({
			img: ({ src, alt, width, height, ...props }: any) => {
				return (
					<img
						src={src}
						alt={alt || '图片'}
						className='max-w-full h-auto rounded-lg my-4 mx-auto block'
						style={{
							width: 'auto',
							height: 'auto',
							maxWidth: '100%'
						}}
						{...props}
						onError={handleImageError}
					/>
				)
			},
			div: ({ children, style, className, ...props }: any) => {
				// 处理包含图片的 div，确保样式和类名正确应用
				return (
					<div style={style} className={className} {...props}>
						{children}
					</div>
				)
			}
		}),
		[handleImageError]
	)


	if (!blocks || blocks.length === 0) {
		return (
			<div className='flex items-center justify-center h-full text-muted-foreground'>
				<p>暂无解析内容</p>
			</div>
		)
	}


	return (
		<div ref={markdownRef} className='h-full overflow-y-auto p-6 markdown-body'>
			<div
				className='max-w-3xl mx-auto relative'
				style={{ height: totalHeight }}
			>
				{blocks.map((block, index) => {
					if (!block.id) return null

					const [startIndex, endIndex] = visibleRange
					const isInRange = index >= startIndex && index <= endIndex

					const isHovered = hoveredBlockId === block.id
					const isSelected = clickedPdfBlockId === block.id
					const isActive = isHovered || isSelected

					// 判断是否为图片块
					const isImage = block.isImage || false

					// 如果不在可见范围内，渲染占位符
					if (!isInRange) {
						const height = blockHeights[index] || VIRTUAL_CONFIG.DEFAULT_BLOCK_HEIGHT
						return (
							<div
								key={block.id}
								data-block-id={block.id}
								className={`px-2 my-2! relative ${isActive ? 'bg-yellow-200/80 dark:bg-yellow-900/70' : 'bg-gray-50/50'}`}
								style={{ minHeight: height }}
							/>
						)
					}

					// 渲染实际块
					return (
						<div
							key={block.id}
							ref={(el) => {
								if (el) {
									// 块渲染后更新高度
									setTimeout(() => handleBlockRenderSuccess(index, el), 0)
								}
							}}
							data-block-id={block.id}
							className={`
								px-2 my-2! transition-all duration-300 relative
								${isActive ? 'bg-yellow-200/80 dark:bg-yellow-900/70 shadow-md' : 'bg-card'}
								${isImage ? 'cursor-default' : 'cursor-pointer'}
							`}
							onMouseEnter={() => {
								setHoveredBlockId(block.id)
								setShowCopyButton(true)
							}}
							onMouseLeave={() => {
								setHoveredBlockId(null)
								// setPageNumber(null)
								setShowCopyButton(false)
							}}
							onClick={() => {
								setClickedBlockId(block.id)
								setShowCopyButton(true)
							}}>
							<div className='prose prose-sm dark:prose-invert max-w-none'>
								<ReactMarkdown
									remarkPlugins={[remarkMath]}
									rehypePlugins={[rehypeRaw, rehypeMathInHtml, [rehypeKatex, katexOptions]]}
									components={markdownComponents}>
									{block.content}
								</ReactMarkdown>
							</div>
							{showCopyButton && isActive && (
								<CopyButton content={block.content} />
							)}
						</div>
					)
				})}
			</div>
		</div>
	)
}
