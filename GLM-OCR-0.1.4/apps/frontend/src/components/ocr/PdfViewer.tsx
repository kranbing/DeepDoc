// PdfViewerCanvasOnly.tsx
import { ChevronLeft, ChevronRight, RotateCcw, ZoomIn, ZoomOut } from 'lucide-react';
import React, { useMemo, useState, useRef, useEffect, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { usePdfNavigation } from '@/hooks/usePdfNavigation';
import { usePdfZoom } from '@/hooks/usePdfZoom';

import 'react-pdf/dist/Page/AnnotationLayer.css';
// import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = `https://registry.npmmirror.com/pdfjs-dist/${pdfjs.version}/files/build/pdf.worker.min.mjs`



interface PdfViewerProps {
    file: File | null;
    className?: string;
    renderPageOverlay?: (pageNumber: number) => React.ReactNode;
    onPageClick?: (e: React.MouseEvent<HTMLDivElement>, pageNumber: number) => void;
    onPageMouseMove?: (e: React.MouseEvent<HTMLDivElement>, pageNumber: number) => void;
    onPageMouseLeave?: (e: React.MouseEvent<HTMLDivElement>, pageNumber: number) => void;
}

// 虚拟渲染配置
const VIRTUAL_CONFIG = {
    BUFFER_PAGES: 2, // 视口前后各渲染的缓冲页数
    PLACEHOLDER_HEIGHT: 842, // A4 页面默认高度（像素），后续根据实际页面高度动态调整
};

const PdfViewerCanvasOnly: React.FC<PdfViewerProps> = ({
    file = null,
    className = '',
    renderPageOverlay,
    onPageClick,
    onPageMouseMove,
    onPageMouseLeave,
}) => {
    const [numPages, setNumPages] = useState<number>(0);
    // 虚拟渲染相关状态
    const [visibleRange, setVisibleRange] = useState<[number, number]>([1, 1]);
    const [pageHeights, setPageHeights] = useState<Record<number, number>>({});
    const [viewportHeight, setViewportHeight] = useState<number>(0);

    const pageRefs = useRef<(HTMLDivElement | null)[]>([]); // 每个页面的 ref
    const scrollContainerRef = useRef<HTMLDivElement | null>(null);
    const resizeObserverRef = useRef<ResizeObserver | null>(null);

    const documentOptions = useMemo(
        () => ({
            cMapUrl: `https://registry.npmmirror.com/pdfjs-dist/${pdfjs.version}/files/cmaps/`,
            cMapPacked: true,
        }),
        []
    );

    // 使用 PDF 缩放 hook
    const { scale, zoomIn, zoomOut, resetZoom, setAutoScale, isInitialScaleSetRef } = usePdfZoom();

    // 计算页面的累计高度（用于占位）- 考虑缩放
    const getPageOffset = useCallback((pageNumber: number): number => {
        let offset = 20; // 容器 padding
        for (let i = 1; i < pageNumber; i++) {
            const pageHeight = (pageHeights[i] || VIRTUAL_CONFIG.PLACEHOLDER_HEIGHT) * scale;
            offset += pageHeight + 20; // 缩放后的页面高度 + mb-5 间距
        }
        return offset;
    }, [pageHeights, scale]);

    // 使用 PDF 导航 hook
    const { currentPage, inputValue, setInputValue, setCurrentPage, prevPage, nextPage, isProgrammaticScrollRef, lastProgrammaticPageRef } = usePdfNavigation({ numPages, getPageOffset, scrollContainerRef });

    const onDocumentLoadSuccess = async ({ numPages }: { numPages: number }) => {
        setNumPages(numPages);
        setCurrentPage(1);
        setInputValue('1');
        pageRefs.current = new Array(numPages).fill(null); // 初始化 refs 数组

        // 使用默认值初始化页面高度
        const initialHeights: Record<number, number> = {};
        for (let i = 1; i <= numPages; i++) {
            initialHeights[i] = VIRTUAL_CONFIG.PLACEHOLDER_HEIGHT;
        }
        setPageHeights(initialHeights);

        // 计算自适应的初始缩放比例
        const container = scrollContainerRef.current;
        if (container && !isInitialScaleSetRef.current) {
            // 等待一帧以确保容器尺寸正确
            await new Promise(resolve => requestAnimationFrame(resolve));

            const containerWidth = container.clientWidth - 32; // 减去 padding
            const containerHeight = container.clientHeight - 32;

            // A4 默认尺寸: 595 x 842 点
            const defaultPageWidth = 595;
            const defaultPageHeight = 842;

            // 计算宽度和高度的缩放比例
            const scaleByWidth = containerWidth / defaultPageWidth;
            const scaleByHeight = containerHeight / defaultPageHeight;

            // 使用较小的缩放比例，确保页面能完全显示
            const autoScale = Math.min(scaleByWidth, scaleByHeight, 1.5); // 最大不超过1.5倍

            setAutoScale(autoScale);
        }
    };

    // 计算总高度 - 考虑缩放
    const totalHeight = useMemo(() => {
        let height = 0;
        for (let i = 1; i <= numPages; i++) {
            height += (pageHeights[i] || VIRTUAL_CONFIG.PLACEHOLDER_HEIGHT) * scale;
        }
        // 添加页面之间的间距（最后一个页面不需要底部间距）
        height += (numPages > 0 ? (numPages - 1) * 20 : 0);
        return height;
    }, [numPages, pageHeights, scale]);

    // 根据滚动位置计算可见页面范围
    const calculateVisibleRange = useCallback(() => {
        if (!scrollContainerRef.current || viewportHeight === 0) {
            return [1, 1];
        }

        const scrollTop = scrollContainerRef.current.scrollTop;
        const { BUFFER_PAGES } = VIRTUAL_CONFIG;

        // 找到第一个部分可见的页面
        let startPage = 1;
        for (let i = 1; i <= numPages; i++) {
            const pageOffset = getPageOffset(i);
            const pageHeight = (pageHeights[i] || VIRTUAL_CONFIG.PLACEHOLDER_HEIGHT) * scale;
            const pageBottom = pageOffset + pageHeight;

            if (pageBottom > scrollTop) {
                startPage = i;
                break;
            }
        }

        // 找到最后一个部分可见的页面
        const viewportBottom = scrollTop + viewportHeight;
        let endPage = numPages;
        for (let i = startPage; i <= numPages; i++) {
            const pageOffset = getPageOffset(i);
            const pageHeight = (pageHeights[i] || VIRTUAL_CONFIG.PLACEHOLDER_HEIGHT) * scale;
            if (pageOffset + pageHeight >= viewportBottom) {
                endPage = i;
                break;
            }
        }

        // 添加缓冲区
        startPage = Math.max(1, startPage - BUFFER_PAGES);
        endPage = Math.min(numPages, endPage + BUFFER_PAGES);

        return [startPage, endPage];
    }, [viewportHeight, numPages, pageHeights, scale, getPageOffset]);

    // 更新可见范围
    const updateVisibleRange = useCallback(() => {
        const [start, end] = calculateVisibleRange();
        setVisibleRange([start, end]);
    }, [calculateVisibleRange]);

    // 页面加载完成时更新高度
    const handlePageRenderSuccess = useCallback((pageNumber: number, pageElement: HTMLDivElement) => {
        // 获取实际渲染高度（已包含scale），需要除以scale得到原始高度
        const renderedHeight = pageElement.offsetHeight;
        const originalHeight = renderedHeight / scale;

        // 更新内部状态（存储原始高度）
        setPageHeights(prev => {
            if (prev[pageNumber] !== originalHeight) {
                return { ...prev, [pageNumber]: originalHeight };
            }
            return prev;
        });
    }, [scale]);

    // 监听滚动
    useEffect(() => {
        const handleScroll = () => {
            // 如果是程序触发的滚动，直接使用目标页码，不重新计算
            if (isProgrammaticScrollRef.current) {
                const targetPage = lastProgrammaticPageRef.current;
                if (targetPage !== currentPage) {
                    setCurrentPage(targetPage);
                    setInputValue(targetPage.toString());
                }
                updateVisibleRange();
                return;
            }

            // 更新当前页码
            let visiblePage = 1;
            pageRefs.current.forEach((ref, idx) => {
                if (ref) {
                    const rect = ref.getBoundingClientRect();
                    if (rect.top <= 100 && rect.bottom >= 100) {
                        visiblePage = idx + 1;
                    }
                }
            });
            if (visiblePage !== currentPage) {
                setCurrentPage(visiblePage);
                setInputValue(visiblePage.toString());
            }

            // 更新可见范围
            updateVisibleRange();
        };

        const container = scrollContainerRef.current;
        container?.addEventListener('scroll', handleScroll);
        return () => container?.removeEventListener('scroll', handleScroll);
    }, [numPages, currentPage, pageHeights, scale, updateVisibleRange]);

    // 监听容器尺寸变化
    useEffect(() => {
        const container = scrollContainerRef.current;
        if (!container) return;

        const updateHeight = () => {
            setViewportHeight(container.clientHeight);
            updateVisibleRange();
        };

        updateHeight();

        resizeObserverRef.current = new ResizeObserver(() => {
            updateHeight();
        });
        resizeObserverRef.current.observe(container);

        return () => {
            resizeObserverRef.current?.disconnect();
            resizeObserverRef.current = null;
        };
    }, [updateVisibleRange]);

    // 监听缩放变化，更新可见范围
    useEffect(() => {
        updateVisibleRange();
    }, [scale, updateVisibleRange]);


    // 渲染页面组件
    const renderPage = (pageNumber: number) => {
        const height = pageHeights[pageNumber] || VIRTUAL_CONFIG.PLACEHOLDER_HEIGHT;

        return (
            <div
                key={`page_${pageNumber}`}
                ref={(el) => {
                    pageRefs.current[pageNumber - 1] = el;
                    if (el) {
                        // 页面渲染后更新高度
                        setTimeout(() => handlePageRenderSuccess(pageNumber, el), 0);
                    }
                }}
                className={`relative shadow-md bg-white mb-5 mx-auto`}
                style={{ minHeight: numPages > 1 ? height * scale : 'auto', width: 'fit-content' }}
                data-pdf-page={pageNumber}
                data-pdf-visible
                onClick={onPageClick ? (e) => onPageClick(e, pageNumber) : undefined}
                onMouseMove={onPageMouseMove ? (e) => onPageMouseMove(e, pageNumber) : undefined}
                onMouseLeave={onPageMouseLeave ? (e) => onPageMouseLeave(e, pageNumber) : undefined}
            >
                <Page
                    pageNumber={pageNumber}
                    scale={scale}
                    renderTextLayer={false}
                    renderAnnotationLayer={false}
                    onRenderError={(error) => console.error(`Page ${pageNumber} render error:`, error)}
                />
                {renderPageOverlay ? renderPageOverlay(pageNumber) : null}
            </div>
        );
    };

    // 渲染占位符
    const renderPlaceholder = (pageNumber: number) => {
        const height = pageHeights[pageNumber] || VIRTUAL_CONFIG.PLACEHOLDER_HEIGHT;

        return (
            <div
                key={`placeholder_${pageNumber}`}
                data-pdf-page={pageNumber}
                className={`relative w-full mb-5`}
                style={{ minHeight: height * scale }}
            >
            </div>
        );
    };

    const [startPage, endPage] = visibleRange;

    return (
        <div className={`pdf-viewer flex flex-col h-full overflow-hidden ${className}`}>
            {/* 工具栏：缩放 + 翻页 */}
            <div className="toolbar bg-white border-b p-2 grid grid-cols-2 xl:grid-cols-3 gap-4 sticky top-0 z-10">
                <div className='hidden xl:block text-nowrap truncate'>{file?.name || 'PDF 文件预览'}</div>
                <div className="flex items-center justify-center gap-3">

                    <button
                        onClick={prevPage}
                        disabled={currentPage <= 1}
                        className="size-6 cursor-pointer"
                    >
                        <ChevronLeft size={20} strokeWidth={1} />
                    </button>
                    <div className="flex items-center gap-1">

                        <input
                            type="number"
                            min={1}
                            max={numPages}
                            value={inputValue}
                            onChange={(e) => {
                                setInputValue(e.target.value);
                            }}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    e.currentTarget.blur();
                                }
                            }}
                            className="w-12 border rounded-sm text-center"
                        />
                        <span className="text-sm text-gray-500">/</span>
                        <span className="text-sm text-gray-500">{numPages || '?'}</span>
                    </div>

                    <button
                        onClick={nextPage}
                        disabled={currentPage >= numPages}
                        className="size-6 cursor-pointer"
                    >
                        <ChevronRight size={20} strokeWidth={1} />
                    </button>

                </div>

                <div className="flex items-center justify-end gap-3">
                    <button onClick={zoomOut} className="size-6 cursor-pointer">
                        <ZoomOut size={20} strokeWidth={1} />
                    </button>
                    <span className="text-sm text-gray-500 w-10 text-center">{Math.round(scale * 100)}%</span>
                    <button onClick={zoomIn} className="size-6 cursor-pointer">
                        <ZoomIn size={20} strokeWidth={1} />
                    </button>
                    <button onClick={resetZoom} className="size-6 cursor-pointer">
                        <RotateCcw size={18} strokeWidth={1} />
                    </button>
                </div>
            </div>

            {/* 滚动容器 - 虚拟渲染 */}
            <div ref={scrollContainerRef} className="flex-1 overflow-auto bg-gray-50 p-4 pdf-scroll-container relative">
                <Document
                    file={file}
                    options={documentOptions}
                    onLoadSuccess={onDocumentLoadSuccess}
                    loading={<div className="text-center py-20 text-gray-500">正在加载 PDF...</div>}
                    error={<div className="text-red-600 text-center py-20">PDF 加载失败，请检查文件</div>}
                >
                    {numPages > 0 && (
                        <div
                            className="relative min-w-full flex flex-col items-center overflow-x-auto overflow-y-hidden"
                            style={{ height: Math.round(totalHeight) }}
                        >
                            {Array.from({ length: numPages }, (_, index) => {
                                const pageNumber = index + 1;
                                if (pageNumber >= startPage && pageNumber <= endPage) {
                                    return renderPage(pageNumber);
                                }
                                return renderPlaceholder(pageNumber);
                            })}
                        </div>
                    )}
                </Document>
            </div>
        </div>
    );
};

export default PdfViewerCanvasOnly;
